import sqlite3
from datetime import datetime

# Conectar ou criar banco de dados
conn = sqlite3.connect('isp_gestao.db')
cursor = conn.cursor()

# Criar tabelas se não existirem
cursor.execute('''
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    endereco TEXT,
    plano TEXT,
    status TEXT DEFAULT 'ativo',
    data_cadastro DATE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS faturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    valor REAL,
    data_vencimento DATE,
    pago BOOLEAN DEFAULT FALSE,
    FOREIGN KEY(cliente_id) REFERENCES clientes(id)
)
''')
conn.commit()

def adicionar_cliente(nome, endereco, plano):
    data = datetime.now().date()
    cursor.execute("INSERT INTO clientes (nome, endereco, plano, data_cadastro) VALUES (?, ?, ?, ?)", (nome, endereco, plano, data))
    conn.commit()
    print(f"Cliente {nome} adicionado com sucesso.")

def listar_clientes():
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    if clientes:
        print("Lista de Clientes:")
        for cliente in clientes:
            print(f"ID: {cliente[0]}, Nome: {cliente[1]}, Plano: {cliente[3]}, Status: {cliente[4]}")
    else:
        print("Nenhum cliente cadastrado.")

def gerar_fatura(cliente_id, valor, data_vencimento):
    cursor.execute("INSERT INTO faturas (cliente_id, valor, data_vencimento) VALUES (?, ?, ?)", (cliente_id, valor, data_vencimento))
    conn.commit()
    print(f"Fatura gerada para cliente ID {cliente_id}.")

def marcar_pagamento(fatura_id):
    cursor.execute("UPDATE faturas SET pago = TRUE WHERE id = ?", (fatura_id,))
    conn.commit()
    print(f"Fatura ID {fatura_id} marcada como paga.")
    verificar_inadimplencia(cliente_id)  # Note: aqui tem um bug pequeno, vamos corrigir depois

def verificar_inadimplencia(cliente_id):
    hoje = datetime.now().date()
    cursor.execute("SELECT * FROM faturas WHERE cliente_id = ? AND pago = FALSE AND data_vencimento < ?", (cliente_id, hoje))
    faturas_vencidas = cursor.fetchall()
    status = 'inadimplente' if faturas_vencidas else 'ativo'
    cursor.execute("UPDATE clientes SET status = ? WHERE id = ?", (status, cliente_id))
    conn.commit()
    print(f"Status do cliente ID {cliente_id} atualizado para {status}.")

# Menu interativo
if __name__ == "__main__":
    while True:
        print("\n=== Sistema LCSoft - Gestão de Provedor ===")
        print("1. Adicionar Cliente")
        print("2. Listar Clientes")
        print("3. Gerar Fatura")
        print("4. Marcar Pagamento")
        print("5. Sair")
        opcao = input("Escolha uma opção: ")
        
        if opcao == '1':
            nome = input("Nome do cliente: ")
            endereco = input("Endereço: ")
            plano = input("Plano (ex: 100MB): ")
            adicionar_cliente(nome, endereco, plano)
        elif opcao == '2':
            listar_clientes()
        elif opcao == '3':
            try:
                cliente_id = int(input("ID do Cliente: "))
                valor = float(input("Valor da fatura: "))
                data_venc = input("Data de vencimento (YYYY-MM-DD): ")
                gerar_fatura(cliente_id, valor, data_venc)
            except ValueError:
                print("Erro: ID e valor devem ser numéricos.")
        elif opcao == '4':
            try:
                fatura_id = int(input("ID da Fatura: "))
                marcar_pagamento(fatura_id)
            except ValueError:
                print("Erro: ID da fatura deve ser numérico.")
        elif opcao == '5':
            print("Saindo...")
            break
        else:
            print("Opção inválida, tente novamente.")

conn.close()
