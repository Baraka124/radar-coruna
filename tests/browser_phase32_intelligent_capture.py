"""Browser acceptance: derived values are live, read-only, and proportional."""
from pathlib import Path
import sys, tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from browser_phase30_premium import boot, check_layout, click_route
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'v32';OUT.mkdir(parents=True,exist_ok=True)

def main():
  with tempfile.TemporaryDirectory() as td:
    server.DB_FILE=Path(td)/'browser_phase32.sqlite3'
    with TestClient(server.app) as c:
      login=c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
      assert login.status_code==200
      with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
        for width in (320,390,768,1024,1440):
          page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
          page.set_default_timeout(18000)
          errors=boot(page,c)
          click_route(page,'cohorte',width<=900)
          page.locator('[data-action="newpatient"]').click()
          page.locator('#patientForm').wait_for()
          check_layout(page,width)
          assert page.locator('#page').get_attribute('readonly') is not None
          assert page.locator('#ppriorex').get_attribute('readonly') is not None
          assert page.locator('#page').input_value()==''
          assert page.locator('#penrol').input_value()=='' # do not silently create V0 on screening
          page.locator('#penrol').fill('2026-01-10')
          page.locator('#pbirthdate').fill('1986-01-10')
          assert page.locator('#page').input_value()=='40'
          page.locator('#pbirthdate').fill('1986-01-11')
          assert page.locator('#page').input_value()=='39'
          page.locator('#pbirthdate').fill('1986-01-10')
          page.locator('#ppriormod').fill('2')
          page.locator('#ppriorsev').fill('3')
          assert page.locator('#ppriorex').input_value()=='5'
          page.locator('#pstatus').select_option('incluido')
          assert 'Inclusión pendiente' in page.locator('#inclusionReadiness').inner_text()
          if width==390: page.screenshot(path=str(OUT/'v32_derivaciones_movil.png'),full_page=True)
          if width==1440:
            page.locator('#pcode').fill('SIM-BROWSER32')
            for fid,value in [('pcopd','si'),('pregular','si'),('pcapacity','si'),
                  ('pexclusion','no'),('pconsent','si'),('palternativedx','no'),
                  ('pdecomp','no'),('ptrial','no'),('pactive','no'),('peligibility','elegible')]:
              page.locator('#'+fid).select_option(value)
            for fid,value in [('plastrevi','2025-07-01'),('pweeks','5'),('pconsentdate','2026-01-05'),
                  ('pspirodate','2025-10-15'),('pratio','0.62')]:
              page.locator('#'+fid).fill(value)
            assert 'Criterios estructurados completos' in page.locator('#inclusionReadiness').inner_text(),page.locator('#inclusionReadiness').inner_text()
            page.screenshot(path=str(OUT/'v32_derivaciones_escritorio.png'),full_page=True)
            page.locator('#patientForm button[type="submit"]').click()
            page.locator('#root[data-view="detalle"]').wait_for()
            data=c.get('/api/state').json()
            saved=next(p for p in data['patients'] if p['id']=='SIM-BROWSER32')
            assert saved['age']==40 and saved['priorEx']==5 and saved['lastCopdReviewDate']=='2025-07-01'

          assert not errors,(width,errors)
          page.close()
        browser.close()
  print('Phase 6 intelligent clinical capture UI PASS · 5 widths, reactive derivations and no overflow')

if __name__=='__main__':main()
