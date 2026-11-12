import sqlite3
from datetime import date, timedelta
import pytest
import database
from application.prospeccao.update_status import UpdateProspecctionStatusRequest, update_prospecction_status_with_repo
from application.leads.add_contato import AddLeadContatoRequest, add_lead_contato_with_repo
from application.leads.update_status import UpdateLeadStatusRequest, update_lead_status_with_repo
from application.shared.status import STATUS_PROSPECCAO, STATUS_LEADS
from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository
from infrastructure.repositories.sqlite_lead_repository import SqliteLeadRepository
from infrastructure.repositories.sqlite_agendamentos_repository import SqliteAgendamentosRepository
from infrastructure.repositories.sqlite_pedido_repository import SqlitePedidoRepository
from infrastructure.repositories.sqlite_relatorio_repository import SqliteRelatorioRepository
from application.vendas.registrar import pedido_from_form
from werkzeug.datastructures import MultiDict
from .conftest import csrf


def prospect(repo, **extra):
    return repo.add({'nome_loja':'Loja Sintética Informática', 'cnpj':'11222333000181', 'cidade':'Vitória', 'estado':'ES', 'segmento':'Acessórios de informática', **extra})[0]


def test_fresh_database_pages_and_idempotent_initialization(crm, browser):
    database.init_db()
    assert database.get_db_connection().execute('PRAGMA foreign_keys').fetchone()[0] == 1
    for url in ['/', '/leads', '/prospeccao', '/agendamentos', '/vendas', '/prospeccao/importar']:
        assert browser.get(url).status_code == 200, url
    pid=prospect(SqliteProspeccaoRepository())
    lid=SqliteProspeccaoRepository().converter_para_lead(pid)
    assert browser.get(f'/leads/{lid}').status_code == 200
    assert browser.get(f'/vendas/registrar/{lid}').status_code == 200
    assert browser.get('/prospeccao?arquivados=1').status_code == 200


@pytest.mark.parametrize('status', [s for s in STATUS_PROSPECCAO if s != 'Convertido em Lead'])
def test_every_prospect_status(crm, status):
    repo=SqliteProspeccaoRepository();pid=prospect(repo)
    schedule = status == 'Pediu para retornar'
    result=update_prospecction_status_with_repo(UpdateProspecctionStatusRequest(pid,status,'Contato de teste','2027-01-15' if schedule else None,'10:00' if schedule else None),repo)
    assert result.ok
    row=repo.get_by_id(pid)
    assert bool(row['arquivado']) == (status in ['Descartado','Interessado','Em negociação'])
    assert bool(row['convertido_lead_id']) == (status in ['Interessado','Em negociação'])
    assert bool(row['data_retorno']) == schedule
    if row['convertido_lead_id']:
        assert SqliteLeadRepository().get_by_id(row['convertido_lead_id'])[0]['status'] == status


@pytest.mark.parametrize('status', STATUS_LEADS)
def test_every_lead_status(crm, status):
    pr=SqliteProspeccaoRepository();pid=prospect(pr);lid=pr.converter_para_lead(pid)
    lr=SqliteLeadRepository()
    if status == 'Cliente ativo':
        data=MultiDict({'lead_id':str(lid),'data_pedido':'2026-11-12','familias[]':'A','codigos[]':'X','descricoes[]':'Mouse','quantidades[]':'1','precos_unt[]':'1.00'})
        SqlitePedidoRepository().registrar(pedido_from_form(data))
    lr.add_contato(lid,'Ligação','Agendar retorno',None,'2027-01-15','10:00')
    assert update_lead_status_with_repo(UpdateLeadStatusRequest(lid,status),lr).ok
    lead,contacts,_=lr.get_by_id(lid)
    assert lead['status']==status
    if status in ['Sem interesse','Descartado','Já tem consultor atendendo']:
        assert not any(c['data_retorno'] and not c['retorno_encerrado'] for c in contacts)
        assert not SqliteAgendamentosRepository().get_view_data('2027-01-15',True).retornos_leads_hoje


def test_schedule_is_not_interest_and_old_callback_does_not_resurrect(crm):
    repo=SqliteLeadRepository();lid=repo.create({'nome_loja':'Teste','status':'Envio de orçamento'})
    request=AddLeadContatoRequest(lid,'Ligação','Agendar retorno','Retornar','2027-01-15','10:00')
    assert add_lead_contato_with_repo(request,repo).ok
    assert repo.get_by_id(lid)[0]['status']=='Envio de orçamento'
    assert add_lead_contato_with_repo(AddLeadContatoRequest(lid,'Ligação','Apresentação feita','Concluído',None,None),repo).ok
    assert not SqliteAgendamentosRepository().get_view_data('2027-01-15',True).retornos_leads_hoje


def test_requalification_reuses_original_lead(crm):
    pr=SqliteProspeccaoRepository();pid=prospect(pr);lid=pr.converter_para_lead(pid)
    lr=SqliteLeadRepository()
    update_lead_status_with_repo(UpdateLeadStatusRequest(lid,'Sem interesse'),lr)
    assert pr.get_by_id(pid)['convertido_lead_id']==lid
    assert not pr.get_by_id(pid)['arquivado']
    result=update_prospecction_status_with_repo(UpdateProspecctionStatusRequest(pid,'Em negociação','Retomou',None,None),pr)
    assert result.ok
    assert pr.converter_para_lead(pid)==lid
    assert lr.get_by_id(lid)[0]['status']=='Em negociação'
    with database.get_db_connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]==1


