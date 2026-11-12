"""Adapter for Maps selections; shares duplicate protection with manual entry."""
from database import DB_PATH
from domain.repositories.prospeccao_temp_repository import AddProspecctionTempResult, ProspecctionTempRepository
from infrastructure.repositories.prospeccao_creation import add_prospect


class SqliteProspecctionTempRepository(ProspecctionTempRepository):
    def add_from_maps_data(self, dados: dict) -> AddProspecctionTempResult:
        pid, created = add_prospect(dados, DB_PATH)
        return AddProspecctionTempResult(pid, created)
