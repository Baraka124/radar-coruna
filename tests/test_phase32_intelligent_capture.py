"""v0.32 structured eligibility and non-editable derivations; synthetic data only."""
from __future__ import annotations
import io
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'synthetic_v32.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c: yield c

def auth(c,name='admin'):
    res=c.post('/api/session',json={'username':name,'password':f'radar-demo-{name}'})
    assert res.status_code==200,res.text
    return {'X-RADAR-CSRF':res.json()['csrf']}

def sample(pid='SIM-VALID32',**kwargs):
    base={ 'id':pid,'center':'SIM-CS01','status':'incluido','copd':'si',
        'regular':'si','lastCopdReviewDate':'2025-05-01',
        'weeks':4,'capacity':'si','activeExacerb':'no',
        'exclusion':'no','alternativeDiagnosis':'no','seriousDecompensation':'no',
        'interferingTrial':'no','consent':'si','consentDate':'2026-01-05',
        'enrolDate':'2026-01-10','spiroDate':'2025-10-15',
        'ratio':0.59,'birthDate':'1986-01-10','age':98,
        'eligibilityDecision':'elegible','priorExModerate':2,'priorExSevere':1,'priorEx':35}
    return {**base,**kwargs}

def post(c,h,p): return c.post('/api/patients',headers=h,json=p)

def test_age_is_derived_on_exact_40th_birthday_and_total_is_derived(client):
    h=auth(client)
    r=post(client,h,sample())
    assert r.status_code==201,r.text
    p=next(p for p in client.get('/api/state').json()['patients'] if p['id']=='SIM-VALID32')
    assert p['age']==40 and p['priorEx']==3
    assert p['birthDate']=='1986-01-10'
    assert p['lastCopdReviewDate']=='2025-05-01'

def test_before_birthday_is_not_40(client):
    h=auth(client)
    r=post(client,h,sample('SIM-UNDER40',birthDate='1986-01-11'))
    assert r.status_code==422

def test_missing_dob_cannot_be_bypassed_by_manual_age(client):
    h=auth(client)
    r=post(client,h,sample('SIM-NODATE',birthDate='',age=90))
    assert r.status_code==422

def test_border_ratio_070_is_not_eligible(client):
    h=auth(client)
    for index,ratio in enumerate([0.70,0.71,None]):
        r=post(client,h,sample(f'SIM-RATIO{index}',ratio=ratio))
        assert r.status_code==422,r.text
    assert post(client,h,sample('SIM-RATIOLOW',ratio=0.699)).status_code==201

def test_all_required_clinical_eligibility_gates_reject_invalid(client):
    h=auth(client)
    cases=[
        {'regular':'no'}, {'lastCopdReviewDate':''},
        {'lastCopdReviewDate':'2024-12-31'}, {'lastCopdReviewDate':'2026-01-10'},
        {'weeks':None},{'weeks':3},{'activeExacerb':''},{'activeExacerb':'si'},
        {'capacity':''},{'capacity':'no'}, {'exclusion':''},{'exclusion':'si'},
        {'alternativeDiagnosis':''},{'alternativeDiagnosis':'si'},
        {'seriousDecompensation':''},{'seriousDecompensation':'si'},
        {'interferingTrial':''},{'interferingTrial':'si'},
        {'consentDate':''},{'consentDate':'2026-01-11'},
        {'eligibilityDecision':'pendiente'}, {'copd':'no'},
        {'spiroDate':''}, {'enrolDate':''}
    ]
    for i,change in enumerate(cases):
        r=post(client,h,sample(f'SIM-BAD{i:02}',**change))
        assert r.status_code==422,(change,r.status_code,r.text[:150])

def test_screening_is_saved_without_fabricating_eligibility(client):
    h=auth(client)
    r=post(client,h,{'id':'SIM-SCREEN32','center':'SIM-CS01','status':'cribado'})
    assert r.status_code==201,r.text
    s=next(p for p in client.get('/api/state').json()['patients'] if p['id']=='SIM-SCREEN32')
    assert s['age'] is None and s['birthDate']=='' and s['enrolDate']==''

def test_date_correction_recomputes_age_without_changing_source(client):
    h=auth(client)
    assert post(client,h,sample()).status_code==201
    before=next(p for p in client.get('/api/state').json()['patients'] if p['id']=='SIM-VALID32')
    headers={**h,'X-RADAR-CHANGE-REASON':quote('Corrección fecha nac de ficha sintética')}
    result=client.put('/api/patients/SIM-VALID32',headers=headers,json={**before,'birthDate':'1985-01-10','age':100})
    assert result.status_code==200,result.text
    after=next(p for p in client.get('/api/state').json()['patients'] if p['id']=='SIM-VALID32')
    assert after['age']==41 and after['birthDate']=='1985-01-10' and after['rev']==2

def test_multicentre_scope_and_export_persist_source_fields(client):
    h=auth(client)
    assert post(client,h,sample('SIM-COST32')).status_code==201
    assert post(client,h,sample('SIM-INT32',center='SIM-CS02')).status_code==201
    auth(client,'costa')
    state=client.get('/api/state').json()
    assert [p['id'] for p in state['patients']]==['SIM-COST32']
    book=client.get('/api/export/xlsx')
    assert book.status_code==200
    with zipfile.ZipFile(io.BytesIO(book.content)) as z:
        assert z.testzip() is None
        sheet=b'\n'.join(z.read(x) for x in z.namelist() if x.startswith('xl/worksheets/sheet'))
        assert b'SIM-COST32' in sheet and b'SIM-INT32' not in sheet
        assert b'2025-05-01' in sheet

