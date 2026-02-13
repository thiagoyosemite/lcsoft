# criar_tabela_os.py
import sqlite3

conn = sqlite3.connect('isp_gestao.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS ordens_servico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    tipo_os TEXT NOT NULL,
    descricao TEXT,
    status TEXT DEFAULT 'Aberta',
    data_abertura DATE NOT NULL,
    data_agendamento DATE,
    tecnico_responsavel TEXT,
    observacoes TEXT,
    data_conclusao DATE,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
)
''')

conn.commit()
conn.close()
print("Tabela criada!")