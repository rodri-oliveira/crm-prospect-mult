from __future__ import annotations
from application.maps.profiles import _BUSINESS_INDICATORS, _INFO_NOISE_NAMES, _INFO_POSITIVE_TERMS, _PERSONAL_FIRST_NAMES

from application.maps.text import _norm_key


def _score_informatica_fit(texto: str, nome: str) -> int:
    score = 20  # Base
    nome_norm = _norm_key(nome)
    texto_norm = _norm_key(texto)

    # Tier 1 (+80): Canal B2B Direto (Distribuidora, Revenda, Atacado)
    if any(t in nome_norm or t in texto_norm for t in ["distribuidora", "distribuidor", "atacadista", "atacado", "revenda"]):
        score += 80
    # Tier 2 (+50): Suprimentos / TI Especializada
    elif any(t in nome_norm or t in texto_norm for t in ["suprimentos", "computadores e perifericos", "hardware", "componentes"]):
        score += 50
    # Tier 3 (+30): Comércio/Loja de TI ou Papelaria + TI
    elif any(t in nome_norm or t in texto_norm for t in ["loja de informatica", "comercio de informatica", "papelaria"]):
        score += 30

    return score

def _filter_noise_informatica(results: list[dict]) -> list[dict]:
    """Filtro para o segmento de Informática.
    Lógica:
      - Remove escolas, cursos e baterias (automotivas)
      - Remove empresas de serviço puro (Software, Nuvem, Consultoria, ISPs, Segurança)
      - Remove autônomos e pessoas físicas sem indicativo comercial
      - Remove lojas genéricas sem correlação com TI
      - Mantém lojas de TI e revendas mesmo que prestem assistência técnica secundária
      - Calcula e atribui Fit Score B2B (informatica_medio_fit_score)
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

        # 1. Filtro de termos e categorias de ruído no texto da LOJA
        is_noise = any(t in texto_loja for t in _INFO_NOISE_NAMES)

        # Exceção: Se o NOME da loja tiver "informatica", "eletronico" ou "suprimentos", mantemos
        tem_nome_comercial_ti = any(b in nome for b in ["informatica", "informática", "eletronico", "eletrônico", "suprimentos", "distribuidora", "revenda", "componentes"])
        if tem_nome_comercial_ti:
            is_noise = False

        # Descartar assistências técnicas puras (sem indicação de loja/revenda/distribuidora no nome)
        termos_reparo = ["assistencia tecnica", "assistência técnica", "computer repair service", "conserto", "reparo"]
        tem_termo_reparo = any(r in texto_loja for r in termos_reparo)
        if tem_termo_reparo:
            tem_canal_loja = any(c in nome for c in ["loja", "store", "distribuidora", "distribuidor", "revenda", "atacadista", "atacado", "suprimentos", "comercio", "comércio", "comercial"])
            if not tem_canal_loja:
                continue

        if is_noise:
            continue

        # 2. Filtro de Pessoas Físicas / Autônomos (Ex: "João da Silva Informática")
        primeira_palavra = nome.split()[0] if nome.split() else ""
        if primeira_palavra in _PERSONAL_FIRST_NAMES:
            tem_indicativo_comercial = any(b in nome for b in _BUSINESS_INDICATORS)
            if not tem_indicativo_comercial:
                continue

        # 3. Filtro de lojas genéricas sem termo de confirmação de TI no texto da LOJA
        tem_termo_positivo = any(p in texto_loja for p in _INFO_POSITIVE_TERMS)
        if not tem_termo_positivo:
            continue

        # Calcular Fit Score B2B
        fit_score = _score_informatica_fit(texto_para_busca, nome_raw)
        item["informatica_medio_fit_score"] = fit_score
        item["informatica_fit_score"] = fit_score

        filtered.append(item)

    # Ordenar por fit score decrescente
    filtered.sort(key=lambda it: int(it.get("informatica_medio_fit_score") or 0), reverse=True)
    return filtered
