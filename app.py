# Topo do app.py (junto com os outros imports)
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, date
from pysnmp.hlapi import *

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_123'

# ... resto do código (def get_db_connection, rotas, etc.)

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_123'

def get_db_connection():
    conn = sqlite3.connect('isp_gestao.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clientes (já tem)
    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM clientes WHERE status = 'ativo'")
    clientes_ativos = cursor.fetchone()[0]
    
    # Inadimplência (já tem)
    cursor.execute("SELECT COUNT(*) FROM faturas WHERE pago = 0")
    faturas_pendentes = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(valor) FROM faturas WHERE pago = 0")
    valor_pendente = cursor.fetchone()[0] or 0.0
    
    # Faturamento do mês atual (já tem)
    mes_atual = datetime.now().strftime('%Y-%m')
    cursor.execute("""
        SELECT SUM(valor) FROM faturas 
        WHERE pago = 1 AND strftime('%Y-%m', data_vencimento) = ?
    """, (mes_atual,))
    faturado_mes = cursor.fetchone()[0] or 0.0
    
    # Novo: Total faturado no ano atual
    ano_atual = datetime.now().strftime('%Y')
    cursor.execute("""
        SELECT SUM(valor) FROM faturas 
        WHERE pago = 1 AND strftime('%Y', data_vencimento) = ?
    """, (ano_atual,))
    faturado_ano = cursor.fetchone()[0] or 0.0
    
    # Novo: ONUs (total e online)
    cursor.execute("SELECT COUNT(*) FROM onus")
    total_onus = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM onus WHERE status = 'Online'")
    onus_online = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM onus WHERE status = 'Offline'")
    onus_offline = cursor.fetchone()[0]
    
    # OS abertas (já tem)
    cursor.execute("SELECT COUNT(*) FROM ordens_servico WHERE status NOT IN ('Concluída', 'Cancelada')")
    os_abertas = cursor.fetchone()[0]

        # Novo: Lista de ONUs para a tabela
    onus = conn.execute('''
        SELECT o.*, c.nome AS cliente_nome 
        FROM onus o 
        LEFT JOIN clientes c ON o.cliente_id = c.id 
        ORDER BY o.serial
        LIMIT 10  -- Mostra apenas as 10 primeiras (para não sobrecarregar o dashboard)
    ''').fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                          total_clientes=total_clientes,
                          clientes_ativos=clientes_ativos,
                          faturas_pendentes=faturas_pendentes,
                          valor_pendente=valor_pendente,
                          faturado_mes=faturado_mes,
                          faturado_ano=faturado_ano,
                          total_onus=total_onus,
                          onus_online=onus_online,
                          onus_offline=onus_offline,
                          os_abertas=os_abertas)

@app.route('/relatorios')
def relatorios():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Faturas pendentes
    cursor.execute("SELECT COUNT(*), SUM(valor) FROM faturas WHERE pago = 0")
    pendentes_count, pendentes_valor = cursor.fetchone()
    pendentes_valor = pendentes_valor or 0.0
    
    # OS por status
    cursor.execute("""
        SELECT status, COUNT(*) 
        FROM ordens_servico 
        GROUP BY status
    """)
    os_por_status = cursor.fetchall()
    
    # Clientes por plano
    cursor.execute("""
        SELECT plano, COUNT(*) 
        FROM clientes 
        GROUP BY plano
    """)
    clientes_por_plano = cursor.fetchall()
    
    conn.close()
    
    return render_template('relatorios.html', 
                          pendentes_count=pendentes_count,
                          pendentes_valor=pendentes_valor,
                          os_por_status=os_por_status,
                          clientes_por_plano=clientes_por_plano)

@app.route('/clientes')
def clientes():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query segura: seleciona status_contrato só se existir
    try:
        cursor.execute('''
            SELECT id, nome, endereco, plano, email, telefone, data_cadastro, status, status_contrato 
            FROM clientes 
            ORDER BY id DESC
        ''')
    except sqlite3.OperationalError:
        # Se coluna não existir, roda sem ela
        cursor.execute('''
            SELECT id, nome, endereco, plano, email, telefone, data_cadastro, status 
            FROM clientes 
            ORDER BY id DESC
        ''')
    
    clientes = cursor.fetchall()
    conn.close()
    return render_template('clientes.html', clientes=clientes)

