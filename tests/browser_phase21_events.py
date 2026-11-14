"""Synthetic browser acceptance: episode R074, contacts and CRD clinical actions."""
from pathlib import Path
import sys,tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data/RADAR_CORUNA_v21_episodios_contactos.png')

def main():
  with tempfile.TemporaryDirectory() as d:
    server.DB_FILE=Path(d)/'phase21_browser.sqlite3'
    with TestClient(server.app) as client, sync_playwright() as pw:
      token=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'}).json()['csrf']
      hdr={'X-RADAR-CSRF':token}
      pid='SIM-BROW21'
      r=client.post('/api/patients',headers=hdr,json={
          'id':pid,'center':'SIM-CS01','status':'incluido','copd':'si','consent':'si',
          'enrolDate':'2026-01-10','spiroDate':'2025-12-20','weeks':5})
      assert r.status_code==201,r.text
      r=client.post('/api/visits',headers=hdr,json={'id':'VIS-B21','patient':pid,'type':'V0',
              'date':'2026-01-10','status':'parcial'})
      assert r.status_code==201,r.text
      browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
      page=browser.new_page(viewport={'width':1360,'height':920});page.set_default_timeout(12000)
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
      page.wait_for_function("document.body.classList.contains('signed-in') && !!document.querySelector('[data-route=eventos]')")
      page.wait_for_timeout(350)
      page.locator('[data-route=eventos]').click()
      page.locator('[data-action=newevent]').first.click()
      page.locator('#epatient').select_option(pid)
      page.locator('#edate').fill('2026-02-11')
      page.locator('#eseverity').select_option('moderada')
      page.locator('#eventForm button[type=submit]').click()
      page.locator('[data-action=contactforevent]').wait_for()
      assert page.get_by_text('01',exact=True).count()>=1
      page.locator('[data-action=contactforevent]').first.click()
      assert page.locator('#eevent').input_value()!=''
      page.locator('#edate').fill('2026-02-11')
      page.locator('#etype').select_option('urgencias')
      page.locator('#edischarged').fill('2026-02-12')
      page.locator('#ecarecentre').fill('Centro ficticio')
      page.locator('#eventForm button[type=submit]').click()
      page.locator('[data-route=eventos]').click()
      assert page.get_by_text('01',exact=True).count()>=2
      page.screenshot(path=str(OUT),full_page=True)
      state=client.get('/api/state').json()
      assert len(state['events'])==1 and len(state['contacts'])==1
      assert state['contacts'][0]['event']==state['events'][0]['id']
      assert state['contacts'][0]['dischargeDate']=='2026-02-12'
      # Visit-specific CRD actions are accessible under existing research measurements.
      page.wait_for_timeout(550)
      page.locator('[data-route=crd]').click()
      page.wait_for_timeout(500)
      field=page.locator('[data-crd-code="action_inhaler_tech"]')
      field.wait_for(state='attached')
      panel_id=field.evaluate('(el) => el.closest(".crd-field-group").id')
      page.locator(f'#crdSectionNav [aria-controls="{panel_id}"]').click()
      field.wait_for(state='visible')
      assert page.locator('[data-crd-code="action_plan_documented"]').count()==1
      page.locator('[data-crd-code="action_inhaler_tech"]').select_option('si')
      page.locator('[data-crd-code="action_plan_documented"]').select_option('no_aplica')
      page.locator('#studyForm button[type=submit]').click()
      page.locator('[data-crd-code="action_inhaler_tech"]').wait_for()
      obs=client.get('/api/study/observations').json()
      assert len([v for v in obs if v['variable_code'] in ('action_inhaler_tech','action_plan_documented')])==2
      assert not errors,errors
      browser.close()
      print('PASS browser v0.21: episode R074, linked emergency, discharge, clinical actions')

if __name__=='__main__':main()
