"""v0.35 synthetic-only design acceptance: proportion, hierarchy, navigation, persistence."""
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
import server
from browser_phase30_premium import boot, click_route, check_layout

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'v35'; OUT.mkdir(parents=True,exist_ok=True)

def main():
    with tempfile.TemporaryDirectory() as td:
        server.DB_FILE=Path(td)/'design.sqlite3'
        with TestClient(server.app) as client:
            a=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
            assert a.status_code==200,a.text
            h={'X-RADAR-CSRF':a.json()['csrf']}
            p={'id':'SIM-DESIGN35','center':'SIM-CS01','status':'incluido','copd':'si','regular':'si','lastCopdReviewDate':'2025-10-01','weeks':8,'capacity':'si','activeExacerb':'no','exclusion':'no','alternativeDiagnosis':'no','seriousDecompensation':'no','interferingTrial':'no','consent':'si','consentDate':'2026-01-08','enrolDate':'2026-01-15','birthDate':'1969-02-15','spiroDate':'2025-12-20','ratio':.61,'fev1':62,'eligibilityDecision':'elegible','smoking':'ex'}
            resp=client.post('/api/patients',json=p,headers=h);assert resp.status_code==201,resp.text
            v0={'id':'VIS-DESIGN35-V0','patient':'SIM-DESIGN35','type':'V0','date':'2026-01-15','status':'completa','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no','cat':10,'mmrc':1,'action':'seguimiento'}
            resp=client.post('/api/visits',json=v0,headers=h);assert resp.status_code==201,resp.text
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
                for width in (320,390,768,1057,1440):
                    mobile=width<=900
                    page=browser.new_page(viewport={'width':width,'height':930},device_scale_factor=1)
                    errs=boot(page,client)
                    for route in ('cohorte','visitas','crd'):
                        click_route(page,route,mobile)
                        check_layout(page,width)
                        if width==1440 and route in ('cohorte','crd'):
                            page.screenshot(path=str(OUT/('v35_'+route+'_escritorio.png')),full_page=False)
                    click_route(page,'visitas',mobile)
                    page.locator('[data-action="newvisit"]').click()
                    page.locator('#visitForm').wait_for()
                    page.locator('#vdate').fill('2026-07-15')
                    page.locator('#vmmrc').select_option('2')
                    page.locator('#vsmoking').select_option('ex')
                    check_layout(page,width)
                    measure=page.evaluate('''() => {
                     const rect=x=>{const r=x.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,right:r.right}};
                     const form=document.querySelector('#visitForm');
                     const title=form.querySelector('.clinical-block-title span');
                     const side=form.querySelector('#visitCompleteness');
                     const p=form.querySelector('#vpatient');
                     return {title:rect(title),p:rect(p),side:rect(side),sideCol:getComputedStyle(side).gridColumnStart,
                             pageWidth:document.documentElement.scrollWidth,view:innerWidth};}''')
                    assert measure['title']['x'] < measure['p']['right'],measure
                    if width>900: assert measure['p']['width']<=253,measure
                    assert measure['pageWidth']<=width+2,measure
                    if width==1440:
                        assert measure['side']['x']>measure['p']['right']+30,measure
                        page.screenshot(path=str(OUT/'v35_evaluacion_escritorio.png'),full_page=False)
                        page.locator('#visitForm button[type="submit"]').click()
                        page.locator('#root[data-view="detalle"]').wait_for()
                        saved=next(v for v in client.get('/api/state').json()['visits'] if v['patient']=='SIM-DESIGN35' and v['type']=='V1')
                        assert saved['date']=='2026-07-15' and saved['mmrc']==2,saved
                    elif width==1057:
                        page.screenshot(path=str(OUT/'v35_evaluacion_portatil.png'),full_page=False)
                    elif width==390:
                        page.screenshot(path=str(OUT/'v35_evaluacion_movil.png'),full_page=False)
                    if mobile:
                        page.locator('#mobileNavToggle').click()
                        page.wait_for_function('''() => document.body.classList.contains('mobile-nav-open') &&
                              document.querySelector('#sidebar').getBoundingClientRect().left>=-0.5''')
                        page.keyboard.press('Escape')
                        assert not page.locator('body').evaluate("e=>e.classList.contains('mobile-nav-open')")
                    assert not errs,(width,errs)
                    page.close()
                browser.close()
    print('v0.35 design PASS: 320/390/768/1057/1440; three modules; field proportions; context rail; save; mobile drawer')

if __name__=='__main__': main()
