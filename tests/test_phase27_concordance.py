"""Phase 27: CRD-to-app concordance and regression of new patient/visit fields."""
import sys
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from synthetic_v32_fixtures import valid_record
from crd_concordance_v27 import report


def test_concordance_107_and_printed_crd_identifiers():
    data=report()
    assert data['total_catalogue']==107
    assert data['printed_code_count']==85  # 84 literal R-codes + R046 implied in R045–R047
    assert [x['id'] for x in data['variables']]==list(range(1,108))
    assert next(v for v in data['variables'] if v['id']==24)['printed_crd'] is False
    assert 'últimas' in next(v for v in data['variables'] if v['id']==56)['review']
    assert 'Patient.consentDate' in next(v for v in data['variables'] if v['id']==22)['technical_source']
    assert 'Visit.assessorCode' in next(v for v in data['variables'] if v['id']==65)['technical_source']


def test_new_screening_baseline_visit_fields_and_reopen(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'radar27.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        login=c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
        assert login.status_code==200,login.text
        h={'X-RADAR-CSRF':login.json()['csrf']}
        d={'id':'SIM-CRD27','center':'SIM-CS01','status':'incluido',
            'copd':'si','consent':'si','consentDate':'2026-10-20',
            'enrolDate':'2026-11-01','spiroDate':'2026-09-10','birthDate':'1968-05-12',
            'regular':'si','weeks':5,'capacity':'ayuda','alternativeDiagnosis':'no',
            'seriousDecompensation':'no','interferingTrial':'no',
            'otherComorbidities':'artritis','charlson':0,'fluVaccination':'si',
            'pneumococcalVaccination':'nc','lastInformationDate':'2026-11-01',
            'priorExModerate':2,'priorExSevere':1}
        d=valid_record(d)
        z=c.post('/api/patients',headers=h,json=d)
        assert z.status_code==201,z.text
        state=c.get('/api/state').json()
        p=next(p for p in state['patients'] if p['id']=='SIM-CRD27')
        assert p['age']==58 and p['priorEx']==3 and p['capacity']=='ayuda'
        assert p['charlson']==0 and p['pneumococcalVaccination']=='nc'
        assert p['consentDate']=='2026-10-20'
        bad={**d,'id':'SIM-BAD27','consentDate':'2026-11-02'}
        assert c.post('/api/patients',headers=h,json=bad).status_code==422
        bad2={**d,'id':'SIM-BAD28','consent':'no'}
        assert c.post('/api/patients',headers=h,json=bad2).status_code==422
        v={'id':'VIS-SIM27','patient':'SIM-CRD27','type':'V0','date':'2026-11-01',
           'assessorCode':'SIM-PRO-M27','status':'parcial'}
        z=c.post('/api/visits',headers=h,json=v);assert z.status_code==201,z.text
        vv=next(v for v in c.get('/api/state').json()['visits'] if v['id']=='VIS-SIM27')
        assert vv['assessorCode']=='SIM-PRO-M27'
        r=c.get('/api/study/concordance');assert r.status_code==200
        assert r.json()['printed_code_count']==85
        assert 'R055' not in [x['id'] for x in r.json()['variables']]
        assert next(x for x in r.json()['variables'] if x['id']==55)['implementation']=='Campo principal · significado actualizado'
    with TestClient(server.app) as c:
        z=c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
        assert z.status_code==200
        p=next(p for p in c.get('/api/state').json()['patients'] if p['id']=='SIM-CRD27')
        assert p['otherComorbidities']=='artritis'
        assert p['lastInformationDate']=='2026-11-01'


def test_r107_missing_reasons_and_specific_crd_codes(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'radar27_missing.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        token=c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'}).json()['csrf']
        h={'X-RADAR-CSRF':token}
        assert c.post('/api/patients',headers=h,json=valid_record({'id':'SIM-CRD27M','center':'SIM-CS01',
           'status':'incluido','copd':'si','consent':'si','enrolDate':'2026-11-01','spiroDate':'2026-09-01'})).status_code==201
        assert c.post('/api/visits',headers=h,json={'id':'VIS-27M','patient':'SIM-CRD27M','type':'V0','date':'2026-11-01'}).status_code==201
        for code,reason in [('R055','no_registrado'),('R056','no_disponible'),('R090','no_realizado'),('R103','no_aplica')]:
            z=c.put('/api/study/missing',headers=h,json={'participant':'SIM-CRD27M','visit_type':'V0','field_code':code,'reason':reason})
            assert z.status_code==200,z.text
        assert len([r for r in c.get('/api/study/missing').json() if r['participant']=='SIM-CRD27M'])==4
        assert c.put('/api/study/missing',headers=h,json={'participant':'SIM-CRD27M','visit_type':'V0','field_code':'R110','reason':'no_aplica'}).status_code==422
        assert c.put('/api/study/missing',headers=h,json={'participant':'SIM-CRD27M','visit_type':'V0','field_code':'R107','reason':'no_aplica'}).status_code==422
        # Older categories and codes are still readable in upgraded databases.
        assert c.put('/api/study/missing',headers=h,json={'participant':'SIM-CRD27M','visit_type':'V0','field_code':'cat','reason':'no_recogido'}).status_code==200
