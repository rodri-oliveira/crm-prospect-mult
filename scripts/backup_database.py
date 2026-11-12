"""Consistent local SQLite backup. Run before updating an existing installation."""
import argparse
from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
from database import DB_PATH


def backup_database(source, destination):
    source, destination = Path(source), Path(destination)
    if not source.is_file():
        raise ValueError('Banco de origem não encontrado.')
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError('Escolha um destino novo, diferente do banco em uso.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)) as original:
        with closing(sqlite3.connect(destination)) as backup:
            original.backup(backup)
            if backup.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError('Falha na verificação do backup.')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=DB_PATH)
    parser.add_argument('--output', default=f'backups/crm_{datetime.now():%Y%m%d_%H%M%S}.db')
    args = parser.parse_args()
    print(backup_database(args.source, args.output))
