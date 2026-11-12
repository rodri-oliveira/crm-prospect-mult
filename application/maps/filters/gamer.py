from __future__ import annotations
from application.maps.profiles import _GAMER_NOISE_NAMES

from application.maps.text import _norm_key


def _filter_noise_gamer(results: list[dict]) -> list[dict]:
    """Filtro para segmento Gamer B2B.
    Descarta negócios voltados para consumo final (lan houses, cyber cafés, arenas de e-sports, fliperamas, etc.).
    """
    filtered = []
    for item in results:
        nome = _norm_key(item.get("nome") or "")
        raw_text = _norm_key(item.get("__raw_text") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])

        texto_para_busca = f"{nome} {raw_text} {categorias_str}"

        # Se contiver qualquer termo de ruído gamer, descarta
        if any(t in texto_para_busca for t in _GAMER_NOISE_NAMES):
            continue

        filtered.append(item)

    return filtered
