"""v0.38 · Invitation lifecycle and centre-scoped collaboration (synthetic only)."""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import sqlite3
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server

@pytest.fixture
def app_client(tmp_path, monkeypatch):
    monkeypatch.setenv('RADAR_SEED_DEMO','1')
    monkeypatch.setattr(server, 'DB_FILE', tmp_path/'study.sqlite3')
    with TestClient(server.app) as client:
        yield client

def login(client, who='admin', password=None):
    pw=password or {'admin':'radar-demo-admin','costa':'radar-demo-costa','interior':'radar-demo-interior','revisor':'radar-demo-revisor'}[who]
    r=client.post('/api/session',json={'username':who,'password':pw})
    assert r.status_code==200, r.text
    return {'X-RADAR-CSRF':r.json()['csrf']}

def invite(client, headers, centre='SIM-CS02', role='investigator', label='Prueba de centro'):
    r=client.post('/api/collaboration/invitations',headers=headers,json={'centre':centre,'role':role,'label':label})
    assert r.status_code==201,r.text
    return r.json()

def accept(client, token, name='medico.sim', password='Correcto-Test-2026'):
    return client.post('/api/collaboration/accept',json={'token':token,'username':name,'password':password})

def test_admin_centre_summary_and_centre_scoping(app_client):
    client=app_client
    assert client.get('/api/collaboration').status_code==401
    login(client)
    out=client.get('/api/collaboration').json()
    assert len(out['centres'])==3 and 'accounts' in out
    login(client,'costa')
    own=client.get('/api/collaboration').json()
    assert [x['code'] for x in own['centres']]==['SIM-CS01']
    assert 'accounts' not in own and 'invitations' not in own
    assert client.post('/api/collaboration/invitations',json={'centre':'SIM-CS02','role':'reviewer'}).status_code==403

def test_invitation_activation_is_scoped_and_one_use(app_client):
    client=app_client
    h=login(client)
    issued=invite(client,h)
    assert len(issued['token'])>=40 and issued['fragment'].startswith('#invite=')
    status=client.get('/api/collaboration').json()
    assert issued['token'] not in str(status)
    assert any(x['status']=='pendiente' for x in status['invitations'])
    r=accept(client,issued['token'])
    assert r.status_code==201,r.text
    assert r.json()['centre']=='SIM-CS02' and r.json()['role']=='investigator'
    assert accept(client,issued['token'],name='second.med').status_code==410
    assert client.post('/api/session',json={'username':'medico.sim','password':'WrongPassword'}).status_code==401
    h=login(client,'medico.sim','Correcto-Test-2026')
    own=client.get('/api/state').json()
    assert all(p['center']=='SIM-CS02' for p in own['patients'])
    assert client.get('/api/study/participant-journey/SIM-001').status_code==403
    assert client.get('/api/study/worklist').status_code==200
    assert client.get('/api/export/xlsx').status_code==200
    assert client.post('/api/collaboration/invitations',headers=h,json={'centre':'SIM-CS01','role':'investigator'}).status_code==403
    assert client.get('/api/collaboration').json()['centres'][0]['code']=='SIM-CS02'

def test_reviewer_readonly_centre_scope(app_client):
    client=app_client
    issued=invite(client,login(client),centre='SIM-CS01',role='reviewer')
    assert accept(client,issued['token'],name='revisor.costa').status_code==201
    h=login(client,'revisor.costa','Correcto-Test-2026')
    state=client.get('/api/state').json()
    assert state['user']['role']=='reviewer'
    assert len(state['centres'])==1 and state['centres'][0]['code']=='SIM-CS01'
    assert all(x['center']=='SIM-CS01' for x in state['patients'])
    assert client.get('/api/study/participant-journey/SIM-002').status_code==403
    assert client.get('/api/audit').status_code==403
    assert client.post('/api/patients',headers=h,json={**state['patients'][0], 'id':'SIM-R038'}).status_code==403

