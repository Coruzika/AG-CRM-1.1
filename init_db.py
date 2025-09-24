#!/usr/bin/env python3
"""
Script para inicializar o banco de dados PostgreSQL.
Execute este script antes de rodar o app.py pela primeira vez.
"""

import os
import sys
from app import app, init_db, get_db
from werkzeug.security import generate_password_hash
from urllib.parse import urlparse
import psycopg
from psycopg import sql

def ensure_database_exists(database_url: str):
    """Garante que o banco de dados especificado na DATABASE_URL exista (cria se não existir)."""
    parsed = urlparse(database_url)
    dbname = (parsed.path or '').lstrip('/')
    if not dbname:
        raise RuntimeError('DATABASE_URL inválida: nome do banco ausente.')

    # Conecta no banco "postgres" para checar/criar o alvo
    admin_dsn = parsed._replace(path='/postgres').geturl()
    try:
        with psycopg.connect(admin_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
                exists = cur.fetchone()
                if not exists:
                    print(f"Criando banco de dados '{dbname}'...")
                    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
                    print(f"Banco de dados '{dbname}' criado.")
    except Exception as e:
        raise RuntimeError(f"Falha ao verificar/criar o banco '{dbname}': {e}") from e

def main():
    """Inicializa o banco de dados."""
    print("Inicializando banco de dados PostgreSQL...")
    
    # Verificar se DATABASE_URL está configurada
    if not os.getenv('DATABASE_URL'):
        print("ERRO: Variável de ambiente DATABASE_URL não está configurada!")
        print("Configure a DATABASE_URL antes de executar este script.")
        print("Windows PowerShell: $env:DATABASE_URL='postgresql://usuario:senha@localhost:5432/crm_db'")
        print("Linux/macOS (bash): export DATABASE_URL='postgresql://usuario:senha@localhost:5432/crm_db'")
        sys.exit(1)
    
    try:
        # Garante que o banco alvo exista antes de criar tabelas
        ensure_database_exists(os.getenv('DATABASE_URL') or '')

        with app.app_context():
            init_db()
            
            # Criar usuários adicionais se não existirem
            db = get_db()
            
            # Lista de usuários padrão
            usuarios_padrao = [
                {
                    'nome': 'Administrador',
                    'email': 'admin@sistema.com',
                    'senha': 'admin123',
                    'tipo': 'admin'
                },
                {
                    'nome': 'João Silva',
                    'email': 'joao.operador@sistema.com',
                    'senha': 'operador123',
                    'tipo': 'operador'
                },
                {
                    'nome': 'Maria Santos',
                    'email': 'maria.gerente@sistema.com',
                    'senha': 'gerente123',
                    'tipo': 'gerente'
                }
            ]
            
            usuarios_criados = []
            for usuario in usuarios_padrao:
                # Verificar se usuário já existe
                existe = db.execute('SELECT id FROM usuarios WHERE email = %s', (usuario['email'],)).fetchone()
                if not existe:
                    senha_hash = generate_password_hash(usuario['senha'])
                    db.execute(
                        'INSERT INTO usuarios (nome, email, senha, tipo) VALUES (%s, %s, %s, %s)',
                        (usuario['nome'], usuario['email'], senha_hash, usuario['tipo'])
                    )
                    usuarios_criados.append(usuario)
            
            db.commit()
            db.close()
            
            print("✅ Banco de dados inicializado com sucesso!")
            print("📊 Tabelas criadas:")
            print("   - usuarios")
            print("   - clientes") 
            print("   - cobrancas")
            print("   - historico_pagamentos")
            print("   - notificacoes")
            print("   - configuracoes")
            
            if usuarios_criados:
                print(f"\n👥 {len(usuarios_criados)} usuário(s) criado(s):")
                for usuario in usuarios_criados:
                    print(f"   📧 {usuario['email']} | 🔑 {usuario['senha']} | 👤 {usuario['tipo']}")
            else:
                print("\n👥 Usuários já existem no banco de dados.")
            
            print("\n🚀 Agora você pode executar: python app.py")
            
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        print("\nVerifique se:")
        print("1. O PostgreSQL está rodando")
        print("2. A DATABASE_URL está correta")
        print("3. O usuário tem permissões para criar tabelas")
        sys.exit(1)

if __name__ == '__main__':
    main()
