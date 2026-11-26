"""Exercise real SQLite predicates, rendered controls and navigation together."""
from datetime import date, timedelta
from html import unescape
from urllib.parse import urlparse, parse_qs
import re
import pytest
import database
from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository
from werkzeug.datastructures import MultiDict
from .conftest import csrf


@pytest.fixture
def prospects(crm):
    today = date.today().isoformat()
    old = (date.today() - timedelta(days=40)).isoformat()
    rows = [
        ('Vitória Automóveis', 'João Silva', 'Vitória', 'ES', 'Lojas de carros', '+55 (27) 3222-1234', None, 'Não contatado', today, 0, None),
        ('São José Informática', 'Maria', 'São Paulo', 'SP', 'Acessórios de informática', None, '+55 (11) 99999-4321', 'Enviado Portfólio Whats', today, 0, None),
        ('Histórico Veículos', 'Ana', 'Vitória', 'ES', 'Lojas de carros', '2732221234', None, 'Não contatado', old, 0, None),
        ('Arquivo Veículos', None, 'Vitória', 'ES', 'Lojas de carros', '2732221234', None, 'Não contatado', today, 1, None),
        ('Retorno Veículos', None, 'Vitória', 'ES', 'Lojas de carros', '27912345678', None, 'Pediu para retornar', today, 0, today),
        ('Sem Contato Veículos', None, 'Belo Horizonte', 'MG', 'Lojas de carros', '   ', None, 'Caixa postal', today, 0, None),
    ]
    with database.get_db_connection() as conn:
        conn.executemany('''INSERT INTO prospeccao_temp
        (nome_loja, responsavel, cidade, estado, segmento, telefone, whatsapp, status_prospeccao, data_prospeccao, arquivado, data_retorno)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', rows)
    return today, old


def ids(**filters):
    return {row['nome_loja'] for row in SqliteProspeccaoRepository().list_by_filters(**filters)}


@pytest.mark.parametrize('filters,expected', [
    ({'nome':'automoveis vitoria'}, {'Vitória Automóveis'}),
    ({'nome':'JOAO SILVA'}, {'Vitória Automóveis'}),
    ({'cidade':'sao paulo'}, {'São José Informática'}),
    ({'estado':'mg'}, {'Sem Contato Veículos'}),
    ({'telefone':'+55 (11) 99999-4321'}, {'São José Informática'}),
    ({'telefone':'abc'}, set()),
    ({'nome':'%'}, set()),
    ({'tipo_telefone':'Celular'}, {'São José Informática'}),
    ({'tipo_telefone':'Sem telefone'}, {'Sem Contato Veículos'}),
    ({'status':'Pediu para retornar,Não contatado'}, {'Retorno Veículos','Vitória Automóveis','Histórico Veículos'}),
])
def test_search_normalization_and_multiple_statuses(prospects, filters, expected):
    assert ids(**filters) == expected


@pytest.mark.parametrize('filters', [
    {}, {'status':'Pediu para retornar,Não contatado'}, {'telefone':'32221234'},
    {'mostrar_arquivados':True}, {'tipo_telefone':'Celular'},
    {'cidade':'vitoria','segmento':'carros','estado':'ES'},
])
def test_counters_match_list_for_every_scope(prospects, filters):
    repo=SqliteProspeccaoRepository()
    rows=repo.list_by_filters(**filters)
    summary=repo.get_summary(None,None,**filters)
    assert summary.total == len(rows) == sum(summary.por_status.values())
    assert set(summary.cidades) == {r['cidade'] for r in rows}


def test_phone_respects_explicit_date_and_archive_filters(prospects):
    today, old=prospects
    assert ids(telefone='2732221234',data_inicio=today,data_fim=today)=={'Vitória Automóveis'}
    assert ids(telefone='2732221234',data_inicio=today,data_fim=today,mostrar_arquivados=True)=={'Vitória Automóveis','Arquivo Veículos'}
    assert ids(telefone='2732221234',data_fim=old)=={'Histórico Veículos'}


def test_default_period_visible_and_clear_means_all_history(prospects,browser):
    today,_=prospects
    text=browser.get('/prospeccao').get_data(as_text=True)
    assert f'name="data_inicio" value="{today}"' in text
    assert f'name="data_fim" value="{today}"' in text
    assert 'Histórico Veículos</h4>' not in text
    text=browser.get('/prospeccao?periodo=todos').get_data(as_text=True)
    assert 'Histórico Veículos</h4>' in text and 'Todo o histórico' in text


def test_shortcuts_keep_filters_and_multi_statuses(prospects,browser):
    query=MultiDict([('status','Não contatado'),('status','Enviado Portfólio Whats'),
                     ('segmento','Lojas de carros'),('estado','ES'),('cidade','Vitória'),
                     ('telefone','32221234'),('tipo_telefone','Fixo'),('arquivados','1'),('periodo','todos')])
    text=browser.get('/prospeccao',query_string=query).get_data(as_text=True)
    # The quick status/city/period links retain scope. Removal chips and the
    # archive toggle deliberately change their respective fields.
    text=text.split('aria-label="Filtros aplicados"')[0]
    links=[unescape(href) for href in re.findall(r'href="([^"]+)"',text)]
    queries=[parse_qs(urlparse(link).query) for link in links if link.startswith('/prospeccao?')]
    for field,expected in [('segmento','Lojas de carros'),('estado','ES'),('telefone','32221234'),('tipo_telefone','Fixo'),('arquivados','1')]:
        assert all(q.get(field)==[expected] for q in queries if 'cidade' in q and (field != 'arquivados' or q.get('arquivados')))
    preset=next(q for q in queries if 'data_inicio' in q)
    assert preset['status']==['Não contatado','Enviado Portfólio Whats']
    assert text.count('class="status-checkbox') >= 17
    assert 'value="Não contatado"\n' in text


def test_action_redirect_keeps_phone_type_and_all_selected_statuses(prospects,browser):
    with database.get_db_connection() as conn:
        pid=conn.execute("SELECT id FROM prospeccao_temp WHERE nome_loja='Vitória Automóveis'").fetchone()[0]
    text=browser.get('/prospeccao?periodo=todos&telefone=32221234&tipo_telefone=Fixo').get_data(as_text=True)
    assert 'name="filtro_telefone" value="32221234"' in text
    assert 'name="filtro_tipo_telefone" value="Fixo"' in text
    result=browser.post(f'/prospeccao/rascunho/{pid}/status',data={
        'csrf_token':csrf(browser),'status':'Não atendeu',
        'filtro_status':'Não contatado,Não atendeu', 'filtro_telefone':'32221234',
        'filtro_tipo_telefone':'Fixo','filtro_estado':'ES','filtro_segmento':'Lojas de carros',
    })
    q=parse_qs(urlparse(result.location).query)
    assert q['telefone']==['32221234'] and q['tipo_telefone']==['Fixo']
    follow=browser.get(result.location).get_data(as_text=True)
    assert re.search(r'value="Não contatado"\s+class="status-checkbox[^>]+checked',follow)
    assert re.search(r'value="Não atendeu"\s+class="status-checkbox[^>]+checked',follow)
    assert 'Vitória Automóveis</h4>' in follow


@pytest.mark.parametrize('query',['data_inicio=2026-99-01','data_inicio=2026-12-10&data_fim=2026-01-01'])
def test_invalid_dates_are_rejected(browser,query):
    assert browser.get('/prospeccao?'+query).status_code==400
