"""Bounded CSV preview and validation. No requests to paid or external services."""
import csv
from datetime import datetime, timezone
from io import StringIO
import re
from application.maps.accessories import SOUTHEAST, assess_accessories, safe_website
from application.maps.text import _norm_key
from application.shared.cnpj_utils import is_valid_cnpj, normalize_cnpj
from application.shared.phone_utils import normalize_phone

MAX_ROWS = 500
MAX_BYTES = 1_000_000
ALIASES = {'nome': 'nome_loja', 'loja': 'nome_loja', 'empresa': 'nome_loja', 'uf': 'estado',
           'site': 'site', 'website': 'site', 'observacoes': 'observacoes', 'observacao': 'observacoes',
           'fone': 'telefone', 'fonte': 'fonte', 'url_fonte': 'url_fonte'}
FIELDS = {'nome_loja', 'cidade', 'estado', 'telefone', 'whatsapp', 'cnpj', 'email', 'site',
          'endereco', 'responsavel', 'observacoes', 'fonte', 'url_fonte'}


def preview_csv(raw):
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError('Envie um CSV de até 1 MB e 500 contatos.')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('cp1252')
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=',;\t')
        reader = csv.DictReader(StringIO(text), dialect=dialect)
        headers = [ALIASES.get(_norm_key(h).replace(' ', '_'), _norm_key(h).replace(' ', '_')) for h in (reader.fieldnames or [])]
        if not {'nome_loja', 'cidade', 'estado'} <= set(headers) or len(headers) != len(set(headers)):
            raise ValueError('Cabeçalho obrigatório: nome_loja, cidade, estado. Não repita colunas.')
        reader.fieldnames = headers
        rows = []
        for number, source in enumerate(reader, 2):
            if len(rows) >= MAX_ROWS:
                raise ValueError('Máximo de 500 contatos por arquivo.')
            if None in source:
                raise ValueError(f'Linha {number}: número de colunas diferente do cabeçalho.')
            row = {k: (source.get(k) or '').strip() for k in FIELDS}
            errors = []
            if any(len(value) > 500 for value in row.values()):
                errors.append('Campo maior que 500 caracteres')
                row = {k: v[:500] for k, v in row.items()}
            row['estado'] = row['estado'].upper()
            if not row['nome_loja'] or not row['cidade']:
                errors.append('Nome e cidade obrigatórios')
            if row['estado'] not in SOUTHEAST:
                errors.append('UF fora do Sudeste (SP, RJ, MG, ES)')
            if row['cnpj']:
                row['cnpj'] = normalize_cnpj(row['cnpj'])
                if not is_valid_cnpj(row['cnpj']):
                    errors.append('CNPJ inválido')
            for field in ('telefone', 'whatsapp'):
                value = re.sub(r'\D', '', row[field])
                if value.startswith('55') and len(value) in (12, 13):
                    value = value[2:]
                if value and (len(value) not in (10, 11) or value[:2] == '00'):
                    errors.append(f'{field}: informe DDD e número')
                row[field] = normalize_phone(row[field]) or ''
            if row['email'] and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', row['email']):
                errors.append('E-mail com formato inválido')
            for field in ('site', 'url_fonte'):
                original = row[field]
                row[field] = safe_website(original)
                if original and not row[field]:
                    errors.append(f'{field}: URL inválida')
            if not any(row[k] for k in ('telefone', 'whatsapp', 'email', 'site')):
                errors.append('Informe ao menos um canal de contato')
            quality = assess_accessories(row)
            if quality['service_only']:
                errors.append('Atividade de serviço sem evidência de revenda de acessórios')
            rows.append({'line': number, 'data': row, 'errors': errors, 'quality': quality})
        if not rows:
            raise ValueError('O arquivo não contém contatos.')
        return rows
    except (csv.Error, UnicodeError) as error:
        raise ValueError('CSV inválido. Use UTF-8 e separador vírgula ou ponto e vírgula.') from error


def import_note(row):
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    source = row.get('fonte') or 'Lista informada pelo usuário'
    return '\n'.join(filter(None, [row.get('observacoes'), f'Importado em {stamp}. Fonte: {source}',
                                  row.get('url_fonte'), 'Revisão pendente: confirmar acessórios, comprador e contato.']))
