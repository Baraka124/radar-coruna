"""v0.49 · No oversized/filled buttons, full clinical editing retained.

Browser runs against an isolated local SQLite DB with only explicitly created synthetic records.
It tests patient registration, CRD field layout and draft/persist behavior, and cross-page actions
at 320, 390, 768, 1024 and 1440 px. Never touches deployed staging.
"""
from pathlib import Path
import sys
import tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_phase30_premium import boot,click_route,check_layout
import server

OUTPUT=Path(__file__).resolve().parents[1]/'docs'/'v49'
OUTPUT.mkdir(parents=True,exist_ok=True)
WIDTHS=(320,390,768,1024,1440)

def scan_actions(page):
 return page.evaluate("""() => {
   const buttons=[...document.querySelectorAll('#root .btn')]
       .filter(el=>el.getClientRects().length && getComputedStyle(el).visibility!=='hidden');
   const info=buttons.map(b=>{
     const style=getComputedStyle(b),rect=b.getBoundingClientRect();
     return {
       label:b.textContent.trim().slice(0,45),
       primary:b.classList.contains('primary'),height:rect.height,width:rect.width,
       paddingL:parseFloat(style.paddingLeft),paddingR:parseFloat(style.paddingRight),
       bg:style.backgroundColor,radius:style.borderRadius,
       overflow:(rect.left<0 || rect.right>innerWidth+3) &&
           !(b.closest('.tablewrap') &&
               b.closest('.tablewrap').scrollWidth>b.closest('.tablewrap').clientWidth+2),
     };
   });
   return {buttons:info,viewport:innerWidth,
       documentWidth:document.documentElement.scrollWidth};
 }""")

def check_actions(page,width,route):
 result=scan_actions(page)
 assert result['documentWidth']<=width+2,(route,width,'horizontal overflow',result)
 assert all(not b['overflow'] for b in result['buttons']),(route,width,'clipped action',result)
 assert all(b['paddingL']<=10.1 and b['paddingR']<=10.1
            for b in result['buttons']),(route,width,'over-padded buttons',result)
 assert all(30<=b['height']<=49 for b in result['buttons']),(route,width,'oversized controls',result)
 # Primary actions stay visibly outlined, never saturated filled CTA buttons.
 for b in result['buttons']:
  if not b['primary']:continue
  assert b['bg'] in ('rgb(249, 251, 255)','rgb(255, 255, 255)',
                     'rgba(0, 0, 0, 0)'),(route,width,'filled primary',b)
 return result

def measure_field(page,selector):
 return page.locator(selector).evaluate("""el=>{
   const css=getComputedStyle(el),rect=el.getBoundingClientRect();
   return {radius:css.borderRadius,height:rect.height,borderBottom:parseFloat(css.borderBottomWidth),
     background:css.backgroundColor,disabled:el.disabled,
     readonly:el.readOnly||false,tag:el.tagName.toLowerCase()};
 }""")

