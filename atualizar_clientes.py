import sqlite3

conn = sqlite3.connect('isp_gestao.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE clientes ADD COLUMN email TEXT")
    cursor.execute("ALTER TABLE clientes ADD COLUMN telefone TEXT")
    print("Colunas 'email' e 'telefone' adicionadas à tabela clientes!")
except sqlite3.OperationalError as e:
    print("Colunas já existem ou erro:", e)

conn.commit()
conn.close()