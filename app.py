# app.py - PostgreSQL Only Version

import os
import sys
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
import re
import psycopg
from psycopg.rows import dict_row
from psycopg.errors import UniqueViolation

# Carregar variáveis de ambiente do arquivo .env se existir
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv não está instalado, usar apenas variáveis de ambiente do sistema

# Inicializa a aplicação Flask
app = Flask(__name__, static_folder='build/static', static_url_path='/static')
# Usa SECRET_KEY do ambiente em produção; gera uma chave temporária caso não definida
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))  # Chave secreta para sessões

# Configuração de CORS
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# --- Configuração e Inicialização do Banco de Dados ---
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL não configurada. Defina a variável de ambiente.')

def get_db():
    """Abre uma nova conexão com o banco de dados PostgreSQL."""
    # Em ambientes gerenciados (ex.: Render), forçar SSL se não especificado
    db_url = DATABASE_URL
    if 'sslmode=' not in db_url and 'localhost' not in db_url and '127.0.0.1' not in db_url:
        separator = '&' if '?' in db_url else '?'
        db_url = f"{db_url}{separator}sslmode=require"
    
    conn = psycopg.connect(db_url)
    return conn

def init_db():
    """Inicializa o banco de dados PostgreSQL e cria as tabelas se não existirem."""
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()

        # Tabela de usuários para autenticação
        cur.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                tipo TEXT DEFAULT 'operador',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de clientes
        cur.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                cpf_cnpj TEXT UNIQUE,
                email TEXT,
                telefone TEXT,
                telefone_secundario TEXT,
                endereco TEXT,
                cidade TEXT,
                estado TEXT,
                cep TEXT,
                referencia TEXT,
                telefone_referencia TEXT,
                endereco_referencia TEXT,
                observacoes TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de cobranças
        cur.execute('''
            CREATE TABLE IF NOT EXISTS cobrancas (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL,
                descricao TEXT,
                valor_original DOUBLE PRECISION NOT NULL,
                valor_pago DOUBLE PRECISION DEFAULT 0,
                multa DOUBLE PRECISION DEFAULT 0,
                juros DOUBLE PRECISION DEFAULT 0,
                desconto DOUBLE PRECISION DEFAULT 0,
                valor_total DOUBLE PRECISION,
                taxa_juros DOUBLE PRECISION DEFAULT 0,
                data_vencimento DATE NOT NULL,
                data_pagamento DATE,
                status TEXT DEFAULT 'Pendente',
                forma_pagamento TEXT,
                numero_parcelas INTEGER DEFAULT 1,
                parcela_atual INTEGER DEFAULT 1,
                tipo_cobranca TEXT DEFAULT 'Única',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_cobrancas_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
        ''')

        # Adicionar coluna taxa_juros se não existir
        cur.execute('''
            ALTER TABLE cobrancas 
            ADD COLUMN IF NOT EXISTS taxa_juros DOUBLE PRECISION DEFAULT 0
        ''')

        # Tabela de histórico de pagamentos
        cur.execute('''
            CREATE TABLE IF NOT EXISTS historico_pagamentos (
                id SERIAL PRIMARY KEY,
                cobranca_id INTEGER NOT NULL,
                cliente_id INTEGER NOT NULL,
                valor_pago DOUBLE PRECISION NOT NULL,
                data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                forma_pagamento TEXT,
                observacoes TEXT,
                usuario_id INTEGER,
                CONSTRAINT fk_hist_cobranca FOREIGN KEY (cobranca_id) REFERENCES cobrancas (id) ON DELETE CASCADE,
                CONSTRAINT fk_hist_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE,
                CONSTRAINT fk_hist_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')

        # Tabela de notificações enviadas
        cur.execute('''
            CREATE TABLE IF NOT EXISTS notificacoes (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL,
                cobranca_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                mensagem TEXT,
                status TEXT DEFAULT 'Enviada',
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_notif_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE,
                CONSTRAINT fk_notif_cobranca FOREIGN KEY (cobranca_id) REFERENCES cobrancas (id) ON DELETE CASCADE
            )
        ''')


        # Tabela de configurações do sistema
        cur.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes (
                id SERIAL PRIMARY KEY,
                chave TEXT UNIQUE NOT NULL,
                valor TEXT,
                descricao TEXT
            )
        ''')

        # Inserir configurações padrão (ignora se já existir)
        default_configs = [
            ('taxa_juros_mensal', '2.0', 'Taxa de juros mensal (%)'),
            ('taxa_multa', '10.0', 'Taxa de multa por atraso (%)'),
            ('dias_tolerancia', '3', 'Dias de tolerância antes de aplicar multa'),
            ('envio_automatico', 'true', 'Ativar envio automático de notificações'),
            ('dias_aviso_vencimento', '3', 'Dias antes do vencimento para enviar aviso'),
        ]
        for chave, valor, descricao in default_configs:
            cur.execute('''
                INSERT INTO configuracoes (chave, valor, descricao)
                VALUES (%s, %s, %s)
                ON CONFLICT (chave) DO NOTHING
            ''', (chave, valor, descricao))

        conn.commit()

        # Adicionar campos de referência se não existirem (migração)
        try:
            cur.execute('ALTER TABLE clientes ADD COLUMN IF NOT EXISTS referencia TEXT')
            cur.execute('ALTER TABLE clientes ADD COLUMN IF NOT EXISTS telefone_referencia TEXT')
            cur.execute('ALTER TABLE clientes ADD COLUMN IF NOT EXISTS endereco_referencia TEXT')
            conn.commit()
        except Exception as e:
            print(f"Aviso: Erro ao adicionar campos de referência: {e}")

        # Criar usuário admin padrão se não existir
        cur.execute('SELECT id FROM usuarios WHERE email = %s', ('admin@sistema.com',))
        admin_exists = cur.fetchone()
        if not admin_exists:
            admin_senha_hash = generate_password_hash('admin123')
            cur.execute(
                'INSERT INTO usuarios (nome, email, senha, tipo) VALUES (%s, %s, %s, %s)',
                ('Administrador', 'admin@sistema.com', admin_senha_hash, 'admin')
            )
            conn.commit()

        cur.close()
        conn.close()

