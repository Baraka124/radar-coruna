"""Phase 13: synthetic-only clinical structure, missingness and outcome accounting."""
from synthetic_v32_fixtures import valid_patient_factory
from pathlib import Path
import sys,zipfile,io,xml.etree.ElementTree as ET
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from phase13_outcomes import gold_airflow_grade

@pytest.fixture
def c(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'p13.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as client:yield client

def login(c,who='admin'):
    q=c.post('/api/session',json={'username':who,'password':'radar-demo-'+who})
    assert q.status_code==200,q.text
    return {'X-RADAR-CSRF':q.json()['csrf']}

@valid_patient_factory
def patient(pid='SIM-301',centre='SIM-CS01',**kw):
    return {'id':pid,'center':centre,'age':66,'copd':'si','consent':'si',
        'regular':'si','capacity':'si','exclusion':'no','status':'incluido',
        'activeExacerb':'no','eligibilityDecision':'elegible','enrolDate':'2026-01-15',
        'spiroDate':'2025-12-12','ratio':0.58,'fev1':43.0,**kw}

def visit(pid,kind):
    dates={'V0':'2026-01-15','V1':'2026-07-15','V2':'2027-01-15'}
    return {'id':f'VIS-{pid}-{kind}','patient':pid,'type':kind,'date':dates[kind],
            'status':'completa','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no',
            'cat':0,'mmrc':0,'action':'seguimiento'}

def workbook_names(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        assert z.testzip() is None
        return [x.attrib['name'] for x in ET.fromstring(z.read('xl/workbook.xml')).findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')]

def test_clean_initial_cohort_and_full_workbook(c):
    login(c)
    assert not c.get('/api/study/phase13-outcomes').json()['eligibility']
    names=workbook_names(c.get('/api/export/xlsx').content)
    assert len(names)==46
    assert {'ELEGIBILIDAD_V13','RESULTADOS_INTERVALO_V13','AUSENCIAS_V13'}<=set(names)
    spec=c.get('/api/study/specification').json()
    assert len(spec['variables'])==107
    assert next(x for x in spec['variables'] if x['code']=='gold_airflow_grade')['implementation']=='Derivada / provisional'

def test_screening_and_vital_status_guards(c):
    h=login(c)
    x=patient(eligibilityDecision='no_elegible')
    r=c.post('/api/patients',json=x,headers=h)
    assert r.status_code==422
    x=patient(activeExacerb='si')
    assert c.post('/api/patients',json=x,headers=h).status_code==422
    x=patient(vitalStatus='fallecido',deathDate='')
    assert c.post('/api/patients',json=x,headers=h).status_code==422
    x=patient(vitalStatus='fallecido',deathDate='2026-10-01',deathCause='respiratoria')
    assert c.post('/api/patients',json=x,headers=h).status_code==201
    e=c.get('/api/study/phase13-outcomes').json()['eligibility'][0]
    assert e['gold_airflow_grade']==3 and e['vital_status']=='fallecido'

def test_gold_not_inferred_without_obstruction():
    assert gold_airflow_grade({'ratio':None,'fev1':33}) is None
    assert gold_airflow_grade({'ratio':.70,'fev1':33}) is None
    assert gold_airflow_grade({'ratio':.56,'fev1':82})==1
    assert gold_airflow_grade({'ratio':.56,'fev1':50})==2
    assert gold_airflow_grade({'ratio':.56,'fev1':49.9})==3
    assert gold_airflow_grade({'ratio':.56,'fev1':29.99})==4

def test_intervals_events_distinct_from_contacts(c):
    h=login(c)
    assert c.post('/api/patients',json=patient(),headers=h).status_code==201
    for kind in ('V0','V1','V2'):
        r=c.post('/api/visits',json=visit('SIM-301',kind),headers=h)
        assert r.status_code==201,r.text
    a={'id':'EP-300','patient':'SIM-301','date':'2026-04-02','severity':'grave','copd':'si','source':'hce'}
    assert c.post('/api/episodes',json=a,headers=h).status_code==201
    b={'id':'CO-300','patient':'SIM-301','date':'2026-04-02','type':'urgencias','event':'EP-300','copd':'si'}
    assert c.post('/api/contacts',json=b,headers=h).status_code==201
    report=c.get('/api/study/phase13-outcomes').json()
    j=next(x for x in report['intervals'] if x['interval']=='V0→V1')
    assert j['exacerbations_copd']==1 and j['er_copd']==1 and j['admissions_copd']==0
    k=next(x for x in report['intervals'] if x['interval']=='V1→V2')
    assert k['exacerbations_copd']==0
    assert len(report['intervals'])==3

def test_missing_records_correction_and_conflicts(c):
    h=login(c)
    assert c.post('/api/patients',json=patient(),headers=h).status_code==201
    assert c.post('/api/visits',json=visit('SIM-301','V0'),headers=h).status_code==201
    d={'participant':'SIM-301','visit_type':'V0','field_code':'cat','reason':'no_disponible'}
    r=c.put('/api/study/missing',json=d,headers=h)
    assert r.status_code==200,r.text
    assert r.json()['rev']==1
    # Stating that CAT is missing while CAT=0 was recorded is a quality conflict.
    o=c.get('/api/study/phase13-outcomes').json()
    assert len(o['missing_conflicts'])==1
    assert c.put('/api/study/missing',json={**d,'rev':1,'reason':'no_recogido'},headers=h).status_code==422
    changed=c.put('/api/study/missing',json={**d,'rev':1,'reason':'no_recogido','correction_reason':'Corrección tras revisión'},headers=h)
    assert changed.status_code==200 and changed.json()['rev']==2
    assert len(c.get('/api/audit/changes').json())>=1
    x=c.get('/api/export/xlsx')
    assert x.status_code==200 and 'AUSENCIAS_V13' in workbook_names(x.content)

def test_centre_isolation_for_missing_and_outcomes(c):
    h=login(c)
    for pid,centre in [('SIM-301','SIM-CS01'),('SIM-302','SIM-CS02')]:
        assert c.post('/api/patients',json=patient(pid,centre),headers=h).status_code==201
        assert c.post('/api/visits',json=visit(pid,'V0'),headers=h).status_code==201
    h=login(c,'costa')
    assert {x['participant'] for x in c.get('/api/study/phase13-outcomes').json()['eligibility']}=={'SIM-301'}
    assert c.put('/api/study/missing',json={'participant':'SIM-302','visit_type':'V0','field_code':'mmrc','reason':'desconocido'},headers=h).status_code==403
    assert c.put('/api/study/missing',json={'participant':'SIM-301','visit_type':'V0','field_code':'mmrc','reason':'desconocido'},headers=h).status_code==200
    with zipfile.ZipFile(io.BytesIO(c.get('/api/export/xlsx').content)) as z:
        content=' '.join(z.read(f).decode() for f in z.namelist() if f.startswith('xl/worksheets/sheet'))
        assert 'SIM-301' in content and 'SIM-302' not in content
