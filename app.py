# app.py

import os
import sys
import psycopg
from psycopg.rows import dict_row
from psycopg.errors import UniqueViolation
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
import re

# Carregar variáveis de ambiente do arquivo .env se existir
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv não está instalado, usar apenas variáveis de ambiente do sistema

# Inicializa a aplicação Flask
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Chave secreta para sessões

# --- Configuração e Inicialização do Banco de Dados ---
DATABASE_URL = os.getenv('DATABASE_URL')


class DBConnection:
    def __init__(self, connection):
        self._conn = connection

    def execute(self, sql, params=None):
        if params is None:
            params = ()
        sql = self._convert_sql(sql)
        cur = self._conn.cursor(row_factory=dict_row)
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def _convert_sql(self, sql: str) -> str:
        # Conversões simples de sintaxe SQLite -> PostgreSQL
        s = sql
        # Placeholders
        s = s.replace('?', '%s')
        # Datas/funções
        s = s.replace("date(\"now\")", 'CURRENT_DATE').replace("date('now')", 'CURRENT_DATE')
        s = s.replace("strftime('%Y-%m', data_vencimento)", "to_char(data_vencimento, 'YYYY-MM')")
        s = s.replace('date(data_vencimento)', 'data_vencimento')
        # Operadores
        s = s.replace(' != ', ' <> ')
        # Strings entre aspas duplas (padrão SQLite)
        s = s.replace('"', "'")
        return s


def get_db():
    """Abre uma nova conexão com o banco de dados PostgreSQL."""
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL não configurada. Defina a variável de ambiente para conectar ao PostgreSQL.')
    conn = psycopg.connect(DATABASE_URL)
    return DBConnection(conn)

