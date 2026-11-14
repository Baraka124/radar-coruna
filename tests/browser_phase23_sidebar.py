"""Visual and interaction checks for light desktop sidebar, collapsed rail, mobile drawer."""
from pathlib import Path
import sys,tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data')

def main():
 with tempfile.TemporaryDirectory() as td:
  server.DB_FILE=Path(td)/'sidebar.sqlite3'
  with TestClient(server.app) as client,sync_playwright() as pw:
   b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
   for name,viewport in [('desktop',{'width':1440,'height':900}),('mobile',{'width':390,'height':844})]:
    page=b.new_page(viewport=viewport);page.set_default_timeout(16000)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def transport(_src,path,init=None):
     init=init or {};body=init.get('body');resp=client.request(init.get('method','GET'),path,headers=init.get('headers',{}),content=body.encode() if isinstance(body,str) else body)
     return {'status':resp.status_code,'body':resp.text,'ctype':resp.headers.get('content-type','application/json')}
    page.expose_binding('py_request',transport)
    page.goto('about:blank')
    page.evaluate("window.fetch=async(path,init={})=>{const r=await window.py_request(path,init);return new Response(r.body,{status:r.status,headers:{'Content-Type':r.ctype}})};true")
    page.set_content((ROOT/'static/index.html').read_text(encoding='utf8'),wait_until='domcontentloaded')
    page.fill('#password','radar-demo-admin');page.locator('#authForm button[type=submit]').click()
    page.wait_for_function("document.body.classList.contains('signed-in')")
    page.wait_for_timeout(350)
    if name=='desktop':
     assert page.locator('#sidebar').is_visible()
     assert page.locator('#sidebarCollapse').is_visible()
     assert page.evaluate("getComputedStyle(document.querySelector('#sidebar')).backgroundColor")== 'rgb(255, 255, 255)'
     page.locator('[data-route=eventos]').click()
     assert page.locator('[data-route=eventos]').get_attribute('aria-current')=='page'
     page.screenshot(path=str(OUT/'RADAR_CORUNA_v23_sidebar_desktop.png'))
     original=page.locator('#sidebar').bounding_box()['width']
     page.locator('#sidebarCollapse').click()
     page.wait_for_timeout(350)
     width=page.locator('#sidebar').bounding_box()['width']
     assert width<original/2,(original,width)
     assert page.locator('[data-route=eventos]').is_visible()
     page.screenshot(path=str(OUT/'RADAR_CORUNA_v23_sidebar_collapsed.png'))
     page.locator('#sidebarCollapse').click()
     assert page.locator('[data-route=eventos]').get_attribute('aria-current')=='page'
     print('desktop sidebar: pass; width',original,'=>',width)
    else:
     page.wait_for_function("document.querySelector('#sidebar').getBoundingClientRect().x < -200")
     assert page.locator('#mobileNavToggle').is_visible()
     page.screenshot(path=str(OUT/'RADAR_CORUNA_v23_mobile_closed.png'))
     page.locator('#mobileNavToggle').click()
     page.wait_for_timeout(350)
     assert page.locator('#sidebar').is_visible()
     assert page.locator('#mobileNavToggle').get_attribute('aria-expanded')=='true'
     page.screenshot(path=str(OUT/'RADAR_CORUNA_v23_mobile_open.png'))
     page.locator('[data-route=analisis]').click()
     assert page.locator('[data-route=analisis]').get_attribute('aria-current')=='page'
     page.wait_for_function("document.querySelector('#sidebar').getBoundingClientRect().x < -200")
     page.locator('#mobileNavToggle').click()
     page.keyboard.press('Escape')
     page.wait_for_function("document.querySelector('#sidebar').getBoundingClientRect().x < -200")
     print('mobile drawer: pass')
    assert not errors,errors
    page.close()
   b.close()
if __name__=='__main__':main()
