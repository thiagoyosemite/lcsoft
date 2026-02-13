import sqlite3

conn = sqlite3.connect('isp_gestao.db')
cursor = conn.cursor()

# Apaga todos os registros
cursor.execute("DELETE FROM clientes")
cursor.execute("DELETE FROM faturas")
cursor.execute("DELETE FROM ordens_servico")
cursor.execute("DELETE FROM onus")

# Reseta os autoincrementos (opcional)
cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('clientes', 'faturas', 'ordens_servico', 'onus')")

conn.commit()
conn.close()
print("Banco de dados limpo! Todos os registros foram apagados.")