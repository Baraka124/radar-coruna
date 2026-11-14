"""v0.26 browser acceptance: CRD sections, per-visit drafts, saving, correction and links."""
from pathlib import Path
import sys,tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data/RADAR_CORUNA_UI_v26')
OUT.mkdir(exist_ok=True)

def open_app(page,client):
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def transport(_src,path,init=None):
  init=init or {};body=init.get('body')
  r=client.request(init.get('method','GET'),path,headers=init.get('headers',{}),content=body.encode() if isinstance(body,str) else body)
  return {'status':r.status_code,'body':r.text,'ctype':r.headers.get('content-type','application/json')}
 page.expose_binding('py_request',transport)
 page.goto('about:blank')
 page.evaluate("window.fetch=async(path,init={})=>{const r=await window.py_request(path,init);return new Response(r.body,{status:r.status,headers:{'Content-Type':r.ctype}})};true")
 page.set_content((ROOT/'static/index.html').read_text(encoding='utf8'),wait_until='domcontentloaded')
 page.fill('#password','radar-demo-admin')
 page.locator('#authForm button[type=submit]').click()
 page.locator('body.signed-in').wait_for()
 page.locator('#root[data-view=inicio]').wait_for()
 page.wait_for_timeout(450)
 return errors

def seed(client):
 auth=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
 assert auth.status_code==200,auth.text
 h={'X-RADAR-CSRF':auth.json()['csrf']}
 payload={'id':'SIM-V26-001','center':'SIM-CS01','copd':'si','consent':'si','enrolDate':'2026-01-10','spiroDate':'2025-12-15','status':'incluido','birthDate':'1968-11-11','weeks':4,'priorExModerate':2,'priorExSevere':1}
 r=client.post('/api/patients',json=payload,headers=h);assert r.status_code==201,r.text
 data={'id':'VIS-V26-0','patient':'SIM-V26-001','type':'V0','date':'2026-01-10','status':'parcial','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no','cat':12,'mmrc':0,'action':'seguimiento','inhaledRegimen':'mono','monotherapyClass':'lama','ianusVerified':'si','ianusCollected':'no'}
 r=client.post('/api/visits',json=data,headers=h);assert r.status_code==201,r.text
 data={**data,'id':'VIS-V26-1','type':'V1','date':'2026-07-11'}
 r=client.post('/api/visits',json=data,headers=h);assert r.status_code==201,r.text

def select_code(page,code,value):
 ctrl=page.locator(f'[data-crd-code="{code}"]')
 assert ctrl.count()==1,code
 panel=ctrl.locator('xpath=ancestor::*[contains(@class,"crd-field-group")]')
 idx=int(panel.get_attribute('id').split('-')[-1]);page.locator(f'#crdSectionNav [data-crd-section="{idx}"]').click()
 assert ctrl.is_visible(),code
 ctrl.select_option(value)
 return idx

def main():
 with tempfile.TemporaryDirectory() as td:
  server.DB_FILE=Path(td)/'radar_v26_test.sqlite3'
  with TestClient(server.app) as client, sync_playwright() as pw:
   seed(client)
   browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
   page=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
   page.set_default_timeout(11000)
   errors=open_app(page,client)
   page.locator('[data-route="crd"]').click()
   page.locator('#root[data-view=crd] #studyForm').wait_for()
   assert 'CRD complementario' in page.locator('.head h1').inner_text()
   assert page.locator('#crdSectionNav button').count()>1
   assert page.locator('.crd-field-group:not([hidden])').count()==1
   idx=select_code(page,'comorb_ihd','no')
   assert '1 cambio sin guardar' in page.locator('#crdDraftStatus').inner_text()
   page.screenshot(path=str(OUT/'v26_crd_desktop.png'),full_page=False)
   # Changing CRD visit must keep unsaved V0 draft but not persist it to SQLite.
   page.locator('[data-crd-visit="V1"]').click()
   assert 'V1' in page.locator('.head h1').inner_text()
   assert not client.get('/api/study/observations').json()
   page.locator('[data-crd-visit="V0"]').click()
   assert page.locator('[data-crd-code="comorb_ihd"]').input_value()=='no'
   assert 'sin guardar' in page.locator('#crdDraftStatus').inner_text()
   # Keyboard tab navigation should work, as should field preservation.
   tabs=page.locator('#crdSectionNav button');tabs.nth(idx).focus();tabs.nth(idx).press('ArrowRight')
   assert page.locator('.crd-field-group:not([hidden])').count()==1
   assert page.locator('[data-crd-code="comorb_ihd"]').input_value()=='no'
   page.locator('#studyForm button[type=submit]').click()
   page.locator('.crd-success').wait_for()
   rows=client.get('/api/study/observations').json()
   assert len(rows)==1 and rows[0]['variable_code']=='comorb_ihd' and rows[0]['value']=='no',rows
   assert 'Sin cambios pendientes' in page.locator('#crdDraftStatus').inner_text()
   # Corrections still require the existing server audit reason.
   select_code(page,'comorb_ihd','si')
   page.locator('#studyForm button[type=submit]').click()
   page.locator('#crdError.show').wait_for()
   assert page.locator('#crdError.show').count()==1
   assert 'sin guardar' in page.locator('#crdDraftStatus').inner_text()
   page.fill('#crdCorrectionReason','Corrección confirmada tras revisar la fuente')
   page.locator('#studyForm button[type=submit]').click()
   page.locator('.crd-success').wait_for()
   rows=client.get('/api/study/observations').json()
   assert len(rows)==1 and rows[0]['value']=='si' and rows[0]['rev']==2,rows
   # A direct contextual route to the primary visit is available and preserves selection.
   page.locator('.crd-context-links [data-action=workflowvisit]').click()
   assert page.locator('#visitForm').count()==1
   assert page.locator('#vpatient').input_value()=='SIM-V26-001'
   assert page.locator('#vtype').input_value()=='V0'
   assert page.locator('#visitForm [data-action=crdfor]').count()==1
   assert not errors,errors
   page.close()
   mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
   mobile.set_default_timeout(11000)
   errors2=open_app(mobile,client)
   mobile.locator('#mobileNavToggle').click()
   mobile.wait_for_function("document.body.classList.contains('mobile-nav-open')")
   mobile.wait_for_timeout(350)
   try:
    mobile.locator('[data-route=crd]').click(timeout=4500)
   except BrowserTimeout:
    if not mobile.evaluate("document.body.classList.contains('mobile-nav-open')"):
     mobile.locator('#mobileNavToggle').click()
    mobile.wait_for_timeout(340)
    mobile.locator('[data-route=crd]').click(timeout=8500)
   mobile.locator('#root[data-view=crd] #studyForm').wait_for()
   mobile.wait_for_function("!document.body.classList.contains('mobile-nav-open')")
   mobile.wait_for_timeout(350)
   assert mobile.locator('#studyForm').count()==1
   mobile.screenshot(path=str(OUT/'v26_crd_mobile.png'),full_page=False)
   assert mobile.evaluate('document.documentElement.scrollWidth-window.innerWidth')<=2,'Horizontal overflow'
   mobile.locator('[data-crd-visit=V1]').click()
   assert 'V1' in mobile.locator('.head h1').inner_text()
   assert not errors2,errors2
   browser.close()
  print('PASS v26: draft across V0/V1, section navigation, corrections, context, mobile 390px, no JS errors')
if __name__=='__main__':main()
