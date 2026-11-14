"""Phase 14: completion of 28 candidate variable paths without demo data."""
from synthetic_v32_fixtures import valid_patient_factory
import io
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from phase12_analysis import catalogue_coverage
from phase14_completion import validate_payload,make_indicators,normalized_events

@pytest.fixture
def c(tmp_path,monkeypatch):
 monkeypatch.setattr(server,'DB_FILE',tmp_path/'p14.sqlite3')
 monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
 with TestClient(server.app) as x:yield x

def login(c,who='admin'):
 r=c.post('/api/session',json={'username':who,'password':'radar-demo-'+who})
 assert r.status_code==200,r.text
 return {'X-RADAR-CSRF':r.json()['csrf']}

def put(c,h,kind,key,payload,rev=0,reason='',centre=''):
 return c.put('/api/study/phase14',headers=h,json={'kind':kind,'key':key,'payload':payload,'rev':rev,'reason':reason,'centre':centre})

@valid_patient_factory
def patient(pid,centre):
 return {'id':pid,'center':centre,'status':'incluido','consent':'si','copd':'si',
 'enrolDate':'2026-01-15','spiroDate':'2025-12-12','ratio':0.57,'fev1':61,
 'eligibilityDecision':'elegible','activeExacerb':'no'}

def visit(pid,typ='V0',when='2026-01-15'):
 return {'id':f'VIS-{pid}-{typ}','patient':pid,'type':typ,'date':when,'status':'completa',
  'rescue':'no','exacerb':'no','dyspnea':'no','activity':'no','mmrc':0,'cat':0,'action':'seguimiento'}

