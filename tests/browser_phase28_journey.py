"""Browser acceptance: integrated longitudinal review, desktop and mobile."""
from pathlib import Path
import sys, tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'v28'
OUT.mkdir(parents=True,exist_ok=True)


def open_app(page,client):
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    def transport(_src,path,init=None):
        init=init or {}
        body=init.get('body')
        r=client.request(init.get('method','GET'),path,headers=init.get('headers',{}),
                         content=body.encode() if isinstance(body,str) else body)
        return {'status':r.status_code,'body':r.text,'ctype':r.headers.get('content-type','application/json')}
    page.expose_binding('py_request',transport)
    page.goto('about:blank')
    page.evaluate('window.fetch=async(path,init={})=>{const r=await window.py_request(path,init);return new Response(r.body,{status:r.status,headers:{"Content-Type":r.ctype}})};true')
    page.set_content((ROOT/'static/index.html').read_text(encoding='utf8'),wait_until='domcontentloaded')
    # The TestClient is already signed in to seed this synthetic journey.
    # Wait for boot() to restore that session instead of submitting a second
    # login concurrently, which can race and close the newly opened mobile menu.
    page.locator('body.signed-in').wait_for()
    page.locator('#root[data-view=inicio]').wait_for()
    page.locator('#navigation [data-route=inicio][aria-current=page]').wait_for()
    return errors


def main():
    with tempfile.TemporaryDirectory() as td:
        server.DB_FILE=Path(td)/'radar_ui28.sqlite3'
        with TestClient(server.app) as client:
            h={'X-RADAR-CSRF':client.post('/api/session',json={
                'username':'admin','password':'radar-demo-admin'}).json()['csrf']}
            p={'id':'SIM-UI28','center':'SIM-CS01','status':'incluido','copd':'si',
               'consent':'si','enrolDate':'2026-01-10','spiroDate':'2025-11-30','weeks':5,
               'vitalStatus':'vivo','lastInformationDate':'2027-01-10'}
            assert client.post('/api/patients',json=p,headers=h).status_code==201
            for stage,day,rescue in [('V0','2026-01-10','no'),('V1','2026-07-10','si'),('V2','2027-01-10','si')]:
                z=client.post('/api/visits',headers=h,json={'id':'VIS-UI-'+stage,'patient':'SIM-UI28',
                    'type':stage,'date':day,'rescue':rescue,'exacerb':'no','dyspnea':'no',
                    'activity':'no','cat':12,'mmrc':0,'action':'seguimiento','status':'completa'})
                assert z.status_code==201,z.text
            assert client.post('/api/episodes',headers=h,json={
                'id':'EPI-UI28','patient':'SIM-UI28','date':'2026-03-01','kind':'agudizacion',
                'severity':'moderada','copd':'si'}).status_code==201
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',
                    args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
                page=browser.new_page(viewport={'width':1440,'height':950},device_scale_factor=1)
                page.set_default_timeout(16000)
                errs=open_app(page,client)
                page.locator('[data-route="cohorte"]').click()
                page.locator('[data-action="detail"]').first.click()
                page.locator('#journeyReview .journey-review-statgrid').wait_for()
                assert '3 / 3' in page.locator('#journeyReview').inner_text()
                assert 'Agudizaciones EPOC' in page.locator('#journeyReview').inner_text()
                assert 'Variación RADAR V2' in page.locator('#journeyReview').inner_text()
                page.screenshot(path=str(OUT/'v28_journey_desktop.png'),full_page=True)
                assert not errs,errs
                mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
                mobile.set_default_timeout(16000)
                errs2=open_app(mobile,client)
                mobile.locator('#mobileNavToggle').click()
                # Allow the off-canvas sidebar's 220ms transform to finish before
                # asking Playwright to scroll and click a link inside it. Otherwise
                # Chromium can cache the pre-animation off-screen click target.
                mobile.wait_for_function("""() => {
                    const sidebar = document.querySelector('#sidebar');
                    return document.body.classList.contains('mobile-nav-open') &&
                        sidebar && sidebar.getBoundingClientRect().left >= -0.5;
                }""",polling=100)
                mobile.locator('[data-route="cohorte"]').click()
                mobile.locator('[data-action="detail"]').first.click()
                mobile.locator('#journeyReview .journey-review-statgrid').wait_for()
                assert mobile.locator('#journeyReview .journey-review-item').count()==3
                mobile.screenshot(path=str(OUT/'v28_journey_mobile.png'),full_page=True)
                # Do not confuse an off-screen navigation animation with horizontal overflow.
                overflow=mobile.evaluate('document.documentElement.scrollWidth>window.innerWidth+2')
                assert not overflow,'Mobile page has horizontal overflow'
                assert not errs2,errs2
                browser.close()
    print('Desktop + mobile longitudinal review: PASS')

if __name__=='__main__':main()
