"""Conservative company identity; shared phone numbers do not merge branches."""
from application.maps.text import _norm_key


def identity_keys(row):
    keys = set()
    cnpj = ''.join(c for c in str(row.get('cnpj') or '') if c.isdigit())
    if cnpj:
        keys.add(('cnpj', cnpj))
    if row.get('maps_place_id'):
        keys.add(('maps', str(row['maps_place_id']).strip()))
    if all(row.get(key) for key in ('nome_loja', 'cidade', 'estado')):
        keys.add(('name', *(_norm_key(row[key]) for key in ('nome_loja', 'cidade', 'estado'))))
    return keys
