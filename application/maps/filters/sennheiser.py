from __future__ import annotations
from application.maps.profiles import _SENNHEISER_BUYER_PROFILE_TERMS, _SENNHEISER_HIGH_INTENT_TERMS, _SENNHEISER_LOW_CONFIDENCE_TERMS, _SENNHEISER_MEDIUM_INTENT_TERMS, _SENNHEISER_NOISE_NAMES, _SENNHEISER_STRONG_QUERY_TERMS

from application.maps.filters.varejo import _looks_like_person_name
from application.maps.text import _norm_key


def _filter_noise_sennheiser(results: list[dict]) -> list[dict]:
    """Filtro para Sennheiser (Pro Audio).
    Lógica:
      - Remove som automotivo (maior poluição)
      - Remove home theater e eletrônicas de conserto
      - Foca em Pro Audio, Broadcast e Rental
    """
    filtered = []
    for item in results:
        nome = _norm_key(item.get("nome") or "")
        raw_text = _norm_key(item.get("__raw_text") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])
        query_sources = item.get("query_sources") or []
        query_sources_str = " ".join([_norm_key(str(q)) for q in query_sources])

        texto_para_bloqueio = f"{nome} {raw_text} {categorias_str}"
        texto_para_score = f"{texto_para_bloqueio} {query_sources_str}"

        is_noise = any(t in texto_para_bloqueio for t in _SENNHEISER_NOISE_NAMES)

        if is_noise:
            continue

        item["sennheiser_fit_score"] = _score_sennheiser_fit(texto_para_score, nome)
        filtered.append(item)

    return sorted(filtered, key=lambda it: int(it.get("sennheiser_fit_score") or 0), reverse=True)

def _score_sennheiser_fit(texto: str, nome: str = "") -> int:
    texto_norm = _norm_key(texto or "")
    nome_norm = _norm_key(nome or "")
    profile_score = sum(1 for term in _SENNHEISER_BUYER_PROFILE_TERMS if term in texto_norm)
    source_score = sum(2 for term in _SENNHEISER_STRONG_QUERY_TERMS if term in texto_norm)
    high_score = sum(5 for term in _SENNHEISER_HIGH_INTENT_TERMS if term in texto_norm)
    medium_score = sum(2 for term in _SENNHEISER_MEDIUM_INTENT_TERMS if term in texto_norm)
    low_penalty = sum(3 for term in _SENNHEISER_LOW_CONFIDENCE_TERMS if term in texto_norm)
    person_penalty = 5 if _looks_like_person_name(nome_norm) else 0
    return profile_score + source_score + high_score + medium_score - low_penalty - person_penalty
