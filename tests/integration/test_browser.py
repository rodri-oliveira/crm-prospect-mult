"""Browser smoke tests use synthetic data and block all external services."""
import shutil
import os
import threading
from pathlib import Path
import pytest
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright


@pytest.mark.skipif(os.environ.get('CRM_BROWSER_TESTS') != '1', reason='Set CRM_BROWSER_TESTS=1 to run Chromium checks.')
def test_browser_prospecting_csv_and_safe_rendering(crm, tmp_path):
    app, _ = crm
    server=make_server('127.0.0.1',0,app)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    origin=f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            executable=shutil.which('chromium')
            if not executable and not Path(p.chromium.executable_path).exists():
                pytest.skip('Install Chromium with python -m playwright install chromium for browser checks.')
            browser=p.chromium.launch(headless=True,executable_path=executable)
            page=browser.new_page(viewport={'width':1440,'height':1000})
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(origin+'/') else route.abort())
            page.goto(origin+'/prospeccao')
            page.wait_for_function("typeof window.searchMap === 'function' && !!window.Alpine")
            assert page.locator('#mapEstado option').all_text_contents()==['UF','SP','RJ','MG','ES']
            assert page.evaluate("Alpine.$data(document.getElementById('segmentoSelector')).selecionados")==['Acessórios de informática']
            page.evaluate("window.__renderMapsResults([{id:'synthetic',nome:'<img src=x onerror=window.injected=1>',endereco:'<script>bad</script>',website:'javascript:alert(1)',telefone:'2732221234'}])")
            assert page.locator('#mapsResults img').count()==0
            assert page.locator('#mapsResults script').count()==0
            assert not page.evaluate('!!window.injected')
            # Run a real multipart upload, signed preview and CSRF-protected confirmation.
            page.goto(origin+'/prospeccao/importar')
            page.locator('input[type=file]').set_input_files({'name':'synthetic.csv','mimeType':'text/csv','buffer':b'nome_loja;cidade;estado;telefone\nLoja Sintetica Informatica;Vitoria;ES;2732221234\n'})
            page.get_by_role('button',name='Conferir arquivo').click()
            page.wait_for_selector('input[name=preview_token]')
            assert page.locator('input[name=selected]').is_checked()
            page.get_by_role('button',name='Importar selecionados').click()
            page.get_by_role('status').wait_for()
            assert '1 contatos importados' in page.get_by_role('status').inner_text()
            page.goto(origin+'/prospeccao')
            assert 'Loja Sintetica Informatica' in page.locator('body').inner_text()
            page.set_viewport_size({'width':390,'height':844})
            page.screenshot(path=str(tmp_path/'prospeccao-mobile.png'),full_page=True)
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown();thread.join(timeout=5)
