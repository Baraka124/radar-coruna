"""Phase 21: R074/R076, episode/contact linkage and R090–R099; synthetic-only regression."""
from synthetic_v32_fixtures import valid_patient_factory
import io, json, sys, zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from study_module import public_catalogue, validate as validate_study
from phase13_outcomes import make_outcomes
from phase18_reporting import make_report


@valid_patient_factory
def pt(pid,center='SIM-CS01'):
    return {'id':pid,'center':center,'status':'incluido','copd':'si','consent':'si',
            'enrolDate':'2026-01-10','spiroDate':'2025-12-22','weeks':5}

def epi(eid,pid,day,**kw):
    d={'id':eid,'patient':pid,'date':day,'severity':'moderada','kind':'agudizacion',
       'copd':'si','steroids':'si','antibiotics':'no','source':'hce'};d.update(kw);return d


def test_episode_numbers_contact_links_and_exports(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'radar21.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        auth=c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'}).json()
        h={'X-RADAR-CSRF':auth['csrf']}
        assert c.get('/api/health').json()['version'] == server.app.version
        assert tuple(map(int, server.app.version.split('.'))) >= (0, 21, 0)
        for pid,centre in [('SIM-A21','SIM-CS01'),('SIM-B21','SIM-CS02')]:
            z=c.post('/api/patients',headers=h,json=pt(pid,centre));assert z.status_code==201,z.text
        d1=epi('EPI-21-1','SIM-A21','2026-02-01')
        d2=epi('EPI-21-2','SIM-A21','2026-03-01',severity='grave')
        d3=epi('EPI-21-3','SIM-A21','2026-03-01',kind='otro',severity='no_aplica',steroids='no')
        d4=epi('EPI-21-4','SIM-B21','2026-04-01')
        for item in [d1,d2,d3,d4]:
            z=c.post('/api/episodes',headers=h,json=item);assert z.status_code==201,z.text
        state=c.get('/api/state').json()
        assert [(x['id'],x['episodeNo']) for x in state['events']]==[
            ('EPI-21-1',1),('EPI-21-2',2),('EPI-21-3',3),('EPI-21-4',1)]
        assert c.post('/api/episodes',headers=h,json=epi('EPI-21-BAD','SIM-A21','2026-05-01',episodeNo=9)).status_code==422
        assert c.post('/api/episodes',headers=h,json=epi('EPI-21-dup','SIM-A21','2026-02-01')).status_code==409
        # Same episode 02 can connect to emergency + admission, without creating a second episode.
        for cid,typ in [('CON-A21-1','urgencias'),('CON-A21-2','ingreso')]:
            d={'id':cid,'patient':'SIM-A21','event':'EPI-21-2','date':'2026-03-01',
               'type':typ,'copd':'si','source':'hce','careCentre':'Centro ficticio',
               'dischargeDate':'2026-03-03'}
            z=c.post('/api/contacts',headers=h,json=d);assert z.status_code==201,z.text
        # A third separate contact at same day/type must be representable, not silently dropped.
        z=c.post('/api/contacts',headers=h,json={'id':'CON-A21-3','patient':'SIM-A21','event':'EPI-21-2',
             'date':'2026-03-01','type':'urgencias','copd':'si','source':'informe'})
        assert z.status_code==201,z.text
        assert c.post('/api/contacts',headers=h,json={'id':'CON-A21-X','patient':'SIM-B21',
             'event':'EPI-21-2','date':'2026-03-01','type':'urgencias'}).status_code==422
        assert c.post('/api/contacts',headers=h,json={'id':'CON-A21-D','patient':'SIM-A21',
             'date':'2026-03-02','type':'ingreso','dischargeDate':'2026-03-01'}).status_code==422
        state=c.get('/api/state').json()
        assert len(state['events'])==4 and len(state['contacts'])==3
        assert all(x['event']=='EPI-21-2' for x in state['contacts'])
        book=c.get('/api/export/xlsx');assert book.status_code==200,book.text[:160] if book.status_code!=200 else ''
        with zipfile.ZipFile(io.BytesIO(book.content)) as z:
            assert z.testzip() is None
            data=''.join(z.read(n).decode('utf8') for n in z.namelist() if n.startswith('xl/worksheets/sheet'))
            assert 'EPI-21-2' in data
            assert 'CON-A21-1' in data
            shared=z.read('xl/sharedStrings.xml').decode() if 'xl/sharedStrings.xml' in z.namelist() else ''
            assert 'N.º episodio' in shared or 'N.º episodio' in data
        audit=c.get('/api/audit');assert audit.status_code==200
        assert any(a['verb']=='CREATE' and 'EPI-21-2'==a['object_id'] for a in audit.json())
        # Re-opening the app does not renumber previously recorded episodes.
    with TestClient(server.app) as c:
        token=c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'}).json()['csrf']
        assert [(x['id'],x['episodeNo']) for x in c.get('/api/state').json()['events']][:2]==[('EPI-21-1',1),('EPI-21-2',2)]


