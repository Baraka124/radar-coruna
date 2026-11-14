"""End-to-end UI checks of v0.33 conditional, derived, and confirmed carry-forward behavior."""
import sys,tempfile,os
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from browser_phase30_premium import boot,check_layout,click_route
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'v33'; OUT.mkdir(parents=True,exist_ok=True)

def main():
 with tempfile.TemporaryDirectory() as td:
  server.DB_FILE=Path(td)/'phase33_browser.sqlite3'
  with TestClient(server.app) as client:
   auth=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
   assert auth.status_code==200,auth.text
   h={'X-RADAR-CSRF':auth.json()['csrf']}
   p={'id':'SIM-SMART33','center':'SIM-CS01','status':'incluido','copd':'si','regular':'si','lastCopdReviewDate':'2025-10-01','weeks':7,'capacity':'si','activeExacerb':'no','exclusion':'no','alternativeDiagnosis':'no','seriousDecompensation':'no','interferingTrial':'no','consent':'si','consentDate':'2026-01-08','enrolDate':'2026-01-15','birthDate':'1969-02-15','spiroDate':'2025-12-20','ratio':0.61,'fev1':62,'eligibilityDecision':'elegible','smoking':'ex'}
   assert client.post('/api/patients',json=p,headers=h).status_code==201
   v0={'id':'VIS-SMART33-V0','patient':'SIM-SMART33','type':'V0','date':'2026-01-15','status':'completa','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no','cat':10,'mmrc':1,'action':'seguimiento','smoking':'ex','inhaledRegimen':'mono','monotherapyClass':'lama','roflumilast':'no','azithromycin':'no','rescuePrescription':'saba','medicationDetails':'Dosis y pauta de V0'}
   res=client.post('/api/visits',json=v0,headers=h);assert res.status_code==201,res.text
   with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
    for width in ((390,1440) if os.getenv('RADAR_CAPTURE_ONLY') else (320,390,768,1024,1440)):
     page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1);page.set_default_timeout(20000)
     errs=boot(page,client);mobile=width<=900
     click_route(page,'cohorte',mobile)
     page.locator('[data-action="newpatient"]').click();page.locator('#patientForm').wait_for()
     assert not page.locator('#pconsentdate').is_visible() # genuinely conditional
     page.locator('#pconsent').select_option('si')
     assert page.locator('#pconsentdate').is_visible()
     page.locator('#pconsentdate').fill('2026-01-01')
     page.locator('#pconsent').select_option('no')
     assert page.locator('#pconsentdate').is_visible() # previous value never silently erased
     assert page.locator('#pconsentdate').input_value()=='2026-01-01'
     # Optional vital section is collapsed in the existing interface; expand before interaction.
     vital=page.locator('#patientForm .clinical-block').filter(has=page.locator('summary:has-text("Estado vital")'))
     vital.locator('summary').click()
     assert not page.locator('#pdeathdate').is_visible()
     page.locator('#pvital').select_option('fallecido')
     assert page.locator('#pdeathdate').is_visible()
     page.locator('#pvital').select_option('vivo')
     assert not page.locator('#pdeathdate').is_visible()
     page.locator('#pratio').fill('0.63');page.locator('#pfev1').fill('51')
     assert page.locator('#pgold').input_value()=='2'
     page.locator('#pfev1').fill('49.9');assert page.locator('#pgold').input_value()=='3'
     page.locator('#pratio').fill('0.70');assert page.locator('#pgold').input_value()==''
     assert page.locator('#pgold').get_attribute('readonly') is not None
     check_layout(page,width)
     # v0.37 requires explicit discard before leaving an edited participant form.
     page.locator('[data-action="discardpatient"]').click()
     click_route(page,'visitas',mobile)
     page.locator('[data-action="newvisit"]').click();page.locator('#visitForm').wait_for()
     assert page.locator('#vtype').input_value()=='V1'
     assert page.locator('#vdate').input_value()=='' # no actual date invented
     assert '2026' in page.locator('#visitWindowGuidance').inner_text()
     assert not page.locator('#vmono').is_visible()
     assert not page.locator('#vreason').is_visible()
     assert not page.locator('#vianuscollected').is_visible()
     # Operator has full control; existing value not overwritten.
     page.locator('#vregimen').select_option('triple')
     page.locator('#copyTreatmentPrior').click()
     assert page.locator('#vregimen').input_value()=='triple'
     assert page.locator('#vmono').input_value()==''  # no incompatible subtype carried from previous monotherapy
     assert page.locator('#vroflumilast').input_value()=='no'
     assert page.locator('#vrescueprescription').input_value()=='saba'
     assert page.locator('#vmeddetails').input_value()=='' # no stale doses copied
     page.locator('#copySmokingPrior').click()
     assert page.locator('#vsmoking').input_value()=='ex'
     page.locator('#vregimen').select_option('mono');assert page.locator('#vmono').is_visible()
     page.locator('#vmono').select_option('lama')
     page.locator('#vstatus').select_option('no_realizada');page.locator('#visitForm .clinical-nested > summary').click();assert page.locator('#vreason').is_visible()
     page.locator('#vstatus').select_option('parcial');assert not page.locator('#vreason').is_visible()
     page.locator('#vianusverified').select_option('si');assert page.locator('#vianuscollected').is_visible()
     page.locator('#vmmrc').select_option('2')
     page.locator('#useMmrcHint').click();assert page.locator('#vdyspnea').input_value()=='si'
     page.locator('#vdate').fill('2026-07-15')
     check_layout(page,width)
     if width==390:
      page.evaluate('window.scrollTo({top:0,behavior:"instant"})');page.wait_for_timeout(240)
      page.screenshot(path=str(OUT/'v33_inteligencia_movil.png'),full_page=True)
     if width==1440:
      page.evaluate('window.scrollTo({top:0,behavior:"instant"})');page.wait_for_timeout(240)
      page.screenshot(path=str(OUT/'v33_inteligencia_escritorio.png'),full_page=True)
      page.locator('#visitForm button[type="submit"]').click()
      page.locator('#root[data-view="detalle"]').wait_for();page.locator('#journeyReview .journey-review-item').first.wait_for()
      saved=next(v for v in client.get('/api/state').json()['visits'] if v['patient']=='SIM-SMART33' and v['type']=='V1')
      assert saved['date']=='2026-07-15' and saved['inhaledRegimen']=='mono' and saved['monotherapyClass']=='lama'
      assert saved['smoking']=='ex' and saved['medicationDetails']==''
      assert saved['dyspnea']=='si'
     assert not errs,(width,errs)
     page.close()
    browser.close()
 print('v0.33 workflow intelligence UI PASS: 320,390,768,1024,1440; derived, conditional, confirmation and persistence')
if __name__=='__main__':main()
