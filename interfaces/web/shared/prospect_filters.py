"""Normalize GET filters and build links without losing the current selection."""
from datetime import date, timedelta
from flask import abort, url_for


FIELDS = ('nome', 'segmento', 'cidade', 'estado', 'telefone', 'tipo_telefone',
          'data_inicio', 'data_fim', 'arquivados', 'periodo')


def status_values(values):
    return list(dict.fromkeys(s.strip() for value in values
                             for s in value.split(',') if s.strip()))


def filter_context(args):
    values = {key: args.get(key, '').strip() for key in FIELDS}
    statuses = status_values(args.getlist('status'))
    values['status'] = statuses
    values['estado'] = values['estado'].upper()
    values['arquivados'] = '1' if values['arquivados'] == '1' else ''
    if not any(values.values()):
        values['data_inicio'] = values['data_fim'] = date.today().isoformat()
    for key in ('data_inicio', 'data_fim'):
        if values[key]:
            try:
                values[key] = date.fromisoformat(values[key]).isoformat()
            except ValueError:
                abort(400, description='Data inválida. Use uma data válida para filtrar.')
    if values['data_inicio'] and values['data_fim'] and values['data_inicio'] > values['data_fim']:
        abort(400, description='A data inicial deve ser anterior ou igual à data final.')
    values['periodo'] = 'todos'  # Explicit dates control the range; empty means all history.

    def filter_url(**changes):
        selection = {**values, **changes}
        return url_for('prospeccao_view', **{k: v for k, v in selection.items() if v})

    today = date.today()
    presets = [('Hoje', today, today), ('Últimos 7 dias', today - timedelta(days=6), today),
               ('Este mês', today.replace(day=1), today), ('Todo o histórico', None, None)]
    active_filters = [
        (f'{label}: {values[key]}', filter_url(**{key: ''}))
        for key, label in [('nome', 'Nome'), ('telefone', 'Telefone'), ('cidade', 'Cidade'),
                           ('estado', 'Estado'), ('segmento', 'Segmento'), ('tipo_telefone', 'Contato')]
        if values[key]
    ]
    active_filters.extend((s, filter_url(status=[v for v in statuses if v != s])) for s in statuses)
    return {
        'filtro_status': ','.join(statuses) or None, 'filtro_status_list': statuses,
        'filtro_nome': values['nome'], 'segmento': values['segmento'],
        'cidade': values['cidade'], 'estado': values['estado'],
        'telefone': values['telefone'], 'tipo_telefone': values['tipo_telefone'],
        'data_inicio': values['data_inicio'], 'data_fim': values['data_fim'],
        'mostrar_arquivados': values['arquivados'] == '1',
        'filter_url': filter_url,
        'active_filters': active_filters,
        'period_presets': [(label, filter_url(data_inicio=start.isoformat() if start else '',
                                             data_fim=end.isoformat() if end else ''))
                           for label, start, end in presets],
    }
