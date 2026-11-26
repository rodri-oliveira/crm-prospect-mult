from unittest.mock import Mock
import interfaces.web.cnpj_routes as routes
from tests.unit.test_cnpj_contact_fallback import company, gateway


def test_enrichment_is_opt_in_and_existing_validation_remains_unchanged(browser,monkeypatch):
    g=gateway(company(),company(telefone='1632221234',email='contato@example.com'))
    monkeypatch.setattr(routes,'cnpj_gateway',lambda:g)
    original=browser.get('/api/cnpj/consultar?cnpj=35303902000181').get_json()
    assert original['ok'] and original['data']['telefone'] is None
    g._receitaws.consultar.assert_not_called()
    enriched=browser.get('/api/cnpj/consultar?cnpj=35303902000181&complementar=1').get_json()
    assert enriched['data']['telefone']=='1632221234'
    assert enriched['data']['email']=='contato@example.com'
    assert enriched['data']['endereco']=='Ribeirania'


def test_invalid_cnpj_never_calls_provider(browser,monkeypatch):
    factory=Mock()
    monkeypatch.setattr(routes,'cnpj_gateway',factory)
    assert browser.get('/api/cnpj/consultar?cnpj=123&complementar=1').status_code==400
    factory.assert_not_called()


def test_no_contact_from_either_source_is_explicit_null(browser,monkeypatch):
    monkeypatch.setattr(routes,'cnpj_gateway',lambda:gateway(company(),company()))
    result=browser.get('/api/cnpj/consultar?cnpj=35303902000181&complementar=1').get_json()
    assert result['ok'] and result['data']['telefone'] is None and result['data']['email'] is None
