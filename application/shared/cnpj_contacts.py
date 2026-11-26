"""Contact preparation for CNPJ autofill; never verifies WhatsApp registration."""
import re
from application.shared.phone_utils import normalize_phone

DDDS = set('11 12 13 14 15 16 17 18 19 21 22 24 27 28 31 32 33 34 35 37 38 41 42 43 44 45 46 47 48 49 51 53 54 55 61 62 63 64 65 66 67 68 69 71 73 74 75 77 79 81 82 83 84 85 86 87 88 89 91 92 93 94 95 96 97 98 99'.split())


def contact_values(raw):
    phones = []
    for part in re.split(r'[/;,]', str(raw or '')):
        digits = re.sub(r'\D', '', part)
        if digits.startswith('55') and len(digits) in (12, 13):
            digits = digits[2:]
        if len(digits) not in (10, 11) or digits[:2] not in DDDS:
            continue
        # Old mobile prefixes 8/9 are recognizable; 6/7 remain ambiguous.
        adjusted = len(digits) == 10 and digits[2] in '89'
        if adjusted:
            digits = digits[:2] + '9' + digits[2:]
        number = normalize_phone(digits)
        if any(p['numero'] == number for p in phones):
            continue
        phones.append({'numero': number, 'original': part.strip(),
                       'celular': len(digits) == 11 and digits[2] == '9',
                       'nono_digito_ajustado': adjusted})
    return {
        'telefone': phones[0]['numero'] if phones else (str(raw or '').strip() or None),
        'telefone_original': raw,
        'telefones': phones,
        'whatsapp': next((p['numero'] for p in phones if p['celular']), None),
        'whatsapp_confirmado': False,
    }