def main():
 with tempfile.TemporaryDirectory() as folder:
  server.POSTGRES_MODE=False
  server.DB_FILE=Path(folder)/'radar_buttons_v49.sqlite3'
  with TestClient(server.app) as client:
   auth=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
   assert auth.status_code==200,auth.text
   headers=lambda:{'X-RADAR-CSRF':client.get('/api/session').json()['csrf']}
   centre=client.post('/api/centres',headers=headers(),
     json={'code':'GAL_UI49','name':'Centro de validación de interfaz'})
   assert centre.status_code==201,centre.text
   participant={
     'id':'SIM-UI49-001','center':'GAL_UI49','status':'incluido',
     'copd':'si','consent':'si','consentDate':'2026-01-05',
     'enrolDate':'2026-01-10','spiroDate':'2025-11-30',
     'weeks':5,'birthDate':'1965-01-03','ratio':0.6,
     'regular':'si','lastCopdReviewDate':'2025-06-01',
     'capacity':'si','activeExacerb':'no','exclusion':'no',
     'alternativeDiagnosis':'no','seriousDecompensation':'no',
     'interferingTrial':'no','eligibilityDecision':'elegible',
   }
   pat=client.post('/api/patients',headers=headers(),json=participant)
   assert pat.status_code==201,pat.text
   visit=client.post('/api/visits',headers=headers(),
       json={'id':'VIS-UI49-V0','patient':'SIM-UI49-001',
             'type':'V0','date':'2026-01-10','rescue':'no','exacerb':'no',
             'dyspnea':'no','activity':'no','cat':8,'mmrc':0,
             'action':'seguimiento','status':'completa'})
   assert visit.status_code==201,visit.text
   with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in WIDTHS:
     page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
     page.set_default_timeout(18000)
     errors=boot(page,client)
     mobile=width<=900
     for route in ('inicio','cohorte','red','visitas','eventos','completitud','estudio','analisis'):
      if route!='inicio':click_route(page,route,mobile)
      check_actions(page,width,route)
      check_layout(page,width)
     click_route(page,'cohorte',mobile)
     page.locator('#root [data-action="newpatient"]').click()
     page.locator('#patientForm').wait_for()
     check_actions(page,width,'participante')
     assert page.locator('#pcode').is_visible()
     assert page.locator('#page').get_attribute('readonly') is not None
     for fid in ('pcode','pcenter','pstatus','pcopd','pconsent','pbirthdate','penrol'):
      field=measure_field(page,'#'+fid)
      assert field['radius']=='0px',(width,fid,'rounded generic box remains',field)
      assert field['borderBottom']>=1,(width,fid,'field underline missing',field)
      assert 38<=field['height']<=43,(width,fid,'field disproportionately tall',field)
     assert measure_field(page,'#page')['readonly']
     page.locator('#penrol').fill('2026-01-10')
     page.locator('#pbirthdate').fill('1986-01-10')
     assert page.locator('#page').input_value()=='40'
     page.locator('#patientForm .section-jump').nth(1).click()
     assert page.locator('#patientForm .section-jump').nth(1).get_attribute('aria-current')=='location'
     page.locator('#patientForm .section-jump').nth(0).click()
     assert page.locator('#penrol').input_value()=='2026-01-10'
     if width in (390,1440):
      page.screenshot(path=str(OUTPUT/f'participant_{width}.png'),full_page=False)
     page.locator('[data-action="discardpatient"]').click()
     click_route(page,'crd',mobile)
     page.locator('#studyForm').wait_for()
     # The connected CRD already has its own participant and V0-V2 selector.
     # It must not repeat the workflow ribbon or top-level Ficha link.
     assert page.locator('#root .workflow-ribbon').count()==0
     assert page.locator('#root .module-firstfold [data-action="detail"]').count()==0
     assert page.locator('#root .crd-context-links [data-action="detail"]').count()==1
     check_actions(page,width,'crd')
     nav=page.locator('#crdSectionNav .crd-section-tab')
     assert nav.count()>1
     stage=page.locator('[data-crd-visit="V0"]')
     assert stage.get_attribute('aria-current')=='step'
     active=stage.evaluate("e=>getComputedStyle(e).backgroundColor")
     assert active in ('rgba(0, 0, 0, 0)','rgb(255, 255, 255)'),(width,active)
     field=page.locator('#studyForm [data-crd-code]').first
     assert field.count()==1
     group=field.locator('xpath=ancestor::*[contains(@class,"crd-field-group")]')
     index=group.get_attribute('id').split('-')[-1]
     nav.locator('nth='+index).click()
     assert field.is_visible()
     css=measure_field(page,'#'+field.get_attribute('id'))
     assert css['radius']=='0px' and 38<=css['height']<=43 and css['borderBottom']>=1,(width,css)
     # Draft is only local until explicit save. This must never silently persist.
     focus=page.locator('[data-crd-code="comorb_ihd"]')
     assert focus.count()==1
     focus_panel=focus.locator('xpath=ancestor::*[contains(@class,"crd-field-group")]')
     pos=focus_panel.get_attribute('id').split('-')[-1]
     nav.locator('nth='+pos).click()
     assert focus.is_enabled()
     focus.select_option('no')
     assert 'sin guardar' in page.locator('#crdDraftStatus').inner_text()
     page.locator('[data-crd-visit="V1"]').click()
     page.locator('[data-crd-visit="V0"]').click()
     assert page.locator('[data-crd-code="comorb_ihd"]').input_value()=='no'
     if width in (390,1440):
      page.screenshot(path=str(OUTPUT/f'crd_{width}.png'),full_page=False)
     assert not errors,(width,errors)
     page.close()
    browser.close()
 print('PASS v0.49: patient + CRD controls, concise actions, drafts, derived fields, 5 viewports')

if __name__=='__main__':
 main()
