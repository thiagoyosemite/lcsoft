import sqlite3
from datetime import datetime

conn = sqlite3.connect('isp_gestao.db')
cursor = conn.cursor()

# Exemplo 1: ONU Online vinculada a cliente 1
cursor.execute('''
INSERT OR IGNORE INTO onus (serial, cliente_id, status, sinal_rx, sinal_tx, loss, ultima_atualizacao)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', ('ZTEGC12345678', 1, 'Online', -18.5, 2.3, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

# Exemplo 2: ONU Offline com loss
cursor.execute('''
INSERT OR IGNORE INTO onus (serial, cliente_id, status, sinal_rx, sinal_tx, loss, ultima_atualizacao)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', ('HWTC98765432', 2, 'Offline', -35.0, 1.0, 12, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

# Exemplo 3: ONU Provisionando sem cliente
cursor.execute('''
INSERT OR IGNORE INTO onus (serial, status, sinal_rx, sinal_tx, loss, ultima_atualizacao)
VALUES (?, ?, ?, ?, ?, ?)
''', ('FHTT00000001', 'Provisionando', -22.1, 1.8, 3, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

conn.commit()
conn.close()
print("3 ONUs de teste adicionadas!")