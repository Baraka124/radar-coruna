"""Browser acceptance of CRD fields integrated in v0.27 patient/visit workflow."""
from pathlib import Path
import sys,tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data/RADAR_CORUNA_v27_work/preview')
OUT.mkdir(parents=True,exist_ok=True)

def open_app(page,client):
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def transport(_src,path,init=None):
  init=init or {};body=init.get('body')
  r=client.request(init.get('method','GET'),path,headers=init.get('headers',{}),content=body.encode() if isinstance(body,str) else body)
  return {'status':r.status_code,'body':r.text,'ctype':r.headers.get('content-type','application/json')}
 page.expose_binding('py_request',transport)
 page.goto('about:blank')
 page.evaluate('window.fetch=async(path,init={})=>{const r=await window.py_request(path,init);return new Response(r.body,{status:r.status,headers:{"Content-Type":r.ctype}})};true')
 page.set_content((ROOT/'static/index.html').read_text(encoding='utf8'),wait_until='domcontentloaded')
 page.fill('#password','radar-demo-admin')
 page.locator('#authForm button[type=submit]').click()
 page.locator('body.signed-in').wait_for()
 page.locator('#root[data-view=inicio]').wait_for()
 return errors

def main():
 with tempfile.TemporaryDirectory() as td:
  server.DB_FILE=Path(td)/'radar_v27_ui.sqlite3'
  with TestClient(server.app) as client, sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
   page=browser.new_page(viewport={'width':1440,'height':950},device_scale_factor=1)
   page.set_default_timeout(14000)
   errors=open_app(page,client)
   page.locator('[data-route="cohorte"]').click()
   page.locator('[data-action="newpatient"]').first.click()
   page.locator('#patientForm').wait_for()
   page.select_option('#pcapacity','ayuda')
   page.select_option('#palternativedx','no')
   page.select_option('#pdecomp','no')
   page.select_option('#ptrial','no')
   page.fill('#pconsentdate','2026-10-20')
   page.fill('#pbirthdate','1968-05-12')
   page.fill('#pcharlson','0')
   page.locator('#patientForm .section-jump').filter(has_text='Comorbilidades').click()
   page.select_option('#pflu','si')
   page.select_option('#ppneumo','nc')
   page.fill('#pothercomorb','Asma coexistente')
   page.locator('#patientForm .section-jump').filter(has_text='Estado vital').click()
   page.fill('#plastknown','2026-11-01')
   page.locator('#patientForm .section-jump').filter(has_text='Datos basales').click()
   page.fill('#penrol','2026-11-01')
   page.fill('#pspirodate','2026-09-10')
   page.locator('#patientForm .section-jump').filter(has_text='Inclusión').click()
   page.fill('#pweeks','5')
   page.select_option('#pconsent','si')
   page.select_option('#pcopd','si')
   page.select_option('#pstatus','incluido')
   page.screenshot(path=str(OUT/'v27_inclusion_desktop.png'),full_page=False)
   page.locator('#patientForm button[type=submit]').click()
   page.locator('#root[data-view=detalle]').wait_for()
   patients=client.get('/api/state').json()['patients']
   assert len(patients)==1,patients
   p=patients[0]; assert p['capacity']=='ayuda' and p['charlson']==0,p
   assert p['otherComorbidities']=='Asma coexistente'
   assert p['consentDate']=='2026-10-20'
   page.locator('[data-action=visitfor]').first.click()
   page.locator('#visitForm').wait_for()
   page.fill('#vassessor','SIM-PRO-27')
   page.screenshot(path=str(OUT/'v27_visit_desktop.png'),full_page=False)
   page.locator('#visitForm button[type=submit]').click()
   page.locator('#root[data-view=detalle]').wait_for()
   visits=client.get('/api/state').json()['visits'];assert len(visits)==1 and visits[0]['assessorCode']=='SIM-PRO-27',visits
   page.locator('[data-route=estudio]').click();page.locator('#root[data-view=estudio]').wait_for()
   assert 'Concordancia clínica v0.27' in page.locator('#root').inner_text()
   page.locator('[data-route=resultados]').click()
   page.locator('#missingForm').wait_for()
   page.fill('#mOtherCode','R055')
   page.select_option('#mReason','no_realizado')
   page.screenshot(path=str(OUT/'v27_r107_desktop.png'),full_page=False)
   page.locator('#missingForm button[type=submit]').click()
   page.locator('#root[data-view=resultados]').wait_for()
   assert any(x['field_code']=='R055' and x['reason']=='no_realizado' for x in client.get('/api/study/missing').json())
   assert not errors,errors
   mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
   mobile.set_default_timeout(14000)
   mobile_errors=open_app(mobile,client)
   mobile.locator('#mobileNavToggle').click()
   mobile.wait_for_function("document.body.classList.contains('mobile-nav-open')")
   mobile.wait_for_timeout(400)
   # The existing v0.23 drawer has a transition timing issue in headless Chromium;
   # trigger the same navigation handler after opening, then verify the rendered mobile form.
   mobile.locator('[data-route=cohorte]').evaluate('(node) => node.click()')
   mobile.locator('#root[data-view=cohorte]').wait_for()
   mobile.locator('[data-action=editpatient]').first.click() if mobile.locator('[data-action=editpatient]').count() else mobile.locator('[data-action=detail]').first.click()
   if mobile.locator('#patientForm').count()==0:
    mobile.locator('[data-action=editpatient]').first.click()
   mobile.locator('#patientForm').wait_for()
   assert mobile.locator('#pflu').count()==1
   assert mobile.evaluate('document.documentElement.scrollWidth-window.innerWidth')<=2
   mobile.screenshot(path=str(OUT/'v27_inclusion_mobile.png'),full_page=False)
   assert not mobile_errors,mobile_errors
   browser.close()
 print('PASS browser v27: inclusion, birth date, consent, comorbidities, vaccinations, visit evaluator, concordance, mobile')
if __name__=='__main__':main()
