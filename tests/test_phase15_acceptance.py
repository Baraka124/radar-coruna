"""End-to-end study acceptance: one synthetic participant, every visit and the research export."""
from __future__ import annotations
import io
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from synthetic_v32_fixtures import valid_record


def sign_in(client, who='admin'):
    res=client.post('/api/session',json={'username':who,'password':'radar-demo-'+who})
    assert res.status_code==200,res.text
    return {'X-RADAR-CSRF':res.json()['csrf']}


def insert(client,headers,path,payload):
    res=client.post(path,headers=headers,json=payload)
    assert res.status_code==201,(path,res.status_code,res.text)
    return res.json()


def worksheets(book):
    with zipfile.ZipFile(io.BytesIO(book)) as z:
        assert z.testzip() is None
        tree=ET.fromstring(z.read('xl/workbook.xml'))
        ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        names=[s.attrib['name'] for s in tree.findall('.//m:sheet',ns)]
        content='\n'.join(z.read(n).decode('utf-8') for n in z.namelist() if n.startswith('xl/worksheets/') and n.endswith('.xml'))
    return names,content


def test_full_study_journey_and_excel(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DB_FILE',tmp_path/'phase15.sqlite3')
    monkeypatch.delenv('RADAR_SEED_DEMO',raising=False)
    with TestClient(server.app) as c:
        h=sign_in(c)
        initial=c.get('/api/state').json()
        assert initial['patients']==initial['visits']==initial['events']==initial['contacts']==[]
        patient={'id':'SIM-F15','center':'SIM-CS01','status':'incluido','consent':'si','copd':'si',
            'eligibilityDecision':'elegible','activeExacerb':'no','enrolDate':'2026-01-10',
            'spiroDate':'2025-12-10','age':65,'fev1':61,'ratio':0.58,'regular':'si','capacity':'si'}
        insert(c,h,'/api/patients',valid_record(patient))
        for typ,day,cat,rescue in [('V0','2026-01-10',16,'si'),('V1','2026-07-10',12,'no'),('V2','2027-01-10',8,'no')]:
            insert(c,h,'/api/visits',{'id':'SIM-VIS-'+typ,'patient':'SIM-F15','type':typ,
                'date':day,'cat':cat,'mmrc':0,'rescue':rescue,'exacerb':'no','dyspnea':'no',
                'activity':'no','action':'seguimiento','status':'completa'})
        result=c.put('/api/study/observations/SIM-F15/V0',headers=h,
            json={'observations':{'adherence_method':'cualitativo','assessment_seconds':120,'action_plan_documented':'si'},
            'revisions':{},'reason':''})
        assert result.status_code==200,result.text
        insert(c,h,'/api/episodes',{'id':'SIM-EPI-15','patient':'SIM-F15','date':'2026-03-15',
            'severity':'moderada','copd':'si','steroids':'si','antibiotics':'no','source':'hce'})
        insert(c,h,'/api/contacts',{'id':'SIM-CON-15','patient':'SIM-F15','date':'2026-03-15',
            'event':'SIM-EPI-15','type':'urgencias','copd':'si','source':'hce'})
        result=c.put('/api/study/phase14',headers=h,json={'kind':'implementation',
            'key':'SIM-CS01:2026-10','payload':{'eligible_copd_visits':10,'visits_with_radar':8},'rev':0,'reason':'','centre':''})
        assert result.status_code==200,result.text
        state=c.get('/api/state').json()
        assert [server.score(v) for v in state['visits']]==[3,0,0]
        assert len(state['events'])==1 and len(state['contacts'])==1
        assert len(c.get('/api/study/observations').json())==3
        assert c.get('/api/study/phase14').json()['metrics']['indicators'][2]['value']==80
        # A correction must appear separately from initial creation.
        old=next(v for v in state['visits'] if v['type']=='V1')
        from urllib.parse import quote
        res=c.put('/api/visits/SIM-VIS-V1',headers={**h,'X-RADAR-CHANGE-REASON':quote('CAT verificado frente a la ficha')},
            json={**old,'cat':10})
        assert res.status_code==200,res.text
        changes=c.get('/api/audit/changes').json()
        assert any(x['kind']=='visit' and x['field_name']=='cat' and x['prior_value']=='12' and x['new_value']=='10' for x in changes)
        wb=c.get('/api/export/xlsx');assert wb.status_code==200
        names,xml=worksheets(wb.content)
        assert len(names)==46
        for required in ['PARTICIPANTES','VISITAS','CRD_MEDICIONES','EPISODIOS','CONTACTOS',
            'ANALISIS_V12','PAREJAS_V12','IMPLANTACION_MENSUAL_V14','CAMBIOS_CAMPO']:
            assert required in names
        for token in ['SIM-F15','SIM-VIS-V0','SIM-VIS-V1','SIM-VIS-V2','SIM-EPI-15','SIM-CON-15','adherence_method','eligible_copd_visits']:
            assert token in xml,token
        assert '#REF!' not in xml and '#DIV/0!' not in xml
        # Export belongs to current user/centre. A second-centre participant must not appear.
        insert(c,h,'/api/patients',valid_record({**patient,'id':'SIM-OTHER15','center':'SIM-CS02'}))
        sign_in(c,'costa')
        scoped=c.get('/api/export/xlsx');assert scoped.status_code==200
        scoped_names,scoped_xml=worksheets(scoped.content)
        assert 'SIM-F15' in scoped_xml and 'SIM-OTHER15' not in scoped_xml
        assert 'CAMBIOS_CAMPO' not in scoped_names
