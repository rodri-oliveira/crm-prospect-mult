from __future__ import annotations


from dataclasses import dataclass


import logging


import time




from typing import Any


from domain.repositories.maps_existing_keys_repository import MapsExistingKeysRepository


from infrastructure.repositories.sqlite_maps_existing_keys_repository import SqliteMapsExistingKeysRepository


from application.maps.filters.brinquedos import _filter_noise_brinquedos
from application.maps.filters.drones import _DRONE_NEGATIVE_CATEGORIES, _DRONE_NOISE_NAMES, _DRONE_POSITIVE_TERMS, _filter_noise_drones
from application.maps.filters.gamer import _filter_noise_gamer
from application.maps.filters.geography import _filter_city_page_results, _filter_items_with_other_city_in_name, _filter_strict_city
from application.maps.filters.informatica import _filter_noise_informatica, _score_informatica_fit
from application.maps.filters.mobilidade import _filter_noise_mobilidade_eletrica, _looks_like_mobilidade_person_name, _score_mobilidade_fit
from application.maps.filters.segments import _filter_segment_noise
from application.maps.filters.sennheiser import _filter_noise_sennheiser, _score_sennheiser_fit
from application.maps.filters.varejo import _filter_large_retail, _filter_noise_varejo_medio, _looks_like_person_name, _score_varejo_medio_fit
from application.maps.queries import _build_queries_for_free_text, _build_queries_for_segments, _looks_like_segment_or_query, _normalize_extra
from application.maps.text import _norm_key, _re_sub_ignoring_case

@dataclass(frozen=True)
class SearchMapsResultsRequest:
    query: str
    cidade: str
    estado: str
    segmentos: list[str]
    limit: int


@dataclass(frozen=True)
class SearchMapsResultsResponse:
    ok: bool
    modo: str
    query: str
    message: str | None
    existing_keys: list[str]
    items: list[dict[str, Any]]
    executed_queries: list[str]
    query_stats: list[dict[str, Any]]
    merged_before_dedupe: int
    merged_after_dedupe: int


@dataclass(frozen=True)
class GenerateQueriesResponse:
    ok: bool
    queries: list[dict[str, str]]  # [{"q": "...", "segmento": "..."}]
    primary_query: str  # Query principal para iframe
    total_queries: int


def generate_queries_for_segments(
    segmentos: list[str],
    cidade: str,
    estado: str,
    extra: str = "",
) -> GenerateQueriesResponse:
    """Gera lista de queries para segmentos sem executar scraper.

    Usado para sincronizar o botão Buscar com o Resultado Beta.
    Retorna a query principal para o iframe e todas as queries para o drawer.
    """
    segs = [s for s in (segmentos or []) if (s or "").strip()]

    if not segs:
        # Fallback: query genérica
        local = ", ".join([p for p in [cidade, estado] if (p or "").strip()])
        if local:
            local = f" em {local}"
        q = f"{extra}{local}".strip() if extra else f"lojas{local}".strip()
        return GenerateQueriesResponse(
            ok=True,
            queries=[{"q": q, "segmento": ""}],
            primary_query=q,
            total_queries=1,
        )

    queries = _build_queries_for_segments(segs=segs, cidade=cidade, estado=estado, extra=extra)

    # Query principal: primeira query (mais genérica/relevante)
    primary_query = queries[0]["q"] if queries else ""

    return GenerateQueriesResponse(
        ok=True,
        queries=queries,
        primary_query=primary_query,
        total_queries=len(queries),
    )


def search_maps_results(req: SearchMapsResultsRequest) -> SearchMapsResultsResponse:
    return search_maps_results_with_repo(req, SqliteMapsExistingKeysRepository())


