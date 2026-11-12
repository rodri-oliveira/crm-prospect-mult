from __future__ import annotations
from application.maps.profiles import _MOBILIDADE_B2B_HIGH_INTENT, _MOBILIDADE_B2B_MEDIUM_INTENT, _MOBILIDADE_BUSINESS_HINTS, _MOBILIDADE_NOISE_NAMES, _MOBILIDADE_POSITIVE_TERMS

from application.maps.text import _norm_key


def _score_mobilidade_fit(texto: str, nome: str) -> int:
    score = 20  # Base
    nome_norm = _norm_key(nome)
    texto_norm = _norm_key(texto)

    # Tier 1 (+80): Canal B2B Direto (Distribuidor, Revenda, Atacado, Concessionária)
    if any(t in nome_norm or t in texto_norm for t in _MOBILIDADE_B2B_HIGH_INTENT):
        score += 80

    # Tier 2 (+50): Produto e Loja Especializada (Moto Elétrica, E-bike, Scooter, Mobilidade Elétrica)
    if any(t in nome_norm or t in texto_norm for t in _MOBILIDADE_B2B_MEDIUM_INTENT):
        score += 50

    # Tier 3 (+30): Termos positivos de mobilidade elétrica
    if any(t in nome_norm or t in texto_norm for t in _MOBILIDADE_POSITIVE_TERMS):
        score += 30

    # Penalidade (-30): Se parecer nome de pessoa física sem indicador comercial
    if _looks_like_mobilidade_person_name(nome_norm):
        score -= 30

    return max(0, score)

def _looks_like_mobilidade_person_name(nome_norm: str) -> bool:
    parts = [p for p in (nome_norm or "").split() if p]
    if len(parts) < 2 or len(parts) > 5:
        return False
    if any(term in nome_norm for term in _MOBILIDADE_BUSINESS_HINTS):
        return False
    return True

def _filter_noise_mobilidade_eletrica(results: list[dict]) -> list[dict]:
    """Filtro semântico e B2B em memória para o segmento 'Mobilidade Elétrica'.

    Lógica:
      - Remove eletropostos, estações de carga, oficinas a combustão, aluguel público e bicicletarias tradicionais sem e-bike
      - Mantém lojas, concessionárias e distribuidores de motos, e-bikes e scooters elétricas
      - Calcula e atribui Fit Score B2B (mobilidade_fit_score)
    """
    filtered = []
    for item in results:
        nome_raw = item.get("nome") or ""
        nome = _norm_key(nome_raw)
        raw_text = _norm_key(item.get("__raw_text") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])
        query_sources = " ".join([_norm_key(str(qs)) for qs in (item.get("query_sources") or [])])

        texto_loja = f"{nome} {raw_text} {categorias_str}"
        texto_para_busca = f"{texto_loja} {query_sources}"

        # 1. Filtro de ruídos óbvios
        is_noise = any(t in texto_loja for t in _MOBILIDADE_NOISE_NAMES)
        if is_noise:
            continue

        # 2. Descarte de bicicletarias e oficinas tradicionais de bicicletas a pedal sem sinal elétrico/e-bike
        termos_bicicletaria_tradicional = ["bicicletaria", "casa das bicicletas", "oficina de bicicletas", "conserto de bicicletas", "loja de bicicletas", "bicicletas"]
        eh_bicicletaria_tradicional = any(b in texto_loja for b in termos_bicicletaria_tradicional)
        if eh_bicicletaria_tradicional:
            tem_sinal_eletrico = any(e in texto_loja for e in ["eletrica", "elétrica", "e-bike", "ebike", "scooter", "moto", "watts", "voltz", "shineray", "niu", "lev", "nxt", "mobilidade"])
            if not tem_sinal_eletrico:
                continue

        # 3. Filtro de negócios genéricos sem qualquer sinal positivo de mobilidade elétrica no texto próprio da loja
        termos_positivos_fracos = ("concessionaria",)
        tem_positivo = any(
            p in texto_loja
            for p in _MOBILIDADE_POSITIVE_TERMS
            if _norm_key(p) not in termos_positivos_fracos
        )
        categorias_relevantes = (
            "bike store", "bicycle store", "loja de bicicletas", "bicicletaria",
            "motorcycle dealer", "motocicletas", "loja de motos", "moto shop",
            "motor scooter dealer", "scooter", "electric vehicle dealer",
            "veiculos eletricos", "veículos elétricos", "electric motor store",
        )
        tem_categoria_relevante = any(c in categorias_str for c in categorias_relevantes)
        tem_sinal_comercial = any(h in texto_loja for h in _MOBILIDADE_BUSINESS_HINTS)
        if not tem_positivo and not (tem_categoria_relevante and tem_sinal_comercial):
            continue

        # Calcular Fit Score B2B
        fit_score = _score_mobilidade_fit(texto_para_busca, nome_raw)
        item["mobilidade_fit_score"] = fit_score

        filtered.append(item)

    filtered.sort(key=lambda it: int(it.get("mobilidade_fit_score") or 0), reverse=True)
    return filtered
