"""v0.51 — genuine white workspace and reduced ornamental padding.

Synthetic-only local SQLite browser acceptance; no staging DB records are created.
"""
from pathlib import Path
import tempfile, sys
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_phase30_premium import boot,click_route,check_layout
import server

OUT=Path(__file__).resolve().parents[1]/'docs'/'v51'
OUT.mkdir(parents=True,exist_ok=True)

def geometry(page):
 return page.evaluate("""() => {
  const q=s=>document.querySelector(s),style=s=>getComputedStyle(q(s));
  const root=q('#root');
  const form=q('#patientForm');
  const toolbar=form?.querySelector(':scope > .clinical-toolbar');
  const body=form?.querySelector(':scope > .panelbody');
  const fields=form?[...form.querySelectorAll('.clinical-block[open] .field input,.clinical-block[open] .field select')]:[];
  return {
   canvas:getComputedStyle(document.body).backgroundColor,
   main:style('.main').backgroundColor,
   content:style('.content').backgroundColor,
   side:style('.sidebar').backgroundColor,
   top:style('.top').backgroundColor,
   leftPadding:parseFloat(style('.content').paddingLeft),
   topHeight:q('.top').getBoundingClientRect().height,
   formPad:body?parseFloat(getComputedStyle(body).paddingLeft):null,
   formShadow:form?getComputedStyle(form).boxShadow:null,
   formHeader:form?getComputedStyle(form.querySelector(':scope > .panelhead')).display:null,
   toolbarHeight:toolbar?.getBoundingClientRect().height,
   fieldSizes:fields.map(x=>({id:x.id,height:x.getBoundingClientRect().height,
      border:parseFloat(getComputedStyle(x).borderBottomWidth)})),
   buttonPaddings:[...document.querySelectorAll('#root .btn')]
      .filter(el=>el.getClientRects().length)
      .map(x=>({label:x.textContent.trim(),padding:parseFloat(getComputedStyle(x).paddingLeft),
        height:x.getBoundingClientRect().height})),
   overflow:document.documentElement.scrollWidth-innerWidth,
   formTop:form?.getBoundingClientRect().top,
   rootTop:root.getBoundingClientRect().top,
   bodyTop:body?.getBoundingClientRect().top,
   topBottom:q('.top').getBoundingClientRect().bottom
  };
 }""")

def assert_white(info,width,route):
 for key in ('canvas','main','content','side','top'):
  assert info[key]=='rgb(255, 255, 255)',(width,route,key,info)
 assert info['overflow']<=2,(width,route,'horizontal overflow',info)
 assert info['leftPadding']<=33,(width,route,'excessive side gutter',info)
 assert info['topHeight']<=55,(width,route,'oversized utility header',info)
 assert all(x['padding']<=10 for x in info['buttonPaddings']),(width,route,'padded action',info)
 assert all(x['height']>=30 for x in info['buttonPaddings']),(width,route,'unusable action',info)

def main():
 with tempfile.TemporaryDirectory() as d:
  server.POSTGRES_MODE=False
  server.DB_FILE=Path(d)/'v51_white.sqlite3'
  with TestClient(server.app) as c:
   auth=c.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
   assert auth.status_code==200,auth.text
   csrf=lambda:{'X-RADAR-CSRF':c.get('/api/session').json()['csrf']}
   assert c.post('/api/centres',headers=csrf(),
      json={'code':'GAL_WHITE51','name':'Centro de prueba visual'}).status_code==201
   assert c.post('/api/patients',headers=csrf(),
      json={'id':'SIM-WHITE51','center':'GAL_WHITE51','status':'incluido'}).status_code==201
   with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in (320,390,768,1024,1440):
     page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
     page.set_default_timeout(18000)
     errors=boot(page,c)
     mobile=width<=900
     for route in ('inicio','cohorte','visitas','red','analisis','crd'):
      if route!='inicio':click_route(page,route,mobile)
      info=geometry(page)
      assert_white(info,width,route)
      check_layout(page,width)
      if route=='inicio' and width in (390,1440):
       page.screenshot(path=str(OUT/f'overview_{width}.png'),full_page=False)
     click_route(page,'cohorte',mobile)
     page.locator('[data-action="newpatient"]').click()
     page.locator('#patientForm').wait_for()
     info=geometry(page)
     assert_white(info,width,'participante')
     assert info['formShadow']=='none',(width,'card shadow remains',info)
     assert info['formHeader']=='none',(width,'duplicated large patient heading remains',info)
     assert 0<info['formPad']<=16,(width,'inflated clinical panel',info)
     assert 28<=info['toolbarHeight']<=42,(width,'oversized tabs bar',info)
     assert 38<=min(x['height'] for x in info['fieldSizes'])<=43,(width,'clinical controls too small',info)
     assert all(x['border']==0 for x in info['fieldSizes']),(width,'decorative resting rules',info)
     assert page.locator('#patientForm .clinical-block[open]').count()==1
     if width in (390,1440):
      page.screenshot(path=str(OUT/f'patient_{width}.png'),full_page=False)
     page.locator('#patientForm .section-jump').nth(1).click()
     assert page.locator('#patientForm .clinical-block[open]').count()==1
     page.locator('#plastrevi').fill('2025-08-12')
     page.locator('#pweeks').fill('5')
     page.locator('#pcopd').select_option('si')
     page.locator('#patientForm .section-jump').nth(2).click()
     page.locator('#penrol').fill('2026-01-10')
     page.locator('#pbirthdate').fill('1986-01-10')
     assert page.locator('#page').input_value()=='40'
     page.locator('#patientForm .section-jump').nth(1).click()
     assert page.locator('#plastrevi').input_value()=='2025-08-12'
     if width in (390,1440):
      page.screenshot(path=str(OUT/f'inclusion_{width}.png'),full_page=False)
     # Previously approved save/validation remains available.
     page.locator('[data-action="discardpatient"]').click()
     assert not errors,(width,errors)
     page.close()
    browser.close()
 print('PASS v0.51 white paper: 6 routes, 5 widths, genuine white canvas, compact form and preserved inputs')

if __name__=='__main__':
 main()
