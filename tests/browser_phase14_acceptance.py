"""Optional browser-level check for the Phase 14 workspace. No patient is created."""
from pathlib import Path
import subprocess,os,sys,time,tempfile,urllib.request
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 env=os.environ.copy();env['RADAR_DB']=str(Path(tmp)/'phase14.sqlite3');env.pop('RADAR_SEED_DEMO',None)
 proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--host','127.0.0.1','--port','8892'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  ready=False
  for _ in range(35):
   try:
    with urllib.request.urlopen('http://127.0.0.1:8892/api/health',timeout=1) as r: ready=r.status==200
    if ready:break
   except Exception:time.sleep(.12)
  if not ready:raise RuntimeError('No se ha iniciado el servidor local')
  with sync_playwright() as pw:
   b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
   page=b.new_page(viewport={'width':1365,'height':930})
   page.goto('http://127.0.0.1:8892/',wait_until='domcontentloaded',timeout=16000)
   page.fill('#username','admin');page.fill('#password','radar-demo-admin')
   page.locator('#authForm button[type=submit]').click()
   page.locator('[data-route="completitud"]').click(timeout=15000)
   page.get_by_text('Implantación y variables',exact=True).last.wait_for(timeout=15000)
   assert page.get_by_text('107/107').count()>=1
   page.select_option('#p14Kind','centre');page.select_option('#p14Target','SIM-CS01')
   page.fill('#p14_center_start_date','2026-01-03')
   page.locator('#p14Form button[type=submit]').click()
   page.get_by_text('Registros adicionales',exact=True).wait_for(timeout=15000)
   page.get_by_text('SIM-CS01').first.wait_for(timeout=15000)
   page.screenshot(path='/mnt/data/RADAR_CORUNA_phase14_interfaz.png',full_page=True)
   print('BROWSER_PASS login/phase14/form/save/reload')
   b.close()
 except Exception as e:
  print('BROWSER_UNAVAILABLE',type(e).__name__,str(e)[:450])
  sys.exit(2)
 finally:
  proc.terminate()
  try:proc.wait(timeout=3)
  except subprocess.TimeoutExpired:proc.kill()
