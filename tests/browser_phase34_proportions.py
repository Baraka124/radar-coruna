"""v0.34 UI: field-measured visit and participant layouts; synthetic-only local browser acceptance."""
import sys,tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from browser_phase30_premium import boot,check_layout,click_route

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'v34';OUT.mkdir(exist_ok=True,parents=True)


def check_measure(page,field,max_width):
    w=page.locator('#'+field).bounding_box()['width']
    assert w<=max_width, f'{field} is {w:.1f}px, expected max {max_width}px'
    return round(w)


def main():
    with tempfile.TemporaryDirectory() as td:
        server.DB_FILE=Path(td)/'v34.sqlite3'
        with TestClient(server.app) as client:
            a=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
            assert a.status_code==200,a.text
            h={'X-RADAR-CSRF':a.json()['csrf']}
            p={'id':'SIM-V34','center':'SIM-CS01','status':'incluido','copd':'si','regular':'si','lastCopdReviewDate':'2025-10-01','weeks':8,'capacity':'si','activeExacerb':'no','exclusion':'no','alternativeDiagnosis':'no','seriousDecompensation':'no','interferingTrial':'no','consent':'si','consentDate':'2026-01-08','enrolDate':'2026-01-15','birthDate':'1969-02-15','spiroDate':'2025-12-20','ratio':0.61,'fev1':62,'eligibilityDecision':'elegible','smoking':'ex'}
            assert client.post('/api/patients',json=p,headers=h).status_code==201
            v0={'id':'VIS-V34-V0','patient':'SIM-V34','type':'V0','date':'2026-01-15','status':'completa','rescue':'no','exacerb':'no','dyspnea':'no','activity':'no','cat':10,'mmrc':1,'action':'seguimiento'}
            assert client.post('/api/visits',json=v0,headers=h).status_code==201
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
                for width in (320,390,768,1057,1440):
                    page=browser.new_page(viewport={'width':width,'height':950})
                    errors=boot(page,client)
                    mobile=width<=900
                    click_route(page,'visitas',mobile)
                    page.locator('[data-action="newvisit"]').click()
                    page.locator('#visitForm').wait_for()
                    page.locator('#vdate').fill('2026-07-15')
                    page.locator('#vmmrc').select_option('2')
                    page.locator('#vsmoking').select_option('ex')
                    check_layout(page,width)
                    if width>=768:
                        measurements={
                         'vpatient':262,'vtype':200,'vdate':190,'vassessor':200,
                         'vcat':145,'vmmrc':145,'vsmoking':205}
                        for field,maxw in measurements.items():check_measure(page,field,maxw)
                    if width==1057:
                        page.locator('#visitForm .clinical-block').first.screenshot(path=str(OUT/'v34_visita_1057.png'))
                        page.screenshot(path=str(OUT/'v34_escritorio_1057.png'),full_page=False)
                    if width==390:page.locator('#visitForm .clinical-block').first.screenshot(path=str(OUT/'v34_visita_390.png'))
                    if width==1440:
                        page.locator('#visitForm .clinical-block').first.screenshot(path=str(OUT/'v34_visita_1440.png'))
                        # Confirm that save still follows normal clinical route.
                        page.locator('#visitForm button[type="submit"]').click()
                        page.locator('#root[data-view="detalle"]').wait_for()
                        saved=next(x for x in client.get('/api/state').json()['visits'] if x['patient']=='SIM-V34' and x['type']=='V1')
                        assert saved['date']=='2026-07-15' and saved['mmrc']==2
                    assert not errors,(width,errors)
                    page.close()
                browser.close()
    print('v0.34 proportional fields PASS on 320,390,768,1057,1440; save and no overflow')

if __name__=='__main__':main()
