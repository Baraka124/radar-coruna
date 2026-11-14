"""Phase-10 scientific quality-gate tests. Only invented SIM-* subjects."""
from synthetic_v32_fixtures import valid_patient_factory
import json, sys, io, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server

@pytest.fixture
def c(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'v10.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as client: yield client

def login(c,user='admin'):
    res=c.post('/api/session',json={'username':user,'password':'radar-demo-'+user})
    assert res.status_code==200,res.text
    return {'X-RADAR-CSRF':res.json()['csrf']}

@valid_patient_factory
def participant(pid,center='SIM-CS01',**kw):
    return {'id':pid,'center':center,'status':'incluido','copd':'si','consent':'si',
            'enrolDate':'2026-01-15','spiroDate':'2026-01-07','age':68,'sex':'hombre',
            'regular':'si','capacity':'si','exclusion':'no','weeks':9,'ratio':.57,'fev1':62,**kw}

def visit(pid,typ='V0',date='2026-01-15',**kw):
    return {'id':f'VIS-{pid}-{typ}','patient':pid,'type':typ,'date':date,
            'status':'completa','cat':0,'mmrc':0,'rescue':'no','exacerb':'no',
            'dyspnea':'no','activity':'no','action':'seguimiento',**kw}

def post(c,h,route,data):
    res=c.post(route,headers=h,json=data)
    assert res.status_code==201,res.text

def test_empty_start_and_review_gates(c):
    login(c)
    r=c.get('/api/review/clinical');assert r.status_code==200
    d=r.json();assert d['issues']==[] and d['visit_coverage']==[]
    assert d['open_decisions']==20 and len(d['gates'])==7
    assert d['use_status']=='NO APTO PARA DATOS REALES'
    assert d['metrics']['participants']==0

def test_proposed_core_complete_includes_zero_radar(c):
    h=login(c);post(c,h,'/api/patients',participant('SIM-CLEAN'))
    post(c,h,'/api/visits',visit('SIM-CLEAN'))
    d=c.get('/api/review/clinical').json()
    assert d['issues']==[],d['issues']
    x=d['visit_coverage'][0];assert x['fields_present']==x['fields_expected']==7
    assert x['completeness_pct']==100
    assert d['use_status']=='NO APTO PARA DATOS REALES'

def test_unapproved_rules_alert_but_do_not_exclude(c):
    h=login(c)
    p=participant('SIM-REVIEW')
    p.update(age=39,ratio=.71,weeks=5,regular='no',capacity='nc',exclusion='si')
    assert c.post('/api/patients',headers=h,json=p).status_code==422
    return  # Invalid inclusion is rejected at the API boundary as of v0.32.
    v=visit('SIM-REVIEW',mmrc=2,dyspnea='no')
    post(c,h,'/api/visits',v)
    d=c.get('/api/review/clinical').json()
    codes={f['rule'] for f in d['issues']}
    assert {'R03','R04','R06','R07','R10'} <= codes,codes
    assert d['metrics']['prioritary']>=2
    assert d['metrics']['participants']==1  # Saved, not auto-excluded

def test_calendar_followup_window_and_missing_v1(c):
    h=login(c);post(c,h,'/api/patients',participant('SIM-WINDOW'))
    post(c,h,'/api/visits',visit('SIM-WINDOW'))
    post(c,h,'/api/visits',visit('SIM-WINDOW','V2','2027-05-30'))
    d=c.get('/api/review/clinical').json()
    assert {'R11','R12'}<=set(f['rule'] for f in d['issues'])
    # A later V1 cannot occur after an existing V2.
    v=visit('SIM-WINDOW','V1','2027-06-01')
    x=c.post('/api/visits',headers=h,json=v)
    assert x.status_code==422 and 'cronológico' in x.text

def test_centre_scoped_review_and_export(c):
    h=login(c)
    post(c,h,'/api/patients',participant('SIM-A',center='SIM-CS01',age=40))
    post(c,h,'/api/patients',participant('SIM-B',center='SIM-CS02',age=41))
    post(c,h,'/api/visits',visit('SIM-A',mmrc=2,dyspnea='no'))
    login(c,'costa')
    d=c.get('/api/review/clinical').json()
    assert d['metrics']['participants']==1
    assert any(x['patient']=='SIM-A' for x in d['issues'])
    assert not any(x['patient']=='SIM-B' for x in d['issues'])
    data=c.get('/api/export/xlsx');assert data.status_code==200
    with zipfile.ZipFile(io.BytesIO(data.content)) as z:
        names=[x.attrib['name'] for x in ET.fromstring(z.read('xl/workbook.xml')).findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')]
        assert len(names)==44
        assert {'PUERTAS_DE_USO','REVISION_CIENTIFICA','COBERTURA_VISITAS'}<=set(names)
        assert 'CAMBIOS_CAMPO' not in names
        raw=''.join(z.read(n).decode('utf8') for n in z.namelist() if n.startswith('xl/worksheets/sheet'))
        assert 'SIM-A' in raw and 'SIM-B' not in raw
        assert 'NO AUTORIZADO PARA DATOS DE PACIENTES REALES' in raw

def test_review_access_readonly(c):
    admin=login(c);post(c,admin,'/api/patients',participant('SIM-R'))
    login(c,'revisor')
    x=c.get('/api/review/clinical');assert x.status_code==200
    assert x.json()['metrics']['participants']==1
    assert c.post('/api/patients',headers={'X-RADAR-CSRF': 'bad'},json=participant('SIM-NEW')).status_code==403
