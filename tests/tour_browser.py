"""Local browser acceptance: python tests/tour_browser.py (requires Playwright/Chrome)."""
import os,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(os.environ.get('CUSTOMCHAT_TEST_ROOT',str(Path(__file__).resolve().parents[1])))
def run():
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    with tempfile.TemporaryDirectory() as folder:
        proc=subprocess.Popen([sys.executable,'-m','customchat','start','--directory',folder+'/workspace','--port',str(port),'--no-browser'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        url='http://127.0.0.1:'+str(port)
        try:
            for _ in range(100):
                try:urllib.request.urlopen(url+'/api/health').close();break
                except OSError:time.sleep(.1)
            with sync_playwright() as pw:
                browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
                page=browser.new_page(viewport={'width':1280,'height':980});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                def bounds():
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    r=page.locator('.cc-tour').bounding_box();assert r['x']>=0 and r['y']>=0 and r['x']+r['width']<=page.viewport_size['width']+1 and r['y']+r['height']<=page.viewport_size['height']+1
                    for selector in ['.cc-tour-skip','.cc-tour-next']:
                        b=page.locator(selector).bounding_box();assert b['y']>=r['y'] and b['y']+b['height']<=r['y']+r['height']+1
                page.goto(url);page.wait_for_selector('.cc-tour');bounds();assert page.locator('.cc-tour-label').text_content()=='Quick tour'
                page.locator('.cc-tour-skip').click();assert page.evaluate('localStorage.getItem("cc_tour")')=='1'
                page.reload();page.wait_for_selector('#q');assert page.locator('.cc-tour').count()==0
                page.locator('#chatGuide').click();page.wait_for_selector('.cc-tour');page.locator('.cc-tour-next').click();assert 'Keep the conversation' in page.locator('.cc-tour h2').inner_text();page.locator('.cc-tour-back').click();page.keyboard.press('Escape');assert page.locator('.cc-tour').count()==0
                page.goto(url+'/settings.html');page.wait_for_selector('.cc-tour');bounds();assert page.locator('.cc-tour-label').text_content()=='Configuration guide'
                initial=page.evaluate('localStorage.getItem("cc_cfg_mode")');page.wait_for_timeout(450);page.screenshot(path='/tmp/tour-config-desktop.png')
                assert page.locator('.cc-tour-orb').evaluate('(e)=>e.getAnimations().length')>0
                for i in range(8):
                    assert page.locator('.cc-tour-count').inner_text()==f'{i+1} / 8';bounds()
                    page.locator('.cc-tour-next').click()
                assert page.locator('.cc-tour').count()==0;assert page.evaluate('localStorage.getItem("cc_cfg_mode")')==initial
                page.reload();page.wait_for_selector('#configGuide');page.wait_for_timeout(400);assert page.locator('.cc-tour').count()==0
                for width,height in [(390,844),(320,568),(820,980),(1280,540)]:
                    page.set_viewport_size({'width':width,'height':height});page.locator('#configGuide').click();page.wait_for_selector('.cc-tour')
                    for i in range(8):
                        bounds()
                        if width==390 and i==5:page.wait_for_timeout(450);page.screenshot(path='/tmp/tour-config-mobile.png')
                        page.locator('.cc-tour-next').click()
                page.emulate_media(reduced_motion='reduce');page.locator('#configGuide').click();assert page.locator('.cc-tour-orb').evaluate('(e)=>e.getAnimations().length')==0
                page.keyboard.press('ArrowRight');assert page.locator('.cc-tour-count').inner_text()=='2 / 8';page.keyboard.press('ArrowLeft');assert page.locator('.cc-tour-count').inner_text()=='1 / 8'
                page.locator('.cc-tour-skip').click();assert page.locator('#configGuide').evaluate('(e)=>e===document.activeElement')
                page.evaluate('localStorage.removeItem("cc_cfg_tour_v1")');page.reload();page.wait_for_selector('.cc-tour');page.locator('.cc-tour-skip').click();page.reload();page.wait_for_selector('#configGuide');page.wait_for_timeout(400);assert page.locator('.cc-tour').count()==0
                page.goto(url+'/?preview=1');page.wait_for_selector('#q');assert page.locator('.cc-tour').count()==0
                assert not errors,errors;print('PASS: independent first-open flags, Skip both guides, eight config steps, replay, Back, Escape/arrows/focus, reduced motion, 4 viewport sizes, no setting changes, no preview guide, no JS errors');browser.close()
        finally:proc.terminate();proc.wait()
if __name__=='__main__':run()
