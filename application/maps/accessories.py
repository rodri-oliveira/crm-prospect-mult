"""Focused, free prospecting for computer-accessory resellers in Southeast Brazil."""
from urllib.parse import urlsplit
import re
from application.maps.text import _norm_key

SOUTHEAST = ('SP', 'RJ', 'MG', 'ES')
SEGMENT = 'Acessórios de informática'
RETAIL_TERMS = ('informatica', 'periferico', 'acessorios de computador', 'suprimentos', 'computer store', 'computer accessories', 'hardware', 'mouse', 'teclado', 'headset', 'webcam')
SERVICE_TERMS = ('software', 'provedor de internet', 'desenvolvimento de sistemas', 'curso de informatica', 'consultoria de ti', 'conserto de celular')


def is_accessories(segment):
    return _norm_key(segment) == _norm_key(SEGMENT)


def accessories_queries(cidade, estado):
    cidade = ' '.join((cidade or '').split()).replace('"', '')
    estado = (estado or '').strip().upper()
    if not cidade or estado not in SOUTHEAST:
        raise ValueError('Informe a cidade e selecione SP, RJ, MG ou ES.')
    # Small local batches; no brand or computer-only searches.
    terms = ('loja de acessórios de informática', 'distribuidor de periféricos de informática',
             'revenda de suprimentos de informática', 'loja de informática mouse teclado headset')
    return [{'q': f'{term} em "{cidade}", {estado}', 'segmento': SEGMENT} for term in terms]


def safe_website(value):
    value = str(value or '').strip()
    if not value:
        return ''
    if re.match(r'^[a-z][a-z0-9+.-]*:', value, re.I) and not re.match(r'^https?://', value, re.I):
        return ''
    if any(c.isspace() for c in value):
        return ''
    if '://' not in value:
        value = 'https://' + value
    try:
        parsed = urlsplit(value)
        _ = parsed.port  # Reject malformed ports.
        return value if parsed.scheme in ('http', 'https') and parsed.hostname and not parsed.username and not any(c in value for c in ('"', '<', '>', '\n', '\r')) else ''
    except ValueError:
        return ''


def assess_accessories(item):
    """A transparent completeness heuristic, never proof of buyer intent or valid WhatsApp."""
    name = _norm_key(item.get('nome') or item.get('nome_loja') or '')
    # query_sources and assigned search segments are NOT evidence of business activity.
    categories = item.get('categorias') or item.get('business_categories') or []
    if isinstance(categories, str):
        categories = [categories]
    evidence = _norm_key(' '.join([name, str(item.get('__raw_text') or ''), *map(str, categories)]))
    fit = any(term in evidence for term in RETAIL_TERMS)
    service_only = any(term in evidence for term in SERVICE_TERMS) and not fit
    phone = ''.join(c for c in str(item.get('telefone') or item.get('whatsapp') or '') if c.isdigit())
    if phone.startswith('55') and len(phone) in (12, 13):
        phone = phone[2:]
    contact = len(phone) in (10, 11) or bool(safe_website(item.get('website') or item.get('site')))
    pending = []
    if not fit:
        pending.append('Confirmar venda de acessórios')
    if not contact:
        pending.append('Conferir canal de contato')
    if not item.get('endereco'):
        pending.append('Conferir endereço')
    pending.append('Confirmar atividade, comprador e telefone antes da abordagem')
    return {'accessories_fit': fit, 'service_only': service_only,
            'quality_priority': 'Priorizar revisão' if fit and contact else 'Revisar dados',
            'quality_notes': pending, 'contact_verified': False}


def filter_accessories(items):
    result = []
    for original in items:
        item = dict(original)
        quality = assess_accessories(item)
        if quality['service_only']:
            continue
        item.update(quality)
        result.append(item)
    return sorted(result, key=lambda item: (not item['accessories_fit'], item['quality_priority'] != 'Priorizar revisão'))
