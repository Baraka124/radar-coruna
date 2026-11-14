"""Optional Chromium DOM acceptance using FastAPI TestClient transport, no localhost navigation.
This tests real rendered controls and real backend responses in an isolated, empty DB.
"""
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]

def main():
 with tempfile.TemporaryDirectory() as td:
  server.DB_FILE=Path(td)/'acceptance.sqlite3'
  with TestClient(server.app) as client,sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
   page=browser.new_page(viewport={'width':1440,'height':950})
   page.set_default_timeout(6000)
   errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   def py_request(_source,path,init=None):
    init=init or {}
    method=init.get('method','GET')
    headers=init.get('headers',{})
    body=init.get('body')
    r=client.request(method,path,headers=headers,content=(body.encode() if isinstance(body,str) else body))
    return {'status':r.status_code,'body':r.text,'ctype':r.headers.get('content-type','application/json')}
   page.expose_binding('py_request',py_request)
   page.goto('about:blank')
   page.evaluate("window.fetch=async (path,init={})=>{const r=await window.py_request(path,init);return new Response(r.body,{status:r.status,headers:{'Content-Type':r.ctype}})}; true")
   page.set_content((ROOT/'static/index.html').read_text(),wait_until='domcontentloaded')
   page.fill('#username','admin');page.fill('#password','radar-demo-admin')
   page.locator('#authForm button[type=submit]').click()
   page.locator('body.signed-in').wait_for(timeout=12000)
   assert client.get('/api/state').json()['patients']==[]
   page.locator('[data-action="newpatient"]').first.click()
   page.fill('#pcode','SIM-E2E15')
   page.select_option('#pstatus','incluido')
   page.select_option('#pcopd','si')
   page.select_option('#pconsent','si')
   page.select_option('#peligibility','elegible')
   page.select_option('#pactive','no')
   page.fill('#pspirodate','2025-12-10')
   page.fill('#penrol','2026-01-10')
   page.fill('#page','65')
   page.locator('#patientForm button[type=submit]').click()
   page.locator('.patient-journey').wait_for(timeout=12000)
   assert 'Recorrido del participante' in page.locator('.patient-journey').inner_text()
   page.locator('.journey-step button[data-visit="V0"]').click()
   assert page.input_value('#vdate')=='2026-01-10', 'Baseline date was not preselected'
   page.fill('#vcat','16')
   page.select_option('#vmmrc','0')
   page.select_option('#vrescue','si')
   page.select_option('#vexacerb','no')
   page.select_option('#vdyspnea','no')
   page.select_option('#vactivity','no')
   page.select_option('#vaction','seguimiento')
   page.select_option('#vstatus','completa')
   page.locator('#visitForm button[type=submit]').click()
   page.locator('.saved-feedback').wait_for(timeout=12000)
   assert 'Visita V0 guardada' in page.locator('.saved-feedback').inner_text()
   page.locator('.saved-feedback button[data-action="crdfor"]').click()
   assert page.locator('#studyVisit').input_value()=='V0'
   assert page.locator('#studyPatient').input_value()=='SIM-E2E15'
   page.locator('[data-route="cohorte"]').click()
   page.locator('[data-action="detail"]').first.click()
   page.locator('.journey-step button[data-visit="V1"]').click()
   page.fill('#vdate','2026-07-10')
   page.fill('#vcat','12')
   page.select_option('#vmmrc','0')
   for field in ('vrescue','vexacerb','vdyspnea','vactivity'):page.select_option('#'+field,'no')
   page.select_option('#vaction','seguimiento')
   page.select_option('#vstatus','completa')
   page.locator('#visitForm button[type=submit]').click()
   page.locator('.saved-feedback').wait_for(timeout=12000)
   page.locator('.journey-step button[data-visit="V2"]').click()
   page.fill('#vdate','2027-01-10')
   page.fill('#vcat','8')
   page.select_option('#vmmrc','0')
   for field in ('vrescue','vexacerb','vdyspnea','vactivity'):page.select_option('#'+field,'no')
   page.select_option('#vaction','seguimiento')
   page.select_option('#vstatus','completa')
   page.locator('#visitForm button[type=submit]').click()
   page.locator('.saved-feedback').wait_for(timeout=12000)
   assert page.locator('.journey-step.done').count()==3
   page.locator('.patient-journey button[data-action="eventfor"]').click()
   assert page.locator('#epatient').input_value()=='SIM-E2E15'
   page.fill('#edate','2026-03-15')
   page.locator('#eventForm button[type=submit]').click()
   page.locator('#eventForm').wait_for(state='detached',timeout=6000)
   page.locator('[data-route="cohorte"]').click()
   page.locator('[data-action="detail"]').first.click()
   page.locator('.patient-journey button[data-action="contactfor"]').click()
   assert page.locator('#epatient').input_value()=='SIM-E2E15'
   page.fill('#edate','2026-03-15')
   page.locator('#eventForm button[type=submit]').click()
   page.locator('#eventForm').wait_for(state='detached',timeout=6000)
   state=client.get('/api/state').json()
   assert len(state['patients'])==1 and len(state['visits'])==3 and len(state['events'])==1 and len(state['contacts'])==1
   assert [server.score(v) for v in state['visits'] if v['patient']=='SIM-E2E15']==[3,0,0]
   assert not errors,errors
   page.locator('[data-route="cohorte"]').click();page.locator('[data-action="detail"]').first.click()
   page.screenshot(path='/mnt/data/RADAR_CORUNA_v15_recorrido.png',full_page=True)
   browser.close()
   print('BROWSER_DOM_PASS login/patient/V0/V1/V2/CRD/events/contacts/score/empty-default')

if __name__=='__main__':main()
