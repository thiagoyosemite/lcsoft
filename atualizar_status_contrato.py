import sqlite3

conn = sqlite3.connect('isp_gestao.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE clientes ADD COLUMN status_contrato TEXT DEFAULT 'ativo'")
    print("Coluna 'status_contrato' adicionada com sucesso!")
except sqlite3.OperationalError as e:
    print("Coluna já existe ou erro:", e)

conn.commit()
conn.close()