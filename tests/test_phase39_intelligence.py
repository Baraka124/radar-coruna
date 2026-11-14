"""v0.39 research intelligence — denominator correctness and centre isolation."""
import io
import os
import sys
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from research_intelligence_v39 import make_intelligence,add_months


def person(pid,centre='SIM-CS01', status='incluido',**extra):
    return {'id':pid,'center':centre,'status':status,'birthDate':'1950-01-01','enrolDate':'2026-01-15','ratio':.55,**extra}


def visit(pid,stage='V0',when='2026-01-15',**kwargs):
    d={'patient':pid,'type':stage,'status':'completa','date':when,'rescue':'no','exacerb':'no','dyspnea':'no','activity':'no','cat':14,'mmrc':2}
    d.update(kwargs);return d


def test_empty_snapshot_does_not_invent_denominators():
    d=make_intelligence([],[])
    assert d['counts']['poor_baseline_pct'] is None
    assert d['stages'][0]['radar_coverage_pct'] is None
    assert d['longitudinal']==[] and d['quality']==[]


def test_radar_cat_mmrc_denominators_remain_independent():
    people=[person('SIM-11'),person('SIM-12'),person('SIM-13',status='cribado')]
    visits=[visit('SIM-11'),visit('SIM-12',rescue='',cat=9,mmrc=0)]
    d=make_intelligence(people,visits)
    assert d['counts']['included']==2 and d['counts']['screening']==1
    assert d['stages'][0]['radar_evaluable']==1
    assert d['stages'][0]['cat_evaluable']==2 and d['stages'][0]['mmrc_evaluable']==2
    assert d['stages'][0]['radar_coverage_pct']==50.0
    assert d['stages'][0]['poor_radar_pct']==0.0


def test_paired_cat_does_not_depend_on_radar():
    visits=[visit('SIM-11'),visit('SIM-11','V2','2027-01-12',rescue='',cat=10,mmrc=0)]
    d=make_intelligence([person('SIM-11')],visits)
    assert d['counts']['paired_cat']==1 and d['counts']['paired_mmrc']==1
    assert d['counts']['paired_radar']==0
    row=d['longitudinal'][0]
    assert row['delta_cat_v2_v0']==-4 and row['delta_radar_v2_v0'] is None


def test_no_realizada_is_not_performed_or_classifiable():
    d=make_intelligence([person('SIM-11')],[visit('SIM-11',status='no_realizada',reason='ausencia',cat=None)])
    assert d['stages'][0]['visits_recorded']==1
    assert d['stages'][0]['visits_performed']==0
    assert d['stages'][0]['radar_evaluable']==0
    assert d['stages'][0]['radar_within_performed_pct'] is None


def test_followup_window_is_calendar_aware_and_not_an_overdue_alert():
    assert add_months(date(2026,1,31),1)==date(2026,2,28)
    assert add_months(date(2026,1,31),5)==date(2026,6,30)
    d=make_intelligence([person('SIM-11')],[visit('SIM-11',when='2026-01-31'),visit('SIM-11','V1','2026-09-01')])
    assert sum(r['code']=='VISIT_WINDOW' for r in d['quality'])==1
    assert not any('vencida' in r['message'].lower() for r in d['quality'])


def test_missing_reason_with_existing_value_is_a_conflict():
    d=make_intelligence([person('SIM-11')],[visit('SIM-11')],missing=[{'participant':'SIM-11','visit_type':'V0','field_code':'cat','reason':'no_disponible'}])
    assert len([r for r in d['quality'] if r['code']=='MISSING_CONFLICT'])==1


def test_contact_not_counted_as_new_exacerbation():
    d=make_intelligence([person('SIM-11')],[visit('SIM-11')],
        episodes=[{'patient':'SIM-11','id':'E1','date':'2026-03-01','kind':'agudizacion','copd':'si'}],
        contacts=[{'patient':'SIM-11','event':'E1','type':'urgencias','copd':'si'},
                  {'patient':'SIM-11','event':'E1','type':'ingreso','copd':'si'}])
    assert d['counts']['episode_records']==1 and d['counts']['contact_records']==2


@pytest.fixture
def app_client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'v39.sqlite3')
    monkeypatch.setenv('RADAR_SEED_DEMO','1')
    with TestClient(server.app) as client:yield client


def login(client,user='admin'):
    p={'admin':'radar-demo-admin','costa':'radar-demo-costa','interior':'radar-demo-interior','revisor':'radar-demo-revisor'}[user]
    r=client.post('/api/session',json={'username':user,'password':p})
    assert r.status_code==200,r.text


def test_intelligence_requires_session_and_scopes_centres(app_client):
    c=app_client
    assert c.get('/api/study/intelligence').status_code==401
    login(c,'costa');x=c.get('/api/study/intelligence').json()
    assert x['version']=='0.39'
    assert set(r['centre'] for r in x['centres'])=={'SIM-CS01'}
    assert all(r['centre']=='SIM-CS01' for r in x['longitudinal'])
    assert all(r['centre']=='SIM-CS01' for r in x['quality'])
    login(c,'interior');y=c.get('/api/study/intelligence').json()
    assert set(r['centre'] for r in y['centres'])=={'SIM-CS02'}
    assert all(r['centre']=='SIM-CS02' for r in y['longitudinal'])


def test_csv_allowlist_and_scoped_output(app_client):
    c=app_client;login(c,'costa')
    assert c.get('/api/export/intelligence.csv?table=secrets').status_code==422
    r=c.get('/api/export/intelligence.csv?table=longitudinal')
    assert r.status_code==200 and 'no-store' in r.headers.get('cache-control','')
    assert b'SIM-001' in r.content
    assert b'SIM-002' not in r.content and b'SIM-003' not in r.content
    r=c.get('/api/export/intelligence.csv?table=centres')
    assert b'SIM-CS01' in r.content and b'SIM-CS02' not in r.content


def test_scoped_excel_contains_new_sheets(app_client):
    c=app_client;login(c,'costa')
    r=c.get('/api/export/xlsx')
    assert r.status_code==200,r.text[:300]
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        wb=z.read('xl/workbook.xml').decode('utf-8')
        assert all(f'name="{n}"' in wb for n in ('V39_CENTROS','V39_COBERTURA','V39_LONGITUDINAL','V39_REVISION','V39_METODOS'))
        assert 'V39_CENTROS' in wb and 'V39_METODOS' in wb
        for name in z.namelist():
            if name.startswith('xl/worksheets/') and name.endswith('.xml'):
                sheet=z.read(name)
                ET.fromstring(sheet)
                assert b'SIM-CS02' not in sheet and b'SIM-CS03' not in sheet


def test_reviewer_has_read_only_intelligence(app_client):
    c=app_client;login(c,'revisor')
    assert c.get('/api/study/intelligence').status_code==200
    assert c.get('/api/export/intelligence.csv?table=quality').status_code==200
    assert c.get('/api/state').json()['user']['role']=='reviewer'
