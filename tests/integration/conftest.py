import sys
import pytest
import database


@pytest.fixture
def crm(tmp_path, monkeypatch):
    path = str(tmp_path / 'crm.db')
    monkeypatch.setattr(database, 'DB_PATH', path)
    from app import app
    for name, module in list(sys.modules.items()):
        if name.startswith('infrastructure.repositories.') and hasattr(module, 'DB_PATH'):
            monkeypatch.setattr(module, 'DB_PATH', path)
    database.init_db()
    monkeypatch.setitem(app.config, 'TESTING', True)
    monkeypatch.setitem(app.config, 'SECRET_KEY', 'integration-test-only')
    monkeypatch.setitem(app.config, 'CRM_USERNAME', None)
    monkeypatch.setitem(app.config, 'CRM_PASSWORD', None)
    return app, path


@pytest.fixture
def browser(crm):
    client = crm[0].test_client()
    client.get('/')
    return client


def csrf(client):
    with client.session_transaction() as session:
        return session['csrf_token']
