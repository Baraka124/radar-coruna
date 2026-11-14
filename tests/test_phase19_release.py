"""Final software-acceptance regression: synthetic data only."""
from __future__ import annotations
import io
import zipfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
import pytest
import server
from synthetic_v32_fixtures import valid_record
from phase16_usability import radar, analysis_long, cohort_wide
from phase12_analysis import radar_score
from phase18_reporting import make_report
from export_research import score_visit


def signin(c,who='admin'):
    res=c.post('/api/session',json={'username':who,'password':'radar-demo-'+who})
    assert res.status_code==200,res.text
    return {'X-RADAR-CSRF':res.json()['csrf']}


def test_non_performed_visit_is_never_scored_in_any_scientific_layer():
    unanswered={'patient':'SIM-TEST','type':'V1','date':'2026-07-10','status':'no_realizada','rescue':'si',
                'exacerb':'si','dyspnea':'si','activity':'si','cat':12,'mmrc':1}
    assert server.score(unanswered) is None
    assert radar(unanswered) is None
    assert radar_score(unanswered) is None
    assert score_visit(unanswered) is None
    p={'id':'SIM-TEST','status':'incluido','center':'SIM-CS01'}
    row=analysis_long([p],[unanswered])[0]
    assert row['radar_score'] is None and row['cat'] is None and row['mmrc'] is None
    report=make_report([p],[unanswered]);stage=report['stages'][1]
    assert stage['radar_complete']==0 and stage['visits_recorded']==0
    assert cohort_wide([p],[unanswered],[],[])[0]['radar_v1'] is None
    v0={**unanswered,'type':'V0','date':'2026-01-10','status':'completa'}
    v2={**unanswered,'type':'V2','date':'2027-01-10','status':'no_realizada'}
    assert cohort_wide([p],[v0,v2],[],[])[0]['cat_delta_v2_v0'] is None


def test_final_release_fresh_start_scoring_export_and_scope(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'fase19.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        h=signin(c)
        empty=c.get('/api/state').json()
        assert not any(empty[key] for key in ('patients','visits','events','contacts'))
        assert c.get('/api/health').json()['version'] == server.app.version
        assert tuple(map(int, server.app.version.split('.'))) >= (0, 19, 0)
        p={'id':'SIM-F19','center':'SIM-CS01','status':'incluido','copd':'si','consent':'si',
           'eligibilityDecision':'elegible','activeExacerb':'no','enrolDate':'2026-01-10',
           'spiroDate':'2025-12-10','age':61,'fev1':60,'ratio':0.59}
        assert c.post('/api/patients',headers=h,json=valid_record(p)).status_code==201
        q={'patient':'SIM-F19','status':'completa','rescue':'no','exacerb':'no','dyspnea':'no',
           'activity':'no','cat':0,'mmrc':0,'action':'seguimiento'}
        assert c.post('/api/visits',headers=h,json={**q,'id':'SIM-V0-F19','type':'V0','date':'2026-01-10'}).status_code==201
        assert c.post('/api/visits',headers=h,json={**q,'id':'SIM-V1-F19','type':'V1','date':'2026-07-10',
            'status':'no_realizada','reason':'no_contacto','rescue':'si'}).status_code==201
        assert c.post('/api/visits',headers=h,json={**q,'id':'SIM-V2-F19','type':'V2','date':'2027-01-10',
            'rescue':'si'}).status_code==201
        result=c.get('/api/study/reporting').json()
        assert result['stages'][0]['radar_complete']==1
        assert result['stages'][1]['radar_complete']==0
        assert result['stages'][2]['radar_complete']==1
        assert result['counts']['radar_pairs']==1
        assert result['counts']['cat_pairs']==1
        book=c.get('/api/export/xlsx')
        assert book.status_code==200
        with zipfile.ZipFile(io.BytesIO(book.content)) as z:
            assert z.testzip() is None
            data='\n'.join(z.read(f).decode() for f in z.namelist() if f.startswith('xl/worksheets/sheet') and f.endswith('.xml'))
            wb=z.read('xl/workbook.xml').decode()
            assert 'INFORME_V18' in wb and 'TRAZABILIDAD' in wb
            assert 'SIM-F19' in data
            assert 'no_realizada' in data
            assert 'IF(F' in data and 'no_realizada' in data
            assert '#REF!' not in data and '#DIV/0!' not in data
        assert signin(c,'interior')
        mine=c.get('/api/state').json()
        assert mine['patients']==[] and mine['visits']==[]
        r=c.get('/api/export/xlsx');assert r.status_code==200
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            xml=''.join(z.read(f).decode() for f in z.namelist() if f.startswith('xl/worksheets/sheet') and f.endswith('.xml'))
            assert 'SIM-F19' not in xml
