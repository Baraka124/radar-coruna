from synthetic_v32_fixtures import valid_patient_factory
from urllib.parse import quote
import copy
import pathlib
import sys
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import server

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('RADAR_SEED_DEMO','1')
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'test.sqlite3')
    with TestClient(server.app) as c:
        yield c

def signin(c,username='admin'):
    password={'admin':'radar-demo-admin','costa':'radar-demo-costa','interior':'radar-demo-interior','revisor':'radar-demo-revisor'}[username]
    r=c.post('/api/session',json={'username':username,'password':password})
    assert r.status_code==200,r.text
    return {'X-RADAR-CSRF':r.json()['csrf']}

@valid_patient_factory
def patient(id='SIM-T001',center='SIM-CS01',status='incluido'):
    d={'id':id,'center':center,'age':65,'copd':'si','consent':'si','status':status,'enrolDate':'2026-01-01','spiroDate':'2025-12-01'}
    return d

def visit(id='VIS-SIM-T001',pid='SIM-T001',type='V0',**kw):
    d={'id':id,'patient':pid,'type':type,'date':'2026-01-01','cat':10,'mmrc':1,'rescue':'no','exacerb':'no','dyspnea':'no','activity':'no','action':'seguimiento','status':'completa'}
    d.update(kw)
    return d

def test_requires_login(client):
    assert client.get('/api/state').status_code==401
    assert client.post('/api/patients',json=patient()).status_code==401
    assert client.post('/api/session',json={'username':'admin','password':'bad'}).status_code==401

def test_csrf_guard(client):
    signin(client)
    assert client.post('/api/patients',json=patient()).status_code==403

def test_synthetic_only(client):
    h=signin(client)
    assert client.post('/api/patients',headers=h,json={**patient(),'id':'CLINICAL-NHC'}).status_code==422
    assert client.post('/api/patients',headers=h,json={**patient(),'name':'Some Name'}).status_code==422

def test_create_persist_and_revision(client):
    h=signin(client)
    assert client.post('/api/patients',headers=h,json=patient()).status_code==201
    r=client.get('/api/state').json()
    p=next(x for x in r['patients'] if x['id']=='SIM-T001')
    assert p['rev']==1
    assert client.put('/api/patients/SIM-T001',headers={**h,'X-RADAR-CHANGE-REASON':quote('Corrección verificada en simulación')},json={**p,'birthDate':'1960-01-01'}).status_code==200
    assert client.put('/api/patients/SIM-T001',headers={**h,'X-RADAR-CHANGE-REASON':quote('Revisión realizada por investigador')},json={**p,'birthDate':'1959-01-01'}).status_code==409
    assert next(x for x in client.get('/api/state').json()['patients'] if x['id']=='SIM-T001')['age']==66

def test_centre_isolation_and_read_only(client):
    h=signin(client,'costa')
    s=client.get('/api/state').json()
    assert s['patients'] and all(x['center']=='SIM-CS01' for x in s['patients'])
    assert client.post('/api/patients',headers=h,json=patient('SIM-T002','SIM-CS02')).status_code==403
    assert client.post('/api/patients',headers=h,json=patient('SIM-T003','SIM-CS01')).status_code==201
    h=signin(client,'interior')
    assert all(x['center']=='SIM-CS02' for x in client.get('/api/state').json()['patients'])
    assert client.post('/api/visits',headers=h,json=visit(pid='SIM-T003')).status_code==403
    h=signin(client,'revisor')
    assert client.post('/api/patients',headers=h,json=patient('SIM-T004')).status_code==403
    assert client.get('/api/audit').status_code==403

def test_visit_workflow_and_missing_radar(client):
    h=signin(client)
    assert client.post('/api/patients',headers=h,json=patient()).status_code==201
    assert client.post('/api/visits',headers=h,json=visit('V1-early','SIM-T001','V1',date='2026-07-01')).status_code==422
    assert client.post('/api/visits',headers=h,json=visit('VIS-T001','SIM-T001','V0')).status_code==201
    assert client.post('/api/visits',headers=h,json=visit('VIS-T002','SIM-T001','V1',date='2026-07-01')).status_code==201
    assert client.post('/api/visits',headers=h,json=visit('VIS-T003','SIM-T001','V1',date='2026-07-05')).status_code==409
    assert client.post('/api/visits',headers=h,json=visit('VIS-T004','SIM-T001','V2',date='2027-01-02',rescue='')).status_code==422
    assert server.score({'rescue':'no','exacerb':'no','dyspnea':'no','activity':''}) is None
    assert server.score({'rescue':'si','exacerb':'no','dyspnea':'no','activity':'no'})==3
    assert server.score({'rescue':'si','exacerb':'si','dyspnea':'si','activity':'si'})==8

def test_events_and_links(client):
    h=signin(client)
    client.post('/api/patients',headers=h,json=patient())
    episode={'id':'EPI-TEST','patient':'SIM-T001','date':'2026-03-15','severity':'moderada','copd':'si','steroids':'si','source':'hce'}
    assert client.post('/api/episodes',headers=h,json=episode).status_code==201
    assert client.post('/api/episodes',headers=h,json={**episode,'id':'EPI-TEST2'}).status_code==409
    contact={'id':'CON-TEST','patient':'SIM-T001','event':'EPI-TEST','date':'2026-03-15','type':'urgencias','copd':'si','source':'hce'}
    assert client.post('/api/contacts',headers=h,json=contact).status_code==201
    assert client.get('/api/state').json()['contacts'][-1]['event']=='EPI-TEST'

def test_audit_survives_reload(client):
    h=signin(client)
    client.post('/api/patients',headers=h,json=patient())
    items=client.get('/api/audit').json()
    assert any(x['kind']=='patient' and x['object_id']=='SIM-T001' for x in items)
    assert client.get('/api/health').json()['environment']=='local_demo'

def test_logout(client):
    h=signin(client)
    assert client.post('/api/logout',headers=h,json={}).status_code==200
    assert client.get('/api/state').status_code==401
