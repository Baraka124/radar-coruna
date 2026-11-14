"""XLSX export: scope, integrity, formulas, auditable metadata. Synthetic data only."""
import io
import pathlib
import sys
import zipfile
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import server

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('RADAR_SEED_DEMO','1')
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'isolated.xlsx.test.sqlite')
    with TestClient(server.app) as c:
        yield c

def signin(c,user):
    passwords={'admin':'radar-demo-admin','costa':'radar-demo-costa','interior':'radar-demo-interior','revisor':'radar-demo-revisor'}
    r=c.post('/api/session',json={'username':user,'password':passwords[user]})
    assert r.status_code==200
    return {'X-RADAR-CSRF':r.json()['csrf']}

def xml_text(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        assert z.testzip() is None
        paths=[f for f in z.namelist() if f.startswith('xl/') and f.endswith('.xml')]
        return '\n'.join(z.read(p).decode('utf-8') for p in paths)

def test_export_login_scope_excel_and_audit(client):
    assert client.get('/api/export/xlsx').status_code==401
    signin(client,'costa')
    r=client.get('/api/export/xlsx')
    assert r.status_code==200,r.text[:250]
    assert r.content.startswith(b'PK')
    assert 'spreadsheetml.sheet' in r.headers['content-type']
    assert 'attachment' in r.headers['content-disposition']
    txt=xml_text(r.content)
    assert 'PARTICIPANTES' in txt and 'VISITAS' in txt and 'DICCIONARIO' in txt
    assert 'name="TRAZABILIDAD"' not in txt  # reserved for admin
    assert 'SIM-001' in txt
    assert 'SIM-002' not in txt and 'SIM-003' not in txt
    assert 'SUM(' not in txt  # score uses explicit 3-2-2-1 entries
    assert 'IF(' in txt
    # Exports are themselves audited.
    signin(client,'admin')
    r2=client.get('/api/export/xlsx')
    txt2=xml_text(r2.content)
    assert 'name="TRAZABILIDAD"' in txt2
    assert 'SIM-002' in txt2
    logs=client.get('/api/audit').json()
    assert any(x['verb']=='EXPORT' and x['kind']=='xlsx' for x in logs)

def test_xlsx_formulas_and_missing_scores(client):
    signin(client,'admin')
    r=client.get('/api/export/xlsx')
    txt=xml_text(r.content)
    assert 'Sin clasificar' in txt
    assert 'Buen control' in txt
    assert 'RADAR' in txt


def test_excel_is_read_only_for_reviewer(client):
    signin(client,'revisor')
    r=client.get('/api/export/xlsx')
    assert r.status_code==200
    assert 'PARTICIPANTES' in xml_text(r.content)
    assert client.post('/api/patients',json={}).status_code==403
