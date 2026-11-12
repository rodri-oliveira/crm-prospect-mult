from __future__ import annotations
from application.maps.profiles import _BRINQUEDOS_NOISE_NAMES, _GAMER_NOISE_NAMES, _SENNHEISER_NOISE_NAMES

from application.maps.text import _norm_key, _re_sub_ignoring_case


def _build_queries_for_free_text(query: str, cidade: str, estado: str) -> list[str]:
    base = (query or "").strip()
    if not base:
        return []

    cidade_clean = (cidade or "").strip()
    estado_clean = (estado or "").strip()
    local_parts = []
    if cidade_clean:
        local_parts.append(f'"{cidade_clean}"')
    if estado_clean:
        local_parts.append(estado_clean)

    local = ", ".join(local_parts)
    if local:
        return [f"{base} em {local}"]
    return [base]

def _build_queries_for_segments(segs: list[str], cidade: str, estado: str, extra: str) -> list[dict[str, str]]:
    """Estratégia inteligente de multi-query baseada nas famílias Multilaser (Curva ABC).

    Divide as âncoras em grupos lógicos por família de produto para maximizar
    cobertura de lojas (B2B e varejo) sem tornar queries muito específicas.

    Otimização para múltiplos segmentos:
    - 1 segmento: estratégia detalhada (~16 queries)
    - 2-3 segmentos: combinar com OR (~20 queries)
    - 4+ segmentos: estratégia genérica + priorização (~25 queries)
    """
    from application.maps.accessories import is_accessories, accessories_queries
    if any(is_accessories(seg) for seg in segs):
        return accessories_queries(cidade, estado)

    cidade_clean = (cidade or "").strip()
    estado_clean = (estado or "").strip()

    local_parts = []
    if cidade_clean:
        local_parts.append(f'"{cidade_clean}"')
    if estado_clean:
        local_parts.append(estado_clean)

    local = ", ".join(local_parts)
    if local:
        local = f" em {local}"

    # Marcas relevantes para capturar revendedores específicos
    # Multilaser + marcas complementares que indicam potencial B2B
    brand_terms = ["Multilaser", "Lenovo", "Dell", "Samsung", "LG", "Positivo"]

    # Termos leves de exclusão para a query do Google Maps (para não estourar limite de tamanho da busca)
    # O descarte pesado de grandes redes e assistências técnicas é feito 100% em memória no Python (_filter_large_retail)
    exclude_terms = [
        "fechado",
        "extinto",
        "falência",
    ]

    # Grupos de âncoras por família Multilaser (Curva ABC Fevereiro)
    # AC = Acessórios/Periféricos | ME = Mídia/Energia | PC = Computadores | IC = SSD/Memória
    anchor_groups: dict[str, list[str]] = {
        "Informática": [
            # Núcleo de Alta Performance B2B e Varejo Especializado
            "distribuidor informática",
            "revenda informática",
            "atacadista informática",
            "loja de informática",
            "comércio de acessórios de informática",
            "loja de eletrônicos e informática",
            "suprimentos de informática",
            "loja de laptops",
            "loja de tablets",
            "papelaria e informática",
            "comércio de informática",
            "distribuidor de componentes de computador",
        ],
        "Celulares": [
            # O Alto Volume
            "atacadista acessórios celular",
            "distribuidor acessórios celular",
            "revenda acessórios celular",
            # O Médio Comércio e Revendedores de Acessórios
            "loja de capinhas de celular",
            "acessórios para celular",
            "comércio de eletrônicos",
            "loja de eletrônicos",
            "loja de celulares centro",
            "venda de celular flip",
            "celular para idoso loja",
            "assistência e venda de celular",
        ],
        "Áudio e Vídeo": [
            # O Alto Volume B2B
            "distribuidor áudio profissional",
            "loja de instrumentos musicais", # Lojas de música revendem muitas caixas de som e fones pesados
            "distribuidor som automotivo",
            # O Médio Comércio
            "loja de som e acessórios",
            "loja de eletrônicos",
            "acústica e som",
            "equipamentos de áudio",
            "instalação de som automotivo", # Compram centrais multimídia aos montes
        ],
        "Utilidades e Variedades": [
            # O Pote de Ouro para produtos de curva B e C Multimarcas (Limpo de alimentos)
            "loja de utilidades",
            "loja de variedades",
            "bazar e presentes",
            "comercial importadora",
            "loja de utilidades domésticas",
        ],
        "Eletroportáteis": [
            # O Alto Volume (Atacadistas e distribuidores regionais)
            "atacadista eletrodomésticos",
            "distribuidor eletrodomésticos",
            "revenda eletrodomésticos",
            # O Médio Comércio (Lojistas de Utensílios e Médio Varejo)
            "loja de eletrodomésticos",
            "loja de eletroportáteis",
            "comércio de eletroportáteis",
            # Vendas Correlatas e Giro Rápido (Lojas menores/bairro e móveis)
            "loja de utilidades domésticas",
            "loja de artigos para o lar",
            "loja de presentes",
            "loja de móveis e eletro",
            # O Novo Nicho (Giro Rápido / Outlets / Saldo)
            "outlet eletrodomésticos",
            "saldão eletrodomésticos",
        ],
        "Gamer": [
            # TIER 1: Compra em volume e revenda B2B
            "distribuidor gamer",
            "distribuidor de games",
            "distribuidor de jogos",
            "atacadista gamer",
            "atacadista de games",
            "revenda gamer",
            "revenda de games",
            "fornecedor gamer",
            "fornecedor de games",
            "importadora gamer",
            "atacado gamer",

            # TIER 2: Varejo especializado com foco em comércio (físico/online)
            "loja gamer",
            "loja de games",
            "loja de jogos",
            "loja de informática gamer",

            # TIER 3: Periféricos e Acessórios
            "acessórios gamer",
            "periféricos gamer",
            "cadeira gamer",
            "pc gamer",
        ],
        "Brinquedos": [
            # TIER 1: compra em volume e revenda
            "distribuidor de brinquedos",
            "atacadista de brinquedos",
            "atacado de brinquedos",
            "revenda de brinquedos",
            "fornecedor de brinquedos",
            "importadora de brinquedos",
            "brinquedos atacado e varejo",
            # TIER 2: varejo especializado com giro
            "loja de brinquedos",
            "lojas de brinquedos",
            "brinquedos educativos",
            "jogos educativos",
            "jogos infantis",
            "loja infantil brinquedos",
            "loja kids brinquedos",
            # TIER 3: correlatos que costumam revender brinquedos
            "papelaria e brinquedos",
            "bazar e brinquedos",
            "loja de presentes e brinquedos",
            "loja de variedades brinquedos",
            "loja de 1.99 brinquedos",
        ],
        "Drones e Câmeras": [
            # TIER 1: Revenda B2B / Distribuidores
            "distribuidor de drones",
            "revenda de drones",
            "importadora de drones",
            "revenda DJI",
            "assistência DJI",

            # TIER 2: Varejo Especializado / Lojas Físicas
            "loja de drones",
            "loja de drones e câmeras",
            "drone shop",
            "drone store",

            # TIER 3: Hobby e FPV (Pequenas revendas especializadas)
            "loja de aeromodelismo",
            "loja fpv",
            "loja de radiocontrole",
        ],
        "Ortopédica": ["ortopedia"],
        "Fitness": ["fitness"],
        "Pet": ["pet shop"],
        "Redes": ["roteador switch", "cabo rede"],
        "Mobilidade Elétrica": [
            # TIER 0: Termos naturais diretos de busca no Maps
            "mobilidade elétrica",
            "lojas de mobilidade elétrica",

            # TIER 1: B2B - Atacadistas e Distribuidores
            "distribuidor de mobilidade elétrica",
            "distribuidor de motos elétricas",
            "distribuidor de bicicletas elétricas",
            "atacadista de mobilidade elétrica",
            "revenda de mobilidade elétrica",
            "revenda de motos elétricas",
            "revenda de bicicletas elétricas",

            # TIER 2: Motos e Scooter Elétricas (Concessionárias e Lojas Especializadas)
            "loja de motos elétricas",
            "concessionária de motos elétricas",
            "loja de scooters elétricas",
            "scooter elétrica",
            "motos elétricas",

            # TIER 3: Bicicletas Elétricas (e-bikes)
            "loja de bicicletas elétricas",
            "loja de e-bikes",
            "ebike shop",
            "bicicletaria elétrica",
            "bicicletas elétricas",

            # TIER 4: Patinetes e Veículos Leves Elétricos
            "loja de patinetes elétricos",
            "veículos elétricos",
            "assistência e venda de moto elétrica",
        ],
        "Health Care": [
            # Atacadistas e distribuidores (foco CNPJ)
            "atacadista equipamentos médicos",
            "distribuidor equipamentos médicos",
            "loja de equipamentos médicos atacado",
            "revenda equipamentos médicos",
        ],
        "Tablets Kids": [
            "loja de tablets",
            "tablet infantil",
            "tablet educativo",
            "acessórios tablet",
            "papelaria digital",
            "brinquedo educativo",
            "loja de eletrônicos",
        ],
        # Multikids - linha infantil completa
        "Multikids": [
            "boneca", "boneca bebê",
            "pelúcia", "ursinho",
            "Disney", "Marvel", "Barbie", "Frozen",
            "carrinho brinquedo", "hot wheels",
            "faz de conta", "kit cozinha", "kit médico",
        ],
        "Sennheiser": [
            # TIER 1: O "Coração" do B2B Pro Audio
            "áudio profissional",
            "equipamentos para estúdio de som",
            "loja de áudio profissional",
            "locaçao de som para eventos",
            "locação de microfones profissionais",
            "sistemas de áudio sem fio",

            # TIER 2: Segmentos Verticais (Broadcast e Touring)
            "revenda broadcast áudio",
            "integrador de sistemas de áudio",
            "sonorização profissional",
            "loja de instrumentos musicais especializada",

            # TIER 3: Nichos Específicos
            "equipamentos para rádio e tv",
            "conferência e áudio corporativo",
            "fones de ouvido audiófilo",
        ],
    }

    # Override Multikids anchors with the updated list
    # Termos genéricos de varejo infantil + marcas/licenciados
    anchor_groups["Multikids"] = [
        # Varejo genérico infantil
        "loja de brinquedos",
        "loja kids",
        "shopping infantil",
        "shopping das crianças",
        "loja de 1.99",
        "jogos para crianças",
        "brinquedos",
        # Marcas/licenciados populares
        "disney",
        "barbie",
        "hot wheels",
        "boneca",
    ]

    # Sennheiser: CNPJ com necessidade profissional de audio, mesmo quando for
    # consumidor final empresarial, e nao apenas revenda em volume.
    anchor_groups["Sennheiser"] = [
        "loja de audio profissional",
        "audio profissional",
        "revenda de audio profissional",
        "equipamentos de audio profissional",
        "loja de instrumentos musicais",
        "distribuidor de instrumentos musicais",
        "revenda de instrumentos musicais",
        "instrumentos musicais e audio profissional",
        "microfones profissionais",
        "sistemas de microfone sem fio",
        "estudio de gravacao",
        "estudio de podcast",
        "podcast studio",
        "produtora audiovisual",
        "produtora de video",
        "integrador audiovisual",
        "solucoes av",
        "emissora de radio",
        "emissora de tv",
        "broadcast audio",
        "equipamentos para radio e tv",
        "sonorizacao profissional",
        "sonorizacao de eventos",
        "equipamentos para eventos",
        "locadora de som",
        "locacao de som para eventos",
        "locacao de audio",
        "som para igreja",
        "sonorizacao para igrejas",
        "audio para auditorio",
        "teatro e auditorio",
        "casa de show",
        "casa de eventos",
        "centro de convencoes",
        "hotel eventos",
        "universidade auditorio",
        "escola de musica",
        "audio corporativo",
        "integrador audio e video",
        "integrador av",
        "videoconferencia corporativa",
        "sistemas de conferencia",
    ]

    anchor_groups["Informática (Médio Porte)"] = [
        "distribuidora de informática",
        "revenda de informática",
        "atacadista de informática",
        "atacado de informática",
        "suprimentos de informática",
        "loja de informática atacado",
        "distribuidor de informática",
        "computadores e periféricos",
    ]

    anchor_groups["Varejistas de Médio Porte"] = [
        "supermercado",
        "supermercados",
        "supermercado regional",
        "rede de supermercados",
        "hipermercado",
        "atacarejo",
        "loja de móveis e eletro",
        "móveis e eletrodomésticos",
        "loja de eletrodomésticos",
        "loja de departamentos",
        "loja de utilidades domésticas",
        "loja de utilidades",
        "loja de variedades",
        "bazar e presentes",
        "eletromóveis",
    ]

    queries: list[dict[str, str]] = []
    num_segs = len(segs)

    # Estratégia baseada no número de segmentos
    if num_segs == 0:
        return []

    # Para cada segmento, usar estratégia detalhada completa
    # Não importa se são 1, 3 ou 5 segmentos - cada um merece atenção
    for seg in segs:
        seg_clean = (seg or "").strip()
        if not seg_clean:
            continue

        anchor_lists = anchor_groups.get(seg_clean, [""])

        # Segmentos especiais que são marcas/linhas (não tipos de loja)
        # Para esses, usar apenas âncoras, não o nome do segmento na query
        is_brand_segment = seg_clean in [
            "Multikids",
            "Health Care",
            "Sennheiser",
            "Informática (Médio Porte)",
            "Varejistas de Médio Porte",
        ]

        if is_brand_segment:
            # Para segmentos de marca/linha, usar queries com âncoras diretamente
            for anchors in anchor_lists:
                if not anchors:
                    continue
                # Usar a âncora diretamente sem adicionar prefixos
                q = f"{anchors}{local}".strip()
                queries.append({"q": q, "segmento": seg_clean})
        else:
            # Para segmentos normais, usar estratégia mais limpa
            # Query principal do segmento
            q = f"loja de {seg_clean}{local}".strip()
            queries.append({"q": q, "segmento": seg_clean})

            # Queries com âncoras específicas (sem repetir o segmento)
            for anchors in anchor_lists:
                if not anchors:
                    continue
                anchor_lower = anchors.lower()

                # Palavras que indicam que a âncora já possui seu próprio prefixo estrutural
                prefixes_to_ignore = (
                    "loja", "comércio", "comercial", "atacadista", "distribuidor",
                    "atacado", "distribuidora", "fornecedor", "revenda", "outlet", "saldão", "bazar", "shopping", "papelaria",
                    "locadora", "equipamento", "drone", "câmera", "estabilizador",
                    "acessório", "clube", "produtora", "estúdio", "importadora",
                    "concessionária", "concessionaria", "ebike", "bicicletaria", "veículos", "veiculos", "assistência", "assistencia",
                )

                if anchor_lower.startswith(prefixes_to_ignore):
                    q = f"{anchors}{local}".strip()
                else:
                    q = f"loja de {anchors}{local}".strip()

                queries.append({"q": q, "segmento": seg_clean})

            # Query B2B do segmento
            q = f"distribuidor de {seg_clean}{local}".strip()
            queries.append({"q": q, "segmento": seg_clean})

            # Queries com marcas relevantes
            # Drones: Inserir "DJI"
            # Mobilidade Elétrica: Inserir marcas do setor ("Watts", "Voltz", "Shineray")
            if "drone" in seg_clean.lower():
                seg_brands = ["DJI"]
            elif "mobilidade" in seg_clean.lower():
                seg_brands = ["Watts", "Voltz", "Shineray"]
            else:
                seg_brands = brand_terms[:2]
            for brand in seg_brands:
                queries.append({"q": f"{brand} {seg_clean}{local}".strip(), "segmento": seg_clean})

    # Remover duplicatas mantendo ordem
    seen = set()
    out: list[dict[str, str]] = []
    for spec in queries:
        q = (spec.get("q") or "").strip()
        k = q.lower()
        if k and k not in seen:
            seen.add(k)
            out.append({"q": q, "segmento": spec.get("segmento") or ""})

    # Adicionar termos de exclusão a todas as queries
    for spec in out:
        seg = spec.get("segmento") or ""
        all_excludes = exclude_terms
        if seg == "Sennheiser":
            all_excludes = exclude_terms + _SENNHEISER_NOISE_NAMES
        if seg == "Brinquedos":
            all_excludes = exclude_terms + _BRINQUEDOS_NOISE_NAMES
        if seg == "Gamer":
            all_excludes = exclude_terms + _GAMER_NOISE_NAMES
        if "varej" in seg.lower():
            all_excludes = exclude_terms + ["magazine luiza", "casas bahia", "lojas cem", "pernambucanas", "marabraz", "farmacia", "drogaria", "oficina", "mecanica"]
        if "inform" in seg.lower():
            all_excludes = exclude_terms + ["assistencia tecnica", "software", "provedor", "consultoria"]
        exclude_suffix = " " + " ".join([f'-"{term}"' for term in all_excludes])
        spec["q"] = f"{spec['q']}{exclude_suffix}".strip()

    return out