def test_revoke_expire_and_password_validation(app_client):
    client=app_client
    h=login(client)
    revoked=invite(client,h,centre='SIM-CS01')
    assert client.post(f"/api/collaboration/invitations/{revoked['id']}/revoke",headers=h,json={}).status_code==200
    assert accept(client,revoked['token'],name='revokeduser').status_code==410
    assert client.post(f"/api/collaboration/invitations/{revoked['id']}/revoke",headers=h,json={}).status_code==409
    expired=invite(client,h,centre='SIM-CS03')
    with server.conn() as c:
        c.execute('UPDATE invitations SET expires_at=? WHERE id=?',((datetime.now(timezone.utc)-timedelta(seconds=5)).isoformat(), expired['id']))
    assert accept(client,expired['token'],name='expireduser').status_code==410
    fresh=invite(client,h)
    assert accept(client,fresh['token'],name='badpass',password='short').status_code==422
    assert accept(client,fresh['token'],name='Admin',password='Correcto-Test-2026').status_code==422
    assert accept(client,fresh['token'],name='admin',password='Correcto-Test-2026').status_code==409
    assert accept(client,fresh['token'],name='gooduser').status_code==201

def test_account_deactivation_revokes_sessions_and_activation(app_client):
    client=app_client
    invite_data=invite(client,login(client),centre='SIM-CS02')
    assert accept(client,invite_data['token'],name='test.persona').status_code==201
    investigator_session=login(client,'test.persona','Correcto-Test-2026')
    assert client.get('/api/state').status_code==200
    admin_session=login(client)
    accounts=client.get('/api/collaboration').json()['accounts']
    account_id=next(x['id'] for x in accounts if x['username']=='test.persona')
    admin_id=next(x['id'] for x in accounts if x['username']=='admin')
    assert client.patch('/api/collaboration/accounts/'+str(admin_id),headers=admin_session,json={'active':False}).status_code==409
    assert client.patch('/api/collaboration/accounts/'+str(account_id),headers=admin_session,json={'active':False}).status_code==200
    assert client.post('/api/session',json={'username':'test.persona','password':'Correcto-Test-2026'}).status_code==401
    assert client.patch('/api/collaboration/accounts/'+str(account_id),headers=admin_session,json={'active':True}).status_code==200
    assert login(client,'test.persona','Correcto-Test-2026')

def test_centre_investigator_cannot_change_account_lifecycle(app_client):
    client=app_client
    h=login(client,'interior')
    assert client.get('/api/collaboration').status_code==200
    assert client.patch('/api/collaboration/accounts/1',headers=h,json={'active':False}).status_code==403
    assert client.post('/api/collaboration/invitations/1/revoke',headers=h,json={}).status_code==403

def test_token_not_accepted_with_cross_origin_header(app_client):
    client=app_client
    data=invite(client,login(client))
    bad=client.post('/api/collaboration/accept',json={'token':data['token'],'username':'safeuser','password':'Correcto-Test-2026'},headers={'Origin':'https://attacker.invalid'})
    assert bad.status_code==403
    assert accept(client,data['token'],name='safeuser').status_code==201

def test_parallel_sessions_never_share_centre_scope(app_client):
    from fastapi.testclient import TestClient
    client_a=TestClient(server.app)
    client_b=TestClient(server.app)
    login(client_a,'costa')
    login(client_b,'interior')
    for _ in range(3):
        assert [x['code'] for x in client_a.get('/api/collaboration').json()['centres']]==['SIM-CS01']
        assert [x['code'] for x in client_b.get('/api/collaboration').json()['centres']]==['SIM-CS02']
        assert {x['center'] for x in client_a.get('/api/state').json()['patients']}=={'SIM-CS01'}
        assert {x['center'] for x in client_b.get('/api/state').json()['patients']}=={'SIM-CS02'}
    client_a.close();client_b.close()


def test_excel_export_excludes_other_centre_metadata(app_client):
    import io,zipfile
    client=app_client
    login(client,'interior')
    result=client.get('/api/export/xlsx')
    assert result.status_code==200
    with zipfile.ZipFile(io.BytesIO(result.content)) as z:
        xml=b' '.join(z.read(n) for n in z.namelist() if n.endswith('.xml'))
        assert b'SIM-CS02' in xml
        assert b'SIM-CS01' not in xml
        assert b'SIM-CS03' not in xml
