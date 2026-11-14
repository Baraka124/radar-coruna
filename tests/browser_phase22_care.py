"""Browser acceptance: status R081/R082 plus contacts and legacy action notice."""
from pathlib import Path
import sys,tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data/RADAR_CORUNA_v22_R081_R082.png')

def main():
 with tempfile.TemporaryDirectory() as td:
  server.DB_FILE=Path(td)/'phase22_browser.sqlite3'
  with TestClient(server.app) as client, sync_playwright() as pw:
   a=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'}).json()
   h={'X-RADAR-CSRF':a['csrf']};pid='SIM-BROW22'
   r=client.post('/api/patients',headers=h,json={'id':pid,'center':'SIM-CS01',
    'status':'incluido','copd':'si','consent':'si','enrolDate':'2026-01-10','spiroDate':'2025-12-20','weeks':5})
   assert r.status_code==201,r.text
   r=client.post('/api/visits',headers=h,json={'id':'VIS-B22','patient':pid,'type':'V0',
    'date':'2026-01-10','status':'parcial','action':'educacion','inhaler':'si'})
   assert r.status_code==201,r.text
   browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
   page=browser.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(16000)
   errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def transport(_src,path,init=None):
    init=init or {};body=init.get('body');resp=client.request(init.get('method','GET'),path,headers=init.get('headers',{}),content=body.encode() if isinstance(body,str) else body)
    return {'status':resp.status_code,'body':resp.text,'ctype':resp.headers.get('content-type','application/json')}
   page.expose_binding('py_request',transport)
   page.goto('about:blank')
   page.evaluate("window.fetch=async(path,init={})=>{const r=await window.py_request(path,init);return new Response(r.body,{status:r.status,headers:{'Content-Type':r.ctype}})};true")
   page.set_content((ROOT/'static/index.html').read_text(),wait_until='domcontentloaded')
   page.fill('#password','radar-demo-admin');page.locator('#authForm button[type=submit]').click()
   page.wait_for_function("document.body.classList.contains('signed-in') && !!document.querySelector('[data-route=eventos]')")
   page.wait_for_timeout(400)
   page.locator('[data-route=eventos]').click()
   page.wait_for_timeout(300)
   page.locator('[data-action=newevent]').first.click()
   page.locator('#epatient').select_option(pid)
   page.locator('#edate').fill('2026-02-01')
   page.locator('#eventForm button[type=submit]').click()
   page.locator('[data-action=careforevent]').wait_for()
   assert page.get_by_text('Sin registrar',exact=True).count()>=1
   page.locator('[data-action=careforevent]').first.click()
   assert page.locator('#careForm').is_visible()
   page.locator('#careUrgentStatus').select_option('no')
   page.locator('#careAdmissionStatus').select_option('nc')
   page.locator('#careForm button[type=submit]').click()
   page.locator('[data-action=careforevent]').first.wait_for()
   one=client.get('/api/state').json()['events'][0]
   assert one['emergencyStatus']=='no' and one['admissionStatus']=='nc'
   page.locator('[data-action=contactforevent]').first.click()
   page.locator('#edate').fill('2026-02-02')
   page.locator('#etype').select_option('urgencias')
   page.locator('#eventForm button[type=submit]').click()
   page.locator('[data-action=careforevent]').first.wait_for()
   one=client.get('/api/state').json()['events'][0]
   assert one['emergencyStatus']=='si' and one['admissionStatus']=='nc'
   assert one['emergencyDate']=='2026-02-02'
   page.locator('[data-action=careforevent]').first.click()
   assert page.locator('#careUrgentStatus').input_value()=='si'
   assert page.locator('#careAdmissionStatus').input_value()=='nc'
   page.screenshot(path=str(OUT),full_page=True)
   page.locator('[data-route=crd]').click()
   field=page.locator('[data-crd-code="action_inhaler_tech"]')
   field.wait_for(state='attached')
   panel_id=field.evaluate('(el) => el.closest(".crd-field-group").id')
   page.locator(f'#crdSectionNav [aria-controls="{panel_id}"]').click()
   field.wait_for(state='visible')
   assert page.locator('.crd-legacy-info summary').inner_text()=='Ver actuaciones antiguas para conciliar'
   page.locator('.crd-legacy-info summary').click()
   assert 'revisión explícita' in page.locator('.crd-legacy-info').inner_text()
   assert not errors,errors
   browser.close()
   print('PASS browser v0.22: R081/R082, contact reconciliation, legacy action notice; screenshot '+str(OUT))
if __name__=='__main__':main()
