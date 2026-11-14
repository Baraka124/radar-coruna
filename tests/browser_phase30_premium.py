"""Phase 4 v0.30 browser acceptance: proportional controls, navigation and no overflow.

Runs against an isolated temporary SQLite database with synthetic participants only.
"""
from pathlib import Path
import sys, tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs'/'v30'
OUT.mkdir(parents=True, exist_ok=True)

def boot(page,client):
    errors=[]
    page.on('pageerror', lambda e:errors.append(str(e)))
    def transport(_src,path,init=None):
        init=init or {}
        body=init.get('body')
        resp=client.request(init.get('method','GET'),path,headers=init.get('headers',{}),
                            content=body.encode() if isinstance(body,str) else body)
        return {'status':resp.status_code, 'body':resp.text,
                'ctype':resp.headers.get('content-type','application/json')}
    page.expose_binding('py_request',transport)
    page.goto('about:blank')
    page.evaluate('window.fetch=async(path,init={})=>{const r=await window.py_request(path,init);return new Response(r.body,{status:r.status,headers:{"Content-Type":r.ctype}})};true')
    page.set_content((ROOT/'static/index.html').read_text(encoding='utf8'),wait_until='domcontentloaded')
    page.locator('body.signed-in').wait_for()
    page.locator('#root[data-view="inicio"]').wait_for()
    return errors

def click_route(page,route,mobile):
    if mobile:
        page.locator('#mobileNavToggle').click()
        page.wait_for_function('''() => document.body.classList.contains('mobile-nav-open') &&
                     document.querySelector('#sidebar').getBoundingClientRect().left >= -0.5''')
    page.locator(f'#navigation [data-route="{route}"]').click()
    page.locator(f'#root[data-view="{route}"]').wait_for()
    if mobile:
        # Screenshots must represent the settled view, not a closing drawer animation.
        page.wait_for_function("() => !document.body.classList.contains('mobile-nav-open')")
        page.wait_for_function("() => document.querySelector('#sidebar').getBoundingClientRect().right<=1")

def check_layout(page,width):
    result=page.evaluate('''() => ({doc:document.documentElement.scrollWidth,screen:innerWidth,
       headButtons:[...document.querySelectorAll('#root .head .actions .btn')].map(b=>Math.round(b.getBoundingClientRect().width)),
       footerButtons:[...document.querySelectorAll('#root .footerbar .btn')].map(b=>Math.round(b.getBoundingClientRect().width))})''')
    assert result['doc'] <= result['screen']+2, f'Horizontal overflow {width}px: {result}'
    assert all(w<=244 for w in result['headButtons']+result['footerButtons']), result


def main():
    with tempfile.TemporaryDirectory() as td:
        server.DB_FILE=Path(td)/'radar_phase30.sqlite3'
        with TestClient(server.app) as client:
            auth=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
            assert auth.status_code==200
            headers={'X-RADAR-CSRF':auth.json()['csrf']}
            result=client.post('/api/patients',headers=headers,json={'id':'SIM-P30','center':'SIM-CS01',
                'status':'incluido','copd':'si','consent':'si','consentDate':'2026-01-05','enrolDate':'2026-01-10','spiroDate':'2025-11-30','weeks':5,'birthDate':'1965-01-03','ratio':0.6,'regular':'si','lastCopdReviewDate':'2025-06-01','capacity':'si','activeExacerb':'no','exclusion':'no','alternativeDiagnosis':'no','seriousDecompensation':'no','interferingTrial':'no','eligibilityDecision':'elegible'})
            assert result.status_code==201,result.text
            result=client.post('/api/visits',headers=headers,json={'id':'V0-P30','patient':'SIM-P30',
                'type':'V0','date':'2026-01-10','rescue':'no','exacerb':'no',
                'dyspnea':'no','activity':'no','cat':8,'mmrc':0,'action':'seguimiento','status':'completa'})
            assert result.status_code==201,result.text
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',
                    args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
                for width in (320,390,768,1024,1440):
                    mobile=width<=900
                    page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
                    page.set_default_timeout(18000)
                    errs=boot(page,client)
                    for route in ('inicio','cohorte','visitas','crd','eventos','analisis'):
                        if route!='inicio':click_route(page,route,mobile)
                        check_layout(page,width)
                        if route=='cohorte':
                            if width==1440:
                                search_w=page.locator('#filterPatients').bounding_box()['width']
                                assert search_w<=302, search_w
                                page.screenshot(path=str(OUT/'v30_cohorte_desktop.png'),full_page=True)
                            if width==390:
                                page.screenshot(path=str(OUT/'v30_cohorte_mobile.png'),full_page=True)
                    click_route(page,'cohorte',mobile)
                    page.locator('[data-action="newpatient"]').click()
                    page.locator('#patientForm').wait_for()
                    check_layout(page,width)
                    if width>900:
                        inp=page.locator('#pweeks')
                        assert inp.bounding_box()['width']<=190,inp.bounding_box()
                        date=page.locator('#pbirth') if page.locator('#pbirth').count() else page.locator('#penrol')
                        if date.count(): assert date.bounding_box()['width']<=207,date.bounding_box()
                    if width==390:
                        page.screenshot(path=str(OUT/'v30_participante_mobile.png'),full_page=True)
                    if width==1440:
                        page.screenshot(path=str(OUT/'v30_participante_desktop.png'),full_page=True)
                    if mobile:
                        page.locator('#mobileNavToggle').click()
                        page.wait_for_function('''() => document.querySelector('#sidebar').getBoundingClientRect().left>=-0.5''')
                        page.keyboard.press('Escape')
                        assert not page.locator('body').evaluate("e=>e.classList.contains('mobile-nav-open')")
                    assert not errs,f'Uncaught JS errors at {width}: {errs}'
                    page.close()
                browser.close()
    print('Phase 4 responsive acceptance PASS · 5 widths, 6 routes, form & mobile menu')

if __name__=='__main__':main()