def search_maps_results_with_repo(
    req: SearchMapsResultsRequest,
    existing_keys_repo: MapsExistingKeysRepository,
) -> SearchMapsResultsResponse:
    logger = logging.getLogger(__name__)
    query = (req.query or "").strip()
    cidade = (req.cidade or "").strip()
    estado = (req.estado or "").strip()
    segmentos = req.segmentos or []

    limit = req.limit or 20
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200

    itens: list[dict[str, Any]] = []
    modo = "mock"
    message: str | None = None
    executed_queries: list[str] = []
    query_stats: list[dict[str, Any]] = []
    merged_before_dedupe = 0
    merged_after_dedupe = 0

    segs = [s for s in (segmentos or []) if (s or "").strip()]

    if query:
        if segs:
            query_specs = _build_queries_for_segments(segs=segs, cidade=cidade, estado=estado, extra=query)
        else:
            query_specs = [{"q": q, "segmento": ""} for q in _build_queries_for_free_text(query=query, cidade=cidade, estado=estado)]

        executed_queries = []

        try:
            from services.maps_scrape_service import scrape_maps_results

            merged: list[dict[str, Any]] = []
            per_query_limit = min(50, limit)

            # Rastrear lojas únicas por query para análise de overlap
            seen_keys_total: set[str] = set()

            for spec in query_specs:
                q = (spec.get("q") or "").strip()
                seg = (spec.get("segmento") or "").strip()
                if not q:
                    continue
                executed_queries.append(q)
                t0 = time.time()
                got = scrape_maps_results(q, limit=per_query_limit, headless=True)
                dt_ms = int((time.time() - t0) * 1000)

                # Enriquecer itens com segmento e fonte da query (antes dos filtros)
                for it in (got or []):
                    it.setdefault("categorias", list(it.get("segmentos") or []))
                    if seg:
                        cur = it.get("segmentos")
                        if not isinstance(cur, list):
                            cur = []
                        if seg not in cur:
                            cur.append(seg)
                        it["segmentos"] = cur
                    src = it.get("query_sources")
                    if not isinstance(src, list):
                        src = []
                    if q not in src:
                        src.append(q)
                    it["query_sources"] = src

                # Filtrar varejo grande dos resultados (Google Maps não respeita exclusão)
                got = _filter_large_retail(got or [])

                # Filtro: remover a própria cidade retornada como se fosse um negócio
                if cidade:
                    got = _filter_city_page_results(got or [], cidade=cidade)

                # Filtro semântico por segmento
                # Para drones: filtro leve (só remove aluguel/locação, não bloqueia lojas genéricas)
                got = _filter_segment_noise(got or [], seg=seg)

                # Filtro conservador: remover itens que declaram outra cidade no nome
                # Ex: "Loja Zema - Casa Branca" quando o alvo é "Aguaí"
                if cidade:
                    got = _filter_items_with_other_city_in_name(got or [], cidade=cidade)

                # Filtro geográfico estrito: remove itens que o scraper identificou como estando em outra cidade
                if cidade:
                    got = _filter_strict_city(got or [], cidade=cidade, estado=estado)

                # Calcular new_unique APÓS filtros → stats refletem o que realmente entra
                new_keys: set[str] = set()
                for it in (got or []):
                    k = _key_from_item(it)
                    if k and k not in seen_keys_total:
                        new_keys.add(k)

                # Atualizar total de lojas únicas
                seen_keys_total.update(new_keys)

                # Log detalhado com estatísticas e nomes das lojas
                lojas_nomes = [it.get("nome", "?")[:30] for it in (got or [])[:5]]
                logger.warning(
                    "maps_query ms=%s items=%s new_unique=%s total_unique=%s segmento=%s q=%s lojas=%s",
                    dt_ms,
                    len(got or []),
                    len(new_keys),
                    len(seen_keys_total),
                    seg or "-",
                    q,
                    lojas_nomes,
                )

                query_stats.append({
                    "q": q,
                    "segmento": seg or None,
                    "ms": dt_ms,
                    "items": len(got or []),
                    "new_unique": len(new_keys),
                    "total_unique": len(seen_keys_total),
                })
                merged.extend(got)

                # Evita gastar queries quando jÃ¡ atingiu o limite Ãºnico desejado
                if limit and len(seen_keys_total) >= limit:
                    logger.warning(
                        "maps_early_stop reason=limit_reached total_unique=%s limit=%s",
                        len(seen_keys_total),
                        limit,
                    )
                    break

            merged_before_dedupe = len(merged)
            merged = _dedupe_items(merged)
            merged_after_dedupe = len(merged)

            # Log final com resumo (valores reais do retorno)
            logger.warning(
                "maps_summary total_queries=%s before_dedupe=%s after_dedupe=%s total_unique_keys=%s",
                len(executed_queries),
                merged_before_dedupe,
                merged_after_dedupe,
                len(seen_keys_total),
            )
            # Preserve existing ordering for legacy segments.
            def _get_sort_priority(it: dict[str, Any]) -> int:
                tel = str(it.get("telefone") or "").strip()
                # Limpa apenas dígitos
                clean = "".join(ch for ch in tel if ch.isdigit())
                # Se tem DDD (10 ou 11 dígitos), o 3º dígito é o definidor
                if len(clean) >= 10:
                    first = clean[2]
                    if first in ('2', '3', '4', '5'): return 1 # Fixo
                    if first == '9': return 2 # Celular
                elif len(clean) > 0:
                    # Sem DDD, pega o 1º dígito
                    first = clean[0]
                    if first in ('2', '3', '4', '5'): return 1
                    if first == '9': return 2
                return 3 # Outros/Sem tel

            from application.maps.accessories import is_accessories, filter_accessories
            if any(is_accessories(s) for s in segs):
                merged = filter_accessories(merged)
            elif any((s or "").strip() == "Sennheiser" for s in segs):
                merged.sort(
                    key=lambda it: (
                        -int(it.get("sennheiser_fit_score") or 0),
                        _get_sort_priority(it),
                    )
                )
            elif any("varej" in (s or "").lower() for s in segs):
                merged.sort(
                    key=lambda it: (
                        -int(it.get("varejo_medio_fit_score") or 0),
                        _get_sort_priority(it),
                    )
                )
            elif any("inform" in (s or "").lower() for s in segs):
                merged.sort(
                    key=lambda it: (
                        -int(it.get("informatica_medio_fit_score") or it.get("informatica_fit_score") or 0),
                        _get_sort_priority(it),
                    )
                )
            elif any("mobilidade" in (s or "").lower() for s in segs):
                merged.sort(
                    key=lambda it: (
                        -int(it.get("mobilidade_fit_score") or 0),
                        _get_sort_priority(it),
                    )
                )
            else:
                merged.sort(key=_get_sort_priority)

            itens = merged[:limit]
            for it in itens:
                it["location_inferred"] = not bool(it.get("cidade"))
                it["cidade"] = it.get("cidade") or cidade
                it["estado"] = it.get("estado") or estado
                if segs:
                    it["segmentos"] = it.get("segmentos") or []
                else:
                    it["segmentos"] = it.get("segmentos") or segs

            modo = "real"
        except Exception as e:
            message = str(e)
            itens = []
            modo = "mock"
            merged_before_dedupe = 0
            merged_after_dedupe = 0
            logger.error("maps_search_failed query=%s error=%s", query, message, exc_info=True)

    existing_data = existing_keys_repo.get_existing_maps_keys()
    existing_keys = _find_existing_keys(itens, existing_keys_repo, existing_data)

    for item in itens:
        key = _key_from_item(item)
        if key in existing_keys:
            item['already_added'] = True
            item['existing_status'] = (existing_data.key_status_map or {}).get(key)

    from application.maps.accessories import is_accessories
    focused_failure = bool(message) and any(is_accessories(s) for s in segs)
    return SearchMapsResultsResponse(
        ok=not focused_failure,
        modo="error" if focused_failure else modo,
        query=query,
        message=message,
        existing_keys=existing_keys,
        items=itens,
        executed_queries=executed_queries,
        query_stats=query_stats,
        merged_before_dedupe=merged_before_dedupe,
        merged_after_dedupe=merged_after_dedupe,
    )


