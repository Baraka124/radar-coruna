"""Operational hardening v0.40; uses synthetic temporary databases only."""
from __future__ import annotations
import json
import os
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from operational_v40 import load_runtime, staging_instance_lock
from backup_manager import backup,verify,restore_new

ORIGIN='https://synthetic-radar.example.test'
SECRET='OnlySynthetic-Staging-Admin-2026!'


def env_stage(monkeypatch,tmp_path):
    db=tmp_path/'vol'/'radar.sqlite3'
    monkeypatch.setattr(server,'DB_FILE',db)
    for k,v in {
        'RADAR_MODE':'synthetic_staging','RADAR_DB':str(db),
        'RADAR_PERSISTENT_DATA_DIR':str(db.parent),
        'RADAR_PUBLIC_ORIGIN':ORIGIN,
        'RADAR_BOOTSTRAP_ADMIN_USER':'radar.admin',
        'RADAR_BOOTSTRAP_ADMIN_PASSWORD':SECRET,
        'RADAR_WORKERS':'1', 'RADAR_SEED_DEMO':'0'
    }.items():monkeypatch.setenv(k,v)
    return db


def stage_client():
    return TestClient(server.app,base_url=ORIGIN)


def stage_signin(c,user='radar.admin',password=SECRET):
    result=c.post('/api/session',json={'username':user,'password':password},headers={'Origin':ORIGIN})
    assert result.status_code==200,result.text
    return {'X-RADAR-CSRF':result.json()['csrf'],'Origin':ORIGIN}


def test_remote_startup_requires_explicit_https_volume_and_non_demo_secret(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'stage.sqlite3')
    monkeypatch.setenv('RADAR_MODE','synthetic_staging')
    monkeypatch.delenv('RADAR_PUBLIC_ORIGIN',raising=False)
    with pytest.raises(RuntimeError,match='RADAR_PUBLIC_ORIGIN'):
        with stage_client():pass
    assert not (tmp_path/'stage.sqlite3').exists()
    env_stage(monkeypatch,tmp_path)
    monkeypatch.setenv('RADAR_PUBLIC_ORIGIN','http://synthetic-radar.example.test')
    with pytest.raises(RuntimeError,match='RADAR_PUBLIC_ORIGIN'):
        with stage_client():pass
    monkeypatch.setenv('RADAR_PUBLIC_ORIGIN',ORIGIN)
    monkeypatch.setenv('RADAR_BOOTSTRAP_ADMIN_PASSWORD','radar-demo-admin')
    with pytest.raises(RuntimeError,match='RADAR_BOOTSTRAP_ADMIN_PASSWORD'):
        with stage_client():pass


def test_staging_secure_cookie_origin_health_bootstrap_and_sessions(tmp_path,monkeypatch):
    db=env_stage(monkeypatch,tmp_path)
    with stage_client() as c:
        assert c.get('/api/health').json()['environment']=='synthetic_staging'
        assert c.get('/api/ready').json()['storage']=='sqlite-single-instance'
        assert c.get('/api/ready',headers={'Host':'healthcheck.railway.app'}).status_code==200
        assert c.get('/api/state',headers={'Host':'healthcheck.railway.app'}).status_code==403
        assert c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'},headers={'Origin':ORIGIN}).status_code==401
        assert c.post('/api/session',json={'username':'radar.admin','password':SECRET}).status_code==403
        assert c.post('/api/session',json={'username':'radar.admin','password':SECRET},headers={'Origin':'https://evil.test'}).status_code==403
        h=stage_signin(c)
        assert c.get('/api/state').json()['user']['role']=='admin'
        cookies=c.cookies.get('radar_session')
        assert cookies
        # HTTPS flag + HttpOnly; never store bearer tokens in SQLite.
        r=c.post('/api/session',json={'username':'radar.admin','password':SECRET},headers={'Origin':ORIGIN})
        cookie=r.headers.get('set-cookie','')
        assert 'Secure' in cookie and 'HttpOnly' in cookie and 'SameSite=strict' in cookie
        assert c.post('/api/collaboration/invitations',json={'centre':'SIM-CS01','role':'reviewer'},headers={'Origin':ORIGIN}).status_code==403
        assert c.post('/api/collaboration/invitations',json={'centre':'SIM-CS01','role':'reviewer'},headers={'X-RADAR-CSRF':r.json()['csrf'],'Origin':ORIGIN}).status_code==201
        assert c.get('/api/state',headers={'host':'bad.example.test'}).status_code==403
        assert c.get('/api/ready').headers['strict-transport-security'].startswith('max-age=')
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT count(*) FROM users WHERE username='admin'").fetchone()[0]==0
        assert con.execute("SELECT count(*) FROM users WHERE username='radar.admin'").fetchone()[0]==1