@app.route('/adicionar_cliente', methods=['GET', 'POST'])
def adicionar_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        endereco = request.form['endereco']
        plano = request.form['plano']
        email = request.form.get('email', '')
        telefone = request.form.get('telefone', '')
        status = request.form.get('status', 'ativo')
        status_contrato = request.form.get('status_contrato', 'ativo')
        
        if not nome:
            flash('Nome obrigatório!', 'danger')
            return redirect(url_for('adicionar_cliente'))
        
        data = datetime.now().date()
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO clientes (nome, endereco, plano, email, telefone, status, status_contrato, data_cadastro) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nome, endereco, plano, email, telefone, status, status_contrato, data))
        conn.commit()
        conn.close()
        
        flash('Cliente adicionado!', 'success')
        return redirect(url_for('clientes'))
    
    return render_template('adicionar_cliente.html')

# Mostrar formulário de edição preenchido
@app.route('/editar_cliente/<int:cliente_id>', methods=['GET'])
def editar_cliente(cliente_id):
    conn = get_db_connection()
    cliente = conn.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,)).fetchone()
    conn.close()
    
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('clientes'))
    
    return render_template('editar_cliente.html', cliente=cliente)


# Salvar alterações do cliente
@app.route('/editar_cliente/<int:cliente_id>', methods=['POST'])
def atualizar_cliente(cliente_id):
    nome = request.form['nome']
    endereco = request.form['endereco']
    plano = request.form['plano']
    email = request.form.get('email', '')
    telefone = request.form.get('telefone', '')
    status = request.form.get('status', 'ativo')
    status_contrato = request.form.get('status_contrato', 'ativo')
    
    if not nome:
        flash('Nome obrigatório!', 'danger')
        return redirect(url_for('editar_cliente', cliente_id=cliente_id))
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE clientes 
        SET nome = ?, endereco = ?, plano = ?, email = ?, telefone = ?, status = ?, status_contrato = ?
        WHERE id = ?
    ''', (nome, endereco, plano, email, telefone, status, status_contrato, cliente_id))
    
    conn.commit()
    conn.close()
    
    flash('Cliente atualizado com sucesso!', 'success')
    return redirect(url_for('clientes'))

# Excluir cliente

@app.route('/excluir_cliente/<int:cliente_id>', methods=['POST'])
def excluir_cliente(cliente_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verifica se o cliente existe
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
    cliente = cursor.fetchone()
    
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        conn.close()
        return redirect(url_for('clientes'))
    
    # Verifica se o cliente tem faturas ou OS vinculadas (opcional - pode remover se quiser permitir exclusão sempre)
    cursor.execute("SELECT COUNT(*) FROM faturas WHERE cliente_id = ?", (cliente_id,))
    faturas_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM ordens_servico WHERE cliente_id = ?", (cliente_id,))
    os_count = cursor.fetchone()[0]
    
    if faturas_count > 0 or os_count > 0:
        flash(f'Não é possível excluir. Cliente possui {faturas_count} fatura(s) e {os_count} OS.', 'warning')
        conn.close()
        return redirect(url_for('clientes'))
    
    # Exclui o cliente
    conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()
    
    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('clientes'))

# Novo: Listar faturas
@app.route('/faturas')
def faturas():
    conn = get_db_connection()
    faturas = conn.execute('''
        SELECT f.*, c.nome 
        FROM faturas f 
        JOIN clientes c ON f.cliente_id = c.id 
        ORDER BY f.data_vencimento DESC
    ''').fetchall()
    conn.close()
    return render_template('faturas.html', faturas=faturas)

# Novo: Gerar fatura
@app.route('/gerar_fatura', methods=['GET', 'POST'])
def gerar_fatura():
    conn = get_db_connection()
    clientes = conn.execute('SELECT id, nome FROM clientes').fetchall()
    
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        valor = request.form['valor']
        data_vencimento = request.form['data_vencimento']
        
        try:
            valor = float(valor)
            conn.execute('INSERT INTO faturas (cliente_id, valor, data_vencimento) VALUES (?, ?, ?)',
                         (cliente_id, valor, data_vencimento))
            conn.commit()
            flash('Fatura gerada com sucesso!', 'success')
            return redirect(url_for('faturas'))
        except ValueError:
            flash('Valor inválido!', 'danger')
    
    conn.close()
    return render_template('gerar_fatura.html', clientes=clientes)

# Novo: Marcar pagamento
@app.route('/marcar_pago/<int:fatura_id>')
def marcar_pago(fatura_id):
    conn = get_db_connection()
    conn.execute('UPDATE faturas SET pago = 1 WHERE id = ?', (fatura_id,))
    conn.commit()
    
    # Atualizar status do cliente se necessário
    cursor = conn.cursor()
    cursor.execute('SELECT cliente_id FROM faturas WHERE id = ?', (fatura_id,))
    cliente_id = cursor.fetchone()['cliente_id']
    
    hoje = date.today()
    cursor.execute("""
        SELECT COUNT(*) FROM faturas 
        WHERE cliente_id = ? AND pago = 0 AND data_vencimento < ?
    """, (cliente_id, hoje))
    vencidas = cusrsor.fetchone()[0]
    
    status = 'inadimplente' if vencidas > 0 else 'ativo'
    conn.execute('UPDATE clientes SET status = ? WHERE id = ?', (status, cliente_id))
    conn.commit()
    conn.close()
    
    flash('Pagamento marcado! Status atualizado.', 'success')
    return redirect(url_for('faturas'))
      
@app.route('/busca')
def busca_global():
    termo = request.args.get('q', '').strip()
    if not termo:
        flash('Digite algo para buscar.', 'warning')
        return redirect(url_for('index'))

    conn = get_db_connection()
    
    # Busca em clientes (mais campos: nome, endereço, plano, serial ONU)
    clientes = conn.execute('''
        SELECT c.*, o.serial AS onu_serial 
        FROM clientes c 
        LEFT JOIN onus o ON o.cliente_id = c.id
        WHERE c.nome LIKE ? OR c.endereco LIKE ? OR c.plano LIKE ? OR c.id = ? OR o.serial LIKE ?
    ''', (f'%{termo}%', f'%{termo}%', f'%{termo}%', termo if termo.isdigit() else 0, f'%{termo}%')).fetchall()
    
    # Busca em OS (por tipo, status, cliente nome)
    os_list = conn.execute('''
        SELECT os.*, c.nome 
        FROM ordens_servico os 
        JOIN clientes c ON os.cliente_id = c.id 
        WHERE os.tipo_os LIKE ? OR os.status LIKE ? OR c.nome LIKE ?
    ''', (f'%{termo}%', f'%{termo}%', f'%{termo}%')).fetchall()
    
    # Busca em faturas (por cliente nome, valor, vencimento)
    faturas = conn.execute('''
        SELECT f.*, c.nome 
        FROM faturas f 
        JOIN clientes c ON f.cliente_id = c.id 
        WHERE c.nome LIKE ? OR f.valor LIKE ? OR f.data_vencimento LIKE ?
    ''', (f'%{termo}%', f'%{termo}%', f'%{termo}%')).fetchall()
    
    # Busca em ONUs (serial, sinal, loss, cliente nome)
    onus = conn.execute('''
        SELECT o.*, c.nome AS cliente_nome 
        FROM onus o 
        LEFT JOIN clientes c ON o.cliente_id = c.id 
        WHERE o.serial LIKE ? OR o.status LIKE ? OR c.nome LIKE ? OR o.sinal_rx LIKE ? OR o.loss LIKE ?
    ''', (f'%{termo}%', f'%{termo}%', f'%{termo}%', f'%{termo}%', f'%{termo}%')).fetchall()

    conn.close()
    
    return render_template('busca_resultados.html', 
                          termo=termo, 
                          clientes=clientes, 
                          os_list=os_list, 
                          faturas=faturas, 
                          onus=onus)

# Formulário para criar nova OS
@app.route('/nova_os', methods=['GET', 'POST'])
def nova_os():
    conn = get_db_connection()
    clientes = conn.execute('SELECT id, nome FROM clientes ORDER BY nome').fetchall()
    
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        tipo_os = request.form.get('tipo_os')
        descricao = request.form.get('descricao')
        data_agendamento = request.form.get('data_agendamento') or None
        tecnico = request.form.get('tecnico')
        
        if not cliente_id or not tipo_os:
            flash('Cliente e Tipo de OS são obrigatórios!', 'danger')
            return redirect(url_for('nova_os'))
        
        data_abertura = datetime.now().date()
        
        conn.execute('''
            INSERT INTO ordens_servico 
            (cliente_id, tipo_os, descricao, data_abertura, data_agendamento, tecnico_responsavel)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cliente_id, tipo_os, descricao, data_abertura, data_agendamento, tecnico))
        
        conn.commit()
        conn.close()
        
        flash('Ordem de Serviço criada com sucesso!', 'success')
        return redirect(url_for('ordens_servico'))
    
    conn.close()
    return render_template('nova_os.html', clientes=clientes)

