"""Browser acceptance for CRD v0.20 additions, synthetic-only data."""
from pathlib import Path
import sys,tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]

def main():
 with tempfile.TemporaryDirectory() as d:
  server.DB_FILE=Path(d)/'v20_crd.sqlite3'
  with TestClient(server.app) as client, sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
   page=browser.new_page(viewport={'width':1440,'height':900});page.set_default_timeout(11000)
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
   page.locator('[data-action=newpatient]').first.click()
   assert page.locator('#pbirthdate').count()==1
   page.fill('#pcode','SIM-CRDUI20');page.select_option('#pstatus','incluido')
   page.select_option('#pcopd','si');page.select_option('#pconsent','si');page.select_option('#peligibility','elegible')
   page.select_option('#pactive','no');page.fill('#pspirodate','2025-12-14');page.fill('#penrol','2026-01-10')
   page.fill('#pbirthdate','1969-01-02');page.fill('#pweeks','4')
   page.fill('#ppriormod','2');page.fill('#ppriorsev','1')
   page.locator('#patientForm button[type=submit]').click();page.locator('.patient-journey').wait_for()
   assert client.get('/api/state',headers={'Accept':'application/json'}).json()['patients'][0]['priorEx']==3
   page.locator('[data-action=workflowvisit][data-visit=V0]').first.click()
   page.fill('#vcat','12');page.select_option('#vmmrc','0')
   for k in ['vrescue','vexacerb','vdyspnea','vactivity']:page.select_option('#'+k,'no')
   page.select_option('#vaction','seguimiento');page.select_option('#vstatus','completa')
   # In order, exact Pedro categories; monotherapy distinction retained.
   assert [page.locator('#vregimen option').nth(i).inner_text() for i in range(1,6)]==[
     '1. Ninguno','2. LAMA o LABA','3. LAMA + LABA','4. LAMA + LABA + ICS','5. LABA + ICS']
   page.select_option('#vregimen','mono');page.select_option('#vmono','laba')
   page.select_option('#vroflumilast','si');page.select_option('#vazithromycin','no')
   page.select_option('#vrescueprescription','saba')
   page.select_option('#vianusverified','si');page.select_option('#vianuscollected','no')
   page.fill('#vianusdate','2026-01-10')
   page.screenshot(path='/mnt/data/RADAR_CORUNA_v20_formulario_visita.png',full_page=True)
   page.locator('#visitForm button[type=submit]').click()
   page.locator('.saved-feedback').wait_for()
   state=client.get('/api/state').json()
   v=state['visits'][0]
   assert v['inhaledRegimen']=='mono' and v['monotherapyClass']=='laba'
   assert (v['lama'],v['laba'],v['ics'])==('no','si','no')
   assert (v['ianusVerified'],v['ianusCollected'])==('si','no')
   assert not errors,errors
   browser.close()
   print('PASS: RADAR v0.20 synthetic CRD baseline/treatment/IANUS UI and persistence')
if __name__=='__main__':main()