def workbook_names(blob):
 with zipfile.ZipFile(io.BytesIO(blob)) as z:
  assert z.testzip() is None
  return [e.attrib['name'] for e in ET.fromstring(z.read('xl/workbook.xml')).findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')]

def test_all_28_catalogue_gaps_are_mapped():
 coverage=catalogue_coverage()
 assert len(coverage)==107
 assert not [x for x in coverage if x['status']=='No implementada']
 # R081/R082 were provisional contact counts in v0.21; v0.22 captures their responses.
 assert sum(x['status']=='Derivada / provisional' for x in coverage)==13
 assert all(next(x for x in coverage if x['id']==rid)['status']=='Capturable' for rid in ('R081','R082'))


def test_empty_pilot_export_contains_completion_architecture(c):
 login(c)
 data=c.get('/api/study/phase14').json()
 assert len(data['coverage'])==107 and data['records']==[]
 assert data['metrics']['indicators'][2]['value'] is None
 names=workbook_names(c.get('/api/export/xlsx').content)
 assert len(names)==46
 assert {'CENTROS_V14','PROFESIONALES_V14','CRIBADO_V14','BASAL_V14','VISITA_ADICIONAL_V14',
 'IMPLANTACION_MENSUAL_V14','INDICADORES_IMPL_V14','EVENTOS_CLASIF_V14','COBERTURA_28_V14'}<=set(names)


def test_aggregate_numerator_and_denominator_validation(c):
 h=login(c)
 key='SIM-CS01:2026-10'
 assert put(c,h,'implementation',key,{'eligible_copd_visits':10,'visits_with_radar':12}).status_code==422
 assert put(c,h,'implementation',key,{'eligible_copd_visits':10,'visits_with_radar':7}).status_code==200
 m=c.get('/api/study/phase14').json()['metrics']['indicators'][2]
 assert (m['numerator'],m['denominator'],m['value'])==(7,10,70.0)
 assert put(c,h,'implementation',key,{'eligible_copd_visits':10,'visits_with_radar':0},rev=1).status_code==422
 assert put(c,h,'implementation',key,{'eligible_copd_visits':10,'visits_with_radar':0},rev=1,reason='Corregido con parte mensual').status_code==200
 m=c.get('/api/study/phase14').json()['metrics']['indicators'][2]
 assert m['value']==0.0 and m['denominator']==10
 details=c.get('/api/audit/changes').json()
 assert any(x['field_name']=='visits_with_radar' and x['prior_value']=='7' and x['new_value']=='0' for x in details)


def test_professional_centre_metrics_and_visit_assessor(c):
 h=login(c)
 assert put(c,h,'centre','SIM-CS01',{'center_start_date':'2026-01-01','center_end_use':'si'}).status_code==200
 assert put(c,h,'professional','SIM-PRO-A',{'clinician_role':'medicina','training_date':'2026-01-03'},centre='SIM-CS01').status_code==200
 assert c.post('/api/patients',headers=h,json=patient('SIM-801','SIM-CS01')).status_code==201
 assert c.post('/api/visits',headers=h,json=visit('SIM-801')).status_code==201
 assert put(c,h,'visit','SIM-801:V0',{'assessor_code':'SIM-PRO-A','clinical_notes_structured':'sin_cambios','ccq_score':0}).status_code==200
 s=c.get('/api/study/phase14').json()
 assert s['metrics']['indicators'][0]['value']==1
 assert s['metrics']['indicators'][1]['value']==1
 assert any(r['payload'].get('assessor_code')=='SIM-PRO-A' for r in s['records'])
 assert put(c,h,'visit','SIM-801:V1',{'assessor_code':'SIM-PRO-A'}).status_code==422


def test_screening_baseline_dates_and_optionals(c):
 h=login(c)
 assert c.post('/api/patients',headers=h,json=patient('SIM-802','SIM-CS02')).status_code==201
 x=put(c,h,'screening','SIM-802',{'screen_code':'SIM-SCR-802','screen_date':'2026-01-01','consent_date':'2026-01-04','interfering_trial':'no'})
 assert x.status_code==200,x.text
 x=put(c,h,'baseline','SIM-802',{'other_comorb':'ninguna','charlson_index':0,'ccq_score':0.0,'flu_vax_up_to_date':'no'})
 assert x.status_code==200,x.text
 assert put(c,h,'baseline','SIM-802',{'charlson_index':-1},rev=1,reason='Corrección de dato basal').status_code==422
 assert validate_payload('baseline',{'ccq_score':0})['ccq_score']==0.0


def test_centre_isolation_and_excel_scope(c):
 admin=login(c)
 for pid,centre in [('SIM-C1','SIM-CS01'),('SIM-C2','SIM-CS02')]:
  assert c.post('/api/patients',headers=admin,json=patient(pid,centre)).status_code==201
  assert put(c,admin,'screening',pid,{'screen_code':'SIM-SCR-'+pid}).status_code==200
 investigator=login(c,'costa')
 rows=c.get('/api/study/phase14').json()['records']
 assert {r['key'] for r in rows}=={'SIM-C1'}
 assert put(c,investigator,'screening','SIM-C2',{'alternative_diagnosis':'si'},rev=1,reason='Revisión comprobada del dato').status_code==403
 with zipfile.ZipFile(io.BytesIO(c.get('/api/export/xlsx').content)) as z:
  text=' '.join(z.read(n).decode() for n in z.namelist() if n.startswith('xl/worksheets/'))
  assert 'SIM-C1' in text and 'SIM-C2' not in text


def test_event_type_does_not_double_count_exacerbation():
 p=[{'id':'SIM-811','vitalStatus':'vivo'}]
 e=[{'id':'EP-1','patient':'SIM-811','date':'2026-03-12','copd':'si'}]
 c=[{'id':'CT-1','patient':'SIM-811','date':'2026-03-12','copd':'si','type':'urgencias','event':'EP-1'}]
 result=normalized_events(p,e,c)
 assert [r['event_type'] for r in result]==['agudizacion','urgencias']
 assert result[1]['related_episode']=='EP-1'


def test_retention_only_for_matured_cohort():
 people=[{'id':'SIM-101','status':'incluido','enrolDate':'2024-01-30'},{'id':'SIM-102','status':'incluido','enrolDate':'2026-12-01'}]
 visits=[{'patient':'SIM-101','type':'V2','status':'completa'}]
 stats=make_indicators([],people,visits,[{'code':'SIM-CS01'}],cutoff='2026-10-27')
 m=stats['indicators'][4]
 assert (m['numerator'],m['denominator'],m['value'])==(1,1,100.0)
 assert make_indicators([],[],[],[{'code':'SIM-CS01'}],cutoff='2026-10-27')['indicators'][4]['value'] is None
