"""Phase 12 regression: correct denominators, real field coverage, role scope."""
from synthetic_v32_fixtures import valid_patient_factory
import io, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from phase12_analysis import make_analysis, catalogue_coverage

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'phase12.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:yield c

def login(c,user='admin'):
    r=c.post('/api/session',json={'username':user,'password':'radar-demo-'+user})
    assert r.status_code==200,r.text
    return {'X-RADAR-CSRF':r.json()['csrf']}

@valid_patient_factory
def patient(code,centre='SIM-CS01'):
    return {'id':code,'center':centre,'copd':'si','consent':'si','status':'incluido',
      'enrolDate':'2026-01-15','spiroDate':'2025-12-01','age':65,'ratio':0.55}

def visit(code,typ,**overrides):
    return {'id':f'SIMVIS-{code}-{typ}','patient':code,'type':typ,'date':{'V0':'2026-01-15','V2':'2027-01-16'}[typ],
      'status':'completa','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no',
      'cat':0,'mmrc':0,'action':'seguimiento',**overrides}

def metric(data,title):
    return next(x for x in data['metrics'] if x['indicator']==title)

def sheet_names(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        assert z.testzip() is None
        return [x.attrib['name'] for x in ET.fromstring(z.read('xl/workbook.xml')).findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')]

def test_empty_pilot_has_107_coverage_and_no_prevalence(client):
    login(client)
    report=client.get('/api/study/scientific-summary').json()
    assert report['total_variables']==107 and not report['paired']
    assert sum(report['coverage_counts'].values())==107
    assert metric(report,'Mal control basal (RADAR ≥4)')['value'] is None
    assert metric(report,'% visitas EPOC con RADAR')['value'] is None
    assert len(sheet_names(client.get('/api/export/xlsx').content))==46
    assert all(x['status']!='Aprobado' for x in report['coverage'])

def test_complete_zero_and_incomplete_radar_not_merged(client):
    h=login(client)
    for code in ['SIM-ZERO','SIM-MISSING','SIM-POOR']:
        assert client.post('/api/patients',headers=h,json=patient(code)).status_code==201
    assert client.post('/api/visits',headers=h,json=visit('SIM-ZERO','V0')).status_code==201
    missing=visit('SIM-MISSING','V0',status='parcial',rescue='')
    assert client.post('/api/visits',headers=h,json=missing).status_code==201
    poor=visit('SIM-POOR','V0',rescue='si',exacerb='si')
    assert client.post('/api/visits',headers=h,json=poor).status_code==201
    report=client.get('/api/study/scientific-summary').json()
    assert metric(report,'Basales con RADAR completo')['numerator']==2
    assert metric(report,'Mal control basal (RADAR ≥4)')['value']==50.0
    assert metric(report,'Mal control basal (RADAR ≥4)')['denominator']==2

def test_paired_radar_and_cat_missingness_separately(client):
    h=login(client)
    assert client.post('/api/patients',headers=h,json=patient('SIM-PAIR')).status_code==201
    assert client.post('/api/visits',headers=h,json=visit('SIM-PAIR','V0',cat=0)).status_code==201
    assert client.post('/api/visits',headers=h,json=visit('SIM-PAIR','V2',cat=10,rescue='si')).status_code==201
    report=client.get('/api/study/scientific-summary').json()
    assert len(report['paired'])==1
    assert report['paired'][0]['delta_radar']==3
    assert report['paired'][0]['delta_cat']==10
    assert metric(report,'Cambio medio RADAR V2−V0')['value']==3

def test_role_scoping_in_analysis_and_spreadsheet(client):
    h=login(client)
    for code,centre in [('SIM-COSTA','SIM-CS01'),('SIM-OTRO','SIM-CS02')]:
        assert client.post('/api/patients',headers=h,json=patient(code,centre)).status_code==201
    login(client,'costa')
    report=client.get('/api/study/scientific-summary').json()
    assert metric(report,'Participantes incluidos')['value']==1
    assert sheet_names(client.get('/api/export/xlsx').content).count('BRECHAS_CRD_V12')==1
    assert len(sheet_names(client.get('/api/export/xlsx').content))==44
    x=client.get('/api/export/xlsx').content
    with zipfile.ZipFile(io.BytesIO(x)) as z:
        payload=''.join(z.read(i).decode('utf-8') for i in z.namelist() if i.startswith('xl/worksheets/sheet'))
        assert 'SIM-COSTA' in payload and 'SIM-OTRO' not in payload

def test_coverage_no_falsely_marked_approved():
    data=catalogue_coverage()
    assert len(data)==107
    assert next(x for x in data if x['code']=='center_start_date')['status']=='Capturable'
    assert next(x for x in data if x['code']=='cat_score')['location']=='Visit.cat'
    assert next(x for x in data if x['code']=='adherence_level')['status']=='Capturable'  # R056 actual: Visit.ianusCollected; legacy observations retained separately
    assert next(x for x in data if x['code']=='radar_total')['status']=='Derivada / provisional'
