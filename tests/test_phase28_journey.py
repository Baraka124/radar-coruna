"""v0.28: end-to-end longitudinal participant review and export regression."""
import io
import sys
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from synthetic_v32_fixtures import valid_record
from journey_v28 import summarize


def test_complete_participant_journey_and_reopen(tmp_path, monkeypatch):
    monkeypatch.setattr(server, 'DB_FILE', tmp_path / 'radar28.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO', raising=False)
    pid = 'SIM-JOURNEY28'
    with TestClient(server.app) as client:
        r = client.post('/api/session', json={'username': 'admin', 'password': 'radar-demo-admin'})
        assert r.status_code == 200, r.text
        h = {'X-RADAR-CSRF': r.json()['csrf']}
        p = {'id': pid, 'center': 'SIM-CS01', 'status': 'incluido', 'copd': 'si', 'regular': 'si',
             'consent': 'si', 'consentDate': '2025-12-22', 'birthDate': '1964-03-11',
             'enrolDate': '2026-01-10', 'spiroDate': '2025-12-01', 'weeks': 6,
             'priorExModerate': 2, 'priorExSevere': 1, 'vitalStatus': 'vivo',
             'lastInformationDate': '2027-01-10'}
        r = client.post('/api/patients', json=valid_record(p), headers=h)
        assert r.status_code == 201, r.text
        # RADAR=0 is a VALID complete result, not a missing value.
        for stage, day, rescue, activity, cat in [('V0','2026-01-10','no','no',8),
                                                  ('V1','2026-07-10','si','no',15),
                                                  ('V2','2027-01-10','si','si',20)]:
            v = {'id': 'VIS-28-'+stage, 'patient': pid, 'type': stage, 'date': day,
                 'assessorCode': 'SIM-EVAL28', 'status': 'completa',
                 'rescue': rescue, 'exacerb': 'no', 'dyspnea': 'no', 'activity': activity,
                 'cat': cat, 'mmrc': 0, 'action': 'seguimiento',
                 'ianusVerified': 'si', 'ianusCollected': 'si',
                 'inhaledRegimen': 'mono', 'monotherapyClass': 'lama'}
            r = client.post('/api/visits', json=v, headers=h)
            assert r.status_code == 201, r.text
        e = {'id':'EPI-28-A','patient':pid,'date':'2026-05-20','kind':'agudizacion',
             'severity':'moderada','copd':'si','steroids':'si','antibiotics':'no'}
        assert client.post('/api/episodes', json=e, headers=h).status_code == 201
        other = {'id':'EPI-28-B','patient':pid,'date':'2026-09-01','kind':'otro',
                 'severity':'no_aplica','copd':'no','steroids':'no','antibiotics':'no'}
        assert client.post('/api/episodes',json=other,headers=h).status_code == 201
        # The SAME episode may have multiple EPOC-related contacts.
        for cid, typ, day in [('CON-28-U','urgencias','2026-05-20'),('CON-28-H','ingreso','2026-05-21')]:
            c = {'id':cid,'patient':pid,'event':'EPI-28-A','date':day,'type':typ,'copd':'si'}
            z=client.post('/api/contacts',json=c,headers=h)
            assert z.status_code == 201, z.text
        r=client.put('/api/study/observations/'+pid+'/V0',headers=h,json={
            'observations': {'action_inhaler_tech':'si'},'revisions':{}})
        assert r.status_code == 200,r.text
        r=client.put('/api/study/missing',headers=h,json={
            'participant':pid,'visit_type':'V1','field_code':'R103','reason':'no_disponible'})
        assert r.status_code == 200,r.text
        z = client.get('/api/study/participant-journey/'+pid)
        assert z.status_code == 200,z.text
        report=z.json()
        assert report['recorded_visits']==3 and report['complete_radar']==3
        assert [row['radar_total'] for row in report['stages']] == [0,3,4]
        assert report['radar_delta_v0_v2']==4
        assert report['events']['all']==2
        assert report['events']['copd_exacerbations']==1 and report['events']['other']==1
        assert report['events']['linked_contact_count']==2 and report['events']['unlinked_contact_count']==0
        assert report['events']['emergency_copd']==1 and report['events']['admission_copd']==1
        assert report['stages'][0]['complementary_count']==1
        assert report['stages'][1]['missing_count']==1
        assert report['outcomes']['vital_status']=='vivo'
        assert report['alerts']==[]
        # Verify the existing full research export still contains the journey.
        x=client.get('/api/export/xlsx')
        assert x.status_code==200
        with zipfile.ZipFile(io.BytesIO(x.content)) as book:
            assert book.testzip() is None
            payload=b' '.join(book.read(name) for name in book.namelist() if name.startswith('xl/worksheets/sheet'))
            assert b'SIM-JOURNEY28' in payload and b'EPI-28-A' in payload
        # Scope is enforced independently of UI route visibility.
        costa=client.post('/api/session',json={'username':'interior','password':'radar-demo-interior'})
        assert costa.status_code == 200, costa.text
        assert client.get('/api/study/participant-journey/'+pid).status_code == 403
    # A restart must not change the summary or reference values.
    with TestClient(server.app) as client:
        assert client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'}).status_code==200
        report=client.get('/api/study/participant-journey/'+pid).json()
        assert report['radar_delta_v0_v2']==4
        assert report['events']['linked_contact_count']==2


def test_read_only_missing_and_evidence_semantics():
    p={'id':'SIM-MISS28','center':'SIM-CS01','status':'incluido'}
    result=summarize(p,[],[{'id':'E-28','patient':p['id'],'kind':'agudizacion','copd':'si',
                              'episodeNo':1,'emergencyStatus':''}],[],[],[])
    assert result['complete_radar']==0
    assert result['stages'][0]['status']=='sin_registrar'
    assert result['events']['emergency_copd']==0
    assert not result['alerts']  # No record is NOT evidence of a negative response
    linked={'id':'C-28','patient':p['id'],'event':'E-28','type':'urgencias','copd':'si'}
    result=summarize(p,[],[{'id':'E-28','patient':p['id'],'kind':'agudizacion','copd':'si',
                              'episodeNo':1,'emergencyStatus':''}],[linked],[],[])
    assert any(x['code']=='CONTACTO_EVIDENCIA' for x in result['alerts'])
    # Unrelated events do not count as EPOC exacerbations.
    result=summarize(p,[],[{'id':'O-28','patient':p['id'],'kind':'otro','copd':'no'}],[],[],[])
    assert result['events']['copd_exacerbations']==0
