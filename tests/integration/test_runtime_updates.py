"""Exercise the real startup and template loader, not just rendered HTML strings."""
import os
from pathlib import Path
import runpy
import shutil
from flask import Flask
from jinja2 import FileSystemLoader


def test_prospecting_updates_sidebar_after_template_changes_without_restart(crm,browser,tmp_path,monkeypatch):
    app,_=crm
    templates=tmp_path/'templates'
    shutil.copytree(Path(app.root_path)/'templates',templates)
    layout=templates/'layout.html'
    original=layout.read_text()
    layout.write_text(original.replace('<body ', '<!-- runtime-before --><body ',1))
    monkeypatch.setattr(app,'jinja_loader',FileSystemLoader(str(templates)))
    app.jinja_env.cache.clear()
    assert '<!-- runtime-before -->' in browser.get('/prospeccao').get_data(as_text=True)
    cached_mtime=layout.stat().st_mtime
    layout.write_text(layout.read_text().replace('runtime-before','runtime-after'))
    os.utime(layout,(cached_mtime+2,cached_mtime+2))
    text=browser.get('/prospeccao').get_data(as_text=True)
    app.jinja_env.cache.clear()
    assert '<!-- runtime-after -->' in text
    assert '<!-- runtime-before -->' not in text


def test_py_app_startup_watches_code_without_exposing_debugger(crm,monkeypatch):
    monkeypatch.delenv('FLASK_DEBUG',raising=False)
    monkeypatch.delenv('CRM_AUTO_RELOAD',raising=False)
    monkeypatch.setattr('application.shared.runtime.port_in_use',lambda host,port:False)
    captured={}
    def capture(self,**kwargs):captured.update(kwargs)
    monkeypatch.setattr(Flask,'run',capture)
    runpy.run_path(str(Path(__file__).resolve().parents[2]/'app.py'),run_name='__main__')
    assert captured['debug'] is False
    assert captured.get('use_reloader') is True



def test_startup_rejects_occupied_port_instead_of_another_process(crm,monkeypatch):
    import pytest
    monkeypatch.delenv('WERKZEUG_RUN_MAIN',raising=False)
    monkeypatch.setattr('application.shared.runtime.port_in_use',lambda host,port:True)
    def unexpected_run(self,**kwargs):raise AssertionError('Another server must not start')
    monkeypatch.setattr(Flask,'run',unexpected_run)
    with pytest.raises(SystemExit,match='já está em uso'):
        runpy.run_path(str(Path(__file__).resolve().parents[2]/'app.py'),run_name='__main__')


def test_reloader_child_can_reuse_parent_socket(crm,monkeypatch):
    monkeypatch.setenv('WERKZEUG_RUN_MAIN','true')
    monkeypatch.setattr('application.shared.runtime.port_in_use',lambda host,port:True)
    captured={}
    monkeypatch.setattr(Flask,'run',lambda self,**kwargs:captured.update(kwargs))
    runpy.run_path(str(Path(__file__).resolve().parents[2]/'app.py'),run_name='__main__')
    assert captured['use_reloader'] is True