def _normalize_extra(extra: str, cidade: str, estado: str) -> str:
    extra_clean = (extra or "").strip()
    if not extra_clean:
        return ""

    cidade_clean = (cidade or "").strip()
    estado_clean = (estado or "").strip()
    if not cidade_clean and not estado_clean:
        return extra_clean

    extra_clean = " ".join(extra_clean.split())

    if cidade_clean and estado_clean:
        import re

        pat = rf"\s+em\s+{re.escape(cidade_clean)}\s*,\s*{re.escape(estado_clean)}\s*$"
        cleaned = _re_sub_ignoring_case(pat, "", extra_clean).strip()
        if cleaned != extra_clean:
            return cleaned

    if cidade_clean:
        import re

        pat = rf"\s+em\s+{re.escape(cidade_clean)}\s*$"
        cleaned = _re_sub_ignoring_case(pat, "", extra_clean).strip()
        if cleaned != extra_clean:
            return cleaned

    if cidade_clean and estado_clean:
        import re

        pat = rf"\s+{re.escape(cidade_clean)}\s*,?\s*{re.escape(estado_clean)}\s*$"
        cleaned = _re_sub_ignoring_case(pat, "", extra_clean).strip()
        if cleaned != extra_clean:
            return cleaned

    if cidade_clean:
        import re

        pat = rf"\s+{re.escape(cidade_clean)}\s*$"
        cleaned = _re_sub_ignoring_case(pat, "", extra_clean).strip()
        if cleaned != extra_clean:
            return cleaned

    return extra_clean

def _looks_like_segment_or_query(extra_clean: str, segs: list[str], cidade: str, estado: str) -> bool:
    """Detecta query do frontend (segmentos com OR + local) para evitar sufixo lixo."""
    if not extra_clean or not segs:
        return False

    extra_norm = _norm_key(extra_clean)
    if " or " not in extra_norm:
        return False

    cidade_clean = (cidade or "").strip()
    estado_clean = (estado or "").strip()
    if cidade_clean and estado_clean:
        loc_norm = _norm_key(f"{cidade_clean} {estado_clean}")
        if extra_norm.endswith(loc_norm):
            extra_norm = extra_norm[: -len(loc_norm)].strip()
    elif cidade_clean:
        loc_norm = _norm_key(cidade_clean)
        if extra_norm.endswith(loc_norm):
            extra_norm = extra_norm[: -len(loc_norm)].strip()

    seg_norms = [_norm_key(s) for s in segs if (s or "").strip()]
    return bool(seg_norms) and all(sn in extra_norm for sn in seg_norms)
