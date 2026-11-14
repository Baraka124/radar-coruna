"""Regression v0.22: explicit R081/R082, evidence, migration and audit; synthetic only."""
from synthetic_v32_fixtures import valid_patient_factory
import json,sys
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from phase12_analysis import catalogue_coverage
from export_research import quality_issues


@valid_patient_factory
def patient(pid='SIM-CARE22', center='SIM-CS01'):
    return dict(id=pid,center=center,status='incluido',consent='si',copd='si',
                enrolDate='2026-01-02',spiroDate='2025-12-01',weeks=5)

def episode(pid='SIM-CARE22',eid='EPI-CARE22'):
    return dict(id=eid,patient=pid,date='2026-02-01',kind='agudizacion',
                severity='moderada',copd='si',steroids='no',antibiotics='si',source='informe')

def auth(client,user='admin',password='radar-demo-admin'):
    r=client.post('/api/session',json={'username':user,'password':password})
    assert r.status_code==200,r.text
    return {'X-RADAR-CSRF':r.json()['csrf']}

def state_episode(client,eid='EPI-CARE22'):
    return next(e for e in client.get('/api/state').json()['events'] if e['id']==eid)

def body(emergencyStatus='',admissionStatus='',emergencyDate='',admissionDate='',rev=0,reason=''):
    return locals()

