import pytest
from application.agendamentos.registrar_tentativa import RegistrarTentativaRequest, registrar_tentativa_with_repo
from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository
from infrastructure.repositories.sqlite_agendamentos_repository import SqliteAgendamentosRepository

OUTCOMES=['Não atendeu','Caixa postal','Enviado Portfólio Whats','Enviado Portfólio por E-mail',
          'Não analisou ainda o material','Aguardando dados para cadastro','Agendar retorno',
          'Solicitou portfólio','Em negociação','Interessado','Aguard. Lista Prod.',
          'Já tem consultor atendendo','Sem interesse','Descartado','Pediu preço']


@pytest.mark.parametrize('outcome',OUTCOMES)
def test_each_callback_outcome(crm,outcome):
    pr=SqliteProspeccaoRepository();ar=SqliteAgendamentosRepository()
    pid,_=pr.add({'nome_loja':'Loja de Informática','cidade':'Rio de Janeiro','estado':'RJ','cnpj':'11222333000181','segmento':'Acessórios de informática'})
    pr.agendar_retorno(pid,'2027-01-15','10:00')
    new_date='2027-02-01' if outcome in ('Agendar retorno','Não analisou ainda o material') else None
    request=RegistrarTentativaRequest(pid,outcome,'Observação do teste',new_date,'11:00' if new_date else None,None,None)
    result=registrar_tentativa_with_repo(request,ar,pr)
    assert result.ok, result
    row=pr.get_by_id(pid)
    if outcome in ('Não atendeu','Caixa postal'):
        assert row['data_retorno']=='2027-01-15'
    elif new_date:
        assert row['data_retorno']==new_date
    else:
        assert not row['data_retorno']
    assert bool(row['convertido_lead_id']) == (outcome in ('Interessado','Em negociação'))
    assert bool(row['arquivado']) == (outcome in ('Interessado','Em negociação','Descartado'))


def test_invalid_callback_does_not_mutate_status(crm):
    pr=SqliteProspeccaoRepository();ar=SqliteAgendamentosRepository()
    pid,_=pr.add({'nome_loja':'Teste'})
    pr.agendar_retorno(pid,'2027-01-15','10:00')
    result=registrar_tentativa_with_repo(RegistrarTentativaRequest(pid,'Agendar retorno',None,'bad','10:00',None,None),ar,pr)
    assert not result.ok
    assert pr.get_by_id(pid)['data_retorno']=='2027-01-15'