def test_stage_refuses_known_demo_accounts(tmp_path,monkeypatch):
    db=env_stage(monkeypatch,tmp_path)
    monkeypatch.setenv('RADAR_MODE','local_demo')
    server.init_db()
    monkeypatch.setenv('RADAR_MODE','synthetic_staging')
    with pytest.raises(RuntimeError,match='credenciales demo'):
        with stage_client():pass
    assert db.exists()


def test_login_throttling_commits_and_resets(tmp_path,monkeypatch):
    env_stage(monkeypatch,tmp_path)
    with stage_client() as c:
        for _ in range(server.AUTH_MAX_FAILURES):
            assert c.post('/api/session',json={'username':'radar.admin','password':'bad'},headers={'Origin':ORIGIN}).status_code==401
        assert c.post('/api/session',json={'username':'radar.admin','password':SECRET},headers={'Origin':ORIGIN}).status_code==429
        with server.conn() as con:
            con.execute('UPDATE auth_attempts SET window_start=window_start-1000')
        stage_signin(c)
        with server.conn() as con:
            assert con.execute('SELECT count(*) FROM auth_attempts').fetchone()[0]==0


def test_staging_invitation_centre_isolation_and_suspension(tmp_path,monkeypatch):
    env_stage(monkeypatch,tmp_path)
    with stage_client() as c:
        h=stage_signin(c)
        inv=c.post('/api/collaboration/invitations',json={'centre':'SIM-CS01','role':'investigator'},headers=h).json()
        assert inv['token']
        accepted=c.post('/api/collaboration/accept',json={'token':inv['token'],'username':'investigator.one','password':'Strong-Researcher-2026-1'},headers={'Origin':ORIGIN})
        assert accepted.status_code==201,accepted.text
        assert c.post('/api/collaboration/accept',json={'token':inv['token'],'username':'investigator.two','password':'Strong-Researcher-2026-2'},headers={'Origin':ORIGIN}).status_code==410
        who=stage_signin(c,'investigator.one','Strong-Researcher-2026-1')
        assert c.get('/api/collaboration').json()['centres'][0]['code']=='SIM-CS01'
        assert c.get('/api/study/participant-journey/SIM-002').status_code in (403,404)
        assert c.get('/api/export/xlsx').status_code==200
        # Restore admin context; revoke user and invalidate session.
        stage_signin(c)
        with server.conn() as con:
            uid=con.execute("SELECT id FROM users WHERE username='investigator.one'").fetchone()[0]
        assert c.patch(f'/api/collaboration/accounts/{uid}',json={'active':False},headers={'Origin':ORIGIN, 'X-RADAR-CSRF':c.get('/api/session').json()['csrf']}).status_code==200
        assert c.post('/api/session',json={'username':'investigator.one','password':'Strong-Researcher-2026-1'},headers={'Origin':ORIGIN}).status_code==401


