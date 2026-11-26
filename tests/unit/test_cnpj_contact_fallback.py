from dataclasses import replace
from unittest.mock import Mock
from domain.gateways.cnpj_gateway import CnpjInfo
from infrastructure.gateways.fallback_cnpj_gateway import FallbackCnpjGateway
from infrastructure.gateways.brasil_api_cnpj_gateway import BrasilApiCnpjGateway


def company(**extra):
    return CnpjInfo(**{
        'cnpj':'35303902000181','razao_social':'Empresa exemplo','nome_fantasia':None,
        'situacao':'ATIVA','ativo':True,'data_abertura':None,'endereco':'Ribeirania',
        'cidade':'Ribeirão Preto','estado':'SP','cep':'14096420','telefone':None,
        'email':None,'atividade_principal':None,**extra})


def gateway(first, second):
    g=FallbackCnpjGateway()
    g._brasil_api=Mock(consultar=Mock(return_value=first))
    g._receitaws=Mock(consultar=Mock(return_value=second))
    return g


def test_validation_keeps_its_original_behavior():
    primary=company()
    g=gateway(primary,company(telefone='1632221234'))
    assert g.consultar(primary.cnpj)==primary
    g._receitaws.consultar.assert_not_called()


def test_autofill_complements_contacts_without_changing_company_details():
    primary=company(ativo=False,situacao='BAIXADA')
    other=company(telefone='1632221234',email='contato@example.com',endereco='Outro endereço',razao_social='Outro nome')
    g=gateway(primary,other)
    result=g.consultar_complementar(primary.cnpj)
    assert result==replace(primary,telefone=other.telefone,email=other.email)
    g._brasil_api.consultar.assert_called_once_with(primary.cnpj)
    g._receitaws.consultar.assert_called_once_with(primary.cnpj)


def test_complete_contacts_need_no_second_request():
    primary=company(telefone='1632221234',email='contato@example.com')
    g=gateway(primary,None)
    assert g.consultar_complementar(primary.cnpj)==primary
    g._receitaws.consultar.assert_not_called()


def test_secondary_failure_keeps_partial_primary_data():
    primary=company()
    assert gateway(primary,None).consultar_complementar(primary.cnpj)==primary


def test_missing_primary_uses_secondary_once():
    secondary=company(telefone='1632221234')
    g=gateway(None,secondary)
    assert g.consultar_complementar(secondary.cnpj)==secondary
    g._receitaws.consultar.assert_called_once()


def test_existing_phone_is_not_overwritten_when_email_missing():
    primary=company(telefone='1632221234')
    result=gateway(primary,company(telefone='16999991234',email='contato@example.com')).consultar_complementar(primary.cnpj)
    assert result.telefone==primary.telefone and result.email=='contato@example.com'


def test_contacts_from_different_cnpj_are_not_merged():
    primary=company()
    assert gateway(primary,company(cnpj='11222333000181',telefone='11999991234')).consultar_complementar(primary.cnpj)==primary


def test_both_sources_without_phone_do_not_invent_one():
    primary=company()
    assert gateway(primary,company()).consultar_complementar(primary.cnpj).telefone is None


def test_brasil_api_uses_second_phone_if_first_empty():
    parser=BrasilApiCnpjGateway()
    for first in (None,'','   '):
        result=parser._parse_response('35303902000181',{'ddd_telefone_1':first,'ddd_telefone_2':'1632221234'})
        assert result.telefone=='1632221234'
