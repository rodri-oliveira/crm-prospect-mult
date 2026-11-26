from dataclasses import replace
from unittest.mock import Mock
import pytest
import interfaces.web.cnpj_routes as routes
from domain.gateways.cnpj_gateway import CnpjInfo
from infrastructure.gateways.fallback_cnpj_gateway import FallbackCnpjGateway
from infrastructure.gateways.brasil_api_cnpj_gateway import BrasilApiCnpjGateway
from application.shared.cnpj_contacts import contact_values


def info(**extra):
    return CnpjInfo(**{
        'cnpj':'35303902000181','razao_social':'Empresa de teste',
        'nome_fantasia':'','situacao':'ATIVA','ativo':True,'data_abertura':'2019-10-24',
        'endereco':'RIBEIRANIA','cidade':'RIBEIRAO PRETO','estado':'SP','cep':'14096420',
        'telefone':'','email':None,'atividade_principal':None,**extra})


def providers(first=None,second=None):
    gateway=FallbackCnpjGateway()
    gateway._brasil_api=Mock(consultar=Mock(return_value=first))
    gateway._receitaws=Mock(consultar=Mock(return_value=second))
    return gateway


def test_default_endpoint_recovers_contact_from_second_source(browser,monkeypatch):
    gateway=providers(info(),info(telefone='(16) 8139-9874',email='contato@example.com',endereco='Other address'))
    monkeypatch.setattr(routes,'cnpj_gateway',lambda:gateway)
    response=browser.get('/api/cnpj/consultar?cnpj=35303902000181')
    assert response.status_code==200
    result=response.get_json()
    assert result['consulta_versao']=='20261126-contatos-1'
    assert result['data']['telefone']=='(16) 98139-9874'
    assert result['data']['whatsapp']=='(16) 98139-9874'
    assert result['data']['whatsapp_confirmado'] is False
    assert result['data']['email']=='contato@example.com'
    assert result['data']['fonte_telefone']=='ReceitaWS'
    assert result['data']['telefone_original']=='(16) 8139-9874'
    assert result['data']['endereco']=='RIBEIRANIA'
    # Repeating the normal request uses the successful short-lived cache.
    assert browser.get('/api/cnpj/consultar?cnpj=35.303.902/0001-81').get_json()==result
    gateway._brasil_api.consultar.assert_called_once()
    gateway._receitaws.consultar.assert_called_once()


def test_complete_primary_contacts_do_not_trigger_second_request():
    primary=info(telefone='16999991234',email='test@example.com')
    gateway=providers(primary,None)
    assert gateway.consultar(primary.cnpj).telefone==primary.telefone
    gateway._receitaws.consultar.assert_not_called()


def test_secondary_does_not_override_existing_phone_or_company_status():
    primary=info(telefone='1632221234',ativo=False,situacao='BAIXADA')
    gateway=providers(primary,info(telefone='16999991234',email='test@example.com'))
    result=gateway.consultar(primary.cnpj)
    assert result.telefone=='1632221234' and result.email=='test@example.com'
    assert result.ativo is False and result.situacao=='BAIXADA'
    assert result.fonte_telefone=='BrasilAPI'


def test_unavailable_contact_is_not_cached_and_can_recover():
    gateway=providers(info(),None)
    partial=gateway.consultar('35303902000181')
    assert not partial.telefone and partial.avisos
    gateway._receitaws.consultar.return_value=info(telefone='16999991234')
    assert gateway.consultar('35303902000181').telefone=='16999991234'
    assert gateway._receitaws.consultar.call_count==2


def test_wrong_company_is_rejected_and_no_phone_is_invented(browser,monkeypatch):
    gateway=providers(info(),info(cnpj='11222333000181',telefone='11999991234'))
    monkeypatch.setattr(routes,'cnpj_gateway',lambda:gateway)
    result=browser.get('/api/cnpj/consultar?cnpj=35303902000181').get_json()
    assert not result['data']['telefone'] and result['data']['whatsapp'] is None
    assert result['avisos']


def test_only_secondary_available():
    gateway=providers(None,info(telefone='1632221234'))
    assert gateway.consultar('35303902000181').fonte_telefone=='ReceitaWS'


def test_brasilapi_second_phone_is_used():
    result=BrasilApiCnpjGateway()._parse_response('35303902000181',{
        'ddd_telefone_1':'  ','ddd_telefone_2':'1632221234'})
    assert result.telefone=='1632221234'


@pytest.mark.parametrize('raw,phone,whatsapp',[
    ('(16) 8139-9874','(16) 98139-9874','(16) 98139-9874'),
    ('+55 16 98139-9874','(16) 98139-9874','(16) 98139-9874'),
    ('1632221234','(16) 3222-1234',None),
    ('1632221234 / 16981399874','(16) 3222-1234','(16) 98139-9874'),
    ('1671234567','(16) 7123-4567',None),
    ('08001234567','08001234567',None),
    ('81399874','81399874',None),
    ('',None,None),
])
def test_phone_and_whatsapp_preparation(raw,phone,whatsapp):
    values=contact_values(raw)
    assert values['telefone']==phone and values['whatsapp']==whatsapp
    assert values['whatsapp_confirmado'] is False


def test_invalid_cnpj_does_not_contact_providers(browser,monkeypatch):
    gateway=providers(info(),info())
    monkeypatch.setattr(routes,'cnpj_gateway',lambda:gateway)
    assert browser.get('/api/cnpj/consultar?cnpj=123').status_code==400
    gateway._brasil_api.consultar.assert_not_called()
