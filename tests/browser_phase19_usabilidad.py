"""End-to-end worklist navigation with an in-memory test transport."""
import sys,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]

def main():
 with tempfile.TemporaryDirectory() as td:
  server.DB_FILE=Path(td)/'v17_browser.sqlite3'
  with TestClient(server.app) as client, sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
   page=browser.new_page(viewport={'width':1366,'height':900})
   page.set_default_timeout(9000)
   errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   def transport(_source,path,init=None):
    init=init or {}
    body=init.get('body')
    r=client.request(init.get('method','GET'),path,headers=init.get('headers',{}),content=body.encode() if isinstance(body,str) else body)
    return {'status':r.status_code,'body':r.text,'ctype':r.headers.get('content-type','application/json')}
   page.expose_binding('py_request',transport)
   page.goto('about:blank')
   page.evaluate("window.fetch=async (path,init={})=>{const r=await window.py_request(path,init);return new Response(r.body,{status:r.status,headers:{'Content-Type':r.ctype}})};true")
   page.set_content((ROOT/'static/index.html').read_text(),wait_until='domcontentloaded')
   page.fill('#password','radar-demo-admin'); page.locator('#authForm button[type=submit]').click()
   page.locator('.action-worklist').wait_for()
   assert page.locator('.nav-divider').count()==2
   assert page.locator('#workspaceContext .context-path').inner_text().find('Resumen')>=0
   assert 'Aún no se han registrado' in page.locator('.action-worklist').inner_text()
   page.locator('[data-action=newpatient]').first.click()
   assert page.locator('#patientForm .clinical-block').count()>=4
   assert page.locator('#patientForm .clinical-block:not([open])').count()==2
   page.fill('#pcode','SIM-V16UI')
   page.select_option('#pstatus','incluido');page.select_option('#pcopd','si');page.select_option('#pconsent','si')
   page.select_option('#peligibility','elegible');page.select_option('#pactive','no')
   page.fill('#pspirodate','2025-12-10');page.fill('#penrol','2026-01-10');page.fill('#page','65')
   page.locator('#patientForm button[type=submit]').click()
   page.locator('.patient-journey').wait_for()
   page.locator('[data-route=inicio]').click()
   assert 'Registrar V0' in page.locator('.action-worklist').inner_text()
   page.locator('[data-action=nextwork]').click()
   assert 'Nueva evaluación' in page.locator('.head').inner_text()
   assert page.input_value('#vpatient')=='SIM-V16UI'
   assert page.locator('.visit-completeness').count()==1
   assert '0 de 7' in page.locator('#visitCompleteness').inner_text()
   assert page.locator('.clinical-nested').count()==1
   assert not page.locator('.clinical-nested').evaluate('(el)=>el.open')
   page.fill('#vcat','0');page.select_option('#vmmrc','0')
   for x in ['vrescue','vexacerb','vdyspnea','vactivity']:page.select_option('#'+x,'no')
   page.select_option('#vaction','seguimiento');page.select_option('#vstatus','completa')
   assert '7 de 7' in page.locator('#visitCompleteness').inner_text()
   page.screenshot(path='/mnt/data/RADAR_CORUNA_v19_evaluacion.png',full_page=True)
   assert page.locator('.completion-track').get_attribute('role')=='progressbar'
   page.locator('#visitForm button[type=submit]').click()
   page.locator('.saved-feedback').wait_for()
   page.locator('[data-route=inicio]').click()
   assert 'Preparar V1' in page.locator('.action-worklist').inner_text()
   page.screenshot(path='/mnt/data/RADAR_CORUNA_v19_consulta.png',full_page=True)
   page.set_viewport_size({'width':390,'height':844})
   page.locator('[data-route=cohorte]').click()
   assert page.locator('.nav').evaluate('(e)=>e.scrollWidth>=e.clientWidth')
   assert page.locator('.context-export').is_visible()
   page.screenshot(path='/mnt/data/RADAR_CORUNA_v19_movil.png',full_page=True)
   assert not errors,errors
   browser.close()
   print('PASS: Phase 17 grouped navigation + form hierarchy + completeness + responsive workflow')
if __name__=='__main__':main()
