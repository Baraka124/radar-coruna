"""Targeted synthetic-only regression for CRD reconciliation (2026-11-10)."""
from __future__ import annotations
from synthetic_v32_fixtures import valid_patient_factory
import io
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server


@valid_patient_factory
def p(**changes):
    item={'id':'SIM-CRD20','center':'SIM-CS01','copd':'si','consent':'si',
          'enrolDate':'2026-01-10','spiroDate':'2025-12-15','status':'incluido',
          'birthDate':'1968-11-11','weeks':4,'priorExModerate':2,'priorExSevere':1}
    item.update(changes)
    return item


def v(**changes):
    item={'id':'VIS-CRD20','patient':'SIM-CRD20','type':'V0','date':'2026-01-10',
          'status':'completa','rescue':'no','exacerb':'si','dyspnea':'no','activity':'no',
          'cat':12,'mmrc':0,'action':'seguimiento','inhaledRegimen':'mono',
          'monotherapyClass':'lama','roflumilast':'no','azithromycin':'no',
          'rescuePrescription':'saba','ianusVerified':'si','ianusCollected':'no',
          'ianusCheckedAt':'2026-01-10'}
    item.update(changes)
    return item


def test_full_birthdate_derived_age_separate_baseline_counts():
    person=server.Patient(**p())
    assert person.age==57
    assert person.priorEx==3
    assert person.priorExModerate==2 and person.priorExSevere==1
    with pytest.raises(ValueError):server.Patient(**p(weeks=3))
    with pytest.raises(ValueError):server.Patient(**p(birthDate='2026-01-11'))
    assert server.Patient(**p(birthDate='',age=62,status='cribado')).age==62  # historical screening fixture


def test_all_five_inhaled_regimens_and_ianus_no_inference():
    expected={
      'ninguno':('no','no','no'), 'mono':('si','no','no'),
      'dual':('si','si','no'), 'triple':('si','si','si'),
      'laba_ics':('no','si','si')}
    for category,flags in expected.items():
        kwargs=v(inhaledRegimen=category,monotherapyClass=('lama' if category=='mono' else ''))
        ob=server.Visit(**kwargs)
        assert (ob.lama,ob.laba,ob.ics)==flags
        assert ob.roflumilast=='no' and ob.azithromycin=='no'
        assert ob.rescue=='no' and ob.rescuePrescription=='saba'
    assert (server.Visit(**v(monotherapyClass='laba')).lama,
            server.Visit(**v(monotherapyClass='laba')).laba)==('no','si')
    with pytest.raises(ValueError):server.Visit(**v(monotherapyClass=''))
    with pytest.raises(ValueError):server.Visit(**v(inhaledRegimen='dual',monotherapyClass='lama'))
    with pytest.raises(ValueError):server.Visit(**v(ianusVerified='no',ianusCollected='no'))
    with pytest.raises(ValueError):server.Visit(**v(ianusVerified='si',ianusCollected='nv'))
    assert server.Visit(**v(ianusVerified='no',ianusCollected='nv')).ianusCollected=='nv'
    assert server.Visit(**v(ianusVerified='',ianusCollected='')).ianusVerified==''


def test_api_roundtrip_audit_excel_and_legacy_compatibility(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'radar_v20_synthetic.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        token=c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'}).json()['csrf']
        h={'X-RADAR-CSRF':token}
        assert c.get('/api/health').json()['version'] == server.app.version
        assert tuple(map(int, server.app.version.split('.'))) >= (0, 20, 0)
        resp=c.post('/api/patients',headers=h,json=p())
        assert resp.status_code==201,resp.text
        resp=c.post('/api/visits',headers=h,json=v())
        assert resp.status_code==201,resp.text
        state=c.get('/api/state').json()
        patient=state['patients'][0];visit=state['visits'][0]
        assert patient['age']==57 and patient['priorEx']==3
        assert visit['inhaledRegimen']=='mono' and visit['lama']=='si'
        assert visit['ianusVerified']=='si' and visit['ianusCollected']=='no'
        # We did NOT reinterpret the IANUS dispensing proxy as real medication adherence.
        assert visit['adherence']==''
        assert server.score(visit)==2
        updated={**visit,'inhaledRegimen':'triple','monotherapyClass':'','roflumilast':'si',
                 'azithromycin':'si','ianusCollected':'si'}
        update=c.put('/api/visits/VIS-CRD20',json=updated,
                     headers={**h,'X-RADAR-CHANGE-REASON':quote('Cambio de pauta en escenario ficticio')})
        assert update.status_code==200,update.text
        state=c.get('/api/state').json()
        assert (state['visits'][0]['lama'],state['visits'][0]['laba'],state['visits'][0]['ics'])==('si','si','si')
        assert state['visits'][0]['rev']==2
        book=c.get('/api/export/xlsx')
        assert book.status_code==200
        with zipfile.ZipFile(io.BytesIO(book.content)) as z:
            assert z.testzip() is None
            xml=''.join(z.read(f).decode() for f in z.namelist() if f.startswith('xl/worksheets/sheet'))
            assert 'Roflumilast' in xml and 'Agudizaciones moderadas 12m' in xml
            assert 'SIM-CRD20' in xml and 'triple' in xml
        audit=c.get('/api/audit/changes')
        assert audit.status_code==200
        assert any(row['field_name']=='inhaledRegimen' for row in audit.json())
