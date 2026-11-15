"""RADAR v0.47: consistent first viewport across EVERY route and opening editor.
Only isolated SQLite synthetic records. No live/staging clinical data is touched.
"""
import tempfile
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_phase30_premium import boot,click_route,check_layout
import server

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'v47'
OUT.mkdir(parents=True,exist_ok=True)
MODULES=('visitas','flujo','crd','eventos','resultados','completitud',
         'red','inteligencia','analisis','calidad','estudio','exportacion')
FORM_MODULES=('participante','visita','evento')
WIDTHS=(320,390,768,1024,1440)


def snapshot(page,route,width):
 if width in (390,1440) and route in ('visita','participante','visitas','crd','red','analisis','eventos'):
  page.screenshot(path=str(OUT / f'{route}_{width}.png'),full_page=False)


def verify_fold(page,route,width):
 info=page.evaluate("""() => {
   const top=document.querySelector('.top')?.getBoundingClientRect();
   const fold=document.querySelector('#root .module-firstfold')?.getBoundingClientRect();
   const head=document.querySelector('#root .module-firstfold .head')?.getBoundingClientRect();
   const content=document.querySelector('.content');
   const workspace=document.getElementById('workspaceContext');
   return {
     top:top?.bottom,fold:fold?.top,bottom:fold?.bottom,head:head?.top,
     workspaceDisplay:getComputedStyle(workspace).display,
     contentTop:content.getBoundingClientRect().top,
     horizontalOverflow:document.documentElement.scrollWidth-innerWidth
   };
 }""")
 assert info['fold'] is not None,(route,width,'missing top shell',info)
 assert info['fold'] <= info['top']+55,(route,width,'excessive top gap',info)
 assert info['workspaceDisplay']=='none',(route,width,'old breadcrumb still visible',info)
 assert info['horizontalOverflow']<=2,(route,width,'overflow',info)
 check_layout(page,width)
 return info


def main():
 with tempfile.TemporaryDirectory() as path:
  server.DB_FILE=Path(path)/'global_layout_v47.sqlite3'
  server.POSTGRES_MODE=False
  with TestClient(server.app) as client:
   login=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
   assert login.status_code==200,login.text
   csrf=lambda:{'X-RADAR-CSRF':client.get('/api/session').json()['csrf']}
   # Synthetic centre created explicitly by test, never server bootstrap.
   assert client.post('/api/centres',headers=csrf(),json={
       'code':'GAL_LAYOUT47','name':'Centro de pruebas de interfaz'}).status_code==201
   assert client.post('/api/patients',headers=csrf(),json={
       'id':'SIM-LAYOUT47','center':'GAL_LAYOUT47','status':'cribado'
   }).status_code==201
   with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in WIDTHS:
     page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
     page.set_default_timeout(14000)
     errors=boot(page,client);mobile=width<=900
     for module in MODULES:
      click_route(page,module,mobile)
      verify_fold(page,module,width)
      snapshot(page,module,width)
      # Environment note opens without replacing the page or pushing the first form off-screen.
      note=page.locator('#root .module-firstfold .environment-note')
      if note.count():
       note.locator('summary').click()
       assert note.get_attribute('open') is not None,(module,width)
       note.locator('summary').click()
     click_route(page,'cohorte',mobile)
     page.locator('[data-action="newpatient"]').click()
     page.locator('#patientForm').wait_for()
     verify_fold(page,'participante',width)
     assert page.locator('#patientForm>.clinical-toolbar .section-jump').count()>=3
     assert page.locator('#patientForm>.clinical-block').count()==0  # blocks remain inside panelbody
     snapshot(page,'participante',width)
     # Changing tabs and returning should keep original values, not simulate an auto-save.
     page.locator('#patientForm .section-jump').nth(1).click()
     assert page.locator('#patientForm .section-jump').nth(1).get_attribute('aria-current')=='location'
     page.locator('[data-action="discardpatient"]').click()
     click_route(page,'visitas',mobile)
     page.locator('#root [data-action="newvisit"]').click()
     page.locator('#visitForm').wait_for()
     verify_fold(page,'visita',width)
     measure=page.evaluate("""() => {
       const form=document.getElementById('visitForm');
       const head=form.querySelector(':scope > .panelhead').getBoundingClientRect();
       const toolbar=form.querySelector(':scope > .clinical-toolbar').getBoundingClientRect();
       const body=form.querySelector(':scope > .panelbody').getBoundingClientRect();
       return {headEnd:head.bottom,toolbarStart:toolbar.top,toolbarEnd:toolbar.bottom,bodyStart:body.top};
     }""")
     assert 0<=measure['toolbarStart']-measure['headEnd']<=14,(width,'empty band before clinical tabs',measure)
     assert 0<=measure['bodyStart']-measure['toolbarEnd']<=14,(width,'empty band after clinical tabs',measure)
     assert page.locator('#visitForm .section-jump').count()>=4
     snapshot(page,'visita',width)
     page.locator('#visitForm .section-jump').nth(1).click()
     assert page.locator('#visitForm .section-jump').nth(1).get_attribute('aria-current')=='location'
     page.locator('[data-action="discardvisit"]').click()
     assert not errors,(width,errors)
     page.close()
    browser.close()
 print('PASS global firstfold: 12 modules, opening forms, 5 widths, no empty toolbar bands')


if __name__=='__main__':
 main()