def init_db():
    """Inicializa o banco PostgreSQL e cria as tabelas se não existirem."""
    with app.app_context():
        db = get_db()

        # Tabela de usuários para autenticação
        db.execute('''
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
        db.execute('''
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
                observacoes TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela de cobranças
        db.execute('''
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

        # Tabela de histórico de pagamentos
        db.execute('''
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
        db.execute('''
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
        db.execute('''
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
            db.execute('''
                INSERT INTO configuracoes (chave, valor, descricao)
                VALUES (%s, %s, %s)
                ON CONFLICT (chave) DO NOTHING
            ''', (chave, valor, descricao))

        db.commit()

        # Criar usuário admin padrão se não existir
        admin_exists = db.execute('SELECT id FROM usuarios WHERE email = %s', ('admin@sistema.com',)).fetchone()
        if not admin_exists:
            admin_senha_hash = generate_password_hash('admin123')
            db.execute(
                'INSERT INTO usuarios (nome, email, senha, tipo) VALUES (%s, %s, %s, %s)',
                ('Administrador', 'admin@sistema.com', admin_senha_hash, 'admin')
            )
            db.commit()

        db.close()

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
        data_venc = datetime.strptime(cobranca['data_vencimento'], '%Y-%m-%d')
        hoje = datetime.now()
        
        if hoje > data_venc:
            dias_atraso = (hoje - data_venc).days
            
            # Buscar configurações
            db = get_db()
            config_rows = db.execute('SELECT chave, valor FROM configuracoes').fetchall()
            config = {row['chave']: row['valor'] for row in config_rows}
            db.close()
            
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
        
        db = get_db()
        usuario = db.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        db.close()
        
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
    db = get_db()
    
    # Estatísticas gerais
    stats = {
        'total_clientes': db.execute('SELECT COUNT(*) as count FROM clientes').fetchone()['count'],
        'cobrancas_pendentes': db.execute("SELECT COUNT(*) as count FROM cobrancas WHERE status = 'Pendente'").fetchone()['count'],
        'cobrancas_vencidas': db.execute("SELECT COUNT(*) as count FROM cobrancas WHERE status = 'Pendente' AND data_vencimento < CURRENT_DATE").fetchone()['count'],
        'valor_total_pendente': db.execute("SELECT COALESCE(SUM(valor_original), 0) as total FROM cobrancas WHERE status = 'Pendente'").fetchone()['total'],
        'valor_total_recebido': db.execute("SELECT COALESCE(SUM(valor_pago), 0) as total FROM cobrancas WHERE status = 'Pago'").fetchone()['total'],
    }
    
    # Cobranças recentes com informações do cliente
    cobrancas = db.execute('''
        SELECT c.*, cl.nome as cliente_nome, cl.telefone, cl.email 
        FROM cobrancas c
        JOIN clientes cl ON c.cliente_id = cl.id
        WHERE c.status <> 'Pago'
        ORDER BY c.data_vencimento ASC
        LIMIT 20
    ''').fetchall()
    
    # Calcular valores atualizados para cada cobrança
    cobrancas_atualizadas = []
    for cobranca in cobrancas:
        cobranca_dict = dict(cobranca)
        valores = calcular_valor_atualizado(cobranca_dict)
        cobranca_dict.update(valores)
        cobrancas_atualizadas.append(cobranca_dict)
    
    db.close()
    
    return render_template('index.html', 
                         stats=stats, 
                         cobrancas=cobrancas_atualizadas,
                         usuario=session)

# --- Rotas de Clientes ---
@app.route('/clientes')
@login_required
def listar_clientes():
    """Lista todos os clientes cadastrados."""
    db = get_db()
    clientes = db.execute('''
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
    ''').fetchall()
    db.close()
    
    return render_template('clientes.html', clientes=clientes)

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
            'observacoes': request.form.get('observacoes', '')
        }
        
        # Validação
        if dados['cpf_cnpj'] and not validar_cpf_cnpj(dados['cpf_cnpj']):
            flash('CPF/CNPJ inválido.', 'danger')
            return render_template('cliente_form.html', cliente=dados)
        
        db = get_db()
        try:
            db.execute('''
                INSERT INTO clientes (nome, cpf_cnpj, email, telefone, telefone_secundario, 
                                    endereco, cidade, estado, cep, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', tuple(dados.values()))
            db.commit()
            flash('Cliente adicionado com sucesso!', 'success')
            return redirect(url_for('listar_clientes'))
        except UniqueViolation:
            flash('CPF/CNPJ já cadastrado.', 'danger')
        finally:
            db.close()
    
    return render_template('cliente_form.html', cliente=None)

@app.route('/cliente/<int:cliente_id>')
@login_required
def visualizar_cliente(cliente_id):
    """Visualiza detalhes de um cliente específico."""
    db = get_db()
    
    cliente = db.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,)).fetchone()
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('listar_clientes'))
    
    # Cobranças do cliente
    cobrancas = db.execute('''
        SELECT * FROM cobrancas 
        WHERE cliente_id = ? 
        ORDER BY data_vencimento DESC
    ''', (cliente_id,)).fetchall()
    
    # Histórico de pagamentos
    historico = db.execute('''
        SELECT h.*, c.descricao as cobranca_descricao
        FROM historico_pagamentos h
        JOIN cobrancas c ON h.cobranca_id = c.id
        WHERE h.cliente_id = ?
        ORDER BY h.data_pagamento DESC
    ''', (cliente_id,)).fetchall()
    
    db.close()
    
    return render_template('cliente_detalhes.html', 
                         cliente=cliente, 
                         cobrancas=cobrancas,
                         historico=historico)

@app.route('/cliente/<int:cliente_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_cliente(cliente_id):
    """Edita informações de um cliente."""
    db = get_db()
    cliente = db.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,)).fetchone()
    
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
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
            'observacoes': request.form.get('observacoes', '')
        }
        
        try:
            db.execute('''
                UPDATE clientes SET 
                    nome = ?, cpf_cnpj = ?, email = ?, telefone = ?, 
                    telefone_secundario = ?, endereco = ?, cidade = ?, 
                    estado = ?, cep = ?, observacoes = ?, 
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (*dados.values(), cliente_id))
            db.commit()
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('visualizar_cliente', cliente_id=cliente_id))
        except UniqueViolation:
            flash('CPF/CNPJ já cadastrado para outro cliente.', 'danger')
        finally:
            db.close()
    
    return render_template('cliente_form.html', cliente=dict(cliente))

# --- Rotas de Cobranças ---
@app.route('/cobranca/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_cobranca():
    """Adiciona uma nova cobrança."""
    db = get_db()
    clientes = db.execute('SELECT id, nome FROM clientes ORDER BY nome').fetchall()
    
    if request.method == 'POST':
        dados = {
            'cliente_id': int(request.form['cliente_id']),
            'descricao': request.form['descricao'],
            'valor_original': float(request.form['valor_original']),
            'data_vencimento': request.form['data_vencimento'],
            'tipo_cobranca': request.form.get('tipo_cobranca', 'Única'),
            'numero_parcelas': int(request.form.get('numero_parcelas', 1))
        }
        
        # Criar cobrança(s)
        if dados['tipo_cobranca'] == 'Parcelada' and dados['numero_parcelas'] > 1:
            # Criar múltiplas cobranças para parcelamento
            valor_parcela = dados['valor_original'] / dados['numero_parcelas']
            data_base = datetime.strptime(dados['data_vencimento'], '%Y-%m-%d')
            
            for i in range(dados['numero_parcelas']):
                data_venc = data_base + timedelta(days=30 * i)
                db.execute('''
                    INSERT INTO cobrancas (cliente_id, descricao, valor_original, data_vencimento, 
                                         tipo_cobranca, numero_parcelas, parcela_atual)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (dados['cliente_id'], 
                     f"{dados['descricao']} - Parcela {i+1}/{dados['numero_parcelas']}", 
                     valor_parcela, 
                     data_venc.strftime('%Y-%m-%d'),
                     'Parcelada',
                     dados['numero_parcelas'],
                     i+1))
        else:
            # Cobrança única
            db.execute('''
                INSERT INTO cobrancas (cliente_id, descricao, valor_original, data_vencimento, tipo_cobranca)
                VALUES (?, ?, ?, ?, ?)
            ''', (dados['cliente_id'], dados['descricao'], dados['valor_original'], 
                 dados['data_vencimento'], 'Única'))
        
        db.commit()
        db.close()
        flash('Cobrança(s) adicionada(s) com sucesso!', 'success')
        return redirect(url_for('index'))
    
    db.close()
    return render_template('cobranca_form.html', clientes=clientes, cobranca=None)

@app.route('/cobranca/<int:cobranca_id>/pagar', methods=['POST'])
@login_required
def registrar_pagamento(cobranca_id):
    """Registra o pagamento de uma cobrança."""
    db = get_db()
    cobranca = db.execute('SELECT * FROM cobrancas WHERE id = ?', (cobranca_id,)).fetchone()
    
    if not cobranca:
        flash('Cobrança não encontrada.', 'danger')
        return redirect(url_for('index'))
    
    valor_pago = float(request.form['valor_pago'])
    forma_pagamento = request.form['forma_pagamento']
    observacoes = request.form.get('observacoes', '')
    
    # Atualizar cobrança
    valores_atualizados = calcular_valor_atualizado(dict(cobranca))
    valor_total = valores_atualizados['valor_total']
    
    # Se o valor pago for maior ou igual ao total, marcar como pago
    if valor_pago >= valor_total:
        status = 'Pago'
        data_pagamento = datetime.now().strftime('%Y-%m-%d')
    else:
        status = 'Parcialmente Pago'
        data_pagamento = None
    
    db.execute('''
        UPDATE cobrancas SET 
            valor_pago = valor_pago + ?,
            multa = ?,
            juros = ?,
            valor_total = ?,
            status = ?,
            data_pagamento = ?,
            forma_pagamento = ?,
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (valor_pago, valores_atualizados['multa'], valores_atualizados['juros'], 
         valor_total, status, data_pagamento, forma_pagamento, cobranca_id))
    
    # Registrar no histórico
    db.execute('''
        INSERT INTO historico_pagamentos (cobranca_id, cliente_id, valor_pago, 
                                         forma_pagamento, observacoes, usuario_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (cobranca_id, cobranca['cliente_id'], valor_pago, forma_pagamento, 
         observacoes, session['usuario_id']))
    
    db.commit()
    db.close()
    
    flash('Pagamento registrado com sucesso!', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/cobranca/<int:cobranca_id>/cancelar', methods=['POST'])
@login_required
def cancelar_cobranca(cobranca_id):
    """Cancela uma cobrança."""
    db = get_db()
    db.execute("UPDATE cobrancas SET status = 'Cancelada' WHERE id = ?", (cobranca_id,))
    db.commit()
    db.close()
    
    flash('Cobrança cancelada com sucesso!', 'info')
    return redirect(request.referrer or url_for('index'))

# --- Rotas de Relatórios ---
@app.route('/relatorios')
@login_required
def relatorios():
    """Exibe página de relatórios."""
    db = get_db()
    
    # Relatório mensal
    relatorio_mensal = db.execute("""
        SELECT 
            to_char(data_vencimento, 'YYYY-MM') AS mes,
            COUNT(*) AS total_cobrancas,
            SUM(CASE WHEN status = 'Pago' THEN 1 ELSE 0 END) AS cobrancas_pagas,
            SUM(CASE WHEN status = 'Pago' THEN valor_pago ELSE 0 END) AS valor_recebido,
            SUM(CASE WHEN status = 'Pendente' THEN valor_original ELSE 0 END) AS valor_pendente
        FROM cobrancas
        WHERE data_vencimento >= (CURRENT_DATE - INTERVAL '12 months')
        GROUP BY mes
        ORDER BY mes DESC
    """).fetchall()
    
    # Top clientes devedores
    top_devedores = db.execute('''
        SELECT cl.nome, cl.telefone, 
               COUNT(co.id) as total_cobrancas,
               SUM(co.valor_original) as valor_total
        FROM clientes cl
        JOIN cobrancas co ON cl.id = co.cliente_id
        WHERE co.status = 'Pendente'
        GROUP BY cl.id
        ORDER BY valor_total DESC
        LIMIT 10
    ''').fetchall()
    
    db.close()
    
    return render_template('relatorios.html', 
                         relatorio_mensal=relatorio_mensal,
                         top_devedores=top_devedores)

# --- Rotas de Administração ---
@app.route('/admin/usuarios')
@admin_required
def listar_usuarios():
    """Lista todos os usuários do sistema."""
    db = get_db()
    usuarios = db.execute('SELECT * FROM usuarios ORDER BY nome').fetchall()
    db.close()
    
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/admin/usuario/adicionar', methods=['GET', 'POST'])
@admin_required
def adicionar_usuario():
    """Adiciona um novo usuário ao sistema."""
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        tipo = request.form['tipo']
        
        senha_hash = generate_password_hash(senha)
        
        db = get_db()
        try:
            db.execute('''
                INSERT INTO usuarios (nome, email, senha, tipo)
                VALUES (?, ?, ?, ?)
            ''', (nome, email, senha_hash, tipo))
            db.commit()
            flash('Usuário adicionado com sucesso!', 'success')
            return redirect(url_for('listar_usuarios'))
        except UniqueViolation:
            flash('Email já cadastrado.', 'danger')
        finally:
            db.close()
    
    return render_template('usuario_form.html', usuario=None)

@app.route('/admin/usuario/<int:usuario_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_usuario(usuario_id):
    """Edita informações de um usuário."""
    db = get_db()
    usuario = db.execute('SELECT * FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('listar_usuarios'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form.get('senha', '')
        tipo = request.form['tipo']
        
        try:
            if senha:
                # Atualizar com nova senha
                senha_hash = generate_password_hash(senha)
                db.execute('''
                    UPDATE usuarios SET nome = ?, email = ?, senha = ?, tipo = ?
                    WHERE id = ?
                ''', (nome, email, senha_hash, tipo, usuario_id))
            else:
                # Manter senha atual
                db.execute('''
                    UPDATE usuarios SET nome = ?, email = ?, tipo = ?
                    WHERE id = ?
                ''', (nome, email, tipo, usuario_id))
            
            db.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('listar_usuarios'))
        except UniqueViolation:
            flash('Email já cadastrado para outro usuário.', 'danger')
        finally:
            db.close()
    
    return render_template('usuario_form.html', usuario=dict(usuario))

@app.route('/admin/usuario/<int:usuario_id>/deletar', methods=['POST'])
@admin_required
def deletar_usuario(usuario_id):
    """Deleta um usuário do sistema."""
    if usuario_id == session.get('usuario_id'):
        flash('Você não pode deletar seu próprio usuário.', 'danger')
        return redirect(url_for('listar_usuarios'))
    
    db = get_db()
    db.execute('DELETE FROM usuarios WHERE id = ?', (usuario_id,))
    db.commit()
    db.close()
    
    flash('Usuário deletado com sucesso!', 'info')
    return redirect(url_for('listar_usuarios'))

@app.route('/cliente/<int:cliente_id>/deletar', methods=['POST'])
@login_required
def deletar_cliente(cliente_id):
    """Deleta um cliente e todas suas cobranças."""
    db = get_db()
    db.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
    db.commit()
    db.close()
    
    flash('Cliente deletado com sucesso!', 'info')
    return redirect(url_for('listar_clientes'))

@app.route('/admin/configuracoes', methods=['GET', 'POST'])
@admin_required
def configuracoes():
    """Gerencia as configurações do sistema."""
    db = get_db()
    
    if request.method == 'POST':
        for chave in request.form:
            valor = request.form[chave]
            db.execute('UPDATE configuracoes SET valor = ? WHERE chave = ?', (valor, chave))
        db.commit()
        flash('Configurações atualizadas com sucesso!', 'success')
    
    configs = db.execute('SELECT * FROM configuracoes').fetchall()
    db.close()
    
    return render_template('configuracoes.html', configs=configs)

# --- APIs para AJAX ---
@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """Retorna estatísticas do dashboard em JSON."""
    db = get_db()
    
    stats = {
        'total_clientes': db.execute('SELECT COUNT(*) as count FROM clientes').fetchone()['count'],
        'cobrancas_pendentes': db.execute("SELECT COUNT(*) as count FROM cobrancas WHERE status = 'Pendente'").fetchone()['count'],
        'cobrancas_vencidas': db.execute("SELECT COUNT(*) as count FROM cobrancas WHERE status = 'Pendente' AND data_vencimento < CURRENT_DATE").fetchone()['count'],
        'valor_total_pendente': db.execute("SELECT COALESCE(SUM(valor_original), 0) as total FROM cobrancas WHERE status = 'Pendente'").fetchone()['total'] or 0,
        'valor_total_recebido': db.execute("SELECT COALESCE(SUM(valor_pago), 0) as total FROM cobrancas WHERE status = 'Pago'").fetchone()['total'] or 0,
    }
    
    db.close()
    return jsonify(stats)

@app.route('/api/cliente/<int:cliente_id>/cobrancas')
@login_required
def api_cliente_cobrancas(cliente_id):
    """Retorna as cobranças de um cliente em JSON."""
    db = get_db()
    cobrancas = db.execute('''
        SELECT * FROM cobrancas 
        WHERE cliente_id = ? 
        ORDER BY data_vencimento DESC
    ''', (cliente_id,)).fetchall()
    db.close()
    
    return jsonify([dict(c) for c in cobrancas])

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
    app.run(debug=True)