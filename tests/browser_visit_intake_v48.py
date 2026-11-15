"""RADAR v0.48: real clinical intake layout browser regression.
Synthetic records are made only in an isolated local SQLite database.
"""
from pathlib import Path
import tempfile
import sys
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_phase30_premium import boot,click_route,check_layout
import server

OUT=Path(__file__).resolve().parents[1]/'docs'/'v48'
OUT.mkdir(parents=True,exist_ok=True)

VISIT_FIELDS=('vpatient','vtype','vdate','vassessor')
MEASURE_FIELDS=('vcat','vmmrc','vsmoking')

def inspect_layout(page):
    return page.evaluate("""() => {
      const block=document.querySelector('#visitForm .visit-intake');
      const left=block.querySelector('.visit-intake-visit').getBoundingClientRect();
      const right=block.querySelector('.visit-intake-measures').getBoundingClientRect();
      const fieldRects=[...block.querySelectorAll('.field')].map(e=>{
        const r=e.getBoundingClientRect();
        const ctrl=e.querySelector('input,select');
        const c=ctrl.getBoundingClientRect();
        const style=getComputedStyle(ctrl);
        return {id:e.dataset.fieldId,x:r.x,y:r.y,width:r.width,controlWidth:c.width,
           height:c.height,radius:style.borderRadius,bottom:style.borderBottomWidth,
           displayed:style.display,label:!!e.querySelector('label[for="'+ctrl.id+'"]')};
      });
      return {
        parentWidth:block.getBoundingClientRect().width,
        left:{x:left.x,y:left.y,width:left.width,right:left.right,bottom:left.bottom},
        right:{x:right.x,y:right.y,width:right.width,right:right.right,bottom:right.bottom},
        fields:fieldRects,
        overflow:document.documentElement.scrollWidth-innerWidth,
        sectionLabels:[...block.querySelectorAll('section[aria-label]')].map(s=>s.getAttribute('aria-label')),
      }
    }""")

def main():
 with tempfile.TemporaryDirectory() as d:
  server.POSTGRES_MODE=False
  server.DB_FILE=Path(d)/'v48.sqlite3'
  with TestClient(server.app) as client:
   response=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
   assert response.status_code==200,response.text
   headers=lambda:{'X-RADAR-CSRF':client.get('/api/session').json()['csrf']}
   with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    empty=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
    empty_errors=boot(empty,client)
    click_route(empty,'visitas',False)
    assert empty.locator('#root .visit-precondition').is_visible()
    assert 'Primero, registra un participante' in empty.locator('.visit-precondition').inner_text()
    assert empty.locator('#root [data-action="newvisit"]').count()==0
    assert empty.locator('#root [data-action="open-admin-centres"]').count()==1
    assert not empty_errors,empty_errors
    empty.screenshot(path=str(OUT/'empty_without_patients_1440.png'),full_page=False)
    empty.close()
    centre=client.post('/api/centres',headers=headers(),json={'code':'GAL_UI48','name':'Centro sintético de evaluación'})
    assert centre.status_code==201,centre.text
    patient=client.post('/api/patients',headers=headers(),
        json={'id':'SIM-PREMIUM48','center':'GAL_UI48','status':'cribado'})
    assert patient.status_code==201,patient.text
    for width in (320,390,768,1024,1440):
     page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
     page.set_default_timeout(16000)
     errors=boot(page,client)
     click_route(page,'visitas',width<=900)
     page.locator('#root [data-action="newvisit"]').click()
     page.locator('#visitForm').wait_for()
     assert page.locator('#visitForm .visit-intake').count()==1
     assert page.locator('#visitForm .visit-intake-group').count()==2
     info=inspect_layout(page)
     assert info['overflow']<=2,(width,'horizontal overflow',info)
     assert info['sectionLabels']==['Identificación de la visita','Medidas clínicas'],info
     assert len(info['fields'])==7,(width,info)
     assert set(x['id'] for x in info['fields'])==set(VISIT_FIELDS+MEASURE_FIELDS)
     assert all(x['label'] and x['width']>=75 and abs(x['width']-x['controlWidth'])<=2
                and 38<=x['height']<=44 for x in info['fields']),(width,info)
     assert all(x['radius']=='0px' and float(x['bottom'].replace('px',''))>=1
                for x in info['fields']),(width,info)
     if width>=1151:
      assert info['right']['x']>=info['left']['right']-1,(width,info)
      assert abs(info['right']['y']-info['left']['y'])<=4,(width,info)
     else:
      assert info['right']['y']>=info['left']['bottom']-1,(width,info)
     assert page.locator('#vpatient').input_value()=='SIM-PREMIUM48'
     assert page.locator('#vtype').input_value()=='V0'
     page.locator('#vdate').fill('2026-11-15')
     page.locator('#vcat').fill('12')
     page.locator('#vmmrc').select_option('2')
     page.locator('#vsmoking').select_option('ex')
     page.locator('#vassessor').fill('RESEARCHER-SIM')
     page.locator('#visitForm .section-jump').nth(1).click()
     assert page.locator('#visitForm .section-jump').nth(1).get_attribute('aria-current')=='location'
     page.locator('#visitForm .section-jump').nth(0).click()
     assert page.locator('#vdate').input_value()=='2026-11-15'
     assert page.locator('#vcat').input_value()=='12'
     assert page.locator('#vsmoking').input_value()=='ex'
     assert page.locator('#vassessor').input_value()=='RESEARCHER-SIM'
     check_layout(page,width)
     if width in (320,390,1024,1440):
      page.screenshot(path=str(OUT/f'evaluation_{width}.png'),full_page=False)
     assert not errors,(width,errors)
     page.close()
    browser.close()
 print('PASS v0.48 premium clinical intake: seven existing controls, two regions, five widths, tab persistence')

if __name__=='__main__':
 main()