def _key_from_item(it: dict[str, Any]) -> str:
    try:
        from services.maps_scrape_service import derive_maps_place_id
    except Exception:
        derive_maps_place_id = None

    u = str(it.get("maps_url") or "").strip()
    if u and derive_maps_place_id:
        try:
            dk = derive_maps_place_id(u)
            if dk:
                return dk
        except Exception:
            pass
    k = str(it.get("maps_place_id") or it.get("id") or "").strip()
    if k:
        return k
    return ""


def _find_existing_keys(
    items: list[dict[str, Any]],
    existing_keys_repo: MapsExistingKeysRepository,
    existing=None,
) -> list[str]:
    incoming_keys = []
    for it in items or []:
        k = _key_from_item(it)
        if k:
            incoming_keys.append(k)

    incoming_set = set(incoming_keys)
    if not incoming_set:
        return []

    existing = existing if existing is not None else existing_keys_repo.get_existing_maps_keys()
    existing_set = set(existing.prospeccao_keys or set()).union(set(existing.lead_keys or set()))

    matched = incoming_set.intersection(existing_set)
    return sorted(matched)


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen = set()
    for it in items or []:
        k = _key_from_item(it)
        if not k:
            continue
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out

# Preserve established imports used by callers and segment regression tests.
__all__ = ['_filter_noise_brinquedos', '_DRONE_NEGATIVE_CATEGORIES', '_DRONE_NOISE_NAMES', '_DRONE_POSITIVE_TERMS', '_filter_noise_drones', '_filter_noise_gamer', '_filter_city_page_results', '_filter_items_with_other_city_in_name', '_filter_strict_city', '_filter_noise_informatica', '_score_informatica_fit', '_filter_noise_mobilidade_eletrica', '_looks_like_mobilidade_person_name', '_score_mobilidade_fit', '_filter_segment_noise', '_filter_noise_sennheiser', '_score_sennheiser_fit', '_filter_large_retail', '_filter_noise_varejo_medio', '_looks_like_person_name', '_score_varejo_medio_fit', '_build_queries_for_free_text', '_build_queries_for_segments', '_looks_like_segment_or_query', '_normalize_extra', '_norm_key', '_re_sub_ignoring_case', 'SearchMapsResultsRequest', 'SearchMapsResultsResponse', 'GenerateQueriesResponse', 'generate_queries_for_segments', 'search_maps_results', 'search_maps_results_with_repo']
