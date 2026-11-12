from __future__ import annotations
from application.maps.profiles import _SENNHEISER_BUSINESS_HINTS, _VAREJO_MEDIO_NOISE_NAMES, _VAREJO_MEDIO_POSITIVE_TERMS

from application.maps.text import _norm_key


def _looks_like_person_name(nome_norm: str) -> bool:
    parts = [p for p in (nome_norm or "").split() if p]
    if len(parts) < 2 or len(parts) > 4:
        return False
    if any(term in nome_norm for term in _SENNHEISER_BUSINESS_HINTS):
        return False
    return True

def _score_varejo_medio_fit(texto: str, nome: str) -> int:
    score = 20  # Base
    nome_norm = _norm_key(nome)
    texto_norm = _norm_key(texto)

    # Tier 1 (+80): Supermercados / Hipermercados / Atacarejos regionais / Redes alimentícias
    if any(t in nome_norm or t in texto_norm for t in ["supermercado", "supermercados", "hipermercado", "hipermercados", "atacarejo", "atacarejos", "rede de supermercados", "comercial de alimentos"]):
        score += 80
    # Tier 2 (+50): Móveis e Eletro / Eletromóveis / Lojas de Departamentos regionais
    elif any(t in nome_norm or t in texto_norm for t in ["moveis e eletro", "móveis e eletro", "eletromoveis", "eletromóveis", "eletrodomesticos", "eletrodomésticos", "departamento", "departamentos", "loja de departamentos", "eletroportateis", "eletroportáteis"]):
        score += 50
    # Tier 3 (+30): Utilidades Domésticas / Variedades / Bazar
    elif any(t in nome_norm or t in texto_norm for t in ["utilidades", "variedades", "bazar", "artigos para o lar", "presentes"]):
        score += 30

    return score

def _filter_noise_varejo_medio(results: list[dict]) -> list[dict]:
    """Filtro para Varejistas de Médio Porte (Tier 3).

    Lógica:
      - Remove serviços puros, autopeças, clínicas, drogarias, construção pesada e restaurantes
      - Mantém supermercados, hipermercados locais, lojas de móveis e eletro, utilidades e departamentos
      - Calcula e atribui Fit Score B2B (varejo_medio_fit_score)
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
        is_noise = any(t in texto_loja for t in _VAREJO_MEDIO_NOISE_NAMES)

        # Bloqueios absolutos (itens usados, brechós e mercados municipais sempre são descartados)
        termos_bloqueio_absoluto = ["usado", "usados", "segunda mao", "segunda mão", "brecho", "brechó", "mercado municipal", "mercadao municipal", "mercadão municipal", "feira livre", "antiguidades"]
        tem_bloqueio_absoluto = any(u in texto_loja for u in termos_bloqueio_absoluto)

        if tem_bloqueio_absoluto:
            is_noise = True
        elif is_noise:
            # Exceção de ruído para nomes fortes de redes (ex: Supermercado do Povo)
            tem_indicativo_forte = any(b in nome for b in ["supermercado", "hipermercado", "atacarejo", "eletromoveis", "eletromóveis", "moveis e eletro", "móveis e eletro"])
            if tem_indicativo_forte:
                is_noise = False

        if is_noise:
            continue

        # 2. Filtro de negócios genéricos sem qualquer sinal positivo de varejo/médio porte
        tem_positivo = any(p in texto_loja for p in _VAREJO_MEDIO_POSITIVE_TERMS)
        if not tem_positivo:
            continue

        # Calcular Fit Score Tier 3
        fit_score = _score_varejo_medio_fit(texto_para_busca, nome_raw)
        item["varejo_medio_fit_score"] = fit_score

        filtered.append(item)

    filtered.sort(key=lambda it: int(it.get("varejo_medio_fit_score") or 0), reverse=True)
    return filtered

def _filter_large_retail(results: list[dict]) -> list[dict]:
    """Filtra grandes redes de varejo e serviços puramente técnicos dos resultados."""
    server_exclusions = [
        "magazine luiza",
        "magalu",
        "americanas",
        "casas bahia",
        "ponto frio",
        "carrefour",
        "extra",
        "walmart",
        "leroy merlin",
        "camicado",
        "madeiramadeira",
        "havan",
        "kalunga",
        "fast shop",
        "kabum",
        "bumerang",
        "pichau",
        "terabyte",
        "lojas cem",
        "loja cem",
        "pernambucanas",
        "marabraz",
        "lojas colombo",
        "gazin",
        "novo mundo",
        "assaí",
        "assai",
        "atacadão",
        "atacadao",
        "sam's club",
        "sams club",
        "pão de açúcar",
        "pao de acucar",
        "mercado livre",
        "ponto de coleta",
        "agência mercado livre",

        "refrigeração",
        "refrigeracao",
        "lavadora",
        "lavadoras",
        "oficina",

        # Lojas irrelevantes para Informática (varal, parafusos, metalurgia, ferragens)
        "varal",
        "varais",
        "parafuso",
        "parafusos",
        "metalurgia",
        "metalúrgica",
        "metalurgica",
        "ferragem",
        "ferragens",
        "ferramenta",
        "ferramentas",
        "serralheria",
        "solda",
        "soldas",
        "máquinas",
        "maquinas",
        "industrial",
        "industriais",
        # Hardware industrial específico
        "spiralock",
        "aço",
        "açoforti",
        "acoforti",
        "afiação",
        "afiacao",
        "pro-lar",
        "prolar",
        "trava",
        "travas",
        "fixação",
        "fixacao",
        "porca",
        "porcas",
        "buchas",
        "arruela",
    ]

    repair_exclusions = [
        "assistência técnica",
        "assistencia tecnica",
        "conserto",
        "reparo",
        "manutenção",
        "manutencao",
    ]

    commercial_exceptions = [
        "informática",
        "informatica",
        "distribuidor",
        "distribuidora",
        "revenda",
        "atacadista",
        "atacado",
        "loja",
        "suprimentos",
        "periféricos",
        "perifericos",
        "eletrônicos",
        "eletronicos",
        "gamer",
        "tecnologia",
        "componentes",
    ]

    filtered = []
    for item in results:
        nome = (item.get("nome", "") or "").lower()
        # Verificar grandes redes e exclusões absolutas
        if any(excl in nome for excl in server_exclusions):
            continue

        # Verificar se é assistência técnica pura (sem termos comerciais de TI)
        has_repair = any(rep in nome for rep in repair_exclusions)
        if has_repair:
            has_commercial = any(comm in nome for comm in commercial_exceptions)
            if not has_commercial:
                continue

        filtered.append(item)

    return filtered
