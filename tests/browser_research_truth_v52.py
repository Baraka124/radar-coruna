"""v0.52 · Research data states must never pretend a failed API returned zero.

All data is isolated in a temporary local SQLite test database. Explicitly intercept
two auxiliary endpoints and verify loading/error/retry/real-empty behavior at three widths.
"""
from pathlib import Path
import sys, tempfile
from httpx import Response
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_phase30_premium import boot,click_route,check_layout
import server

OUT=Path(__file__).resolve().parents[1]/'docs'/'v52'
OUT.mkdir(parents=True,exist_ok=True)

def verify_white(page,width):
    info=page.evaluate("""() => {
        const selectors=['body','.main','.content','.top','.sidebar'];
        return {colors:selectors.map(x=>getComputedStyle(document.querySelector(x)).backgroundColor),
            overflow:document.documentElement.scrollWidth-innerWidth,
            top:document.querySelector('.top').getBoundingClientRect().bottom,
            root:document.getElementById('root').getBoundingClientRect().top};
    }""")
    assert all(c=='rgb(255, 255, 255)' for c in info['colors']),(width,info)
    assert info['overflow']<=2,(width,info)
    check_layout(page,width)

def main():
 with tempfile.TemporaryDirectory() as d:
  server.POSTGRES_MODE=False
  server.DB_FILE=Path(d)/'research_v52.sqlite3'
  with TestClient(server.app) as client:
   response=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
   assert response.status_code==200,response.text
   original=client.request
   failed=set()
   def transport(method,path,*args,**kwargs):
    if method.upper()=='GET' and path.split('?')[0] in failed:
     return Response(status_code=503,json={'detail':'Incidencia simulada en prueba automatizada'})
    return original(method,path,*args,**kwargs)
   client.request=transport
   with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in (390,768,1440):
     page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
     page.set_default_timeout(18000)
     failed.clear()
     failed.add('/api/study/intelligence')
     failed.add('/api/study/reporting')
     errors=boot(page,client)
     mobile=width<=900
     click_route(page,'inteligencia',mobile)
     gate=page.locator('#root .research-resource-state[data-resource-state="error"]')
     gate.wait_for()
     assert 'No se han podido consultar estos datos' in gate.inner_text()
     assert 'inteligencia de datos' in gate.inner_text()
     assert page.locator('#root .int-stat').count()==0,(width,'fabricated metrics on outage')
     assert page.locator('#root [data-action="retry-research"]').count()==1
     verify_white(page,width)
     if width in (390,1440):
      page.screenshot(path=str(OUT/f'intelligence_api_error_{width}.png'),full_page=False)
     failed.remove('/api/study/intelligence')
     page.locator('[data-action="retry-research"]').click()
     page.locator('#root .int-stat').first.wait_for()
     assert page.locator('.research-resource-state').count()==0
     assert 'Participantes incluidos' in page.locator('#root').inner_text()
     assert '0' in page.locator('#root .int-stat').first.inner_text()
     verify_white(page,width)
     if width in (390,1440):
      page.screenshot(path=str(OUT/f'intelligence_real_empty_{width}.png'),full_page=False)
     click_route(page,'analisis',mobile)
     page.locator('#root .research-resource-state[data-resource-state="error"]').wait_for()
     assert page.locator('#root .metric').count()==0,(width,'analysis presented false zero')
     assert 'informe de cohorte' in page.locator('.research-resource-state').inner_text()
     failed.remove('/api/study/reporting')
     page.locator('#root [data-action="retry-research"]').click()
     page.locator('#root .metric').first.wait_for()
     assert page.locator('.research-resource-state').count()==0
     verify_white(page,width)
     # The dictionary and linked CRD still use persisted definitions.
     click_route(page,'estudio',mobile)
     page.locator('#specSearch').wait_for()
     assert page.locator('#specTable tr').count()>0
     verify_white(page,width)
     assert not errors,(width,errors)
     page.close()
    browser.close()
 print('PASS v0.52: API outage not displayed as zero; explicit retry; white research modules at three widths')

if __name__=='__main__':
 main()
