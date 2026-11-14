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
  server.DB_FILE=Path(td)/'v16_browser.sqlite3'
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
   assert 'Aún no se han registrado' in page.locator('.action-worklist').inner_text()
   page.locator('[data-action=newpatient]').first.click()
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
   page.fill('#vcat','0');page.select_option('#vmmrc','0')
   for x in ['vrescue','vexacerb','vdyspnea','vactivity']:page.select_option('#'+x,'no')
   page.select_option('#vaction','seguimiento');page.select_option('#vstatus','completa')
   page.locator('#visitForm button[type=submit]').click()
   page.locator('.saved-feedback').wait_for()
   page.locator('[data-route=inicio]').click()
   assert 'Preparar V1' in page.locator('.action-worklist').inner_text()
   page.screenshot(path='/mnt/data/RADAR_CORUNA_v16_trabajo_pendiente.png',full_page=True)
   assert not errors,errors
   browser.close()
   print('PASS: empty dashboard -> patient -> nextwork V0 -> zero-score -> nextwork V1 -> no JS errors')
if __name__=='__main__':main()
