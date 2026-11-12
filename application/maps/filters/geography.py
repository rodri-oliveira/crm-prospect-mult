from __future__ import annotations

from application.maps.text import _norm_key


def _filter_city_page_results(results: list[dict], cidade: str) -> list[dict]:
    """Remove resultados onde o nome É a própria cidade.

    Acontece quando o Google Maps retorna a página da cidade/região (ex: 'Adamantina')
    em vez de um negócio real. Filtro exato + variações comuns.
    """
    if not cidade:
        return results

    target = _norm_key(cidade)
    if not target:
        return results

    out: list[dict] = []
    for item in results or []:
        nome = _norm_key(str(item.get("nome") or ""))
        if not nome:
            out.append(item)
            continue
        # Nome IDÊNTICO à cidade → lixo (página da cidade no Maps)
        if nome == target:
            continue
        # Nome é a cidade + sufixo genérico (ex: "Adamantina - SP", "Adamantina SP")
        if nome.startswith(target) and len(nome) - len(target) < 5:
            continue
        out.append(item)

    return out

def _filter_items_with_other_city_in_name(results: list[dict], cidade: str) -> list[dict]:
    """Remove itens que declaram explicitamente outra cidade no nome.

    Ex: ao buscar em "Altair", remove "Shineray Suzano", "Shineray Ferraz de Vasconcelos" ou "Loja Zema - Casa Branca".
    """
    import re

    target_city = _norm_key(cidade)
    if not target_city:
        return results

    out: list[dict] = []
    for item in results or []:
        nome_raw = str(item.get("nome") or "").strip()
        if not nome_raw:
            out.append(item)
            continue

        norm_nome = _norm_key(nome_raw)

        # 1. Checa separadores " - Cidade", " / Cidade", " (Cidade)" ou palavra isolada de cidade no final
        m = re.search(r"[\s\-/\(]\s*([A-Za-zÀ-ÿ0-9\s]{2,40})[\)]?$", nome_raw)
        if m:
            declared_city = _norm_key(m.group(1))
            if declared_city and declared_city != target_city and target_city not in norm_nome:
                # Se declarou explicitamente outra cidade no nome e a cidade alvo não está no nome, descarte
                continue

        out.append(item)

    return out

def _filter_strict_city(results: list[dict], cidade: str, estado: str = "") -> list[dict]:
    """Remove itens que são explícitos sobre estarem em outra cidade,
    ou quando o resultado é apenas o marcador da própria cidade.
    """
    import re

    target_city = _norm_key(cidade)
    target_state = _norm_key(estado)
    if not target_city:
        return results

    out: list[dict] = []

    # Lista de siglas de estados para o regex
    estados = "AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO"

    # Regex melhorado:
    # Detecta "Cidade - UF" ou "Cidade, UF"
    city_state_re = re.compile(
        rf'([A-Za-zÀ-ÿ0-9\s\-]+)\s*[,·\-]\s*(?:{estados})\b',
        re.IGNORECASE
    )

    for item in results or []:
        nome_raw = str(item.get("nome") or "").strip()
        if not nome_raw:
            out.append(item)
            continue

        # 1. Bloqueia o marcador genérico da cidade (Ex: name="Americana")
        norm_nome = _norm_key(nome_raw)
        if norm_nome == target_city:
            continue

        # 2. Verifica se o campo cidade extraído do scraper está diferente da cidade alvo
        cidade_extraida = str(item.get("cidade") or "").strip()
        if cidade_extraida:
            cidade_extraida = re.split(r"[,·|]", cidade_extraida)[-1].strip()
            norm_cidade_extraida = _norm_key(cidade_extraida)
            if norm_cidade_extraida and norm_cidade_extraida != target_city:
                # Cidade extraída é diferente da cidade alvo - descarta
                continue

        estado_extraido = _norm_key(str(item.get("estado") or ""))
        if target_state and estado_extraido and estado_extraido != target_state:
            continue

        # 3. Fallback: Verifica se o texto bruto do card do Maps acusa uma cidade diferente
        raw_text = str(item.get("__raw_text") or "")
        if raw_text:
            matches = city_state_re.findall(raw_text)
            if matches:
                found_wrong_city = False
                for match_city in reversed(matches):
                    match_city = re.split(r"[,·|]", match_city)[-1]
                    candidate = match_city.split("·")[-1].split("|")[-1].split("-")[-1].strip()
                    candidate = _norm_key(candidate)

                    if candidate and candidate != target_city:
                        found_wrong_city = True
                        break

                if found_wrong_city:
                    continue

        # Se passou pelos filtros, mantém
        out.append(item)

    return out
