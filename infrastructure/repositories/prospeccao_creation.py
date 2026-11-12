"""One insertion path for manual prospects and Google Maps selections."""
from contextlib import closing
from database import get_db_connection
from application.shared.company_identity import identity_keys
from application.shared.workflow import canonical_status, TERMINAL


def add_prospect(dados: dict, db_path) -> tuple[int, bool]:
    if not (dados.get('nome_loja') or '').strip():
        raise ValueError('Informe o nome da loja.')
    status = canonical_status(dados.get('status_prospeccao') or 'Não contatado')
    incoming = identity_keys(dados)
    with closing(get_db_connection(db_path)) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        for record in conn.execute('SELECT id, nome_loja, cidade, estado, cnpj, maps_place_id FROM prospeccao_temp'):
            if incoming & identity_keys(dict(record)):
                # Importing or collecting again must not erase decisions, notes or appointments.
                return record['id'], False
        for record in conn.execute('SELECT nome_loja, cidade, estado, cnpj, maps_place_id FROM leads'):
            if incoming & identity_keys(dict(record)):
                raise ValueError('Esta loja já está cadastrada em Leads.')
        fields = ['nome_loja','cnpj','telefone','whatsapp','endereco','cidade','estado','segmento',
                  'maps_place_id','maps_url','site','responsavel','email']
        values = [(dados.get(field) or '').strip() or None for field in fields]
        note = dados.get('observacoes') or dados.get('observacao') or None
        retorno = dados.get('data_retorno') if status not in TERMINAL else None
        hora = dados.get('hora_retorno') if retorno else None
        cursor = conn.execute(
            f"INSERT INTO prospeccao_temp ({', '.join(fields)}, status_prospeccao, observacao, data_retorno, hora_retorno) "
            f"VALUES ({', '.join('?' for _ in range(len(fields)+4))})",
            [*values, status, note, retorno, hora],
        )
        pid = cursor.lastrowid
        if status != 'Não contatado':
            conn.execute('INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe) VALUES (?, ?, ?)',
                         (pid, 'STATUS_CHANGE', status + (f' | {note}' if note else '')))
        return pid, True