# --- Decoradores de Autenticação ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        if session.get('usuario_tipo') != 'admin':
            flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Funções Auxiliares ---
def calcular_valor_atualizado(cobranca):
    """Calcula o valor atualizado de uma cobrança com juros e multa."""
    if cobranca['status'] != 'Pago' and cobranca['data_vencimento']:
        # Handle both string and date object formats
        if isinstance(cobranca['data_vencimento'], str):
            data_venc = datetime.strptime(cobranca['data_vencimento'], '%Y-%m-%d')
        else:
            # It's already a date object, convert to datetime
            data_venc = datetime.combine(cobranca['data_vencimento'], datetime.min.time())
        hoje = datetime.now()
        
        if hoje > data_venc:
            dias_atraso = (hoje - data_venc).days
            
            # Buscar configurações
            conn = get_db()
            cur = conn.cursor(row_factory=dict_row)
            cur.execute('SELECT chave, valor FROM configuracoes')
            config_rows = cur.fetchall()
            config = {row['chave']: row['valor'] for row in config_rows}
            cur.close()
            conn.close()
            
            dias_tolerancia = int(config.get('dias_tolerancia', 3))
            
            if dias_atraso > dias_tolerancia:
                # Aplicar multa
                taxa_multa = float(config.get('taxa_multa', 10.0))
                multa = cobranca['valor_original'] * (taxa_multa / 100)
                
                # Aplicar juros
                taxa_juros = float(config.get('taxa_juros_mensal', 2.0))
                meses_atraso = dias_atraso / 30
                juros = cobranca['valor_original'] * (taxa_juros / 100) * meses_atraso
                
                return {
                    'multa': round(multa, 2),
                    'juros': round(juros, 2),
                    'valor_total': round(cobranca['valor_original'] + multa + juros - cobranca.get('desconto', 0), 2),
                    'dias_atraso': dias_atraso
                }
    
    return {
        'multa': 0,
        'juros': 0,
        'valor_total': cobranca['valor_original'] - cobranca.get('desconto', 0),
        'dias_atraso': 0
    }

def validar_cpf_cnpj(documento):
    """Valida CPF ou CNPJ."""
    # Remove caracteres não numéricos
    documento = re.sub(r'\D', '', documento)
    
    if len(documento) == 11:  # CPF
        # Validação simplificada do CPF
        return len(documento) == 11
    elif len(documento) == 14:  # CNPJ
        # Validação simplificada do CNPJ
        return len(documento) == 14
    
    return False

