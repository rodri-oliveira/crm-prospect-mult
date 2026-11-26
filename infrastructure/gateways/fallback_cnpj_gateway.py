from __future__ import annotations

from collections import OrderedDict
from dataclasses import replace
from threading import Lock
from time import monotonic

from application.shared.cnpj_utils import normalize_cnpj, is_valid_cnpj
from domain.gateways.cnpj_gateway import CnpjGateway, CnpjInfo
from infrastructure.gateways.brasil_api_cnpj_gateway import BrasilApiCnpjGateway
from infrastructure.gateways.receitaws_cnpj_gateway import ReceitaWsCnpjGateway


def present(value):
    return bool(str(value or '').strip())


class FallbackCnpjGateway(CnpjGateway):
    """Complete missing contacts, even when the first registry lookup succeeds."""

    def __init__(self, timeout_seconds: int = 8):
        self._brasil_api = BrasilApiCnpjGateway(timeout_seconds=timeout_seconds)
        self._receitaws = ReceitaWsCnpjGateway(timeout_seconds=timeout_seconds + 2)
        self._cache = OrderedDict()
        self._lock = Lock()

    def consultar(self, cnpj: str) -> CnpjInfo | None:
        key = normalize_cnpj(cnpj)
        if not is_valid_cnpj(key):
            return None
        with self._lock:
            cached = self._cache.get(key)
            if cached and monotonic() - cached[0] < 300:
                self._cache.move_to_end(key)
                return cached[1]
            self._cache.pop(key, None)

        primary = self._brasil_api.consultar(key)
        if primary and normalize_cnpj(primary.cnpj) != key:
            primary = None
        info = replace(primary, fonte_telefone='BrasilAPI' if present(primary.telefone) else None) if primary else None
        if not info or not present(info.telefone) or not present(info.email):
            secondary = self._receitaws.consultar(key)
            if secondary and normalize_cnpj(secondary.cnpj) != key:
                secondary = None
            if not info:
                info = replace(secondary, fonte_telefone='ReceitaWS' if present(secondary.telefone) else None) if secondary else None
            elif secondary:
                info = replace(info,
                    telefone=info.telefone if present(info.telefone) else secondary.telefone,
                    email=info.email if present(info.email) else secondary.email,
                    fonte_telefone=info.fonte_telefone if present(info.telefone) else ('ReceitaWS' if present(secondary.telefone) else None))
            else:
                info = replace(info, avisos=('Segunda fonte temporariamente indisponível; consulta de contatos incompleta.',))
        # Cache only a successful contact lookup. Missing contacts can be retried.
        if info and present(info.telefone):
            with self._lock:
                self._cache[key] = (monotonic(), info)
                self._cache.move_to_end(key)
                while len(self._cache) > 128:
                    self._cache.popitem(last=False)
        return info

    def is_ativo(self, cnpj: str) -> bool:
        info = self.consultar(cnpj)
        return info.ativo if info else False
