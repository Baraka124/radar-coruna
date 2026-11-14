"""Phase 18: reproducible scientific-report calculations with minimal fictional records."""
import io
import zipfile
import xml.etree.ElementTree as ET
from fastapi.testclient import TestClient
import server
from synthetic_v32_fixtures import valid_record
from phase18_reporting import make_report,wilson_95

NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

def pat(pid='SIM-1801',centre='SIM-CS01'):
    return {'id':pid,'center':centre,'status':'incluido'}

def v(pid,stage,**kw):
    return {'id':f'SIM-18-{pid}-{stage}','patient':pid,'type':stage,'date':'2026-01-10' if stage=='V0' else '2027-01-10',
            'status':'completa','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no',
            'cat':0,'mmrc':0,'action':'seguimiento',**kw}

def get(report,name):
    return next(r for r in report['indicators'] if r['indicator']==name)

def test_empty_cohort_has_no_false_percentages():
    r=make_report([],[])
    assert r['counts']['included']==0
    assert get(r,'Mal control basal RADAR ≥4')['value'] is None
    assert get(r,'Cambio medio CAT V2−V0')['value'] is None
    assert r['transitions'][0]['percent'] is None
    assert wilson_95(0,0)==(None,None)

def test_independent_cat_and_mmrc_pairs_without_radar_pair():
    p=[pat()]
    visits=[v('SIM-1801','V0',rescue='',cat=0,mmrc=0),v('SIM-1801','V2',rescue='si',cat=14,mmrc=2)]
    r=make_report(p,visits)
    assert r['counts']['radar_pairs']==0 and r['counts']['cat_pairs']==1
    assert get(r,'Cambio medio CAT V2−V0')['value']==14
    assert get(r,'Cambio medio mMRC V2−V0')['value']==2
    assert r['pairs'][0]['delta_radar'] is None
    assert all(x['percent'] is None for x in r['transitions'])

def test_denominators_zero_valid_and_control_transitions():
    patients=[pat('SIM-A'),pat('SIM-B'),pat('SIM-C')]
    visits=[v('SIM-A','V0'),v('SIM-A','V2',rescue='si',exacerb='si'),
        v('SIM-B','V0',rescue='si',exacerb='si'),v('SIM-B','V2'),
        v('SIM-C','V0',rescue=''),v('SIM-C','V2',cat=None)]
    r=make_report(patients,visits)
    assert get(r,'Mal control basal RADAR ≥4')['numerator']==1
    assert get(r,'Mal control basal RADAR ≥4')['denominator']==2
    assert get(r,'Mal control basal RADAR ≥4')['value']==50
    assert r['counts']['radar_pairs']==2 and r['counts']['cat_pairs']==2
    assert r['stages'][0]['radar_incomplete_recorded']==1
    assert sum(x['n'] for x in r['transitions'])==2
    assert [x for x in r['transitions'] if x['control_v0']=='Buen control' and x['control_v2']=='Mal control'][0]['n']==1
    low,high=wilson_95(1,2)
    assert low<50<high

def test_unperformed_visit_excluded_and_events_distinct():
    r=make_report([pat()], [v('SIM-1801','V0'),v('SIM-1801','V2',status='no_realizada')],
                  episodes=[{'patient':'SIM-1801','copd':'si'}],
                  contacts=[{'patient':'SIM-1801','copd':'si','type':'ingreso'}])
    assert r['stages'][2]['visits_recorded']==0
    assert get(r,'Agudizaciones EPOC registradas')['value']==1
    assert get(r,'Ingresos EPOC registrados')['value']==1
    assert get(r,'RADAR V2 completo')['value']==0.0

def test_api_and_export_centre_scope(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'v18.sqlite3')
    with TestClient(server.app) as c:
        a=c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
        assert a.status_code==200
        h={'X-RADAR-CSRF':a.json()['csrf']}
        for pid,cent in [('SIM-18CO','SIM-CS01'),('SIM-18OT','SIM-CS02')]:
            response=c.post('/api/patients',headers=h,json=valid_record({'id':pid,'center':cent,'status':'incluido',
                'copd':'si','consent':'si','enrolDate':'2026-01-10','spiroDate':'2025-12-10'}))
            assert response.status_code==201,response.text
        report=c.get('/api/study/reporting')
        assert report.status_code==200 and report.json()['counts']['included']==2
        ex=c.get('/api/export/xlsx');assert ex.status_code==200
        with zipfile.ZipFile(io.BytesIO(ex.content)) as z:
            names=[node.attrib['name'] for node in ET.fromstring(z.read('xl/workbook.xml')).findall('.//'+NS+'sheet')]
            assert len(names)==46 and 'PAREJAS_INDEP_V18' in names and 'TRANSICIONES_V18' in names
        a=c.post('/api/session',json={'username':'costa','password':'radar-demo-costa'})
        assert a.status_code==200
        scoped=c.get('/api/study/reporting').json()
        assert scoped['counts']['included']==1
        workbook=c.get('/api/export/xlsx').content
        with zipfile.ZipFile(io.BytesIO(workbook)) as z:
            xml=' '.join(z.read(k).decode() for k in z.namelist() if k.startswith('xl/worksheets/sheet'))
            assert 'SIM-18CO' in xml and 'SIM-18OT' not in xml

def test_legacy_indicator_does_not_suppress_independent_cat_pair():
    from phase12_analysis import make_analysis
    patients=[pat()]
    visits=[v('SIM-1801','V0',rescue='',cat=0),v('SIM-1801','V2',cat=8)]
    m=next(x for x in make_analysis(patients,visits)['metrics'] if x['indicator']=='Cambio medio CAT V2−V0')
    assert m['denominator']==1 and m['value']==8
