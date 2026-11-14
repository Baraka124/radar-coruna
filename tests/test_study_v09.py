"""Architecture and v0.9 CRD tests using only fictional records."""
import io,json,sys,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from synthetic_v32_fixtures import valid_record

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'clean.sqlite3')
    with TestClient(server.app) as c:yield c

def auth(c,who='admin'):
    x=c.post('/api/session',json={'username':who,'password':'radar-demo-'+who})
    assert x.status_code==200,x.text
    return {'X-RADAR-CSRF':x.json()['csrf']}

def enroll(c,heads,pid='SIM-9001',centre='SIM-CS01'):
    assert c.post('/api/patients',headers=heads,json=valid_record({'id':pid,'center':centre,'status':'incluido','consent':'si','copd':'si','enrolDate':'2026-04-01','spiroDate':'2026-03-15'})).status_code==201
    assert c.post('/api/visits',headers=heads,json={'id':'VIS-'+pid,'patient':pid,'type':'V0','date':'2026-04-01','status':'parcial'}).status_code==201

def test_empty_default_and_catalogue(client):
    auth(client)
    assert client.get('/api/state').json()['patients']==[]
    x=client.get('/api/study/specification'); assert x.status_code==200
    j=x.json(); assert len(j['variables'])==107 and len(j['decisions'])==20
    assert any(v['code']=='comorb_ihd' and v['visit_scope']==['V0'] for v in j['variables'])
    assert all(v['approved'] is False for v in j['variables'])
    assert len(client.get('/api/study/observations').json())==0

def test_crd_save_correction_and_audit(client):
    h=auth(client);enroll(client,h)
    path='/api/study/observations/SIM-9001/V0'
    body={'observations':{'comorb_ihd':'no','adherence_level':'buena'},'revisions':{}}
    r=client.put(path,headers=h,json=body);assert r.status_code==200,r.text
    assert r.json()['changed']==2
    rows=client.get('/api/study/observations').json(); assert len(rows)==2
    old=next(x for x in rows if x['variable_code']=='comorb_ihd')
    assert old['rev']==1 and old['value']=='no'
    # A correction cannot erase history without a reason.
    body={'observations':{'comorb_ihd':'si'},'revisions':{'comorb_ihd':1}}
    assert client.put(path,headers=h,json=body).status_code==422
    body['reason']='Revisión verificada de la documentación'
    assert client.put(path,headers=h,json=body).status_code==200
    assert client.put(path,headers=h,json=body).status_code==409
    rows=client.get('/api/audit/changes').json()
    assert any(r['field_name']=='comorb_ihd' and r['prior_value']=='"no"' and r['new_value']=='"si"' for r in rows)

def test_roles_scopes_visit_rules_and_invalid_choices(client):
    admin=auth(client)
    enroll(client,admin,'SIM-9001','SIM-CS01')
    enroll(client,admin,'SIM-9002','SIM-CS02')
    client.put('/api/study/observations/SIM-9002/V0',headers=admin,json={'observations':{'comorb_ihd':'si'}})
    coast=auth(client,'costa')
    assert client.put('/api/study/observations/SIM-9002/V0',headers=coast,json={'observations':{'comorb_ihd':'no'}}).status_code==403
    assert client.put('/api/study/observations/SIM-9001/V1',headers=coast,json={'observations':{'adherence_level':'buena'}}).status_code==422
    assert client.put('/api/study/observations/SIM-9001/V0',headers=coast,json={'observations':{'comorb_ihd':'maybe'}}).status_code==422
    assert client.put('/api/study/observations/SIM-9001/V1',headers=coast,json={'observations':{'comorb_ihd':'si'}}).status_code==422
    assert client.get('/api/study/observations').json()==[]
    review=auth(client,'revisor')
    assert client.put('/api/study/observations/SIM-9001/V0',headers=review,json={'observations':{'comorb_ihd':'no'}}).status_code==403
    assert len(client.get('/api/study/observations').json())==1

def test_export_includes_architecture_even_no_data(client):
    auth(client)
    b=client.get('/api/export/xlsx');assert b.status_code==200,b.text[:200]
    with zipfile.ZipFile(io.BytesIO(b.content)) as z:
        assert z.testzip() is None
        root=ET.fromstring(z.read('xl/workbook.xml'))
        names=[node.attrib['name'] for node in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')]
        assert len(names)==46,names
        assert {'CRD_MEDICIONES','CATALOGO_107','DECISIONES_20','CAMBIOS_CAMPO'}<=set(names)
        data=' '.join(z.read(name).decode('utf8') for name in z.namelist() if name.startswith('xl/worksheets/sheet'))
        assert 'comorb_ihd' in data and 'RADAR' in data
        assert 'Sin acordar' in data

def test_excel_includes_saved_observations_without_cross_center_leak(client):
    h=auth(client)
    enroll(client,h,'SIM-9001','SIM-CS01');enroll(client,h,'SIM-9002','SIM-CS02')
    for i in (1,2):
        pid=f'SIM-900{i}'
        x=client.put('/api/study/observations/'+pid+'/V0',headers=h,json={'observations':{'comorb_ihd':'si' if i==1 else 'no'}})
        assert x.status_code==200,x.text
    coast=auth(client,'costa')
    export=client.get('/api/export/xlsx');assert export.status_code==200
    with zipfile.ZipFile(io.BytesIO(export.content)) as z:
        b=' '.join(z.read(name).decode('utf8') for name in z.namelist() if name.startswith('xl/worksheets/sheet'))
        assert 'SIM-9001' in b and 'SIM-9002' not in b
        workbook=ET.fromstring(z.read('xl/workbook.xml'))
        names=[e.attrib['name'] for e in workbook.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')]
        assert 'CAMBIOS_CAMPO' not in names and len(names)==44
