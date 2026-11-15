"""RADAR v0.50: progressive participant form and readable native dates.

Uses only an isolated local SQLite database. No live participants or staging values.
"""
from pathlib import Path
import tempfile,sys
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_phase30_premium import boot,click_route,check_layout
import server

OUT=Path(__file__).resolve().parents[1]/'docs'/'v50'
OUT.mkdir(parents=True,exist_ok=True)
WIDTHS=(320,390,768,1024,1440)

def inspect(page):
 return page.evaluate("""() => {
  const root=document.getElementById('patientForm');
  const sections=[...root.querySelectorAll('.clinical-block')];
  const dates=[...root.querySelectorAll('.date-surface')];
  const rules=[...root.querySelectorAll('.clinical-block-body>.fields>.field input,.clinical-block-body>.fields>.field select')]
   .filter(el=>el.getClientRects().length).map(el=>({
     id:el.id,border:getComputedStyle(el).borderBottomWidth,
     background:getComputedStyle(el).backgroundColor,
     focused:document.activeElement===el,
   }));
  return {
   opened:sections.map((x,i)=>x.open?i:null).filter(x=>x!==null),
   dateFaces:dates.map(x=>x.querySelector('.date-face').textContent.trim()),
   rawDateTypes:dates.map(x=>x.querySelector('input').type),
   rules,
   fullWidth:document.documentElement.scrollWidth,
   viewport:innerWidth
  };
 }""")

def main():
 with tempfile.TemporaryDirectory() as td:
  server.POSTGRES_MODE=False
  server.DB_FILE=Path(td)/'radar_v50_ui.sqlite3'
  with TestClient(server.app) as c:
   auth=c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
   assert auth.status_code==200
   csrf=lambda:{'X-RADAR-CSRF':c.get('/api/session').json()['csrf']}
   assert c.post('/api/centres',headers=csrf(),json={
     'code':'GAL_UI50','name':'Centro sintético de control visual'}).status_code==201
   with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in WIDTHS:
     page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
     page.set_default_timeout(18000)
     errors=boot(page,c)
     click_route(page,'cohorte',width<=900)
     page.locator('[data-action="newpatient"]').click()
     page.locator('#patientForm').wait_for()
     info=inspect(page)
     assert info['opened']==[0],(width,'all sections opened at once',info)
     assert info['fullWidth']<=width+2,(width,'page overflow',info)
     assert all(t=='date' for t in info['rawDateTypes']),(width,'date inputs replaced',info)
     assert all(x['border']=='0px' for x in info['rules']),(width,'too many lines',info)
     assert page.locator('#patientForm .field-help').count()>0
     assert page.locator('#patientForm .clinical-block').count()>=5
     assert page.locator('#patientForm .date-face').first.count()==1
     assert page.locator('#patientForm .clinical-block').nth(1).get_attribute('open') is None
     page.locator('#patientForm .section-jump').nth(1).click()
     assert page.locator('#patientForm .clinical-block').nth(0).get_attribute('open') is None
     assert page.locator('#patientForm .clinical-block').nth(1).get_attribute('open') is not None
     assert page.locator('#plastrevi').is_visible()
     assert page.locator('#plastrevi').get_attribute('type')=='date'
     assert page.locator('#plastrevi').input_value()==''
     assert page.locator('#plastrevi').locator('xpath=..').locator('.date-face').inner_text()=='Seleccionar fecha'
     page.locator('#plastrevi').fill('2025-08-12')
     page.locator('#pweeks').fill('5')
     page.locator('#pcopd').select_option('si')
     page.locator('#plastrevi').blur()
     assert '2025' in page.locator('#plastrevi').locator('xpath=..').locator('.date-face').inner_text()
     assert 'mm/dd/yyyy' not in page.locator('#plastrevi').locator('xpath=..').locator('.date-face').inner_text().lower()
     assert page.locator('#patientForm .field-help').first.locator('summary').is_visible()
     page.locator('#patientForm .field-help').first.locator('summary').click()
     assert page.locator('#patientForm .field-help').first.get_attribute('open') is not None
     page.locator('#patientForm .section-jump').nth(2).click()
     assert page.locator('#patientForm .clinical-block').nth(1).get_attribute('open') is None
     page.locator('#penrol').fill('2026-01-10')
     page.locator('#pbirthdate').fill('1986-01-10')
     assert page.locator('#page').input_value()=='40'
     page.locator('#patientForm .section-jump').nth(1).click()
     assert page.locator('#plastrevi').input_value()=='2025-08-12'
     page.locator('#patientForm .section-jump').nth(0).click()
     assert page.locator('#pcode').is_visible()
     page.locator('#pcode').fill('SIM-UI50-'+str(width))
     page.locator('#pcenter').select_option('GAL_UI50')
     assert page.locator('#patientForm .section-jump.active').count()==1
     check_layout(page,width)
     if width in (390,1440):
      page.screenshot(path=str(OUT/f'participant_firstfold_{width}.png'),full_page=False)
      page.locator('#patientForm .section-jump').nth(1).click()
      page.screenshot(path=str(OUT/f'participant_inclusion_{width}.png'),full_page=False)
     page.locator('#patientForm [type="submit"]').click()
     page.locator('#root[data-view="detalle"]').wait_for()
     p=next(v for v in c.get('/api/state').json()['patients'] if v['id']=='SIM-UI50-'+str(width))
     assert p['lastCopdReviewDate']=='2025-08-12',(width,p)
     assert p['age']==40,(width,p)
     assert not errors,(width,errors)
     page.close()
    browser.close()
 print('PASS v0.50: five widths, progressive disclosure, native dates with Spanish resting display, saved real values')

if __name__=='__main__':
 main()
