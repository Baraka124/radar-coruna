"""v0.46 browser regression: no fake content, top-aligned cohort, responsive workflow."""
from pathlib import Path
import sys
import tempfile
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from browser_phase30_premium import boot, click_route, check_layout
import server

OUTPUT = Path(__file__).resolve().parents[1] / 'docs' / 'v46'
OUTPUT.mkdir(parents=True, exist_ok=True)


def visible_geometry(page):
    return page.evaluate("""() => {
      const main=document.querySelector('.cohort-workspace');
      const top=document.querySelector('.top');
      const rect=main.getBoundingClientRect();
      const topRect=top.getBoundingClientRect();
      return {
        top: rect.top, headerBottom: topRect.bottom, width: rect.width,
        documentWidth: document.documentElement.scrollWidth, viewport: innerWidth,
        contextualVisible: document.querySelector('.workspace-context').getBoundingClientRect().height > 0
      };
    }""")


def capture(page, label, width):
    if width in (390, 1440):
        page.screenshot(path=str(OUTPUT / f'cohort_{label}_{width}.png'), full_page=False)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        server.DB_FILE=Path(tmp)/'cohort_v46.sqlite3'
        server.POSTGRES_MODE=False
        with TestClient(server.app) as client:
            login=client.post('/api/session',json={'username':'admin','password':'radar-demo-admin'})
            assert login.status_code==200, login.text
            csrf={'X-RADAR-CSRF':login.json()['csrf']}
            assert client.get('/api/state').json()['centres']==[]
            assert client.get('/api/state').json()['patients']==[]
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
                for width in (320,390,768,1024,1440):
                    page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
                    page.set_default_timeout(18000)
                    errors=boot(page,client)
                    click_route(page,'cohorte',width<=900)
                    assert page.locator('#root .cohort-workspace.is-empty').count()==1
                    assert page.locator('#filterPatients').count()==0
                    assert page.locator('#filterCentre').count()==0
                    assert page.locator('.cohort-zero').is_visible()
                    assert 'Primero, registra un centro' in page.locator('.cohort-zero').inner_text()
                    assert page.locator('.cohort-zero [data-action="open-admin-centres"]').count()==1
                    assert page.locator('#root [data-action="newpatient"]').count()==0
                    assert page.locator('.cohort-zero-stat strong').inner_text()=='0'
                    size=visible_geometry(page)
                    assert size['top']<=size['headerBottom']+55,(width,size)
                    assert not size['contextualVisible'],(width,size)
                    check_layout(page,width)
                    capture(page,'no_centres',width)
                    assert not errors,(width,errors)
                    page.close()
                created=client.post('/api/centres',headers=csrf,
                    json={'code':'GAL_AP_01','name':'Centro de ensayo creado por prueba automatizada'})
                assert created.status_code==201,created.text
                for width in (390,1440):
                    page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
                    errors=boot(page,client)
                    click_route(page,'cohorte',width<=900)
                    assert page.locator('.cohort-workspace.is-empty').count()==1
                    assert page.locator('.cohort-zero [data-action="newpatient"]').count()==1
                    assert page.locator('#filterPatients').count()==0
                    capture(page,'centre_no_records',width)
                    assert not errors,(width,errors)
                    page.close()
                created_patient=client.post('/api/patients',headers=csrf,
                    json={'id':'SIM-UI-V46-01','center':'GAL_AP_01'})
                assert created_patient.status_code==201,created_patient.text
                for width in (320,390,768,1024,1440):
                    page=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
                    errors=boot(page,client)
                    click_route(page,'cohorte',width<=900)
                    assert page.locator('.cohort-workspace.has-records').count()==1
                    assert page.locator('#filterPatients').is_visible()
                    assert page.locator('#filterCentre').is_visible()
                    assert page.locator('#cohortTable tbody tr').count()==1
                    assert 'SIM-UI-V46-01' in page.locator('#cohortTable').inner_text()
                    assert 'Centro de ensayo creado por prueba automatizada' in page.locator('#cohortTable').inner_text()
                    page.locator('#filterPatients').fill('NO_MATCH')
                    assert page.locator('#cohortTable tbody tr').count()==0
                    assert 'No hay coincidencias' in page.locator('#cohortTable').inner_text()
                    page.locator('#clearCohortFilters').click()
                    assert page.locator('#cohortTable tbody tr').count()==1
                    assert page.locator('#cohortCount').inner_text()=='1 de 1'
                    check_layout(page,width)
                    capture(page,'with_records',width)
                    assert not errors,(width,errors)
                    page.close()
                browser.close()
    print('PASS cohort v0.46: true zero states, desktop/mobile top alignment, filters and real persisted records')


if __name__=='__main__':
    main()
