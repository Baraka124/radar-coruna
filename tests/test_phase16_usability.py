"""Phase 16: no filled-in synthetic cohort, just isolated records in test DB."""
import io, zipfile, xml.etree.ElementTree as ET
from fastapi.testclient import TestClient
import server
from synthetic_v32_fixtures import valid_record
from phase16_usability import pending_work, analysis_long, cohort_wide

NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

def test_empty_worklist_and_empty_analysis():
    assert pending_work([],[])==[]
    assert analysis_long([],[])==[]
    assert cohort_wide([],[],[],[])==[]

def test_zero_score_missing_and_stage_labels():
    p={'id':'SIM-TEST','center':'SIM-CS01','status':'incluido'}
    v={'patient':'SIM-TEST','type':'V0','date':'2026-01-10','status':'completa',
       'rescue':'no','exacerb':'no','dyspnea':'no','activity':'no','cat':0,'mmrc':0,'action':'seguimiento'}
    one=analysis_long([p],[v]); assert one[0]['radar_score']==0 and one[0]['cat']==0
    assert pending_work([p],[v])[0]['step']=='Preparar V1'
    v2={**v,'type':'V2','date':'2027-01-10','cat':10}
    # V0/V2 pairs are permitted for descriptive output; absence of V1 remains visible as blank.
    wide=cohort_wide([p],[v,v2],[],[])[0]
    assert wide['radar_delta_v2_v0']==0 and wide['cat_delta_v2_v0']==10
    missing={**v,'type':'V1','date':'2026-07-10','rescue':''}
    x=analysis_long([p],[missing])[0]
    assert x['radar_score'] is None and x['radar_complete']=='no'
    assert x['cat']==0

def test_noneligible_screening_is_not_an_inclusion_task():
    p={'id':'SIM-EXCL','center':'SIM-CS01','status':'cribado','eligibilityDecision':'no_elegible'}
    row=pending_work([p],[])[0]
    assert row['priority']=='Sin pendientes de núcleo' and row['step']=='Cribado cerrado'

def login(c,user='admin'):
    r=c.post('/api/session',json={'username':user,'password':'radar-demo-'+user})
    assert r.status_code==200,r.text
    return {'X-RADAR-CSRF':r.json()['csrf']}

def names_and_sheet_text(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None
        names=[x.attrib['name'] for x in ET.fromstring(z.read('xl/workbook.xml')).findall('.//'+NS+'sheet')]
        joined=' '.join(z.read(k).decode() for k in z.namelist() if k.startswith('xl/worksheets/sheet') and k.endswith('.xml'))
    return names,joined

def test_worklist_export_and_scoping(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'v16.sqlite3')
    with TestClient(server.app) as client:
        h=login(client)
        assert client.get('/api/study/worklist').json()['rows']==[]
        zero=client.get('/api/export/xlsx');assert zero.status_code==200
        names,xml=names_and_sheet_text(zero.content)
        assert len(names)==46
        for x in ['ANALISIS_LONG_V16','COHORTE_LONGITUD_V16','PENDIENTES_V16']:
            assert x in names
        assert 'SIM-V16A' not in xml
        for pid,centre in [('SIM-V16A','SIM-CS01'),('SIM-V16B','SIM-CS02')]:
            r=client.post('/api/patients',headers=h,json=valid_record({'id':pid,'center':centre,'status':'incluido',
                'consent':'si','copd':'si','enrolDate':'2026-01-10','spiroDate':'2025-12-10'}))
            assert r.status_code==201,r.text
        a=client.post('/api/visits',headers=h,json={
            'id':'SIM-V16VIS0','patient':'SIM-V16A','type':'V0','date':'2026-01-10',
            'status':'completa','cat':0,'mmrc':0,'rescue':'no','exacerb':'no',
            'dyspnea':'no','activity':'no','action':'seguimiento'})
        assert a.status_code==201,a.text
        w=client.get('/api/study/worklist').json()['rows']
        assert {x['participant']:x['step'] for x in w}=={'SIM-V16A':'Preparar V1','SIM-V16B':'Registrar V0'}
        admin_export=client.get('/api/export/xlsx'); assert admin_export.status_code==200
        names,xml=names_and_sheet_text(admin_export.content)
        assert 'SIM-V16A' in xml and 'SIM-V16B' in xml
        login(client,'costa')
        only=client.get('/api/study/worklist').json()['rows']
        assert len(only)==1 and only[0]['participant']=='SIM-V16A'
        names,xml=names_and_sheet_text(client.get('/api/export/xlsx').content)
        assert len(names)==44 and 'CAMBIOS_CAMPO' not in names
        assert 'SIM-V16A' in xml and 'SIM-V16B' not in xml
