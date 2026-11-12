import sqlite3
import os

DB_PATH = os.environ.get('CRM_DATABASE_PATH') or os.path.join(os.path.dirname(__file__), 'database.db')

def get_db_connection(path=None):
    """All runtime connections enforce relationships before any transaction."""
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Tabela leads
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_loja TEXT NOT NULL,
            cnpj TEXT,
            telefone TEXT,
            whatsapp TEXT,
            email TEXT,
            cidade TEXT,
            estado TEXT,
            endereco TEXT,
            responsavel TEXT,
            status TEXT DEFAULT 'Novo Lead',
            observacoes TEXT,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute("PRAGMA table_info(leads)")
    lead_cols = [row[1] for row in c.fetchall()]
    if 'maps_place_id' not in lead_cols:
        c.execute('ALTER TABLE leads ADD COLUMN maps_place_id TEXT')
    if 'maps_url' not in lead_cols:
        c.execute('ALTER TABLE leads ADD COLUMN maps_url TEXT')
    if 'site' not in lead_cols:
        c.execute('ALTER TABLE leads ADD COLUMN site TEXT')
    if 'responsavel' not in lead_cols:
        c.execute('ALTER TABLE leads ADD COLUMN responsavel TEXT')
    if 'email' not in lead_cols:
        c.execute('ALTER TABLE leads ADD COLUMN email TEXT')

    # Tabela segmentos_loja
    c.execute('''
        CREATE TABLE IF NOT EXISTS segmentos_loja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            segmento TEXT NOT NULL,
            FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
        )
    ''')

    # Tabela contatos
    c.execute('''
        CREATE TABLE IF NOT EXISTS contatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            data DATETIME DEFAULT CURRENT_TIMESTAMP,
            tipo_contato TEXT NOT NULL,
            resultado TEXT,
            observacao TEXT,
            FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
        )
    ''')

    c.execute("PRAGMA table_info(contatos)")
    contato_cols = [row[1] for row in c.fetchall()]
    if 'data_retorno' not in contato_cols:
        c.execute('ALTER TABLE contatos ADD COLUMN data_retorno DATE')
    if 'hora_retorno' not in contato_cols:
        c.execute('ALTER TABLE contatos ADD COLUMN hora_retorno TIME')
    if 'retorno_encerrado' not in contato_cols:
        c.execute('ALTER TABLE contatos ADD COLUMN retorno_encerrado INTEGER NOT NULL DEFAULT 0')

    # Tabela prospeccao_temp
    c.execute('''
        CREATE TABLE IF NOT EXISTS prospeccao_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_loja TEXT NOT NULL,
            cnpj TEXT,
            telefone TEXT,
            whatsapp TEXT,
            email TEXT,
            site TEXT,
            responsavel TEXT,
            endereco TEXT,
            cidade TEXT,
            estado TEXT,
            segmento TEXT,
            status_prospeccao TEXT DEFAULT 'Não contatado',
            observacao TEXT,
            data_retorno DATE,
            data_prospeccao DATE DEFAULT CURRENT_DATE,
            arquivado BOOLEAN DEFAULT 0,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            convertido_lead_id INTEGER,
            maps_url TEXT,
            maps_place_id TEXT,
            FOREIGN KEY(convertido_lead_id) REFERENCES leads(id)
        )
    ''')

    c.execute("PRAGMA table_info(prospeccao_temp)")
    cols = [row[1] for row in c.fetchall()]

    # Colunas faltantes na prospeccao_temp
    for col in ['responsavel', 'email', 'site', 'maps_url', 'maps_place_id', 'cnpj',
                'data_primeiro_agendamento', 'tentativas_retorno', 'data_ultima_tentativa',
                'hora_retorno']:
        if col not in cols:
            type_str = 'TEXT'
            if col == 'tentativas_retorno': type_str = 'INTEGER DEFAULT 0'
            elif col in ['data_primeiro_agendamento', 'data_ultima_tentativa']: type_str = 'DATE'
            elif col == 'hora_retorno': type_str = 'TIME'
            c.execute(f'ALTER TABLE prospeccao_temp ADD COLUMN {col} {type_str}')

    # updated_at: registra o momento exato da última tabulação (status, agendamento, draft)
    if 'updated_at' not in cols:
        c.execute('ALTER TABLE prospeccao_temp ADD COLUMN updated_at DATETIME')

    c.execute('''
        CREATE TABLE IF NOT EXISTS prospeccao_eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospeccao_id INTEGER NOT NULL,
            data_evento DATETIME DEFAULT CURRENT_TIMESTAMP,
            tipo_evento TEXT NOT NULL,
            detalhe TEXT,
            data_retorno_antes DATE,
            data_retorno_depois DATE,
            FOREIGN KEY(prospeccao_id) REFERENCES prospeccao_temp(id) ON DELETE CASCADE
        )
    ''')

    # Additive migration: preserve existing clients and sales.
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL REFERENCES leads(id),
        data_pedido DATE NOT NULL, numero_pedido TEXT,
        valor_total NUMERIC NOT NULL CHECK(valor_total >= 0),
        status_faturamento TEXT NOT NULL DEFAULT 'Faturado',
        data_proximo_contato DATE, observacoes TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pedido_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
        familia TEXT, codigo_produto TEXT, descricao TEXT NOT NULL,
        quantidade INTEGER NOT NULL CHECK(quantidade > 0),
        preco_unitario NUMERIC NOT NULL CHECK(preco_unitario >= 0),
        preco_total NUMERIC NOT NULL CHECK(preco_total >= 0)
    )''')
    for name, table, columns in [
        ('idx_contatos_lead_data', 'contatos', 'lead_id, data'),
        ('idx_eventos_prospeccao_data', 'prospeccao_eventos', 'prospeccao_id, data_evento'),
        ('idx_prospeccao_retorno', 'prospeccao_temp', 'arquivado, data_retorno'),
        ('idx_pedidos_lead', 'pedidos', 'lead_id'),
        ('idx_pedido_itens_pedido', 'pedido_itens', 'pedido_id'),
    ]:
        c.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
