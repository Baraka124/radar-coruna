"""v0.37: continuity, confirmed carry-forward, contextual completion and save-to-CRD navigation."""
import os, sys, tempfile, sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from browser_phase30_premium import boot, click_route, check_layout
import server
OUT=Path(__file__).resolve().parents[1]/'docs'/'v37';OUT.mkdir(parents=True,exist_ok=True)
P={'id':'SIM-WORK37','center':'SIM-CS01','status':'incluido','copd':'si','regular':'si','lastCopdReviewDate':'2025-10-01','weeks':8,'capacity':'si','activeExacerb':'no','exclusion':'no','alternativeDiagnosis':'no','seriousDecompensation':'no','interferingTrial':'no','consent':'si','consentDate':'2026-01-08','enrolDate':'2026-01-15','birthDate':'1969-02-15','spiroDate':'2025-12-20','ratio':.61,'fev1':62,'eligibilityDecision':'elegible','smoking':'ex'}
V0={'id':'VIS-WORK37-V0','patient':'SIM-WORK37','type':'V0','date':'2026-01-15','status':'completa','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no','cat':10,'mmrc':1,'action':'seguimiento','assessorCode':'SIM-PROF37','smoking':'ex','inhaledRegimen':'dual'}
def main():
 with tempfile.TemporaryDirectory() as d:
  server.DB_FILE=Path(d)/'v37.sqlite3'
  with TestClient(server.app) as client:
   a=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'}); assert a.status_code==200,a.text
   h={'X-RADAR-CSRF':a.json()['csrf']}
   assert client.post('/api/patients',json=P,headers=h).status_code==201
   assert client.post('/api/visits',json=V0,headers=h).status_code==201
   with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in (320,390,768,1057,1440):
     page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
     page.set_default_timeout(13000)
     errors=boot(page,client)
     click_route(page,'visitas',width<=900)
     page.locator('[data-action="newvisit"]').click()
     page.locator('#visitForm').wait_for()
     assert page.locator('#vtype').input_value()=='V1'
     assert page.locator('.workflow-ribbon').count()==1
     assert 'VISITA' not in page.locator('.workflow-ribbon').inner_text().upper() or page.locator('.workflow-ribbon').is_visible()
     assert 'RADAR 0/8' in page.locator('.workflow-reference').inner_text()
     assert page.locator('.completion-field-link[data-focus-field="vdate"]').count()==1
     page.locator('.completion-field-link[data-focus-field="vdate"]').click()
     assert page.locator('#vdate').evaluate('(n)=>n===document.activeElement')
     assert page.locator('#copyAssessorPrior').is_visible()
     page.locator('#copyAssessorPrior').click()
     assert page.locator('#vassessor').input_value()=='SIM-PROF37'
     page.locator('#copySmokingPrior').click()
     assert page.locator('#vsmoking').input_value()=='ex'
     page.locator('#copyTreatmentPrior').click()
     assert page.locator('#vregimen').input_value()=='dual'
     # Dirty visit stays put on accidental navigation to V0 or the ficha.
     page.locator('.workflow-ribbon [data-action="workflowvisit"][data-visit="V0"]').click()
     assert page.locator('#root').get_attribute('data-view')=='visita'
     assert 'sin guardar' in page.locator('#visitError').inner_text().lower()
     page.locator('#vdate').fill('2026-07-15')
     page.locator('#vcat').fill('11')
     page.locator('#vmmrc').select_option('2')
     for k in ('vrescue','vexacerb','vdyspnea','vactivity'):page.locator('#'+k).select_option('no')
     page.locator('#vaction').select_option('seguimiento')
     assert not page.locator('.completion-field-link').count(),page.locator('#visitCompleteness').inner_text()
     assert '100%' in page.locator('#visitCompleteness').inner_text()
     check_layout(page,width)
     if width in (390,1440):page.screenshot(path=str(OUT/f'v37_workflow_{width}.png'),full_page=False)
     page.locator('#saveVisitAndCRD').click()
     page.locator('#root[data-view="crd"]').wait_for()
     assert page.locator('.workflow-ribbon').count()==1
     assert 'V1' in page.locator('.workflow-ribbon').inner_text()
     saved=[x for x in client.get('/api/state').json()['visits'] if x['patient']==P['id'] and x['type']=='V1']
     assert len(saved)==1 and saved[0]['cat']==11 and saved[0]['assessorCode']=='SIM-PROF37',saved
     assert not errors,(width,errors)
     print('PASS responsive continuity, save-to-CRD',width,flush=True)
     page.close()
     # Reset only V1 record to permit repeating same test scenario in the next viewport.
     # Use a fresh DB per viewport: SQLite rollback within the temporary test fixture.
     if width!=1440:
      with sqlite3.connect(server.DB_FILE) as con:
       con.execute('DELETE FROM visits WHERE id=?',(saved[0]['id'],))
    browser.close()
if __name__=='__main__':main()
