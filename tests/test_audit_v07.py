from urllib.parse import quote
"""Regression tests for field-level audit, correction reasons and permission scope.
All identities and clinical values are fictional.
"""
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('RADAR_SEED_DEMO','1')
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'audit.sqlite3')
    with TestClient(server.app) as c:yield c

def login(client,user='admin'):
    pw={'admin':'radar-demo-admin','costa':'radar-demo-costa','interior':'radar-demo-interior','revisor':'radar-demo-revisor'}[user]
    response=client.post('/api/session',json={'username':user,'password':pw})
    assert response.status_code==200
    return {'X-RADAR-CSRF':response.json()['csrf']}

def test_audit_field_values_and_corrector(client):
    h=login(client)
    p=next(x for x in client.get('/api/state').json()['patients'] if x['id']=='SIM-001')
    data={**p,'birthDate':'1956-04-02','age':99,'packs':0,'smoking':'nunca'}
    assert client.put('/api/patients/SIM-001',json=data,headers=h).status_code==422
    assert client.put('/api/patients/SIM-001',json=data,headers={**h,'X-RADAR-CHANGE-REASON':quote('short')}).status_code==422
    reason='Corrección de registro en prueba sintética'
    r=client.put('/api/patients/SIM-001',json=data,headers={**h,'X-RADAR-CHANGE-REASON':quote(reason)})
    assert r.status_code==200,r.text
    logs=client.get('/api/audit').json()
    a=next(x for x in logs if x['kind']=='patient' and x['verb']=='UPDATE' and x['object_id']=='SIM-001')
    assert a['revision_from']==1 and a['revision_to']==2
    assert a['field_count']==4 and a['reason']==reason and len(a['record_digest'])==64
    rows=[x for x in client.get('/api/audit/changes').json() if x['audit_id']==a['id']]
    assert len(rows)==4
    by_name={x['field_name']:x for x in rows}
    assert by_name['age']['prior_value']=='68' and by_name['age']['new_value']=='69'
    assert by_name['birthDate']['new_value']=='"1956-04-02"'
    assert by_name['packs']['prior_value']=='35.0' and by_name['packs']['new_value']=='0.0'
    assert by_name['smoking']['new_value']=='"nunca"'
    # A no-op does not create a new version or a misleading change event.
    new=next(x for x in client.get('/api/state').json()['patients'] if x['id']=='SIM-001')
    r=client.put('/api/patients/SIM-001',json=new,headers={**h,'X-RADAR-CHANGE-REASON':quote('Revisión de calidad sin modificaciones')})
    assert r.status_code==200 and r.json().get('unchanged') is True
    assert r.json()['rev']==2

def test_centre_roles_and_visit_changes(client):
    h=login(client,'costa')
    s=client.get('/api/state').json()
    visit=next(x for x in s['visits'] if x['id']=='VIS-S001')
    changed={**visit,'cat':11,'rescue':'no'}
    r=client.put('/api/visits/VIS-S001',json=changed,headers={**h,'X-RADAR-CHANGE-REASON':quote('Revisión de respuestas originales')})
    assert r.status_code==200,r.text
    assert client.get('/api/audit/changes').status_code==403
    assert client.get('/api/audit').status_code==403
    h=login(client,'interior')
    assert client.put('/api/visits/VIS-S001',json={**changed,'rev':2},headers={**h,'X-RADAR-CHANGE-REASON':quote('Intento de cambio en otro centro')}).status_code==403
    h=login(client,'revisor')
    assert client.get('/api/audit/changes').status_code==403
    h=login(client,'admin')
    rows=client.get('/api/audit/changes').json()
    assert {r['field_name'] for r in rows if r['object_id']=='VIS-S001'}=={'cat','rescue'}
    assert all(r['participant_id']=='SIM-001' for r in rows if r['object_id']=='VIS-S001')

def test_export_uses_audit_tables(client):
    import zipfile,io
    h=login(client)
    p=next(x for x in client.get('/api/state').json()['patients'] if x['id']=='SIM-001')
    assert client.put('/api/patients/SIM-001',json={**p,'birthDate':'1955-04-02'},headers={**h,'X-RADAR-CHANGE-REASON':quote('Corrección de campo para exportación')}).status_code==200
    r=client.get('/api/export/xlsx')
    assert r.status_code==200,r.text[:300]
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        assert z.testzip() is None
        xml='\n'.join(z.read(f).decode() for f in z.namelist() if f.startswith('xl/') and f.endswith('.xml'))
    for word in ('CAMBIOS_CAMPO','TRAZABILIDAD','revision','Corrección de campo para exportación','SIM-001','age'):
        assert word.lower() in xml.lower()
    login(client,'costa')
    with zipfile.ZipFile(io.BytesIO(client.get('/api/export/xlsx').content)) as z:
        xml='\n'.join(z.read(f).decode() for f in z.namelist() if f.startswith('xl/') and f.endswith('.xml'))
    assert 'name="CAMBIOS_CAMPO"' not in xml

def test_old_database_migration(tmp_path,monkeypatch):
    import sqlite3
    path=tmp_path/'legacy.sqlite'
    with sqlite3.connect(path) as c:
        c.execute('CREATE TABLE audit(id INTEGER PRIMARY KEY AUTOINCREMENT, happened_at TEXT NOT NULL, username TEXT NOT NULL, role TEXT NOT NULL, centre TEXT, verb TEXT NOT NULL, kind TEXT NOT NULL, object_id TEXT NOT NULL)')
        c.execute('INSERT INTO audit(happened_at,username,role,centre,verb,kind,object_id) VALUES (?,?,?,?,?,?,?)',('2026-01-01T00:00:00+00:00','system','admin',None,'CREATE','patient','SIM-LEGACY'))
    monkeypatch.setenv('RADAR_SEED_DEMO','1')
    monkeypatch.setattr(server,'DB_FILE',path)
    server.init_db()
    server.init_db()  # idempotent
    with sqlite3.connect(path) as c:
        # v0.21 migrates pre-v21 synthetic episodes to stable R074 and audits the change.
        assert c.execute("SELECT count(*) FROM audit WHERE verb='CREATE' AND object_id='SIM-LEGACY'").fetchone()[0]==1
        assert c.execute("SELECT count(*) FROM audit WHERE verb='MIGRATE' AND kind='episode'").fetchone()[0]==1
        columns={r[1] for r in c.execute('PRAGMA table_info(audit)')}
        assert {'reason','field_count','revision_from','record_digest'}<=columns
        # Historical audit remains unchanged; only the numbered episode is assigned R074.
        assert c.execute('SELECT count(*) FROM audit_field_changes').fetchone()[0]==1
