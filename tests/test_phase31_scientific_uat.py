"""Phase 5 scientific UAT safeguards, ALL examples synthetic and non-decisory."""
from __future__ import annotations

import io
import json
import sqlite3
import sys
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from scientific_preflight import evaluate_participant, aggregate
from scripts.phase5_readonly_audit import inspect_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'scientific_uat_31.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        yield c


def auth(c, who='admin'):
    r=c.post('/api/session',json={'username':who,'password':f'radar-demo-{who}'})
    assert r.status_code==200,r.text
    return {'X-RADAR-CSRF':r.json()['csrf']}


def patient(pid='SIM-UAT31',**kwargs):
    base={'id':pid,'center':'SIM-CS01','status':'incluido','copd':'si',
          'regular':'si','lastCopdReviewDate':'2025-09-12','weeks':4,'capacity':'ayuda','activeExacerb':'no',
          'exclusion':'no','alternativeDiagnosis':'no','seriousDecompensation':'no','interferingTrial':'no',
          'consent':'si','consentDate':'2026-01-05','enrolDate':'2026-01-10',
          'spiroDate':'2025-12-10','ratio':0.59,'birthDate':'1960-02-12',
          'eligibilityDecision':'elegible'}
    return {**base,**kwargs}


def insert(c,h,p):
    r=c.post('/api/patients',headers=h,json=p)
    assert r.status_code==201,r.text


def visit(pid='SIM-UAT31',typ='V0',day='2026-01-10',**kw):
    return {'id':'SIM-V31-'+typ,'patient':pid,'type':typ,'date':day,'status':'parcial',**kw}


def codes(p,v=None,level=None):
    return {r['code'] for r in evaluate_participant(p,v)['findings'] if level is None or r['level']==level}


def test_four_week_stability_is_resolved_and_three_weeks_rejected(client):
    h=auth(client)
    insert(client,h,patient())
    r=client.post('/api/patients',headers=h,json=patient('SIM-TOO-EARLY',weeks=3))
    assert r.status_code==422
    saved=next(p for p in client.get('/api/state').json()['patients'] if p['id']=='SIM-UAT31')
    assert 'ESTABILIDAD_4_SEMANAS' not in codes(saved)


def test_age_and_ratio_are_scientific_acceptance_gaps_not_silently_approved(client):
    h=auth(client)
    assert client.post('/api/patients',headers=h,json=patient('SIM-AGE38',birthDate='1987-06-01')).status_code==422
    assert client.post('/api/patients',headers=h,json=patient('SIM-RATIO75',ratio=0.75)).status_code==422
    # v0.32 rejects both at the API boundary, instead of only flagging them afterward.


def test_unknown_not_equivalent_to_satisfied_eligibility():
    p=patient(regular='',capacity='',activeExacerb='',alternativeDiagnosis='',
              seriousDecompensation='',interferingTrial='',consentDate='',ratio=None,
              birthDate='',age=None,eligibilityDecision='pendiente')
    found=codes(p)
    for key in ('SEGUIMIENTO_AP','CAPACIDAD','AGUDIZACION_ACTIVA','R017','R019','R020',
                'R022','FEV1_FVC','EDAD','R023'):
        assert key in found,key
    assert not any(x['level']=='bloqueo' and x['code']=='FEV1_FVC' for x in evaluate_participant(p)['findings'])


def test_no_automatic_approval_even_for_complete_synthetic_fields():
    result=evaluate_participant(patient())
    assert result['stage']=='incluido'
    assert 'VISITA_AP_ANO_PREVIO' not in {x['code'] for x in result['findings']}
    assert 'autorizado' not in result['conclusion'].lower()
    assert aggregate([patient()],[])['structural_limits']


def test_visit_windows_are_flagged_without_rewriting_dates(client):
    h=auth(client)
    insert(client,h,patient())
    for t,day in [('V0','2026-01-10'),('V1','2026-10-10'),('V2','2027-01-10')]:
        res=client.post('/api/visits',headers=h,json=visit(typ=t,day=day))
        assert res.status_code==201,(t,res.text)
    state=client.get('/api/state').json()
    p=next(p for p in state['patients'] if p['id']=='SIM-UAT31')
    assert 'V1_VENTANA' in codes(p,state['visits'])
    assert 'V2_VENTANA' not in codes(p,state['visits'])
    assert next(v['date'] for v in state['visits'] if v['type']=='V1')=='2026-10-10'


def test_multicentre_scope_and_reviewer_read_only(client):
    h=auth(client)
    insert(client,h,patient('SIM-COAST'))
    insert(client,h,patient('SIM-INLAND',center='SIM-CS02'))
    auth(client,'costa')
    state=client.get('/api/state').json()
    assert {x['id'] for x in state['patients']}=={'SIM-COAST'}
    assert client.get('/api/study/participant-journey/SIM-INLAND').status_code==403
    assert client.get('/api/study/participant-journey/SIM-COAST').status_code==200
    auth(client,'revisor')
    state=client.get('/api/state').json()
    assert {x['id'] for x in state['patients']}=={'SIM-COAST','SIM-INLAND'}
    assert client.post('/api/patients',json=patient('SIM-CANNOT-WRITE'),headers={'X-RADAR-CSRF':auth(client,'revisor')['X-RADAR-CSRF']}).status_code==403


def test_scoped_excel_and_version_still_work(client):
    h=auth(client)
    insert(client,h,patient('SIM-COAST'))
    insert(client,h,patient('SIM-INLAND',center='SIM-CS02'))
    assert client.get('/api/health').json()['version']==server.app.version
    auth(client,'costa')
    wb=client.get('/api/export/xlsx')
    assert wb.status_code==200
    with zipfile.ZipFile(io.BytesIO(wb.content)) as z:
        assert z.testzip() is None
        xml=b'\n'.join(z.read(name) for name in z.namelist() if name.startswith('xl/worksheets/sheet'))
    assert b'SIM-COAST' in xml and b'SIM-INLAND' not in xml


def test_readonly_cli_is_non_mutating_and_rejects_non_synthetic(client,tmp_path):
    h=auth(client)
    insert(client,h,patient())
    db=Path(server.DB_FILE)
    before=db.read_bytes()
    r=inspect_db(db)
    assert r['participants']==1 and r['included']==1
    assert db.read_bytes()==before
    with sqlite3.connect(db) as c:
        d=patient('SIM-TEMP')
        d['id']='NOT-SYNTHETIC'
        c.execute('INSERT INTO patients VALUES (?,?,?,?,?,?)',
                  ('NOT-SYNTHETIC','SIM-CS01',json.dumps(d),1,'uat','2026-11-12'))
    with pytest.raises(ValueError,match='no sintético'):
        inspect_db(db)