def test_conversion_rolls_back_all_changes_on_history_failure(crm):
    pr=SqliteProspeccaoRepository();pid=prospect(pr)
    pr.update_status(pid,'Em negociação')
    with database.get_db_connection() as conn:
        conn.execute("CREATE TRIGGER fail_history BEFORE INSERT ON contatos BEGIN SELECT RAISE(ABORT, 'test failure'); END")
    with pytest.raises(sqlite3.IntegrityError):pr.converter_para_lead(pid)
    assert not pr.get_by_id(pid)['convertido_lead_id']
    with database.get_db_connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]==0
        assert conn.execute('SELECT COUNT(*) FROM segmentos_loja').fetchone()[0]==0


def test_full_cycle_negotiation_sale_post_sale_and_reports(crm, browser):
    pr=SqliteProspeccaoRepository();pid=prospect(pr)
    pr.agendar_retorno(pid,'2027-01-15','10:00')
    result=update_prospecction_status_with_repo(UpdateProspecctionStatusRequest(pid,'Em negociação','Proposta','2027-01-15','10:00'),pr)
    assert result.ok
    lid=pr.get_by_id(pid)['convertido_lead_id']
    agenda=SqliteAgendamentosRepository().get_view_data('2027-01-15',True)
    assert not agenda.retornos_hoje
    assert [r['id'] for r in agenda.retornos_leads_hoje]==[lid]
    assert SqliteRelatorioRepository().get_relatorio_completo()['convertidos']==1
    form=MultiDict({'lead_id':str(lid),'data_pedido':'2026-11-12','data_proximo_contato':'2027-02-01','familias[]':'Acessórios','codigos[]':'EXEMPLO','descricoes[]':'Mouse sintético','quantidades[]':'3','precos_unt[]':'0.10'})
    response=browser.post('/vendas/registrar',data=form,headers={'X-CSRF-Token':csrf(browser)})
    assert response.status_code==302
    assert SqlitePedidoRepository().get_faturamento_total(lid)==0.30
    assert SqliteLeadRepository().get_by_id(lid)[0]['status']=='Cliente ativo'
    assert SqliteAgendamentosRepository().get_view_data('2027-02-01',True).retornos_leads_hoje
    assert browser.get('/vendas').status_code==200
    assert browser.get(f'/leads/{lid}').status_code==200


def test_preserve_old_callback_as_overdue(crm):
    pr=SqliteProspeccaoRepository();pid=prospect(pr)
    yesterday=(date.today()-timedelta(days=1)).isoformat()
    pr.agendar_retorno(pid,yesterday,'09:00')
    view=SqliteAgendamentosRepository().get_view_data(date.today().isoformat(),True)
    assert [r['id'] for r in view.retornos_atrasados]==[pid]
    assert pr.get_by_id(pid)['data_retorno']==yesterday


@pytest.mark.parametrize('quantity,price',[('0','1'),('-1','1'),('1','-1'),('1','nan'),('1','inf'),('abc','1')])
def test_sales_reject_invalid_numbers(quantity,price):
    data=MultiDict({'lead_id':'1','data_pedido':'2026-11-12','familias[]':'A','codigos[]':'X','descricoes[]':'Mouse','quantidades[]':quantity,'precos_unt[]':price})
    with pytest.raises(ValueError):pedido_from_form(data)


def test_active_client_requires_a_recorded_sale(crm):
    lr=SqliteLeadRepository();lid=lr.create({'nome_loja':'Sem venda'})
    with pytest.raises(ValueError,match='Registre uma venda'):
        update_lead_status_with_repo(UpdateLeadStatusRequest(lid,'Cliente ativo'),lr)
    assert lr.get_by_id(lid)[0]['status']=='Novo Lead'


@pytest.mark.parametrize('outcome',['Não atendeu','Caixa postal','Sem contato'])
def test_failed_lead_attempt_retains_callback_and_history(crm,outcome):
    repo=SqliteLeadRepository();lid=repo.create({'nome_loja':'Teste'})
    repo.add_contato(lid,'Ligação','Agendar retorno',None,'2027-01-15','10:00')
    result=add_lead_contato_with_repo(AddLeadContatoRequest(lid,'Ligação',outcome,None,None,None),repo)
    assert result.ok
    assert SqliteAgendamentosRepository().get_view_data('2027-01-15',True).retornos_leads_hoje
    rows=repo.get_by_id(lid)[1]
    assert len(rows)==2 and all(row['data_retorno']=='2027-01-15' for row in rows)


def test_conversion_events_are_not_counted_as_successful_phone_contacts(crm):
    pr=SqliteProspeccaoRepository();pid=prospect(pr)
    pr.update_status(pid,'Em negociação')
    pr.converter_para_lead(pid)
    assert SqliteRelatorioRepository().get_resumo_hoje()['efetivos']==0


def test_report_pdf_compatibility_adapters(crm):
    from services.relatorio_pdf_service import build_relatorio_pdf_bytes, build_relatorio_prospeccao_pdf_bytes
    repo=SqliteRelatorioRepository()
    prospect(SqliteProspeccaoRepository())
    today=date.today().isoformat()
    assert build_relatorio_pdf_bytes(repo.get_relatorio_completo(today,today),today,today).startswith(b'%PDF')
    assert build_relatorio_prospeccao_pdf_bytes(repo.get_relatorio_prospeccao(today,today),today,today).startswith(b'%PDF')
