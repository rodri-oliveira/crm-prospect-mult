"""Compatibility adapter; all reporting SQL lives in the repository."""
from datetime import date
from infrastructure.repositories.sqlite_relatorio_repository import SqliteRelatorioRepository


def get_resumo_hoje():
    return SqliteRelatorioRepository().get_resumo_hoje()


def get_relatorio_completo(data_inicio=None, data_fim=None):
    return SqliteRelatorioRepository().get_relatorio_completo(data_inicio, data_fim)


def get_detalhes_relatorio_hoje():
    today = date.today().isoformat()
    return get_relatorio_completo(today, today)['detalhes_leads']
