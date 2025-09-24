# app.py - PostgreSQL Only Version

import os
import sys
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
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
app = Flask(__name__)
# Usa SECRET_KEY do ambiente em produção; gera uma chave temporária caso não definida
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))  # Chave secreta para sessões

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

        # Tabela de dívidas
        cur.execute('''
            CREATE TABLE IF NOT EXISTS dividas (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL,
                descricao TEXT NOT NULL,
                valor_original DOUBLE PRECISION NOT NULL,
                valor_atualizado DOUBLE PRECISION NOT NULL,
                data_vencimento DATE NOT NULL,
                data_inadimplencia DATE,
                dias_atraso INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Em Aberto',
                tipo_divida TEXT DEFAULT 'Comercial',
                origem TEXT,
                observacoes TEXT,
                prioridade TEXT DEFAULT 'Média',
                responsavel_cobranca TEXT,
                ultimo_contato DATE,
                proxima_acao DATE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_dividas_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
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
    
    cur.execute("SELECT COALESCE(SUM(valor_original), 0) as total FROM cobrancas WHERE status = 'Pendente'")
    valor_total_pendente = cur.fetchone()['total']
    
    cur.execute("SELECT COALESCE(SUM(valor_pago), 0) as total FROM cobrancas WHERE status = 'Pago'")
    valor_total_recebido = cur.fetchone()['total']
    
    stats = {
        'total_clientes': total_clientes,
        'cobrancas_pendentes': cobrancas_pendentes,
        'cobrancas_vencidas': cobrancas_vencidas,
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
