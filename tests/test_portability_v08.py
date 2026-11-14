"""v0.8 portability, XLSX cache, safe local access, and verified backup tests."""
import io
import json
import sqlite3
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from backup_manager import backup,restore_new,verify

N={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('RADAR_SEED_DEMO','1')
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'pilot.sqlite3')
    with TestClient(server.app) as c:yield c


def auth(c,name='admin'):
    r=c.post('/api/session',json={'username':name,'password':f'radar-demo-{name}'})
    assert r.status_code==200,r.text
    return {'X-RADAR-CSRF':r.json()['csrf']}


def parse_xlsx(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        assert z.testzip() is None
        for key in z.namelist():
            if key.endswith(('.xml','.rels')):ET.fromstring(z.read(key))
        book=ET.fromstring(z.read('xl/workbook.xml'))
        names=[e.attrib['name'] for e in book.findall('.//s:sheet',N)]
        return {name:ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml')) for i,name in enumerate(names,1)}


def excel_cell(root,coordinate):
    return root.find(f'.//s:c[@r="{coordinate}"]',N)


def cached(cell):
    v=cell.find('s:v',N)
    return None if v is None else v.text


def test_excel_portable_structure_and_zero_score(client):
    auth(client)
    r=client.get('/api/export/xlsx')
    assert r.status_code==200,r.text[:250]
    sheets=parse_xlsx(r.content)
    assert len(sheets)==46
    assert 'CAMBIOS_CAMPO' in sheets and 'TRAZABILIDAD' in sheets
    assert sheets['VISITAS'].find('s:autoFilter',N) is not None
    # Synthetic VIS-S004 is the fourth visit and has a complete four-item zero score.
    v=sheets['VISITAS']
    assert cached(excel_cell(v,'M11'))=='0'
    assert cached(excel_cell(v,'N11'))=='Buen control'
    assert 'IF(' in excel_cell(v,'M11').find('s:f',N).text
    assert cached(excel_cell(sheets['RESUMEN'],'B7'))=='3'
    assert cached(excel_cell(sheets['RESUMEN'],'B12'))=='4'


def test_nonadmin_excel_has_only_centre_data(client):
    auth(client,'costa')
    blob=client.get('/api/export/xlsx').content
    sheets=parse_xlsx(blob)
    assert len(sheets)==44  # v0.39 adds five analytical worksheets to the centre-scoped workbook
    assert 'CAMBIOS_CAMPO' not in sheets
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        combined=' '.join(z.read(k).decode() for k in z.namelist() if k.startswith('xl/worksheets/'))
    assert 'SIM-001' in combined and 'SIM-002' not in combined


def test_off_site_and_host_spoofing_rejected(client):
    assert client.get('/api/health',headers={'host':'example.org'}).status_code==403
    # Reaching localhost from a remote peer must also be rejected.
    from starlette.requests import Request
    class DummyResponse:
        pass
    async def ok(_):return DummyResponse()
    import asyncio
    async def remote():
        scope={'type':'http','method':'GET','headers':[(b'host',b'127.0.0.1')],
               'scheme':'http','server':('127.0.0.1',8878),'client':('203.0.113.7',5555),'path':'/api/health','root_path':'','query_string':b''}
        return await server.security_headers(Request(scope),ok)
    response=asyncio.run(remote())
    assert response.status_code==403


def test_backup_verification_restore_to_fresh_file(client,tmp_path):
    auth(client)
    source=server.DB_FILE
    backups=tmp_path/'backups'
    snapshot,manifest=backup(source,backups)
    expected=verify(manifest)
    assert expected['verified'] and expected['rows']['patients']==3
    fresh=tmp_path/'recovered'/'restored.sqlite3'
    result=restore_new(manifest,fresh)
    assert result['integrity']=='ok' and fresh.is_file()
    with sqlite3.connect(fresh) as c:
        assert c.execute('SELECT count(*) FROM audit').fetchone()[0]>=0
        assert c.execute('SELECT count(*) FROM visits').fetchone()[0]==4
    with pytest.raises(FileExistsError):restore_new(manifest,fresh)
    # Corruption is detected before a restore can happen.
    with snapshot.open('ab') as w:w.write(b'CORRUPT')
    with pytest.raises(ValueError,match='SHA-256'):verify(manifest)


def test_xlsx_text_remains_text_not_formula():
    from export_research import create_excel_snapshot
    fake={'id':'SIM-X','center':'SIM-CS01','status':'cribado','smoking':'=2+2'}
    binary=create_excel_snapshot(patients=[fake],visits=[],episodes=[],contacts=[],audit=[],centres=[],user={'role':'investigator','centre':'SIM-CS01'})
    sheet=parse_xlsx(binary)['PARTICIPANTES']
    c=excel_cell(sheet,'M8')
    assert c.attrib['t']=='inlineStr'
    assert c.find('s:f',N)is None
    assert "'=2+2" in ET.tostring(c,encoding='unicode')
