from __future__ import annotations
from application.maps.profiles import _BRINQUEDOS_NOISE_NAMES, _BRINQUEDOS_POSITIVE_TERMS

from application.maps.text import _norm_key


def _filter_noise_brinquedos(results: list[dict]) -> list[dict]:
    """Filtro para Brinquedos B2B/revenda.

    Mantem lojas, distribuidores e varejos correlatos com sinal claro de
    brinquedos; remove servicos infantis como buffet, locacao e escolas.
    """
    filtered = []
    for item in results:
        nome = _norm_key(item.get("nome") or "")
        raw_text = _norm_key(item.get("__raw_text") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])

        texto_para_busca = f"{nome} {raw_text} {categorias_str}"

        if any(t in texto_para_busca for t in _BRINQUEDOS_NOISE_NAMES):
            continue

        if any(t in texto_para_busca for t in _BRINQUEDOS_POSITIVE_TERMS):
            filtered.append(item)

    return filtered
