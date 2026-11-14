"""Phase 18 browser acceptance using only one fictional participant."""
from pathlib import Path
import sys,tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]

def main():
 with tempfile.TemporaryDirectory() as d:
  server.DB_FILE=Path(d)/'v18_browser.sqlite3'
  with TestClient(server.app) as client, sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
   page=browser.new_page(viewport={'width':1440,'height':900});page.set_default_timeout(8500)
   errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def transport(_src,path,init=None):
    init=init or {};body=init.get('body')
    response=client.request(init.get('method','GET'),path,headers=init.get('headers',{}),content=body.encode() if isinstance(body,str) else body)
    return {'status':response.status_code,'body':response.text,'ctype':response.headers.get('content-type','application/json')}
   page.expose_binding('py_request',transport)
   page.goto('about:blank')
   page.evaluate("window.fetch=async(path,init={})=>{const r=await window.py_request(path,init);return new Response(r.body,{status:r.status,headers:{'Content-Type':r.ctype}})};true")
   page.set_content((ROOT/'static/index.html').read_text(),wait_until='domcontentloaded')
   page.fill('#password','radar-demo-admin');page.locator('#authForm button[type=submit]').click()
   page.locator('[data-route=analisis]').click()
   page.locator('text=Informe de cohorte · v0.18').wait_for()
   assert 'No estimable' in page.locator('.head').locator('xpath=..').inner_text() or 'No estimable' in page.locator('#root').inner_text()
   page.locator('[data-action=newpatient]').count()
   page.locator('[data-route=inicio]').click()
   page.locator('[data-action=newpatient]').first.click()
   page.fill('#pcode','SIM-V18A');page.select_option('#pstatus','incluido')
   page.select_option('#pcopd','si');page.select_option('#pconsent','si');page.select_option('#peligibility','elegible');page.select_option('#pactive','no')
   page.fill('#pspirodate','2025-12-10');page.fill('#penrol','2026-01-10');page.fill('#page','65')
   page.locator('#patientForm button[type=submit]').click();page.locator('.patient-journey').wait_for()
   page.locator('[data-action=workflowvisit][data-visit=V0]').first.click()
   page.fill('#vcat','0');page.select_option('#vmmrc','0')
   for q in ['vrescue','vexacerb','vdyspnea','vactivity']:page.select_option('#'+q,'no')
   page.select_option('#vaction','seguimiento');page.select_option('#vstatus','completa')
   page.locator('#visitForm button[type=submit]').click();page.locator('.saved-feedback').wait_for()
   page.locator('[data-route=analisis]').click();page.locator('text=Informe de cohorte · v0.18').wait_for()
   assert 'Mal control en V0' in page.locator('#root').inner_text()
   assert '0 %' in page.locator('#root').inner_text()
   page.screenshot(path='/mnt/data/RADAR_CORUNA_v19_informe.png',full_page=True)
   assert not errors,errors
   browser.close()
   print('PASS: Phase 18 scientific dashboard zero-score and reporting browser check')
if __name__=='__main__':main()
