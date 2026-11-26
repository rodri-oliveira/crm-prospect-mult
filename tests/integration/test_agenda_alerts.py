from datetime import datetime, timezone
import re
import pytest
import database
import application.agendamentos.alerts as alerts
from application.agendamentos.alerts import get_return_alerts, BUSINESS_TZ
from infrastructure.repositories.sqlite_agendamentos_repository import SqliteAgendamentosRepository

NOW = datetime(2026, 11, 26, 16, 14, tzinfo=BUSINESS_TZ)


@pytest.fixture
def clock(crm, monkeypatch):
    monkeypatch.setattr(alerts, 'business_now', lambda: NOW)


def prospect(day, hour=None, archived=0, status='Enviado Portfólio Whats'):
    with database.get_db_connection() as conn:
        return conn.execute('''INSERT INTO prospeccao_temp
            (nome_loja,cidade,estado,status_prospeccao,data_retorno,hora_retorno,arquivado)
            VALUES ('Empresa sintética','Vitória','ES',?,?,?,?)''', (status,day,hour,archived)).lastrowid


def lead(day, hour=None, status='Enviado Portfólio Whats', closed=0):
    with database.get_db_connection() as conn:
        lid=conn.execute("INSERT INTO leads (nome_loja,status) VALUES ('Lead sintético',?)",(status,)).lastrowid
        conn.execute('''INSERT INTO contatos (lead_id,tipo_contato,resultado,data_retorno,hora_retorno,retorno_encerrado)
            VALUES (?,'Ligação','Agendar retorno',?,?,?)''',(lid,day,hour,closed))
        return lid


def stats(now=NOW):
    return get_return_alerts(SqliteAgendamentosRepository(), now=now)


def test_screenshot_case_is_visible_in_api_and_navigation(clock, browser):
    prospect('2026-11-19','10:00')
    prospect('2026-11-26','16:30')  # 16 minutes from now, still in portfolio status.
    response=browser.get('/api/retornos/stats')
    data=response.get_json()
    assert response.headers['Cache-Control']=='no-store'
    assert {k:data[k] for k in ['total','hoje','atrasados','urgentes']}==dict(total=2,hoje=1,atrasados=1,urgentes=1)
    assert data['nivel']=='atrasado'
    for url in ['/prospeccao','/agendamentos','/leads']:
        text=browser.get(url).get_data(as_text=True)
        assert re.search(r'id="badge-agendamentos"[^>]*>2</span>',text)
        assert 'Atrasados: 1 · Em até 1h: 1' in text
        assert 'id="nav-agendamentos"' in text
        assert 'agenda-badge-red animate-pulse-red' in text


def test_empty_page_always_renders_badges_for_future_updates(clock,browser):
    text=browser.get('/agendamentos').get_data(as_text=True)
    assert re.search(r'id="badge-agendamentos"\s+hidden',text)
    assert re.search(r'id="badge-agendamentos-mobile"\s+hidden',text)


def test_all_pending_sources_are_counted_once_and_closed_records_ignored(clock):
    prospect('2026-11-19','10:00')
    for hour in ['16:30','16:00','20:00',None]:prospect('2026-11-26',hour)
    prospect('2026-11-27','10:00')
    prospect('2026-11-19','10:00',archived=1)
    lead('2026-11-26','16:45')
    lead('2026-11-26')
    lead('2026-11-26','16:20',closed=1)
    lead('2026-11-26','16:20',status='Descartado')
    lid=lead('2026-11-26','16:20')
    # Only the latest still-pending callback per lead belongs in the agenda.
    with database.get_db_connection() as conn:
        conn.execute("INSERT INTO contatos (lead_id,tipo_contato,resultado,data_retorno,hora_retorno) VALUES (?,'Ligação','Agendar retorno','2026-12-01','10:00')",(lid,))
    result=stats()
    assert {k:result[k] for k in ['total','hoje','atrasados','urgentes','sem_horario']}==dict(total=7,hoje=6,atrasados=2,urgentes=2,sem_horario=2)


def test_lead_alone_can_trigger_urgent_alert(clock):
    lead('2026-11-26','16:30')
    result=stats()
    assert result['total']==1 and result['urgentes']==1 and result['nivel']=='urgente'


def test_today_becomes_overdue_at_its_time_without_double_counting(clock):
    prospect('2026-11-26','16:30')
    assert stats()['urgentes']==1
    result=stats(NOW.replace(hour=16,minute=30))
    assert result['total']==1 and result['hoje']==1 and result['atrasados']==1
    assert result['urgentes']==0


def test_one_hour_boundary_and_timezone_conversion(clock):
    prospect('2026-11-26','17:14')
    prospect('2026-11-26','17:15')
    assert stats()['urgentes']==1
    assert stats(NOW.astimezone(timezone.utc))==stats()


def test_window_crossing_midnight_includes_upcoming_next_day(clock):
    prospect('2026-11-26','23:00')
    prospect('2026-11-27','00:10')
    prospect('2026-11-27','02:00')
    result=stats(NOW.replace(hour=23,minute=30))
    assert {k:result[k] for k in ['total','hoje','atrasados','urgentes']}==dict(total=2,hoje=1,atrasados=1,urgentes=1)
    assert result['mostrar_futuros'] is True


def test_no_hour_is_pending_today_without_false_overdue(clock):
    prospect('2026-11-26')
    result=stats()
    assert result['total']==1 and result['sem_horario']==1 and result['nivel']=='hoje'
    assert result['atrasados']==0 and result['urgentes']==0


@pytest.mark.parametrize('url',['/','/prospeccao','/leads','/vendas','/relatorio'])
def test_prominent_alert_is_inside_sidebar_outside_agenda(clock,browser,url):
    prospect('2026-11-19','10:00')
    prospect('2026-11-26','16:30')
    response=browser.get(url)
    assert response.status_code==200
    aside=re.search(r'<aside\b[^>]*>([\s\S]*?)</aside>',response.get_data(as_text=True)).group(1)
    assert 'id="sidebar-agenda-callout"' in aside
    assert '⚠ RETORNOS ATRASADOS' in aside
    assert 'Atrasados: 1 · Em até 1h: 1' in aside
    assert not re.search(r'id="sidebar-agenda-callout"\s+hidden',aside)
    assert aside.index('CRM') < aside.index('sidebar-agenda-callout') < aside.index('<nav')


def test_monitoring_error_is_visible_in_sidebar_instead_of_silent_zero(clock,browser,monkeypatch):
    class Unavailable:
        def get_retornos_stats(self):raise RuntimeError('synthetic monitoring failure')
    monkeypatch.setattr('app.prospeccao_repository',lambda:Unavailable())
    text=browser.get('/prospeccao').get_data(as_text=True)
    aside=re.search(r'<aside\b[^>]*>([\s\S]*?)</aside>',text).group(1)
    assert '⚠ VERIFIQUE A AGENDA' in aside
    assert not re.search(r'id="sidebar-agenda-callout"\s+hidden',aside)
    assert 'Não foi possível atualizar os avisos.' in aside
