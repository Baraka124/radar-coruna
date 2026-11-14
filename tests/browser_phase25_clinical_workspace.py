"""v0.25 acceptance: connected forms, section jumps, and preserved saved records."""
from pathlib import Path
import tempfile, sys
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data/RADAR_CORUNA_UI_v25')

def open_app(page,client):
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def transport(_src,path,init=None):
        init=init or {};body=init.get('body')
        r=client.request(init.get('method','GET'),path,headers=init.get('headers',{}),content=body.encode() if isinstance(body,str) else body)
        return {'status':r.status_code,'body':r.text,'ctype':r.headers.get('content-type','application/json')}
    page.expose_binding('py_request',transport)
    page.goto('about:blank')
    page.evaluate("window.fetch=async(path,init={})=>{const r=await window.py_request(path,init);return new Response(r.body,{status:r.status,headers:{'Content-Type':r.ctype}})};true")
    page.set_content((ROOT/'static/index.html').read_text(encoding='utf8'),wait_until='domcontentloaded')
    page.fill('#password','radar-demo-admin')
    page.locator('#authForm button[type=submit]').click()
    page.locator('body.signed-in').wait_for()
    return errors

def main():
 with tempfile.TemporaryDirectory() as td:
    server.DB_FILE=Path(td)/'clinical_workspace.sqlite3'
    with TestClient(server.app) as client, sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--no-proxy-server'])
        page=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
        page.set_default_timeout(11000)
        errors=open_app(page,client)
        page.locator('[data-route=cohorte]').click()
        page.locator('button[data-action=newpatient]').first.click()
        nav=page.locator('#patientForm .clinical-section-nav')
        assert nav.locator('button').count()==5
        page.screenshot(path=str(OUT/'v25_registro_desktop.png'),full_page=False)
        page.fill('#pcode','SIM-V25-001')
        page.select_option('#pstatus','incluido')
        nav.get_by_text('Inclusión').click()
        assert page.locator('#pcopd').is_visible()
        page.select_option('#pcopd','si')
        page.select_option('#pconsent','si')
        page.select_option('#peligibility','elegible')
        page.select_option('#pactive','no')
        page.fill('#pweeks','5')
        nav.get_by_text('Datos basales').click()
        page.fill('#pbirthdate','1963-05-14')
        page.fill('#pspirodate','2025-12-14')
        page.fill('#penrol','2026-01-10')
        page.fill('#ppriormod','2')
        page.fill('#ppriorsev','1')
        nav.get_by_text('Inclusión').click()
        assert page.locator('#pbirthdate').input_value()=='1963-05-14' # no loss on navigation
        page.screenshot(path=str(OUT/'v25_registro_inclusion.png'),full_page=False)
        page.locator('#patientForm button[type=submit]').click()
        page.locator('.patient-journey').wait_for()
        page.locator('[data-action=workflowvisit][data-visit=V0]').first.click()
        visit=page.locator('#visitForm')
        assert visit.locator('.clinical-section-nav button').count()==5
        assert 'V0' in visit.locator('.clinical-stage-mark').inner_text()
        assert 'SIM-V25-001' in visit.locator('.clinical-stage-mark').inner_text()
        page.screenshot(path=str(OUT/'v25_visita_desktop.png'),full_page=False)
        vnav=visit.locator('.clinical-section-nav')
        page.fill('#vcat','11')
        page.select_option('#vmmrc','1')
        vnav.get_by_text('RADAR',exact=True).click()
        for q in ['vrescue','vexacerb','vdyspnea','vactivity']:page.select_option('#'+q,'no')
        vnav.get_by_text('Tratamiento',exact=True).click()
        page.select_option('#vregimen','mono')
        page.select_option('#vmono','lama')
        page.select_option('#vroflumilast','no')
        page.select_option('#vazithromycin','no')
        page.select_option('#vrescueprescription','saba')
        page.screenshot(path=str(OUT/'v25_visita_tratamiento.png'),full_page=False)
        vnav.get_by_text('IANUS',exact=True).click()
        page.select_option('#vianusverified','si')
        page.select_option('#vianuscollected','si')
        vnav.get_by_text('Actuación',exact=True).click()
        page.select_option('#vaction','seguimiento')
        page.select_option('#vstatus','completa')
        assert page.locator('#vregimen').input_value()=='mono'
        page.locator('#visitForm button[type=submit]').click()
        page.locator('.patient-journey').wait_for()
        state=client.get('/api/state').json()
        assert len(state['patients'])==1 and state['patients'][0]['birthDate']=='1963-05-14'
        assert len(state['visits'])==1 and state['visits'][0]['inhaledRegimen']=='mono'
        page.locator('[data-route=visitas]').click()
        page.locator('button[data-action=editvisit]').first.click()
        assert page.locator('#visitForm').count()==1
        assert page.locator('#workspaceContext').inner_text().find('SIM-V25-001')>=0
        assert page.locator('#visitForm .clinical-return[data-action=detail]').get_attribute('data-id')=='SIM-V25-001'
        page.locator('#visitForm .clinical-return[data-action=detail]').click()
        assert page.locator('.patient-journey').count()==1
        assert 'SIM-V25-001' in page.locator('.head h1').inner_text()
        assert not errors,errors
        page.close()
        mob=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
        mob.set_default_timeout(11000)
        e2=open_app(mob,client)
        mob.locator('#root[data-view=inicio]').wait_for()
        mob.wait_for_timeout(180)
        mob.locator('#mobileNavToggle').click()
        mob.locator('[data-route=cohorte]').click()
        mob.locator('button[data-action=detail]').first.click()
        mob.locator('button[data-action=editpatient]').first.click()
        assert mob.locator('#patientForm .clinical-toolbar').is_visible()
        mob.screenshot(path=str(OUT/'v25_registro_mobile.png'),full_page=False)
        mob.locator('#patientForm .clinical-section-nav').get_by_text('Datos basales').click()
        assert mob.locator('#pbirthdate').is_visible()
        assert mob.evaluate('document.documentElement.scrollWidth - window.innerWidth')<=2
        assert not e2,e2
        mob.close();browser.close()
        print('PASS: desktop registration, section jumps, saved V0, treatment, edit-return context; mobile section navigation; no browser errors')
if __name__=='__main__':main()