def test_concurrent_independent_scoped_reads_and_verified_restore(tmp_path,monkeypatch):
    db=env_stage(monkeypatch,tmp_path)
    with stage_client() as admin:
        h=stage_signin(admin)
        invited=[]
        for centre,person in [('SIM-CS01','test.costa'),('SIM-CS02','test.interior')]:
            inv=admin.post('/api/collaboration/invitations',headers=h,json={'centre':centre,'role':'investigator'}).json()
            r=admin.post('/api/collaboration/accept',headers={'Origin':ORIGIN},json={'token':inv['token'],'username':person,'password':'Valid-Researcher-2026-1'})
            assert r.status_code==201,r.text
            invited.append(person)
        def run(person):
            # Requests share the ONE running ASGI instance. A separate TestClient
            # lifespan would correctly be rejected by the single-instance lock.
            c=stage_client()
            try:
                stage_signin(c,person,'Valid-Researcher-2026-1')
                for i in range(4):
                    r=c.get('/api/study/intelligence')
                    if r.status_code!=200:return (person,r.status_code)
                    assert all(x['centre']==('SIM-CS01' if person=='test.costa' else 'SIM-CS02') for x in r.json()['centres'])
                return (person,200)
            finally:
                c.close()
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(run,invited*6))
        assert all(code==200 for _,code in results),results
        out,manifest=backup(db,tmp_path/'backups')
        assert verify(manifest)['verified']
        restored=tmp_path/'restored'/'study.sqlite3'
        assert restore_new(manifest,restored)['integrity']=='ok'
        with sqlite3.connect(restored) as con:
            assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert con.execute('SELECT count(*) FROM users').fetchone()[0]==3
        out.write_bytes(out.read_bytes()+b'corruption')
        with pytest.raises(ValueError,match='hash'):
            verify(manifest)


def test_staging_only_one_lockholder_on_same_host(tmp_path,monkeypatch):
    db=env_stage(monkeypatch,tmp_path)
    runtime=load_runtime(db)
    with staging_instance_lock(runtime):
        with pytest.raises(RuntimeError,match='Ya hay una instancia'):
            with staging_instance_lock(runtime):pass


def test_concurrent_centre_writes_and_stale_edit_conflict(tmp_path,monkeypatch):
    """Single-instance staging: both centres can write, but stale cross-session edits conflict."""
    env_stage(monkeypatch,tmp_path)
    with stage_client() as admin:
        admin_headers=stage_signin(admin)
        people=[('SIM-CS01','write.costa'),('SIM-CS02','write.interior')]
        for centre,username in people:
            inv=admin.post('/api/collaboration/invitations',headers=admin_headers,
                           json={'centre':centre,'role':'investigator'}).json()
            res=admin.post('/api/collaboration/accept',headers={'Origin':ORIGIN},
                  json={'token':inv['token'],'username':username,'password':'Valid-Researcher-2026-1'})
            assert res.status_code==201,res.text
        tasks=[(people[i%2][1],people[i%2][0],i) for i in range(10)]
        def create_one(task):
            username,centre,i=task
            c=stage_client()
            try:
                headers=stage_signin(c,username,'Valid-Researcher-2026-1')
                response=c.post('/api/patients',headers=headers,
                                json={'id':f'SIM-W40{i:02d}','center':centre,'status':'cribado'})
                return response.status_code
            finally:c.close()
        with ThreadPoolExecutor(max_workers=6) as pool:
            assert list(pool.map(create_one,tasks))==[201]*10
        admin_headers=stage_signin(admin)
        state=admin.get('/api/state').json()
        assert len(state['patients'])==10
        assert len([x for x in state['audit'] if x['action']=='CREATE' and x['object']=='patient'])==10
        original=next(p for p in state['patients'] if p['center']=='SIM-CS01')
        own_client=stage_client()
        try:
            own_headers=stage_signin(own_client,'write.costa','Valid-Researcher-2026-1')
            def modify(client,headers,smoking):
                return client.put('/api/patients/'+original['id'],headers={**headers,'X-RADAR-CHANGE-REASON':'Revision simultanea simulada'},
                                  json={**original,'smoking':smoking}).status_code
            with ThreadPoolExecutor(max_workers=2) as pool:
                f1=pool.submit(modify,admin,admin_headers,'actual')
                f2=pool.submit(modify,own_client,own_headers,'ex')
                assert sorted([f1.result(),f2.result()])==[200,409]
            assert own_client.get('/api/state').json()['patients']
            # An investigator in centre 1 never sees centre 2 participants.
            assert all(x['center']=='SIM-CS01' for x in own_client.get('/api/state').json()['patients'])
        finally:
            own_client.close()
