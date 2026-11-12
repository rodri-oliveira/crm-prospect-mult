"""Shared vocabulary and scheduling rules for every entry point."""
from datetime import date, time
from application.maps.text import _norm_key
from application.shared.status import STATUS_PROSPECCAO, STATUS_LEADS, RESULTADOS_INTERACAO

TERMINAL = {'Sem interesse', 'Descartado', 'Já tem consultor atendendo'}
ALLOWED = set(STATUS_PROSPECCAO + STATUS_LEADS + RESULTADOS_INTERACAO) - {'Convertido em Lead'}
ALIASES = {_norm_key(s): s for s in ALLOWED}
ALIASES.update({'agendamento': 'Pediu para retornar', 'pediu portfolio': 'Em negociação', 'negociacao': 'Em negociação'})


def canonical_status(value):
    result = ALIASES.get(_norm_key(value or ''))
    if not result:
        raise ValueError('Status ou resultado inválido.')
    return result


def validate_schedule(data, hora, required=False):
    if required and (not data or not hora):
        raise ValueError('Informe a data e o horário de retorno.')
    if hora and not data:
        raise ValueError('Informe a data para o horário de retorno.')
    try:
        if data:
            date.fromisoformat(data)
        if hora:
            time.fromisoformat(hora)
    except (ValueError, TypeError) as error:
        raise ValueError('Data ou horário de retorno inválido.') from error
