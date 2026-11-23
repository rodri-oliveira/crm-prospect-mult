"""Car dealerships are prospective channels for WATTS, not confirmed electric-vehicle resellers."""
import re
from application.maps.accessories import SOUTHEAST
from application.maps.text import _norm_key

SEGMENT = 'Lojas de carros'
CAMPAIGN = 'WATTS Mobilidade Elétrica'
CAMPAIGN_NOTE = f'Oferta: {CAMPAIGN}. Interesse e viabilidade de revenda a confirmar.'


def is_car_dealer(segment):
    return _norm_key(segment or '') == _norm_key(SEGMENT)


def car_dealer_queries(cidade, estado):
    city = ' '.join((cidade or '').split()).replace('"', '')
    state = (estado or '').strip().upper()
    if not city or state not in SOUTHEAST:
        raise ValueError('Informe a cidade e selecione SP, RJ, MG ou ES.')
    # Search for the target channel, not for established WATTS partners.
    terms = ('loja de carros', 'revenda de veículos', 'loja de seminovos',
             'carros usados', 'concessionária de automóveis')
    return [{'q': f'{term} em "{city}", {state}', 'segmento': SEGMENT} for term in terms]


def campaign_note(note, segments):
    if isinstance(segments, str):
        segments = segments.split(',')
    text = note or ''
    if any(is_car_dealer(s) for s in (segments or [])) and _norm_key(CAMPAIGN) not in _norm_key(text):
        return '\n'.join(filter(None, [text, CAMPAIGN_NOTE]))
    return text


def assess_car_dealer(item):
    name = _norm_key(item.get('nome') or item.get('nome_loja') or '')
    categories = item.get('categorias') or item.get('business_categories') or []
    if isinstance(categories, str):
        categories = [categories]
    category = _norm_key(' '.join(map(str, categories)))
    raw = _norm_key(item.get('__raw_text') or '')
    identity = f'{name} {category}'
    retail_pattern = (r'\b(car dealer|used car dealer|motor vehicle dealer|'
                      r'(?:loja|revenda|revendedora|concessionaria) de (?:carros|automoveis|veiculos)|'
                      r'loja de seminovos)\b')
    retail_category = bool(re.search(retail_pattern, category or raw))
    car_name = bool(re.search(r'\b(carros|automoveis|veiculos|seminovos|semi novos|multimarcas)\b', name))
    explicit_sale = car_name and bool(re.search(r'\b(venda|revenda|comercio|concessionaria|loja)\b', name))
    education = bool(re.search(r'\b(autoescola|auto escola|escola|faculdade|universidade)\b', identity))
    services = bool(re.search(r'\b(oficina|mecanica|autopecas|auto pecas|funilaria|despachante|'
                              r'locadora|locacao|aluguel|estacionamento|lava rapido|lava jato|'
                              r'concessionaria de motos|loja de motos|bicicletaria)\b', identity))
    two_wheels = bool(re.search(r'\b(motos?|motocicletas?|motorcycle dealer|motorcycle shop|bicycle store)\b', identity))
    explicit_car_sale = explicit_sale and bool(re.search(r'\b(carros|automoveis|seminovos|semi novos|multimarcas)\b', name))
    excluded = (education or (services and not retail_category and not explicit_sale)
                or (two_wheels and not retail_category and not explicit_car_sale))
    fit = (retail_category or car_name) and not excluded
    pending = ['Confirmar venda de carros e falar com o responsável comercial',
               'Apresentar WATTS e avaliar interesse em mobilidade elétrica']
    return {'car_dealer_fit': fit, 'profile_fit': fit, 'excluded': excluded,
            'campaign': CAMPAIGN, 'contact_verified': False,
            'quality_priority': 'Priorizar revisão' if fit else 'Revisar atividade',
            'quality_notes': pending}


def filter_car_dealers(items):
    result = []
    for source in items:
        quality = assess_car_dealer(source)
        if quality['profile_fit']:
            result.append({**source, **quality})
    return result
