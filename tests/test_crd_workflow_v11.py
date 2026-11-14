"""Phase 11: single visit worklist + research export; all records fictitious."""
from synthetic_v32_fixtures import valid_patient_factory
import io,zipfile,xml.etree.ElementTree as ET
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from crd_workflow import build_workflow,manifest

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'phase11.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:yield c

def login(c,user='admin'):
    r=c.post('/api/session',json={'username':user,'password':'radar-demo-'+user})
    assert r.status_code==200
    return {'X-RADAR-CSRF':r.json()['csrf']}

@valid_patient_factory
def patient(pid,centre='SIM-CS01',smoking='nunca',packs=None):
    return {'id':pid,'center':centre,'status':'incluido','copd':'si','consent':'si','regular':'si',
            'capacity':'si','exclusion':'no','weeks':10,'enrolDate':'2026-01-15','spiroDate':'2025-12-03',
            'age':65,'sex':'mujer','smoking':smoking,'packs':packs,'ratio':.59,'fev1':64,'priorEx':0,'priorHosp':0}

def visit(pid,**extra):
    return {'id':'VIS-'+pid,'patient':pid,'type':'V0','date':'2026-01-15',
            'status':'completa','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no',
            'cat':0,'mmrc':0,'action':'seguimiento',**extra}

def test_workflow_starts_empty_and_definitions_explicit(client):
    login(client)
    d=client.get('/api/study/crd-workflow').json()
    assert d['rows']==[] and d['summary']['no_records']
    assert d['version']=='0.11-draft' and len(d['manifest'])>=30
    assert {x['stage'] for x in d['manifest']}=={'V0','V0/V1/V2'}
    assert all(x['approval'].startswith('Pendiente') for x in d['manifest'])

def test_zero_values_and_smoker_conditional_coverage(client):
    h=login(client)
    for pid,smoking,packs in [('SIM-NEVER','nunca',None),('SIM-SMOKER','actual',None)]:
        r=client.post('/api/patients',headers=h,json=patient(pid,smoking=smoking,packs=packs));assert r.status_code==201,r.text
    assert client.post('/api/visits',headers=h,json=visit('SIM-NEVER')).status_code==201
    d=client.get('/api/study/crd-workflow').json()
    a=next(r for r in d['rows'] if r['patient']=='SIM-NEVER' and r['stage']=='V0')
    b=next(r for r in d['rows'] if r['patient']=='SIM-SMOKER' and r['stage']=='V0')
    assert a['core_pct']==100 and a['baseline_missing']==[],a
    assert b['baseline_missing']==['Paquetes-año (si procede)']
    assert next(r for r in d['rows'] if r['patient']=='SIM-NEVER' and r['stage']=='V1')['core_pct'] is None
    assert d['summary']['core_complete']==1

def test_missing_radar_never_classified_and_missing_adherence_method_alert(client):
    h=login(client)
    assert client.post('/api/patients',headers=h,json=patient('SIM-PARTIAL')).status_code==201
    v=visit('SIM-PARTIAL',rescue='',status='parcial')
    assert client.post('/api/visits',headers=h,json=v).status_code==201
    # CRD observation can be saved only after visit, but does not silently certify the score.
    assert client.put('/api/study/observations/SIM-PARTIAL/V0',headers=h,
        json={'observations':{'adherence_level':'buena'}}).status_code==200
    d=client.get('/api/study/crd-workflow').json()
    v=next(r for r in d['rows'] if r['patient']=='SIM-PARTIAL' and r['stage']=='V0')
    assert v['core_present']==6 and 'RADAR · Medicación de rescate' in v['core_missing']
    assert 'Adherencia consignada sin método documentado' in v['alerts']

def test_center_scope_and_excel_phase11_tables(client):
    h=login(client)
    assert client.post('/api/patients',headers=h,json=patient('SIM-A',centre='SIM-CS01')).status_code==201
    assert client.post('/api/patients',headers=h,json=patient('SIM-B',centre='SIM-CS02')).status_code==201
    login(client,'costa')
    d=client.get('/api/study/crd-workflow').json()
    assert d['summary']['patients']==1 and {r['patient'] for r in d['rows']}=={'SIM-A'}
    res=client.get('/api/export/xlsx');assert res.status_code==200
    with zipfile.ZipFile(io.BytesIO(res.content)) as z:
        assert z.testzip() is None
        names=[e.attrib['name'] for e in ET.fromstring(z.read('xl/workbook.xml')).findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')]
        assert len(names)==44
        assert {'FLUJO_CRD_V11','GUIA_CRD_V11'}<=set(names)
        assert 'TRAZABILIDAD' not in names and 'CAMBIOS_CAMPO' not in names
        sheets=''.join(z.read(n).decode('utf-8') for n in z.namelist() if n.startswith('xl/worksheets/sheet'))
        assert 'SIM-A' in sheets and 'SIM-B' not in sheets
        assert 'NO AUTORIZADO PARA DATOS DE PACIENTES REALES' in sheets

def test_reviewer_cannot_change_workflow(client):
    login(client,'revisor')
    assert client.get('/api/study/crd-workflow').status_code==200
    assert client.post('/api/patients',headers={'X-RADAR-CSRF':'wrong'},json=patient('SIM-NO')).status_code==403