def test_legacy_included_record_is_flagged_and_requires_backfill_before_edit(client):
    h=auth(client)
    # Migration rule: old data are readable, not silently reclassified as eligible.
    # Direct SQL illustrates a historic pre-v32 record, never a new API admission.
    import json
    with server.conn() as c:
        old={'id':'SIM-LEGACY','center':'SIM-CS01','status':'incluido','copd':'si','consent':'si',
             'enrolDate':'2026-01-10','spiroDate':'2025-12-10','age':62}
        c.execute('INSERT INTO patients VALUES (?,?,?,?,?,?)',('SIM-LEGACY','SIM-CS01',json.dumps(old),1,'legacy','2026-01-10'))
    s=next(p for p in client.get('/api/state').json()['patients'] if p['id']=='SIM-LEGACY')
    assert s['age']==62
    result=client.put('/api/patients/SIM-LEGACY',headers={**h,'X-RADAR-CHANGE-REASON':quote('Corrección de ficha antigua ficticia')},json={**s,'age':63})
    assert result.status_code==422

def test_current_version(client):
    auth(client)
    assert client.get('/api/health').json()['version']==server.app.version

def test_stale_writes_and_persistence_across_reopen(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'restart_v32.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        h=auth(c)
        assert post(c,h,sample('SIM-REOPEN32')).status_code==201
        saved=next(p for p in c.get('/api/state').json()['patients'] if p['id']=='SIM-REOPEN32')
        correction={**h,'X-RADAR-CHANGE-REASON':quote('Cambio simulado antes de confirmar persistencia')}
        change=c.put('/api/patients/SIM-REOPEN32',headers=correction,json={**saved,'priorExModerate':3})
        assert change.status_code==200,change.text
        rejected=c.put('/api/patients/SIM-REOPEN32',headers=correction,json={**saved,'priorExSevere':5})
        assert rejected.status_code==409
    with TestClient(server.app) as restarted:
        auth(restarted)
        new=next(p for p in restarted.get('/api/state').json()['patients'] if p['id']=='SIM-REOPEN32')
        assert new['priorExModerate']==3 and new['priorEx']==4 and new['rev']==2
        assert restarted.get('/api/export/xlsx').status_code==200


def test_repeated_screening_edit_retains_legacy_age_and_total(client):
    import json
    h=auth(client)
    legacy={'id':'SIM-ARCHIVE32','center':'SIM-CS01','status':'cribado','age':57,'priorEx':4}
    with server.conn() as c:
        c.execute('INSERT INTO patients VALUES (?,?,?,?,?,?)',('SIM-ARCHIVE32','SIM-CS01',json.dumps(legacy),1,'legacy','2026-01-10'))
    stored=next(p for p in client.get('/api/state').json()['patients'] if p['id']=='SIM-ARCHIVE32')
    r=client.put('/api/patients/SIM-ARCHIVE32',headers={**h,'X-RADAR-CHANGE-REASON':quote('Cambio ficticio de cribado antiguo')},json={**stored,'regular':'si'})
    assert r.status_code==200,r.text
    updated=next(p for p in client.get('/api/state').json()['patients'] if p['id']=='SIM-ARCHIVE32')
    assert updated['age']==57 and updated['priorEx']==4

def test_verified_backup_restoration_preserves_computed_values(tmp_path,monkeypatch):
    from backup_manager import backup, verify, restore_new
    live=tmp_path/'live.sqlite3'
    monkeypatch.setattr(server,'DB_FILE',live)
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        h=auth(c)
        assert post(c,h,sample('SIM-BACKUP32')).status_code==201
    snapshot,manifest=backup(live,tmp_path/'copies')
    assert verify(manifest)['verified']
    restored=tmp_path/'reopened.sqlite3'
    info=restore_new(manifest,restored)
    assert info['integrity']=='ok'
    monkeypatch.setattr(server,'DB_FILE',restored)
    with TestClient(server.app) as reloaded:
        auth(reloaded)
        p=next(p for p in reloaded.get('/api/state').json()['patients'] if p['id']=='SIM-BACKUP32')
        assert p['age']==40 and p['priorEx']==3 and p['lastCopdReviewDate']=='2025-05-01'

def test_leap_day_age_boundary(client):
    h=auth(client)
    base=dict(birthDate='1984-02-29',enrolDate='2024-02-29',
              consentDate='2024-02-20',spiroDate='2024-02-01',lastCopdReviewDate='2023-08-12')
    good=post(client,h,sample('SIM-LEAP40',**base))
    assert good.status_code==201,good.text
    p=next(p for p in client.get('/api/state').json()['patients'] if p['id']=='SIM-LEAP40')
    assert p['age']==40
    before=post(client,h,sample('SIM-LEAP39',**{**base,'enrolDate':'2024-02-28'}))
    assert before.status_code==422
