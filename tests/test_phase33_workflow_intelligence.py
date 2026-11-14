"""v0.33: 107-variable semantics, derived measurements, non-fabricated data and conditional validity."""
import json,sys,io,zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from phase13_outcomes import gold_airflow_grade
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'intelligence33.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:yield c

def auth(c):
    v=c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
    assert v.status_code==200
    return {'X-RADAR-CSRF':v.json()['csrf']}

def patient():
    return {'id':'SIM-INTE33','center':'SIM-CS01','status':'incluido','copd':'si',
        'regular':'si','lastCopdReviewDate':'2025-09-01', 'weeks':6,'capacity':'si',
        'activeExacerb':'no','exclusion':'no','alternativeDiagnosis':'no',
        'seriousDecompensation':'no','interferingTrial':'no','consent':'si',
        'consentDate':'2026-01-08','enrolDate':'2026-01-15','spiroDate':'2025-12-12',
        'birthDate':'1970-06-09','ratio':0.65,'fev1':51,'eligibilityDecision':'elegible'}

def visit(**kw):
    return {**{'id':'VIS-INTE33-V0','patient':'SIM-INTE33','type':'V0','date':'2026-01-15',
        'status':'parcial','rescue':'','exacerb':'','dyspnea':'','activity':'',
        'ianusVerified':'','ianusCollected':'','reason':''},**kw}

def test_107_codes_are_complete_unique_and_versioned():
    audit=json.loads((ROOT/'AUDITORIA_INTELIGENCIA_R001_R107_V33.json').read_text())
    rows=audit['variables']; assert len(rows)==107
    assert [r['code'] for r in rows]==[f'R{i:03}' for i in range(1,108)]
    assert all(r['source'] and r['recommendation'] and r['v33_behavior'] for r in rows)
    assert audit['summary']['no_new_crd_codes']

def test_r026_is_inclusion_not_birth_date():
    audit=json.loads((ROOT/'AUDITORIA_INTELIGENCIA_R001_R107_V33.json').read_text())
    row=next(r for r in audit['variables'] if r['code']=='R026')
    assert 'inclusión' in row['label'].lower()
    assert 'birthdate' in row['recommendation'].lower()
    assert 'fecha de nacimiento' not in row['label'].lower()

def test_gold_grade_needs_real_obstruction_and_correct_boundaries():
    for f,result in ((80,1),(79.99,2),(50,2),(49.99,3),(30,3),(29.99,4)):
        assert gold_airflow_grade({'ratio':0.68,'fev1':f})==result
    assert gold_airflow_grade({'ratio':0.7,'fev1':20}) is None
    assert gold_airflow_grade({'ratio':None,'fev1':20}) is None
    assert gold_airflow_grade({'ratio':0.6,'fev1':None}) is None

def test_radar_zero_is_evaluable_and_not_missing():
    assert server.score({'status':'parcial','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no'})==0
    assert server.score({'status':'parcial','rescue':'','exacerb':'no','dyspnea':'no','activity':'no'}) is None

def test_adherence_ianus_yes_no_requires_verified_source():
    for state in ('','no'):
        with pytest.raises(ValueError):server.Visit(**visit(ianusVerified=state,ianusCollected='si'))
    assert server.Visit(**visit(ianusVerified='si',ianusCollected='no')).ianusCollected=='no'
    assert server.Visit(**visit(ianusVerified='no',ianusCollected='nv')).ianusCollected=='nv'
    assert server.Visit(**visit(ianusVerified='',ianusCollected='')).ianusCollected==''

def test_not_performed_reason_is_conditional_and_not_silently_kept():
    with pytest.raises(ValueError):server.Visit(**visit(status='no_realizada',reason=''))
    with pytest.raises(ValueError):server.Visit(**visit(status='parcial',reason='traslado'))
    with pytest.raises(ValueError):server.Visit(**visit(status='completa',reason='abandono'))
    assert server.Visit(**visit(status='no_realizada',reason='no_contacto')).status=='no_realizada'

def test_no_fake_visit_date_and_stable_inclusion_contract(client):
    h=auth(client)
    assert client.post('/api/patients',headers=h,json=patient()).status_code==201
    invalid=client.post('/api/visits',headers=h,json=visit(date=''))
    assert invalid.status_code==422
    good=client.post('/api/visits',headers=h,json=visit())
    assert good.status_code==201,good.text
    rows=client.get('/api/state').json()['visits']
    assert rows[0]['date']=='2026-01-15'
    assert rows[0]['ianusCollected']==''

def test_regimen_derivation_no_second_manual_flags():
    v=server.Visit(**visit(inhaledRegimen='triple',lama='no',laba='no',ics='no'))
    assert (v.lama,v.laba,v.ics)==('si','si','si')
    with pytest.raises(ValueError):server.Visit(**visit(inhaledRegimen='mono',monotherapyClass=''))

def test_export_labels_keep_birth_and_old_adherence_distinct(client):
    from export_research import SPEC
    p={k:(label,unit) for k,label,unit in SPEC['PARTICIPANTES']}
    v={k:(label,unit) for k,label,unit in SPEC['VISITAS']}
    assert 'R026' in p['enrolDate'][0]
    assert 'NO R026' in p['birthDate'][0]
    assert 'NO usar' in v['adherence'][0]
    h=auth(client)
    assert client.post('/api/patients',headers=h,json=patient()).status_code==201
    r=client.get('/api/export/xlsx');assert r.status_code==200
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:assert z.testzip() is None

def test_version_bumped_for_explicit_contract(client):
    assert client.get('/api/health').json()['version']==server.app.version