def test_r081_r082_full_status_audit_optimistic_concurrency(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'care22.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        h=auth(c)
        assert c.get('/api/health').json()['version'] == server.app.version
        assert tuple(map(int, server.app.version.split('.'))) >= (0, 22, 0)
        assert c.post('/api/patients',headers=h,json=patient()).status_code==201
        assert c.post('/api/episodes',headers=h,json=episode()).status_code==201
        old=state_episode(c)
        assert old['episodeNo']==1
        assert old['emergencyStatus']==old['admissionStatus']==''  # absence != No
        path='/api/episodes/EPI-CARE22/care'
        result=c.put(path,headers=h,json=body('no','nc',rev=0))
        assert result.status_code==200,result.text
        assert result.json()['rev']==1
        updated=state_episode(c)
        assert (updated['emergencyStatus'],updated['admissionStatus'])==('no','nc')
        assert updated['emergencyDate']==updated['admissionDate']==''
        assert c.put(path,headers=h,json=body('si','nc',emergencyDate='2026-02-02',rev=0)).status_code==409
        assert c.put(path,headers=h,json=body('si','nc',emergencyDate='2026-02-02',rev=1)).status_code==422  # change reason
        changed=c.put(path,headers=h,json=body('si','nc',emergencyDate='2026-02-02',rev=1,reason='Corrección con informe'))
        assert changed.status_code==200,changed.text
        assert changed.json()['rev']==2
        assert c.put(path,headers=h,json=body('no','nc',emergencyDate='2026-02-02',rev=2,reason='Corrección con informe')).status_code==422
        assert c.put(path,headers=h,json=body('si','nc',emergencyDate='2026-02-31',rev=2,reason='Corrección con informe')).status_code==422
        # Status no longer becomes negative just because another type is missing.
        events=c.get('/api/state').json()['events'];assert len(events)==1
        rows=c.get('/api/audit/changes').json()
        assert any(r['field_name']=='emergencyStatus' and r['new_value']=='"si"' for r in rows)
        assert any(r['field_name']=='admissionStatus' and r['new_value']=='"nc"' for r in rows)
        assert c.put(path,headers=h,json=body('si','nc',emergencyDate='2026-02-02',rev=2)).json()['unchanged']


def test_linked_contacts_positive_reconciliation_multiple_and_migration(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'legacy22.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    server.init_db()
    pid='SIM-LEGACY22';eid='EPI-LEGACY22'
    with server.conn() as db:
        d=server.Patient(**patient(pid)).model_dump(exclude={'rev'})
        db.execute('INSERT INTO patients VALUES (?,?,?,?,?,?)',(pid,'SIM-CS01',json.dumps(d),1,'system',server.now()))
        raw=episode(pid,eid);raw['episodeNo']=1
        db.execute('INSERT INTO episodes VALUES (?,?,?)',(eid,pid,json.dumps(raw)))
        contact=dict(id='CON-OLD22',patient=pid,date='2026-02-04',event=eid,type='urgencias',copd='si')
        db.execute('INSERT INTO contacts VALUES (?,?,?,?)',(contact['id'],pid,eid,json.dumps(contact)))
    server.init_db();server.init_db()  # migration only once
    with TestClient(server.app) as c:
        h=auth(c)
        e=state_episode(c,eid)
        assert e['emergencyStatus']=='si' and e['emergencyDate']=='2026-02-04'
        assert e.get('admissionStatus','')==''
        r=c.get('/api/audit').json()
        assert len([x for x in r if x['verb']=='MIGRATE' and x['object_id']==eid])==1
        # The evidence-backed positive R081 may not be negated.
        assert c.put('/api/episodes/'+eid+'/care',headers=h,json=body('no','nc',rev=1,reason='Cambio deliberado')).status_code==422
        # Manually record hospital absence; then new admission evidence supersedes it with audit.
        r=c.put('/api/episodes/'+eid+'/care',headers=h,json=body('si','no',emergencyDate='2026-02-04',rev=1,reason='Comprobado en revisión'))
        assert r.status_code==200,r.text
        cid='CON-NEW22'
        x=c.post('/api/contacts',headers=h,json=dict(id=cid,patient=pid,event=eid,type='ingreso',date='2026-02-05',copd='si'))
        assert x.status_code==201,x.text
        e=state_episode(c,eid)
        assert e['admissionStatus']=='si' and e['admissionDate']=='2026-02-05'
        assert e['episodeNo']==1 and e['emergencyStatus']=='si'
        assert e['careAssessmentRev']==3
        audit=c.get('/api/audit').json()
        assert any(x['verb']=='UPDATE' and 'contacto ingreso' in (x['reason'] or '') for x in audit)
        # Another urgent contact must not create a new episode.
        assert c.post('/api/contacts',headers=h,json=dict(id='CON-NEW23',patient=pid,event=eid,type='urgencias',date='2026-02-02',copd='si')).status_code==201
        e=state_episode(c,eid)
        assert e['emergencyDate']=='2026-02-02'
        assert len(c.get('/api/state').json()['events'])==1
        assert len(c.get('/api/state').json()['contacts'])==3
        assert quality_issues([patient(pid)],[],[e],[contact]) is not None


def test_care_access_control_and_catalogue(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'acl22.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        admin=auth(c)
        assert c.post('/api/patients',headers=admin,json=patient('SIM-OTHER22','SIM-CS02')).status_code==201
        assert c.post('/api/episodes',headers=admin,json=episode('SIM-OTHER22','EPI-OTHER22')).status_code==201
        # Real centre policy is not certified; only synthetic centre scoping tested.
        costa=auth(c,'costa','radar-demo-costa')
        assert c.put('/api/episodes/EPI-OTHER22/care',headers=costa,json=body('no','no',rev=0)).status_code==403
        reviewer=auth(c,'revisor','radar-demo-revisor')
        assert c.put('/api/episodes/EPI-OTHER22/care',headers=reviewer,json=body('no','no',rev=0)).status_code==403
        m={r['id']:r for r in catalogue_coverage()}
        assert 'Episode.emergencyStatus' in m['R081']['location'] and m['R081']['status']=='Capturable'
        assert 'Episode.admissionStatus' in m['R082']['location'] and m['R082']['status']=='Capturable'


def test_unrelated_contacts_do_not_prove_r081_or_r082(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'different_cause22.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        h=auth(c)
        assert c.post('/api/patients',headers=h,json=patient()).status_code==201
        assert c.post('/api/episodes',headers=h,json=episode()).status_code==201
        unrelated=dict(id='CON-OTHER22',patient='SIM-CARE22',event='EPI-CARE22',
                       date='2026-02-04',type='urgencias',copd='no')
        assert c.post('/api/contacts',headers=h,json=unrelated).status_code==201
        e=state_episode(c)
        assert e['emergencyStatus']=='' and e['emergencyDate']==''
        assert c.put('/api/episodes/EPI-CARE22/care',headers=h,
                     json=body('no','nc',rev=0)).status_code==200
        assert state_episode(c)['emergencyStatus']=='no'
        # A new, proven EPOC-related urgent contact would correct the explicit negative.
        proven={**unrelated,'id':'CON-COPD22','copd':'si','date':'2026-02-05'}
        assert c.post('/api/contacts',headers=h,json=proven).status_code==201
        assert state_episode(c)['emergencyStatus']=='si'


def test_legacy_unspecified_copd_contact_is_not_positive_migration(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'unconfirmed22.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    server.init_db()
    with server.conn() as c:
        pid='SIM-UNC22';eid='EPI-UNC22'
        person=server.Patient(**patient(pid)).model_dump(exclude={'rev'})
        c.execute('INSERT INTO patients VALUES (?,?,?,?,?,?)',(pid,'SIM-CS01',json.dumps(person),1,'system',server.now()))
        raw=episode(pid,eid)
        c.execute('INSERT INTO episodes VALUES (?,?,?)',(eid,pid,json.dumps(raw)))
        contact=dict(id='CON-UNC22',patient=pid,event=eid,type='urgencias',date='2026-02-03')
        c.execute('INSERT INTO contacts VALUES (?,?,?,?)',(contact['id'],pid,eid,json.dumps(contact)))
    server.init_db()
    with server.conn() as c:
        e=json.loads(c.execute('SELECT payload FROM episodes WHERE id=?',(eid,)).fetchone()['payload'])
        assert not e.get('emergencyStatus') and not e.get('emergencyDate')
