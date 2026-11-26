"""One predicate for both the prospect list and its counters."""
from __future__ import annotations

import unicodedata


def search_text(value) -> str:
    text = unicodedata.normalize('NFKD', str(value or '').casefold())
    return ''.join(c for c in text if not unicodedata.combining(c))


def phone_digits(value) -> str:
    digits = ''.join(c for c in str(value or '') if c in '0123456789')
    return digits[2:] if digits.startswith('55') and len(digits) > 11 else digits


def register_filter_functions(conn):
    conn.create_function('crm_text', 1, search_text, deterministic=True)
    conn.create_function('crm_phone', 1, phone_digits, deterministic=True)


def filter_where(*, status=None, nome=None, segmento=None, cidade=None,
                 estado=None, telefone=None, data_inicio=None, data_fim=None,
                 mostrar_arquivados=False, tipo_telefone=None):
    parts, params = [], []
    if not mostrar_arquivados:
        parts.append('COALESCE(arquivado, 0) = 0')
    statuses = list(dict.fromkeys(s.strip() for s in (status or '').split(',') if s.strip()))
    if statuses:
        parts.append('status_prospeccao IN (' + ','.join('?' for _ in statuses) + ')')
        params.extend(statuses)
    else:
        # Scheduled prospects have their own queue. An explicit status search can find them.
        parts.append("(data_retorno IS NULL OR data_retorno = '')")
    for token in search_text(nome).split():
        parts.append("instr(replace(crm_text(COALESCE(nome_loja, '') || ' ' || COALESCE(responsavel, '')), ' ', ''), ?) > 0")
        params.append(token)
    for column, value in [('segmento', segmento), ('cidade', cidade)]:
        if value and value.strip():
            parts.append(f'instr(crm_text({column}), ?) > 0')
            params.append(search_text(value.strip()))
    if estado and estado.strip():
        parts.append('upper(trim(estado)) = ?')
        params.append(estado.strip().upper())
    if telefone and telefone.strip():
        digits = phone_digits(telefone)
        if digits:
            parts.append('(instr(crm_phone(telefone), ?) > 0 OR instr(crm_phone(whatsapp), ?) > 0)')
            params.extend([digits, digits])
        else:
            parts.append('0 = 1')  # Invalid input must not accidentally return every contact.
    if tipo_telefone in ('Fixo', 'Celular'):
        test = "IN ('2', '3', '4', '5')" if tipo_telefone == 'Fixo' else "= '9'"
        parts.append('(' + ' OR '.join(
            f'(length(crm_phone({col})) IN (10, 11) AND substr(crm_phone({col}), 3, 1) {test})'
            for col in ('telefone', 'whatsapp')) + ')')
    elif tipo_telefone == 'Sem telefone':
        parts.append("(crm_phone(telefone) = '' AND crm_phone(whatsapp) = '')")
    if data_inicio:
        parts.append('date(data_prospeccao) >= date(?)')
        params.append(data_inicio)
    if data_fim:
        parts.append('date(data_prospeccao) <= date(?)')
        params.append(data_fim)
    return ' AND '.join(parts) or '1=1', params
