"""Phase 3 regression: editing historical records must preserve longitudinal integrity.

Only fictitious IDs. Existing clinical measurements and methodology are unchanged.
"""
from __future__ import annotations
import pathlib
import sys
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import server


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'phase29.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        yield c


def auth(c, username='admin'):
    r=c.post('/api/session',json={'username':username,'password':'radar-demo-'+username})
    assert r.status_code==200,r.text
    return {'X-RADAR-CSRF':r.json()['csrf']}


def patient(pid='SIM-REGR29', centre='SIM-CS01'):
    return {'id':pid,'center':centre,'copd':'si','consent':'si','status':'incluido',
            'enrolDate':'2026-01-10','spiroDate':'2025-12-10','weeks':5,'birthDate':'1965-03-12',
            'ratio':0.61,'regular':'si','lastCopdReviewDate':'2025-08-10','capacity':'si',
            'activeExacerb':'no','exclusion':'no','alternativeDiagnosis':'no',
            'seriousDecompensation':'no','interferingTrial':'no','consentDate':'2026-01-05',
            'eligibilityDecision':'elegible'}


def change(headers):
    return {**headers,'X-RADAR-CHANGE-REASON':quote('Corrección simulada documentada')}


def setup_patient(c, h, *, include_v0=True):
    assert c.post('/api/patients',headers=h,json=patient()).status_code==201
    if include_v0:
        visit={'id':'SIM-V0-REG29','patient':'SIM-REGR29','type':'V0','date':'2026-01-10',
               'status':'completa','rescue':'no','exacerb':'no','dyspnea':'no',
               'activity':'no','cat':0,'mmrc':0,'action':'seguimiento'}
        assert c.post('/api/visits',headers=h,json=visit).status_code==201


def test_baseline_correction_does_not_invalidate_saved_v0(client):
    h=auth(client)
    setup_patient(client,h)
    before=next(x for x in client.get('/api/state').json()['patients'] if x['id']=='SIM-REGR29')
    history=len(client.get('/api/audit').json())
    response=client.put('/api/patients/SIM-REGR29',json={**before,'enrolDate':'2026-01-11'},headers=change(h))
    assert response.status_code==409,response.text
    after=next(x for x in client.get('/api/state').json()['patients'] if x['id']=='SIM-REGR29')
    assert after['enrolDate']=='2026-01-10' and after['rev']==before['rev']
    assert len(client.get('/api/audit').json())==history
    journey=client.get('/api/study/participant-journey/SIM-REGR29')
    assert journey.status_code==200 and journey.json()['recorded_visits']==1


def test_existing_followup_cannot_be_stranded_by_reverting_to_screening(client):
    h=auth(client)
    setup_patient(client,h)
    before=next(x for x in client.get('/api/state').json()['patients'] if x['id']=='SIM-REGR29')
    response=client.put('/api/patients/SIM-REGR29',json={**before,'status':'cribado'},headers=change(h))
    assert response.status_code==409,response.text
    assert next(x for x in client.get('/api/state').json()['patients'] if x['id']=='SIM-REGR29')['status']=='incluido'


def test_no_history_patient_correction_stays_editable(client):
    h=auth(client)
    setup_patient(client,h,include_v0=False)
    before=next(x for x in client.get('/api/state').json()['patients'] if x['id']=='SIM-REGR29')
    response=client.put('/api/patients/SIM-REGR29',json={**before,'enrolDate':'2026-01-12','age':62},headers=change(h))
    assert response.status_code==200,response.text
    changed=next(x for x in client.get('/api/state').json()['patients'] if x['id']=='SIM-REGR29')
    assert changed['rev']==2 and changed['enrolDate']=='2026-01-12'
    assert client.post('/api/visits',headers=h,json={
        'id':'SIM-V0-REG29','patient':'SIM-REGR29','type':'V0','date':'2026-01-12',
        'status':'completa','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no',
        'cat':0,'mmrc':0,'action':'seguimiento'}).status_code==201


def test_centre_isolation_and_reviewer_stay_enforced(client):
    h=auth(client)
    setup_patient(client,h)
    coast=auth(client,'costa')
    assert client.get('/api/study/participant-journey/SIM-REGR29').status_code==200
    other=auth(client,'interior')
    assert client.get('/api/study/participant-journey/SIM-REGR29').status_code==403
    reviewer=auth(client,'revisor')
    state=client.get('/api/state').json()
    record=next(x for x in state['patients'] if x['id']=='SIM-REGR29')
    assert client.put('/api/patients/SIM-REGR29',json={**record,'age':70},headers=change(reviewer)).status_code==403


def test_export_version_matches_running_application(client):
    h=auth(client)
    assert client.get('/api/health').json()['version']==server.app.version
    assert client.get('/api/state').json()['version']=='.'.join(server.app.version.split('.')[:2])
    r=client.get('/api/export/xlsx')
    assert r.status_code==200 and r.content.startswith(b'PK')
