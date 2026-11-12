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
    # Discover by the merchant's actual Maps category, then qualify accessories.
    # Most small resellers are listed as computer stores, not as peripheral distributors.
    terms = ('loja de informática', 'informática', 'suprimentos de informática',
             'periféricos de informática', 'distribuidor de informática', 'papelaria e informática')
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
    identity = _norm_key(' '.join([name, *map(str, categories)]))
    education = bool(re.search(r'\b(faculdade|universidade|fatec|escola|cursos? de informatica|instituto de ensino)\b', identity))
    computer_merchant = any(term in identity for term in ('informatica', 'periferico', 'suprimentos de computador', 'computer store', 'computer accessories'))
    unrelated_security = any(term in evidence for term in ('portoes', 'portao', 'fornecedor de sistema de seguranca', 'automacao de portoes', 'serralheria')) and not computer_merchant
    service_only = education or unrelated_security or (any(term in evidence for term in SERVICE_TERMS) and not computer_merchant)
    exclusion_reason = 'ensino' if education else 'portões/segurança sem comércio de informática' if unrelated_security else 'serviço sem evidência de revenda' if service_only else ''
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
            'quality_notes': pending, 'contact_verified': False, 'exclusion_reason': exclusion_reason}


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


def filter_accessories_location(items, cidade, estado):
    """Use explicit location fields; company suffixes like 'Tecnologia' are not cities."""
    result = []
    from services.maps_card_parser import card_location, STREET
    target_city, target_state = _norm_key(cidade), (estado or '').upper()
    for item in items:
        city, uf = card_location(item.get('endereco') or item.get('__raw_text') or '')
        extracted = str(item.get('cidade') or '').strip()
        if not city and extracted and not item.get('location_inferred'):
            # Old scraper values sometimes contain the whole street/category: those are inconclusive.
            if not STREET.search(extracted) and not re.search(r'[\d|,]', extracted) and not re.search(r'\b(rua|avenida|loja|fornecedor)\b', extracted, re.I):
                city = extracted
        uf = uf or str(item.get('estado') or '').strip().upper()
        if city and target_city and _norm_key(city) != target_city:
            continue
        if uf and target_state and uf != target_state:
            continue
        result.append(item)
    return result
