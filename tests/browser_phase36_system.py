"""v0.36 browser-wide visual contract: 12 routes, synthetic data, 5 widths, core actions."""
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from browser_phase30_premium import boot,click_route,check_layout
import server

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'v36'; OUT.mkdir(parents=True,exist_ok=True)
ROUTES=('inicio','cohorte','visitas','flujo','crd','eventos','resultados','completitud','analisis','calidad','estudio','exportacion')

def main():
    with tempfile.TemporaryDirectory() as td:
        server.DB_FILE=Path(td)/'ui-system.sqlite3'
        with TestClient(server.app) as client:
            a=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'}); assert a.status_code==200,a.text
            h={'X-RADAR-CSRF':a.json()['csrf']}
            participant={'id':'SIM-DESIGN36','center':'SIM-CS01','status':'incluido','copd':'si','regular':'si','lastCopdReviewDate':'2025-09-15','weeks':8,'capacity':'si','activeExacerb':'no','exclusion':'no','alternativeDiagnosis':'no','seriousDecompensation':'no','interferingTrial':'no','consent':'si','consentDate':'2026-01-08','enrolDate':'2026-01-15','birthDate':'1969-02-15','spiroDate':'2025-12-20','ratio':.61,'fev1':62,'eligibilityDecision':'elegible','smoking':'ex'}
            a=client.post('/api/patients',json=participant,headers=h); assert a.status_code==201,a.text
            a=client.post('/api/visits',json={'id':'VIS-DESIGN36-V0','patient':'SIM-DESIGN36','type':'V0','date':'2026-01-15','status':'completa','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no','cat':10,'mmrc':1,'action':'seguimiento'},headers=h);assert a.status_code==201,a.text
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
                for width in (320,390,768,1057,1440):
                    mobile=width<=900
                    page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
                    page.set_default_timeout(18000)
                    errors=boot(page,client)
                    for route in ROUTES:
                        if route!='inicio':click_route(page,route,mobile)
                        check_layout(page,width)
                        layout=page.evaluate('''() => ({width:document.documentElement.scrollWidth,viewport:window.innerWidth,
                         buttons:[...document.querySelectorAll('#root .head .btn')].map(x=>Math.round(x.getBoundingClientRect().width)),
                         top:Math.round(document.querySelector('.top').getBoundingClientRect().height)})''')
                        assert layout['width']<=width+2,(route,width,layout)
                        assert all(x<260 for x in layout['buttons']),(route,width,layout)
                        if width==1440:
                            page.screenshot(path=str(OUT/f'v36_{route}_desktop.png'),full_page=False)
                        if width==390 and route in ('inicio','cohorte','crd','calidad','eventos'):
                            page.screenshot(path=str(OUT/f'v36_{route}_mobile.png'),full_page=False)
                    click_route(page,'visitas',mobile)
                    page.locator('[data-action="newvisit"]').click()
                    page.locator('#visitForm').wait_for()
                    check_layout(page,width)
                    pwidth=page.locator('#vpatient').bounding_box()['width']
                    if width>=1057:assert pwidth<=255,(width,pwidth)
                    if width in (390,1057,1440):page.screenshot(path=str(OUT/f'v36_evaluacion_{width}.png'),full_page=False)
                    if width==1440:
                        page.locator('#vdate').fill('2026-07-15')
                        page.locator('#vmmrc').select_option('2')
                        page.locator('#vsmoking').select_option('ex')
                        page.locator('#visitForm button[type="submit"]').click()
                        page.locator('#root[data-view="detalle"]').wait_for()
                        saved=next(v for v in client.get('/api/state').json()['visits'] if v['patient']=='SIM-DESIGN36' and v['type']=='V1')
                        assert saved['date']=='2026-07-15' and saved['mmrc']==2,saved
                    # Other editors use the same field-width discipline as the visit editor.
                    click_route(page,'cohorte',mobile)
                    page.locator('[data-action="newpatient"]').click()
                    page.locator('#patientForm').wait_for()
                    check_layout(page,width)
                    if width>=1057:
                        assert page.locator('#pcenter').bounding_box()['width']<=245
                    if width in (390,1440):
                        page.screenshot(path=str(OUT/f'v36_participant_form_{width}.png'),full_page=False)
                    click_route(page,'eventos',mobile)
                    page.locator('[data-action="newevent"]').click()
                    page.locator('#eventForm').wait_for()
                    check_layout(page,width)
                    if width>=1057:
                        assert page.locator('#epatient').bounding_box()['width']<=250
                    if width in (390,1440):
                        page.screenshot(path=str(OUT/f'v36_event_form_{width}.png'),full_page=False)
                    if mobile:
                        page.locator('#mobileNavToggle').click()
                        page.wait_for_function('''() => document.body.classList.contains('mobile-nav-open') && document.querySelector('#sidebar').getBoundingClientRect().left >= -0.5''')
                        page.keyboard.press('Escape')
                        assert not page.locator('body').evaluate("e=>e.classList.contains('mobile-nav-open')")
                    assert not errors,(width,errors)
                    page.close()
                    print('PASS width',width, '12 routes',flush=True)
                browser.close()
    print('v0.36 PASS: 12 routes x 5 widths + visit form, save, mobile drawer, no JS errors')
if __name__=='__main__':main()
