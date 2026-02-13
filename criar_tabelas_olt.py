import sqlite3

conn = sqlite3.connect('isp_gestao.db')
cursor = conn.cursor()

# Tabela OLTs (opcional, mas boa para futuro)
cursor.execute('''
CREATE TABLE IF NOT EXISTS olts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    ip TEXT NOT NULL,
    modelo TEXT,
    status TEXT DEFAULT 'Online',
    ultima_atualizacao DATETIME
)
''')

# Tabela ONUs/ONTs
cursor.execute('''
CREATE TABLE IF NOT EXISTS onus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    olt_id INTEGER,
    serial TEXT UNIQUE NOT NULL,
    cliente_id INTEGER,
    status TEXT DEFAULT 'Offline',  -- Online, Offline, Provisionando, Erro
    sinal_rx REAL,
    sinal_tx REAL,
    loss INTEGER DEFAULT 0,
    ultima_atualizacao DATETIME,
    FOREIGN KEY (olt_id) REFERENCES olts(id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
)
''')

conn.commit()
conn.close()

print("Tabelas 'olts' e 'onus' criadas ou já existentes. Tudo ok!")