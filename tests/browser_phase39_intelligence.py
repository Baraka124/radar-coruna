"""v0.39 responsive research-intelligence acceptance; synthetic TestClient."""
import sys,tempfile,os
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_phase30_premium import boot,click_route,check_layout
import server
OUT=Path(__file__).resolve().parents[1]/'docs'/'v39';OUT.mkdir(parents=True,exist_ok=True)

def main():
 with tempfile.TemporaryDirectory() as td:
  server.DB_FILE=Path(td)/'v39-browser.sqlite3';os.environ['RADAR_SEED_DEMO']='1'
  with TestClient(server.app) as client:
   client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
   with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
    for width in (320,390,768,1057,1440):
     page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1);page.set_default_timeout(15000)
     errs=boot(page,client)
     click_route(page,'inteligencia',width<=900)
     assert page.get_by_text('Cobertura por visita').is_visible()
     assert page.get_by_text('Trayectorias longitudinales').is_visible()
     assert page.locator('.int-stat').count()==4
     assert page.locator('.int-table').count()>=4
     assert page.locator('[data-intel-export]').count()==4
     check_layout(page,width)
     if width in (390,1057,1440):page.screenshot(path=str(OUT/f'v39_inteligencia_{width}.png'),full_page=False)
     page.locator('#intelSearch').fill('SIM-001')
     assert page.locator('#intelQualityCount').count()==1
     assert not errs,(width,errs)
     page.close();print('PASS intelligence width',width,flush=True)
    browser.close()
 print('v0.39 browser PASS · 5 widths')
if __name__=='__main__':main()
