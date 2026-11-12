"""Parse evidence present in one result card, without guessing a city from its name."""
import re

STATES = 'AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO'
LOCATION = re.compile(rf'([^,|·\n]+?)\s*[,\-]\s*({STATES})\b(?:\s*,?\s*\d{{5}}-?\d{{3}})?\s*$', re.I)
STREET = re.compile(r'^(?:rua|r\.|avenida|av\.?|rodovia|estrada|alameda|travessa|praça)(?=\s|$)', re.I)


def card_location(text):
    for part in reversed(re.split(r'[\n|·]', text or '')):
        match = LOCATION.search(part.strip())
        if not match:
            continue
        city = match[1].rsplit(' - ', 1)[-1].strip()
        if not city or re.search(r'\d', city) or STREET.search(city) or len(city) > 60:
            continue
        return city, match[2].upper()
    return '', ''


def card_categories(text, name):
    """Return a source category only; search terms are never category evidence."""
    for raw in (text or '').splitlines():
        line = raw.split('·')[0].strip()
        if not line or line.casefold() == name.casefold():
            continue
        if not line[0].isalpha() or re.search(r'\d', line) or STREET.search(line):
            continue
        if re.match(r'^(aberto|fechado|fecha|abre|rotas|salvar|compartilhar|entrega|retirada|compras|site|telefone|patrocinado|anúncio)\b', line, re.I):
            continue
        if len(line) <= 90:
            return [line]
    return []