# --- Rotas de Autenticação ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        conn = get_db()
        cur = conn.cursor(row_factory=dict_row)
        cur.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
        usuario = cur.fetchone()
        cur.close()
        conn.close()
        
        if usuario and check_password_hash(usuario['senha'], senha):
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['usuario_tipo'] = usuario['tipo']
            flash(f'Bem-vindo, {usuario["nome"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha incorretos.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('login'))

# --- Rotas do Dashboard ---
@app.route('/')
@login_required
def index():
    """Renderiza o dashboard com estatísticas e lista de cobranças."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    # Estatísticas gerais
    cur.execute('SELECT COUNT(*) as count FROM clientes')
    total_clientes = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM cobrancas WHERE status = 'Pendente'")
    cobrancas_pendentes = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM cobrancas WHERE status = 'Pendente' AND data_vencimento < CURRENT_DATE")
    cobrancas_vencidas = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM cobrancas WHERE status = 'Pago'")
    cobrancas_pagas = cur.fetchone()['count']
    
    cur.execute("SELECT COALESCE(SUM(valor_total), 0) as total FROM cobrancas WHERE status = 'Pendente'")
    valor_total_pendente = cur.fetchone()['total']
    
    cur.execute("SELECT COALESCE(SUM(valor_pago), 0) as total FROM cobrancas WHERE status = 'Pago'")
    valor_total_recebido = cur.fetchone()['total']
    
    stats = {
        'total_clientes': total_clientes,
        'cobrancas_pendentes': cobrancas_pendentes,
        'cobrancas_vencidas': cobrancas_vencidas,
        'cobrancas_pagas': cobrancas_pagas,
        'valor_total_pendente': valor_total_pendente,
        'valor_total_recebido': valor_total_recebido,
    }
    
    # Cobranças recentes com informações do cliente
    cur.execute('''
        SELECT c.*, cl.nome as cliente_nome, cl.telefone, cl.email 
        FROM cobrancas c
        JOIN clientes cl ON c.cliente_id = cl.id
        WHERE c.status <> 'Pago'
        ORDER BY c.data_vencimento ASC
        LIMIT 20
    ''')
    cobrancas = cur.fetchall()
    
    # Calcular valores atualizados para cada cobrança
    cobrancas_atualizadas = []
    for cobranca in cobrancas:
        cobranca_dict = dict(cobranca)
        valores = calcular_valor_atualizado(cobranca_dict)
        cobranca_dict.update(valores)
        cobrancas_atualizadas.append(cobranca_dict)
    
    cur.close()
    conn.close()
    
    return render_template('index.html', 
                         stats=stats, 
                         cobrancas=cobrancas_atualizadas,
                         usuario=session)

# --- Rotas de Clientes ---
@app.route('/clientes')
@login_required
def listar_clientes():
    """Lista todos os clientes cadastrados."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    cur.execute('''
        SELECT 
            c.*,
            COALESCE(agg.total_cobrancas, 0) AS total_cobrancas,
            COALESCE(agg.cobrancas_pendentes, 0) AS cobrancas_pendentes,
            COALESCE(agg.valor_pendente, 0) AS valor_pendente
        FROM clientes c
        LEFT JOIN (
            SELECT 
                cliente_id,
                COUNT(id) AS total_cobrancas,
                SUM(CASE WHEN status = 'Pendente' THEN 1 ELSE 0 END) AS cobrancas_pendentes,
                SUM(CASE WHEN status = 'Pendente' THEN valor_original ELSE 0 END) AS valor_pendente
            FROM cobrancas
            GROUP BY cliente_id
        ) agg ON agg.cliente_id = c.id
        ORDER BY c.nome ASC
    ''')
    clientes = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('clientes.html', clientes=clientes)

@app.route('/api/clientes', methods=['GET'])
@login_required
def api_listar_clientes():
    """API para listar todos os clientes em formato JSON."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    cur.execute('''
        SELECT 
            c.*,
            COALESCE(agg.total_cobrancas, 0) AS total_cobrancas,
            COALESCE(agg.cobrancas_pendentes, 0) AS cobrancas_pendentes,
            COALESCE(agg.valor_pendente, 0) AS valor_pendente
        FROM clientes c
        LEFT JOIN (
            SELECT 
                cliente_id,
                COUNT(id) AS total_cobrancas,
                SUM(CASE WHEN status = 'Pendente' THEN 1 ELSE 0 END) AS cobrancas_pendentes,
                SUM(CASE WHEN status = 'Pendente' THEN valor_original ELSE 0 END) AS valor_pendente
            FROM cobrancas
            GROUP BY cliente_id
        ) agg ON agg.cliente_id = c.id
        ORDER BY c.nome ASC
    ''')
    clientes = cur.fetchall()
    cur.close()
    conn.close()
    
    # Converter para lista de dicionários
    clientes_list = []
    for cliente in clientes:
        cliente_dict = dict(cliente)
        # Converter valores decimais para float para serialização JSON
        if cliente_dict.get('valor_pendente'):
            cliente_dict['valor_pendente'] = float(cliente_dict['valor_pendente'])
        clientes_list.append(cliente_dict)
    
    return jsonify(clientes_list)

@app.route('/cliente/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_cliente():
    """Adiciona um novo cliente."""
    if request.method == 'POST':
        dados = {
            'nome': request.form['nome'],
            'cpf_cnpj': request.form.get('cpf_cnpj', ''),
            'email': request.form.get('email', ''),
            'telefone': request.form['telefone'],
            'telefone_secundario': request.form.get('telefone_secundario', ''),
            'endereco': request.form.get('endereco', ''),
            'cidade': request.form.get('cidade', ''),
            'estado': request.form.get('estado', ''),
            'cep': request.form.get('cep', ''),
            'referencia': request.form.get('referencia', ''),
            'telefone_referencia': request.form.get('telefone_referencia', ''),
            'endereco_referencia': request.form.get('endereco_referencia', ''),
            'observacoes': request.form.get('observacoes', '')
        }
        
        # Validação
        if dados['cpf_cnpj'] and not validar_cpf_cnpj(dados['cpf_cnpj']):
            flash('CPF/CNPJ inválido.', 'danger')
            return render_template('cliente_form.html', cliente=dados)
        
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO clientes (nome, cpf_cnpj, email, telefone, telefone_secundario, 
                                    endereco, cidade, estado, cep, referencia, telefone_referencia, endereco_referencia, observacoes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', tuple(dados.values()))
            conn.commit()
            flash('Cliente adicionado com sucesso!', 'success')
            return redirect(url_for('listar_clientes'))
        except UniqueViolation:
            flash('CPF/CNPJ já cadastrado.', 'danger')
        finally:
            cur.close()
            conn.close()
    
    return render_template('cliente_form.html', cliente=None)

@app.route('/cliente/<int:cliente_id>')
@login_required
def visualizar_cliente(cliente_id):
    """Visualiza detalhes de um cliente específico."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    cur.execute('SELECT * FROM clientes WHERE id = %s', (cliente_id,))
    cliente = cur.fetchone()
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('listar_clientes'))
    
    # Cobranças do cliente
    cur.execute('''
        SELECT * FROM cobrancas 
        WHERE cliente_id = %s 
        ORDER BY data_vencimento DESC
    ''', (cliente_id,))
    cobrancas = cur.fetchall()
    
    # Histórico de pagamentos
    cur.execute('''
        SELECT h.*, c.descricao as cobranca_descricao
        FROM historico_pagamentos h
        JOIN cobrancas c ON h.cobranca_id = c.id
        WHERE h.cliente_id = %s
        ORDER BY h.data_pagamento DESC
    ''', (cliente_id,))
    historico = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('cliente_detalhes.html', 
                         cliente=cliente, 
                         cobrancas=cobrancas,
                         historico=historico)

@app.route('/cliente/<int:cliente_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_cliente(cliente_id):
    """Edita um cliente existente."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    cur.execute('SELECT * FROM clientes WHERE id = %s', (cliente_id,))
    cliente = cur.fetchone()
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('listar_clientes'))
    
    if request.method == 'POST':
        dados = {
            'nome': request.form['nome'],
            'cpf_cnpj': request.form.get('cpf_cnpj', ''),
            'email': request.form.get('email', ''),
            'telefone': request.form['telefone'],
            'telefone_secundario': request.form.get('telefone_secundario', ''),
            'endereco': request.form.get('endereco', ''),
            'cidade': request.form.get('cidade', ''),
            'estado': request.form.get('estado', ''),
            'cep': request.form.get('cep', ''),
            'referencia': request.form.get('referencia', ''),
            'telefone_referencia': request.form.get('telefone_referencia', ''),
            'endereco_referencia': request.form.get('endereco_referencia', ''),
            'observacoes': request.form.get('observacoes', '')
        }
        
        # Validação
        if dados['cpf_cnpj'] and not validar_cpf_cnpj(dados['cpf_cnpj']):
            flash('CPF/CNPJ inválido.', 'danger')
            cur.close()
            conn.close()
            return render_template('cliente_form.html', cliente=dados)
        
        try:
            cur.execute('''
                UPDATE clientes 
                SET nome=%s, cpf_cnpj=%s, email=%s, telefone=%s, telefone_secundario=%s,
                    endereco=%s, cidade=%s, estado=%s, cep=%s, referencia=%s, telefone_referencia=%s, endereco_referencia=%s, observacoes=%s,
                    atualizado_em=CURRENT_TIMESTAMP
                WHERE id=%s
            ''', (dados['nome'], dados['cpf_cnpj'], dados['email'], dados['telefone'], 
                 dados['telefone_secundario'], dados['endereco'], dados['cidade'], 
                 dados['estado'], dados['cep'], dados['referencia'], dados['telefone_referencia'], dados['endereco_referencia'], dados['observacoes'], cliente_id))
            conn.commit()
            flash('Cliente atualizado com sucesso!', 'success')
            cur.close()
            conn.close()
            return redirect(url_for('listar_clientes'))
        except UniqueViolation:
            flash('CPF/CNPJ já cadastrado.', 'danger')
        finally:
            cur.close()
            conn.close()
    
    cur.close()
    conn.close()
    return render_template('cliente_form.html', cliente=cliente)

@app.route('/cliente/<int:cliente_id>/deletar', methods=['POST'])
@login_required
def deletar_cliente(cliente_id):
    """Deleta um cliente e todas suas cobranças relacionadas."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    # Verificar se o cliente existe
    cur.execute('SELECT nome FROM clientes WHERE id = %s', (cliente_id,))
    cliente = cur.fetchone()
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('listar_clientes'))
    
    try:
        # Deletar cliente (cascata deletará cobranças e histórico)
        cur.execute('DELETE FROM clientes WHERE id = %s', (cliente_id,))
        conn.commit()
        flash(f'Cliente "{cliente["nome"]}" e todas as cobranças relacionadas foram excluídos com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir cliente: {str(e)}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('listar_clientes'))

@app.route('/cobranca/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_cobranca():
    """Adiciona uma nova cobrança."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    cur.execute('SELECT id, nome FROM clientes ORDER BY nome')
    clientes = cur.fetchall()
    cur.close()
    conn.close()
    
    if request.method == 'POST':
        dados = {
            'cliente_id': int(request.form['cliente_id']),
            'descricao': request.form['descricao'],
            'valor_original': float(request.form['valor_emprestimo']),
            'taxa_juros': float(request.form['taxa_juros']),
            'valor_devido': float(request.form['valor_devido']),
            'data_vencimento': request.form['data_vencimento'],
            'tipo_cobranca': request.form.get('tipo_cobranca', 'Única'),
            'numero_parcelas': int(request.form.get('numero_parcelas', 1))
        }
        
        # Validar se a data de vencimento não é domingo
        data_venc = datetime.strptime(dados['data_vencimento'], '%Y-%m-%d')
        if data_venc.weekday() == 6:  # 6 = domingo (0=segunda, 6=domingo)
            flash('Domingos não são permitidos para data de vencimento. Selecione outro dia.', 'danger')
            return render_template('cobranca_form.html', clientes=clientes, cobranca=None)
        
        conn = get_db()
        cur = conn.cursor()
        
        # Criar cobrança(s)
        if dados['tipo_cobranca'] == 'Parcelada' and dados['numero_parcelas'] > 1:
            # Criar múltiplas cobranças para parcelamento
            valor_parcela = dados['valor_original'] / dados['numero_parcelas']
            data_base = datetime.strptime(dados['data_vencimento'], '%Y-%m-%d')
            
            for i in range(dados['numero_parcelas']):
                data_venc = data_base + timedelta(days=30 * i)
                # Calcular valor total da parcela com juros
                valor_total_parcela = valor_parcela + (valor_parcela * dados['taxa_juros'] / 100)
                
                cur.execute('''
                    INSERT INTO cobrancas (cliente_id, descricao, valor_original, taxa_juros, valor_total, data_vencimento, 
                                         tipo_cobranca, numero_parcelas, parcela_atual)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (dados['cliente_id'], 
                     f"{dados['descricao']} - Parcela {i+1}/{dados['numero_parcelas']}", 
                     valor_parcela,
                     dados['taxa_juros'],
                     valor_total_parcela,
                     data_venc.strftime('%Y-%m-%d'),
                     'Parcelada',
                     dados['numero_parcelas'],
                     i+1))
        else:
            # Cobrança única
            cur.execute('''
                INSERT INTO cobrancas (cliente_id, descricao, valor_original, taxa_juros, valor_total, data_vencimento, tipo_cobranca)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (dados['cliente_id'], dados['descricao'], dados['valor_original'], 
                 dados['taxa_juros'], dados['valor_devido'], dados['data_vencimento'], 'Única'))
        
        conn.commit()
        cur.close()
        conn.close()
        flash('Cobrança(s) adicionada(s) com sucesso!', 'success')
        return redirect(url_for('index'))
    
    return render_template('cobranca_form.html', clientes=clientes, cobranca=None)

@app.route('/cobranca/<int:cobranca_id>/cancelar', methods=['POST'])
@login_required
def cancelar_cobranca(cobranca_id):
    """Cancela uma cobrança."""
    conn = get_db()
    cur = conn.cursor()
    
    # Verificar se a cobrança existe
    cur.execute('SELECT id FROM cobrancas WHERE id = %s', (cobranca_id,))
    cobranca = cur.fetchone()
    if not cobranca:
        flash('Cobrança não encontrada.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    
    # Atualizar status para cancelada
    cur.execute('''
        UPDATE cobrancas 
        SET status='Cancelada', atualizado_em=CURRENT_TIMESTAMP
        WHERE id=%s
    ''', (cobranca_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    flash('Cobrança cancelada com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/cobranca/<int:cobranca_id>/pagar', methods=['POST'])
@login_required
def pagar_cobranca(cobranca_id):
    """Processa o pagamento de uma cobrança."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    # Buscar cobrança
    cur.execute('SELECT * FROM cobrancas WHERE id = %s', (cobranca_id,))
    cobranca = cur.fetchone()
    if not cobranca:
        flash('Cobrança não encontrada.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    
    # Obter dados do formulário
    valor_pago = float(request.form.get('valor_pago', cobranca['valor_original']))
    forma_pagamento = request.form.get('forma_pagamento', 'Dinheiro')
    observacoes = request.form.get('observacoes', '')
    
    # Calcular valores atualizados
    valores = calcular_valor_atualizado(dict(cobranca))
    valor_total = valores['valor_total']
    
    # Verificar se o valor pago é suficiente
    if valor_pago < valor_total:
        flash(f'Valor insuficiente. Valor total: R$ {valor_total:.2f}', 'warning')
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    
    # Atualizar cobrança
    cur.execute('''
        UPDATE cobrancas 
        SET status='Pago', valor_pago=%s, forma_pagamento=%s, 
            data_pagamento=CURRENT_DATE, atualizado_em=CURRENT_TIMESTAMP
        WHERE id=%s
    ''', (valor_pago, forma_pagamento, cobranca_id))
    
    # Registrar no histórico de pagamentos
    cur.execute('''
        INSERT INTO historico_pagamentos (cobranca_id, cliente_id, valor_pago, forma_pagamento, observacoes, usuario_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (cobranca_id, cobranca['cliente_id'], valor_pago, forma_pagamento, observacoes, session.get('usuario_id')))
    
    conn.commit()
    cur.close()
    conn.close()
    flash('Pagamento registrado com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/cobrancas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cobranca(id):
    """Edita uma cobrança existente."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    # Buscar cobrança
    cur.execute('SELECT * FROM cobrancas WHERE id = %s', (id,))
    cobranca = cur.fetchone()
    if not cobranca:
        flash('Cobrança não encontrada.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    
    # Buscar cliente da cobrança
    cur.execute('SELECT * FROM clientes WHERE id = %s', (cobranca['cliente_id'],))
    cliente = cur.fetchone()
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Obter novo valor do formulário
        novo_valor_devido = request.form.get('valor_devido')
        if not novo_valor_devido:
            flash('Valor devido é obrigatório.', 'danger')
            cur.close()
            conn.close()
            return render_template('cobranca_form.html', cobranca=cobranca, cliente=cliente)
        
        try:
            valor_devido_float = float(novo_valor_devido)
            if valor_devido_float <= 0:
                flash('Valor devido deve ser maior que zero.', 'danger')
                cur.close()
                conn.close()
                return render_template('cobranca_form.html', cobranca=cobranca, cliente=cliente)
        except ValueError:
            flash('Valor devido deve ser um número válido.', 'danger')
            cur.close()
            conn.close()
            return render_template('cobranca_form.html', cobranca=cobranca, cliente=cliente)
        
        # Atualizar o valor_devido na cobrança
        cur.execute('''
            UPDATE cobrancas 
            SET valor_original=%s, atualizado_em=CURRENT_TIMESTAMP
            WHERE id=%s
        ''', (valor_devido_float, id))
        
        conn.commit()
        cur.close()
        conn.close()
        flash('Cobrança atualizada com sucesso!', 'success')
        return redirect(url_for('visualizar_cliente', cliente_id=cobranca['cliente_id']))
    
    cur.close()
    conn.close()
    return render_template('cobranca_form.html', cobranca=cobranca, cliente=cliente)












# --- Rotas de Usuários ---
@app.route('/usuarios')
@login_required
@admin_required
def listar_usuarios():
    """Lista todos os usuários do sistema."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    cur.execute('SELECT * FROM usuarios ORDER BY nome')
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuario/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def adicionar_usuario():
    """Adiciona um novo usuário."""
    if request.method == 'POST':
        dados = {
            'nome': request.form['nome'],
            'email': request.form['email'],
            'senha': request.form['senha'],
            'tipo': request.form.get('tipo', 'operador')
        }
        
        conn = get_db()
        cur = conn.cursor()
        try:
            senha_hash = generate_password_hash(dados['senha'])
            cur.execute(
                'INSERT INTO usuarios (nome, email, senha, tipo) VALUES (%s, %s, %s, %s)',
                (dados['nome'], dados['email'], senha_hash, dados['tipo'])
            )
            conn.commit()
            flash('Usuário adicionado com sucesso!', 'success')
            return redirect(url_for('listar_usuarios'))
        except UniqueViolation:
            flash('Email já cadastrado.', 'danger')
        finally:
            cur.close()
            conn.close()
    
    return render_template('usuario_form.html', usuario=None)

@app.route('/usuario/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(usuario_id):
    """Edita um usuário existente."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    cur.execute('SELECT * FROM usuarios WHERE id = %s', (usuario_id,))
    usuario = cur.fetchone()
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('listar_usuarios'))
    
    if request.method == 'POST':
        dados = {
            'nome': request.form['nome'],
            'email': request.form['email'],
            'tipo': request.form.get('tipo', 'operador')
        }
        
        # Se uma nova senha foi fornecida
        if request.form.get('senha'):
            dados['senha'] = generate_password_hash(request.form['senha'])
            cur.execute(
                'UPDATE usuarios SET nome=%s, email=%s, senha=%s, tipo=%s WHERE id=%s',
                (dados['nome'], dados['email'], dados['senha'], dados['tipo'], usuario_id)
            )
        else:
            cur.execute(
                'UPDATE usuarios SET nome=%s, email=%s, tipo=%s WHERE id=%s',
                (dados['nome'], dados['email'], dados['tipo'], usuario_id)
            )
        
        conn.commit()
        cur.close()
        conn.close()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('listar_usuarios'))
    
    cur.close()
    conn.close()
    return render_template('usuario_form.html', usuario=usuario)

# --- Rotas de Configurações ---
@app.route('/configuracoes', methods=['GET', 'POST'])
@login_required
@admin_required
def configuracoes():
    """Exibe e permite editar as configurações do sistema."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    if request.method == 'POST':
        # Atualizar configurações
        configs = {
            'taxa_juros_mensal': request.form.get('taxa_juros_mensal', '2.0'),
            'taxa_multa': request.form.get('taxa_multa', '10.0'),
            'dias_tolerancia': request.form.get('dias_tolerancia', '3'),
            'envio_automatico': request.form.get('envio_automatico', 'false'),
            'dias_aviso_vencimento': request.form.get('dias_aviso_vencimento', '3')
        }
        
        for chave, valor in configs.items():
            cur.execute(
                'UPDATE configuracoes SET valor=%s WHERE chave=%s',
                (valor, chave)
            )
        
        conn.commit()
        flash('Configurações atualizadas com sucesso!', 'success')
    
    # Buscar configurações atuais
    cur.execute('SELECT chave, valor, descricao FROM configuracoes ORDER BY chave')
    configs = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('configuracoes.html', configs=configs)


# --- Rotas do Calendário ---
@app.route('/calendario')
@login_required
def calendario():
    """Renderiza a página do calendário."""
    return render_template('calendario.html')

@app.route('/api/calendario/eventos')
@login_required
def api_calendario_eventos():
    """API para buscar eventos do calendário."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    # Buscar todas as cobranças com informações do cliente
    cur.execute('''
        SELECT 
            co.id,
            co.descricao,
            co.valor_original,
            co.valor_pago,
            co.data_vencimento,
            co.data_pagamento,
            co.status,
            co.numero_parcelas,
            co.parcela_atual,
            co.tipo_cobranca,
            c.nome as cliente_nome,
            c.telefone,
            c.email
        FROM cobrancas co
        JOIN clientes c ON co.cliente_id = c.id
        ORDER BY co.data_vencimento ASC
    ''')
    
    cobrancas = cur.fetchall()
    
    # Converter para formato de eventos do calendário
    eventos = []
    for cobranca in cobrancas:
        # Calcular valores atualizados
        valores = calcular_valor_atualizado(dict(cobranca))
        
        # Determinar cor baseada no status
        if cobranca['status'] == 'Pago':
            cor = '#28a745'  # Verde
        elif cobranca['status'] == 'Pendente':
            if valores['dias_atraso'] > 0:
                cor = '#dc3545'  # Vermelho (vencida)
            else:
                cor = '#007bff'  # Azul (a pagar)
        else:
            cor = '#6c757d'  # Cinza (cancelada)
        
        evento = {
            'id': cobranca['id'],
            'title': f"{cobranca['cliente_nome']} - R$ {valores['valor_total']:.2f}",
            'start': cobranca['data_vencimento'].strftime('%Y-%m-%d'),
            'backgroundColor': cor,
            'borderColor': cor,
            'textColor': '#ffffff',
            'extendedProps': {
                'cliente_nome': cobranca['cliente_nome'],
                'cliente_telefone': cobranca['telefone'],
                'cliente_email': cobranca['email'],
                'descricao': cobranca['descricao'],
                'valor_original': float(cobranca['valor_original']),
                'valor_pago': float(cobranca['valor_pago']) if cobranca['valor_pago'] else 0,
                'valor_total': valores['valor_total'],
                'multa': valores['multa'],
                'juros': valores['juros'],
                'dias_atraso': valores['dias_atraso'],
                'status': cobranca['status'],
                'numero_parcelas': cobranca['numero_parcelas'],
                'parcela_atual': cobranca['parcela_atual'],
                'tipo_cobranca': cobranca['tipo_cobranca'],
                'data_pagamento': cobranca['data_pagamento'].strftime('%Y-%m-%d') if cobranca['data_pagamento'] else None
            }
        }
        eventos.append(evento)
    
    cur.close()
    conn.close()
    
    return jsonify(eventos)

@app.route('/api/calendario/estatisticas')
@login_required
def api_calendario_estatisticas():
    """API para buscar estatísticas do calendário."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    # Estatísticas gerais
    cur.execute("SELECT COUNT(*) as count FROM cobrancas WHERE status = 'Pago'")
    total_pagas = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM cobrancas WHERE status = 'Pendente' AND data_vencimento >= CURRENT_DATE")
    total_a_pagar = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM cobrancas WHERE status = 'Pendente' AND data_vencimento < CURRENT_DATE")
    total_vencidas = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(*) as count FROM cobrancas WHERE status = 'Cancelada'")
    total_canceladas = cur.fetchone()['count']
    
    # Valores totais
    cur.execute("SELECT COALESCE(SUM(valor_original), 0) as total FROM cobrancas WHERE status = 'Pago'")
    valor_total_pagas = cur.fetchone()['total']
    
    cur.execute("SELECT COALESCE(SUM(valor_original), 0) as total FROM cobrancas WHERE status = 'Pendente' AND data_vencimento >= CURRENT_DATE")
    valor_total_a_pagar = cur.fetchone()['total']
    
    cur.execute("SELECT COALESCE(SUM(valor_original), 0) as total FROM cobrancas WHERE status = 'Pendente' AND data_vencimento < CURRENT_DATE")
    valor_total_vencidas = cur.fetchone()['total']
    
    # Próximos vencimentos (próximos 7 dias)
    cur.execute('''
        SELECT 
            co.id,
            co.descricao,
            co.valor_original,
            co.data_vencimento,
            c.nome as cliente_nome,
            c.telefone
        FROM cobrancas co
        JOIN clientes c ON co.cliente_id = c.id
        WHERE co.status = 'Pendente' 
        AND co.data_vencimento BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
        ORDER BY co.data_vencimento ASC
        LIMIT 10
    ''')
    proximos_vencimentos = cur.fetchall()
    
    cur.close()
    conn.close()
    
    estatisticas = {
        'contadores': {
            'pagas': total_pagas,
            'a_pagar': total_a_pagar,
            'vencidas': total_vencidas,
            'canceladas': total_canceladas
        },
        'valores': {
            'pagas': float(valor_total_pagas),
            'a_pagar': float(valor_total_a_pagar),
            'vencidas': float(valor_total_vencidas)
        },
        'proximos_vencimentos': [
            {
                'id': v['id'],
                'cliente_nome': v['cliente_nome'],
                'descricao': v['descricao'],
                'valor': float(v['valor_original']),
                'data_vencimento': v['data_vencimento'].strftime('%Y-%m-%d'),
                'telefone': v['telefone']
            }
            for v in proximos_vencimentos
        ]
    }
    
    return jsonify(estatisticas)

@app.route('/api/calendario/pagar/<int:cobranca_id>', methods=['POST'])
@login_required
def api_calendario_pagar(cobranca_id):
    """API para processar pagamento via calendário."""
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    # Buscar cobrança
    cur.execute('SELECT * FROM cobrancas WHERE id = %s', (cobranca_id,))
    cobranca = cur.fetchone()
    if not cobranca:
        cur.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Cobrança não encontrada'}), 404
    
    # Obter dados do formulário
    data = request.get_json()
    valor_pago = float(data.get('valor_pago', cobranca['valor_original']))
    forma_pagamento = data.get('forma_pagamento', 'Dinheiro')
    observacoes = data.get('observacoes', '')
    
    # Calcular valores atualizados
    valores = calcular_valor_atualizado(dict(cobranca))
    valor_total = valores['valor_total']
    
    # Verificar se o valor pago é suficiente
    if valor_pago < valor_total:
        cur.close()
        conn.close()
        return jsonify({
            'success': False, 
            'message': f'Valor insuficiente. Valor total: R$ {valor_total:.2f}'
        }), 400
    
    try:
        # Atualizar cobrança
        cur.execute('''
            UPDATE cobrancas 
            SET status='Pago', valor_pago=%s, forma_pagamento=%s, 
                data_pagamento=CURRENT_DATE, atualizado_em=CURRENT_TIMESTAMP
            WHERE id=%s
        ''', (valor_pago, forma_pagamento, cobranca_id))
        
        # Registrar no histórico de pagamentos
        cur.execute('''
            INSERT INTO historico_pagamentos (cobranca_id, cliente_id, valor_pago, forma_pagamento, observacoes, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (cobranca_id, cobranca['cliente_id'], valor_pago, forma_pagamento, observacoes, session.get('usuario_id')))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Pagamento registrado com sucesso!'})
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Erro ao processar pagamento: {str(e)}'}), 500


# --- Rota "Catch-All" para servir a aplicação React ---
# Esta rota garante que qualquer URL que não seja uma rota de API 
# seja gerenciada pelo React, permitindo o roteamento no lado do cliente.
# IMPORTANTE: Esta rota deve ficar por último para não interceptar as rotas de API
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@login_required # Garante que o usuário esteja logado para carregar o app
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, '..', path)):
        return send_from_directory(os.path.join(app.static_folder, '..'), path)
    else:
        return send_from_directory(os.path.join(app.static_folder, '..'), 'index.html')


# --- Execução da Aplicação ---
if __name__ == '__main__':
    # Verificar se DATABASE_URL está configurada
    if not DATABASE_URL:
        print("❌ ERRO: Variável de ambiente DATABASE_URL não está configurada!")
        print("Configure a DATABASE_URL antes de executar o app.")
        print("Exemplo: export DATABASE_URL='postgresql://usuario:senha@localhost:5432/crm_db'")
        print("\nOu execute primeiro: python init_db.py")
        sys.exit(1)

    try:
        init_db()  # Inicializa o banco na primeira execução
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        print("Execute primeiro: python init_db.py")
        sys.exit(1)

    print("🚀 Iniciando aplicação Flask...")
    port = int(os.environ.get("PORT", 5000))  # Pega a porta do ambiente ou usa 5000 como padrão
    app.run(host='0.0.0.0', port=port, debug=True)