def test_legacy_episode_migration_preserves_links(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'legacy.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    server.init_db()
    # A v0.20 row exists without episodeNo; its internal ID may already be referenced by contacts.
    old=epi('EPI-LEGACY21','SIM-LEG21','2026-04-01');old.pop('kind')
    person=server.Patient(**pt('SIM-LEG21')).model_dump(exclude={'rev'})
    with server.conn() as c:
        c.execute('INSERT INTO patients VALUES (?,?,?,?,?,?)',('SIM-LEG21','SIM-CS01',json.dumps(person),1,'system',server.now()))
        c.execute('INSERT INTO episodes VALUES (?,?,?)',(old['id'],old['patient'],json.dumps(old)))
        linked={'id':'CON-LEG21','patient':'SIM-LEG21','event':old['id'],'date':'2026-04-01','type':'ingreso','copd':'si'}
        c.execute('INSERT INTO contacts VALUES (?,?,?,?)',(linked['id'],linked['patient'],linked['event'],json.dumps(linked)))
    server.init_db();server.init_db()
    with server.conn() as c:
        row=json.loads(c.execute('SELECT payload FROM episodes WHERE id=?',(old['id'],)).fetchone()['payload'])
        contact=json.loads(c.execute('SELECT payload FROM contacts WHERE id=?',(linked['id'],)).fetchone()['payload'])
        assert row['episodeNo']==1 and row['kind']=='agudizacion'
        assert contact['event']==old['id']
        rows=c.execute("SELECT * FROM audit WHERE verb='MIGRATE' AND object_id=?",(old['id'],)).fetchall()
        assert len([r for r in rows if 'Asignación R074' in (r['reason'] or '')])==1
        assert len([r for r in rows if 'R081/R082' in (r['reason'] or '')])==1


def test_visit_specific_actions_all_ten_codes_and_other_event_not_exacerbation():
    catalogue=public_catalogue()
    ids=[v['id'] for v in catalogue['variables'] if v['code'] in {
      'action_inhaler_tech','action_adherence_counsel','action_smoking_counsel',
      'action_activity_counsel','action_vaccine_review','action_comorb_review',
      'action_pulm_rehab_offer','action_inhaled_change','action_specialty_referral','action_plan_documented'}]
    assert set(ids)=={f'R{i:03d}' for i in range(90,100)}
    for key in ('action_inhaler_tech','action_specialty_referral','action_plan_documented'):
        assert validate_study(key,'V0','no_aplica')=='no_aplica'
        assert validate_study(key,'V1','no_consta')=='no_consta'
    p=[pt('SIM-Q21')]
    a=epi('EPI-M21','SIM-Q21','2026-02-01')
    b=epi('EPI-O21','SIM-Q21','2026-03-01',kind='otro',severity='no_aplica')
    events=[a,b]
    # Do not classify an 'otro evento' as an EPOC exacerbation.
    report=make_report(p,[],events,[],[],[])
    vals=[x for x in report['indicators'] if x['indicator']=='Agudizaciones EPOC registradas']
    assert vals and vals[0]['value']==1
