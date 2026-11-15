"""RADAR v0.45: centre registration is persisted and never inferred from fixtures."""
import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from phase14_completion import valid_key


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    monkeypatch.setenv('RADAR_MODE', 'local_demo')
    monkeypatch.delenv('RADAR_SEED_DEMO', raising=False)
    monkeypatch.setattr(server, 'POSTGRES_MODE', False)
    monkeypatch.setattr(server, 'DB_FILE', tmp_path / 'radar_v45.sqlite3')
    with TestClient(server.app) as client:
        yield client


def login(client, username='admin', password='radar-demo-admin'):
    resp = client.post('/api/session', json={'username':username,'password':password})
    assert resp.status_code == 200, resp.text
    return {'X-RADAR-CSRF':resp.json()['csrf']}


def register(client, auth, code='GAL_AP_01', name='Centro registrado por administrador'):
    return client.post('/api/centres',headers=auth,json={'code':code,'name':name})


def test_empty_registry_has_no_fictitious_centres(app_client):
    auth=login(app_client)
    state=app_client.get('/api/state').json()
    assert state['centres']==[] and state['patients']==[]
    collab=app_client.get('/api/collaboration').json()
    assert collab['centres']==[] and collab['centre_registry']==[]
    resp=app_client.post('/api/collaboration/invitations', headers=auth,
        json={'centre':'SIM-CS01','role':'investigator','label':'No automatic centre'})
    assert resp.status_code==422
    resp=app_client.post('/api/patients',headers=auth,
        json={'id':'SIM-EMPTY-01','center':'SIM-CS01'})
    assert resp.status_code==422
    assert app_client.get('/api/state').json()['patients']==[]


def test_registered_centre_is_real_and_visible(app_client):
    auth=login(app_client)
    created=register(app_client,auth)
    assert created.status_code==201, created.text
    assert created.json()['code']=='GAL_AP_01'
    assert register(app_client,auth).status_code==409
    assert app_client.get('/api/state').json()['centres']==[
        {'code':'GAL_AP_01','name':'Centro registrado por administrador','active':True}]
    meta=app_client.get('/api/collaboration').json()
    assert meta['centre_registry']==[{'code':'GAL_AP_01',
        'name':'Centro registrado por administrador','active':True}]
    assert meta['centres'][0]['participants']==0
    renamed=app_client.patch('/api/centres/GAL_AP_01',headers=auth,
        json={'name':'Centro actualizado y persistido'})
    assert renamed.status_code==200, renamed.text
    assert app_client.get('/api/state').json()['centres'][0]['name']=='Centro actualizado y persistido'


def test_invitations_require_actual_centre_and_scope_data(app_client):
    auth=login(app_client)
    assert register(app_client,auth).status_code==201
    invited=app_client.post('/api/collaboration/invitations',headers=auth,
        json={'centre':'GAL_AP_01','role':'investigator','label':'Personal de prueba'})
    assert invited.status_code==201,invited.text
    token=invited.json()['token']
    accepted=app_client.post('/api/collaboration/accept',
        json={'token':token,'username':'medico.registrado',
              'password':'Segura-Sintetica-2026'})
    assert accepted.status_code==201,accepted.text
    assert app_client.post('/api/collaboration/accept',
        json={'token':token,'username':'otro.medico','password':'Otra-Sintetica-2026'}).status_code==410
    auth2=login(app_client,'medico.registrado','Segura-Sintetica-2026')
    state=app_client.get('/api/state').json()
    assert [x['code'] for x in state['centres']]==['GAL_AP_01']
    assert app_client.post('/api/centres',headers=auth2,
        json={'code':'GAL_AP_02','name':'No permitido'}).status_code==403
    patient=app_client.post('/api/patients',headers=auth2,
        json={'id':'SIM-DYNAMIC-01','center':'GAL_AP_01'})
    assert patient.status_code==201,patient.text
    assert [p['id'] for p in app_client.get('/api/state').json()['patients']]==['SIM-DYNAMIC-01']


def test_safe_deactivation_preserves_invites_and_patients(app_client):
    auth=login(app_client)
    assert register(app_client,auth).status_code==201
    invited=app_client.post('/api/collaboration/invitations',headers=auth,
        json={'centre':'GAL_AP_01','role':'reviewer','label':'Pendiente'})
    assert invited.status_code==201,invited.text
    centre='/api/centres/GAL_AP_01'
    assert app_client.patch(centre,headers=auth,json={'active':False}).status_code==409
    inv_id=invited.json()['id']
    assert app_client.post('/api/collaboration/invitations/'+str(inv_id)+'/revoke',
        headers=auth,json={}).status_code==200
    stopped=app_client.patch(centre,headers=auth,json={'active':False})
    assert stopped.status_code==200,stopped.text
    assert app_client.get('/api/state').json()['centres']==[]
    assert app_client.get('/api/collaboration').json()['centre_registry'][0]['active'] is False
    assert app_client.post('/api/collaboration/invitations',headers=auth,
        json={'centre':'GAL_AP_01','role':'investigator'}).status_code==422
    assert app_client.patch(centre,headers=auth,json={'active':True}).status_code==200
    assert app_client.post('/api/patients',headers=auth,
        json={'id':'SIM-RET-01','center':'GAL_AP_01'}).status_code==201
    assert app_client.patch(centre,headers=auth,json={'active':False}).status_code==409


def test_phase14_syntax_no_longer_has_three_centre_ids():
    assert valid_key('centre','GAL_AP_01')
    assert valid_key('implementation','GAL_AP_01:2026-11')
    assert valid_key('centre','SIM-CS01')
    assert not valid_key('centre','bad code')
    assert not valid_key('implementation','GAL_AP_01:2026-13')