# Ver detalhes de uma OS específica
@app.route('/ver_os/<int:os_id>')
def ver_os(os_id):
    conn = get_db_connection()
    os_data = conn.execute('''
        SELECT os.*, c.nome 
        FROM ordens_servico os 
        JOIN clientes c ON os.cliente_id = c.id 
        WHERE os.id = ?
    ''', (os_id,)).fetchone()
    
    if not os_data:
        flash('Ordem de Serviço não encontrada.', 'danger')
        return redirect(url_for('ordens_servico'))
    
    conn.close()
    return render_template('ver_os.html', os=os_data)


# Atualizar status da OS
@app.route('/atualizar_status_os/<int:os_id>', methods=['POST'])
def atualizar_status_os(os_id):
    novo_status = request.form.get('status')
    observacoes = request.form.get('observacoes', '')
    data_conclusao = None
    
    # Se for concluída ou cancelada, registra a data de conclusão
    if novo_status in ['Concluída', 'Cancelada']:
        data_conclusao = datetime.now().date()
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE ordens_servico 
        SET status = ?, observacoes = ?, data_conclusao = ?
        WHERE id = ?
    ''', (novo_status, observacoes, data_conclusao, os_id))
    
    conn.commit()
    conn.close()
    
    flash(f'Status atualizado para "{novo_status}" com sucesso!', 'success')
    return redirect(url_for('ver_os', os_id=os_id))


# Provisionamento (lista de ONUs)
@app.route('/provisionamento')
def provisionamento():
    conn = get_db_connection()
    onus = conn.execute('''
        SELECT o.*, c.nome AS cliente_nome 
        FROM onus o 
        LEFT JOIN clientes c ON o.cliente_id = c.id 
        ORDER BY o.serial
    ''').fetchall()
    conn.close()
    return render_template('provisionamento.html', onus=onus)


@app.route('/provisionar_onu/<int:onu_id>', methods=['POST'])
def provisionar_onu(onu_id):
    conn = get_db_connection()
    conn.execute("UPDATE onus SET status = 'Provisionando' WHERE id = ?", (onu_id,))
    conn.commit()
    conn.close()
    flash('ONU enviada para provisionamento (simulado)!', 'success')
    return redirect(url_for('provisionamento'))

# OLT config (change to your real data)
# Configuração real da sua OLT Huawei
OLT_CONFIG = {
    'name': 'OLT-Huawei',
    'host': '181.189.80.14',                # IP da OLT
    'telnet_port': 2338,
    'telnet_user': 'smartoltusr',
    'telnet_pass': 'cloudfiber2023',
    'snmp_community_ro': 'iKu6y{Mk7xjm',    # Read-only (para leitura de status)
    'snmp_community_rw': 'ex9oh0^VcgvM',    # Read-write (se precisar alterar algo)
    'snmp_port': 2340,
    'version': '2c',                        # SNMP v2c (padrão Huawei)
}

@app.route('/olt_dashboard')
def olt_dashboard():
    online = 0
    offline = 0
    com_loss = 0
    error_msg = None

    try:
        session = Session(hostname=OLT_CONFIG['host'], 
                          community=OLT_CONFIG['snmp_community_ro'], 
                          version=2,
                          timeout=5,
                          retries=3)

        # OID exemplo Huawei para nome da OLT (teste básico)
        sysname = session.get('1.3.6.1.2.1.1.5.0').value

        # Placeholder para ONUs (substitua com OIDs reais)
        # online = int(session.get('OID_ONLINE_COUNT').value or 0)
        # total = int(session.get('OID_TOTAL_ONUS').value or 0)
        # offline = total - online
        # com_loss = int(session.get('OID_LOSS_COUNT').value or 0)

        # Teste com valores simulados
        online = 145
        total = 150
        offline = total - online
        com_loss = 5

    except Exception as e:
        error_msg = f'Erro ao consultar OLT: {str(e)}'

    if error_msg:
        flash(error_msg, 'danger')

    return render_template('olt_dashboard.html', 
                          online=online, 
                          offline=offline, 
                          com_loss=com_loss,
                          olt_name=OLT_CONFIG['name'],
                          sysname=sysname if 'sysname' in locals() else 'N/A')
                          
if __name__ == '__main__':
    app.run(debug=True)