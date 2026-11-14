"""v0.38 browser with an isolated TestClient transport; network stays local to test runtime."""
import sys,tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_phase30_premium import boot,click_route,check_layout
import server
OUT=Path(__file__).resolve().parents[1]/'docs'/'v38'; OUT.mkdir(parents=True,exist_ok=True)

def main():
 with tempfile.TemporaryDirectory() as td:
  server.DB_FILE=Path(td)/'ui-v38.sqlite3'
  with TestClient(server.app) as client:
   with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
    for width in (320,390,768,1057,1440):
     client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
     page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1);page.set_default_timeout(20000)
     errors=boot(page,client)
     click_route(page,'red',width<=900)
     assert page.locator('#networkInviteForm').is_visible()
     assert page.locator('.network-centre').count()==3
     check_layout(page,width)
     if width in (390,1440):page.screenshot(path=str(OUT/f'v38_red_admin_{width}.png'),full_page=False)
     page.locator('#networkCentre').select_option('SIM-CS02')
     page.locator('#networkRole').select_option('reviewer' if width==390 else 'investigator')
     page.locator('#networkLabel').fill('Investigación de prueba')
     page.locator('#networkInviteForm button[type=submit]').click()
     page.locator('#networkCreatedUrl').wait_for(state='visible')
     link=page.locator('#networkCreatedUrl').inner_text()
     assert '#invite=' in link,link
     secret=link.split('#invite=')[1]
     assert len(secret)>40
     # Sign out, switch hash to show the invitation acceptance gate.
     page.locator('#signout').click()
     page.evaluate('(token)=>{ location.hash="#invite="+token; window.dispatchEvent(new HashChangeEvent("hashchange")) }',secret)
     page.locator('#inviteGate').wait_for(state='visible')
     username='researcher'+str(width)
     page.locator('#inviteUsername').fill(username)
     page.locator('#invitePassword').fill('Contrasena-Prueba-2026')
     page.locator('#inviteAcceptForm button[type=submit]').click()
     page.wait_for_function("() => document.querySelector('#authError').textContent.includes('Cuenta activada')",timeout=5000)
     assert page.locator('#authForm').is_visible()
     page.locator('#password').fill('Contrasena-Prueba-2026')
     page.locator('#authForm button[type=submit]').click()
     page.locator('body.signed-in').wait_for()
     click_route(page,'red',width<=900)
     assert page.locator('.network-centre').count()==1
     assert 'SIM-CS02' in page.locator('.network-centre').inner_text()
     assert not page.locator('#networkInviteForm').count()
     check_layout(page,width)
     if width in (390,1440):page.screenshot(path=str(OUT/f'v38_red_centro_{width}.png'),full_page=False)
     assert not errors,(width,errors)
     print('PASS centre collaboration, activation, scoped access:',width,flush=True)
     page.close()
    browser.close()
if __name__=='__main__':main()
