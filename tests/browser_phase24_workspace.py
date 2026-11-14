"""RADAR-CORUÑA v0.24: main workspace visual and interaction acceptance."""
from pathlib import Path
import tempfile, sys
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data/RADAR_CORUNA_UI_v24')

def main():
 with tempfile.TemporaryDirectory() as td:
  server.DB_FILE=Path(td)/'workspace.sqlite3'
  with TestClient(server.app) as client, sync_playwright() as pw:
   auth=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'}).json()
   head={'X-RADAR-CSRF':auth['csrf']}
   for p in [
    {'id':'SIM-CRD-001','center':'SIM-CS01','status':'incluido','copd':'si','consent':'si','enrolDate':'2026-01-10','spiroDate':'2025-12-20','weeks':5},
    {'id':'SIM-CRD-002','center':'SIM-CS01','status':'cribado','copd':'si','consent':'no','enrolDate':'2026-01-11','spiroDate':'2025-12-21','weeks':5},
   ]:
    r=client.post('/api/patients',headers=head,json=p)
    assert r.status_code==201,r.text
   r=client.post('/api/visits',headers=head,json={'id':'VIS-UI-001','patient':'SIM-CRD-001','type':'V0','date':'2026-01-10','status':'completa','action':'seguimiento','inhaler':'si','rescue':'no','exacerb':'no','dyspnea':'si','activity':'no','cat':12,'mmrc':2})
   assert r.status_code==201,r.text
   browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
   for name,width,height in [('desktop',1440,900),('mobile',390,844)]:
    page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
    page.set_default_timeout(14000)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def transport(_src,path,init=None):
     init=init or {};body=init.get('body')
     resp=client.request(init.get('method','GET'),path,headers=init.get('headers',{}),content=body.encode() if isinstance(body,str) else body)
     return {'status':resp.status_code,'body':resp.text,'ctype':resp.headers.get('content-type','application/json')}
    page.expose_binding('py_request',transport)
    page.goto('about:blank')
    page.evaluate("window.fetch=async(path,init={})=>{const r=await window.py_request(path,init);return new Response(r.body,{status:r.status,headers:{'Content-Type':r.ctype}})};true")
    page.set_content((ROOT/'static/index.html').read_text(encoding='utf8'),wait_until='domcontentloaded')
    page.fill('#password','radar-demo-admin')
    page.locator('#authForm button[type=submit]').click()
    page.locator('body.signed-in').wait_for()
    page.wait_for_timeout(250)
    assert page.locator('.environment-note').count()==1
    assert not page.locator('.environment-note').get_attribute('open')
    page.locator('.environment-note summary').click()
    assert page.locator('.environment-note').get_attribute('open') is not None
    page.locator('.environment-note summary').click()
    assert page.locator('.environment-note').get_attribute('open') is None
    if name=='desktop':
     page.screenshot(path=str(OUT/'v24_overview.png'),full_page=False)
     page.locator('[data-route=cohorte]').click()
     page.wait_for_timeout(180)
     assert page.locator('#cohortCount').inner_text()=='2 de 2 participantes'
     page.locator('#filterPatients').fill('002')
     assert page.locator('#cohortCount').inner_text()=='1 de 2 participantes'
     page.locator('#filterPatients').fill('NONEXIST')
     assert page.locator('#cohortCount').inner_text()=='0 de 2 participantes'
     assert page.get_by_text('No hay participantes con estos filtros.',exact=False).count()==1
     page.locator('#clearCohortFilters').click()
     assert page.locator('#filterPatients').input_value()==''
     assert page.locator('#cohortCount').inner_text()=='2 de 2 participantes'
     page.screenshot(path=str(OUT/'v24_participants.png'),full_page=False)
     page.locator('[data-route=visitas]').click();page.wait_for_timeout(180)
     assert page.get_by_text('VIS-UI-001').count()==0 # internal ids not shown
     assert page.get_by_text('SIM-CRD-001').count()>0
     page.screenshot(path=str(OUT/'v24_visits.png'),full_page=False)
     page.locator('[data-route=analisis]').click();page.wait_for_timeout(180)
     page.screenshot(path=str(OUT/'v24_analysis.png'),full_page=False)
     assert page.locator('#root[data-view=analisis]').count()==1
     print('desktop: overview, cohort filter/reset, visits, analysis PASS')
    else:
     page.screenshot(path=str(OUT/'v24_mobile_overview.png'),full_page=False)
     page.locator('#mobileNavToggle').click();page.locator('[data-route=cohorte]').click()
     page.wait_for_timeout(200)
     assert page.locator('#cohortCount').is_visible()
     assert page.locator('#filterPatients').is_visible()
     assert page.locator('#clearCohortFilters').is_visible()
     page.screenshot(path=str(OUT/'v24_mobile_participants.png'),full_page=False)
     viewport_overflow=page.evaluate('document.documentElement.scrollWidth-innerWidth')
     assert viewport_overflow<=2,f'page overflow {viewport_overflow}'
     print('mobile: drawer, cohort filters, no horizontal page overflow PASS')
    assert not errors,errors
    page.close()
   browser.close()
if __name__=='__main__':main()
