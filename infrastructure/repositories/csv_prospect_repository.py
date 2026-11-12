"""Atomic CSV imports; duplicates never overwrite current commercial history."""
from contextlib import closing
from application.shared.company_identity import identity_keys
from database import get_db_connection
from application.prospeccao.import_csv import import_note
from application.maps.accessories import SEGMENT



class CsvProspectRepository:
    def import_rows(self, rows):
        added, duplicate = 0, 0
        with closing(get_db_connection()) as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            known = set()
            # Include archived prospects and converted leads: importing must not reopen them.
            for table in ('prospeccao_temp', 'leads'):
                for record in conn.execute(f'SELECT nome_loja, cidade, estado, cnpj FROM {table}'):
                    known.update(identity_keys(dict(record)))
            for row in rows:
                keys = identity_keys(row)
                if keys & known:
                    duplicate += 1
                    continue
                fields = ['nome_loja', 'cnpj', 'telefone', 'whatsapp', 'email', 'site', 'responsavel', 'endereco', 'cidade', 'estado']
                values = [row.get(field) or None for field in fields]
                conn.execute(f"INSERT INTO prospeccao_temp ({', '.join(fields)}, segmento, observacao) VALUES ({', '.join('?' for _ in range(len(fields)+2))})",
                             [*values, SEGMENT, import_note(row)])
                known.update(keys)
                added += 1
        return {'added': added, 'duplicates': duplicate}
