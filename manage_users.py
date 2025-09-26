#!/usr/bin/env python3
"""
Script para gerenciar usuários do sistema.
Permite criar, listar e alterar senhas de usuários.
"""

import os
import sys
import getpass
from app import app, get_db
from werkzeug.security import generate_password_hash
from psycopg.rows import dict_row

def listar_usuarios():
    """Lista todos os usuários do sistema."""
    with app.app_context():
        conn = get_db()
        cur = conn.cursor(row_factory=dict_row)
        cur.execute('SELECT id, nome, email, tipo, criado_em FROM usuarios ORDER BY nome')
        usuarios = cur.fetchall()
        cur.close()
        conn.close()
        
        if not usuarios:
            print("❌ Nenhum usuário encontrado.")
            return
        
        print("👥 Usuários cadastrados:")
        print("-" * 80)
        print(f"{'ID':<3} {'Nome':<20} {'Email':<30} {'Tipo':<10} {'Criado em'}")
        print("-" * 80)
        
        for usuario in usuarios:
            data_criacao = usuario['criado_em'].strftime('%d/%m/%Y') if usuario['criado_em'] else 'N/A'
            print(f"{usuario['id']:<3} {usuario['nome']:<20} {usuario['email']:<30} {usuario['tipo']:<10} {data_criacao}")

def criar_usuario():
    """Cria um novo usuário."""
    print("\n📝 Criar novo usuário:")
    
    nome = input("Nome completo: ").strip()
    if not nome:
        print("❌ Nome é obrigatório.")
        return
    
    email = input("Email: ").strip()
    if not email:
        print("❌ Email é obrigatório.")
        return
    
    print("Tipos disponíveis: admin, gerente, operador")
    tipo = input("Tipo (admin/gerente/operador): ").strip().lower()
    if tipo not in ['admin', 'gerente', 'operador']:
        print("❌ Tipo inválido.")
        return
    
    senha = getpass.getpass("Senha: ")
    if not senha:
        print("❌ Senha é obrigatória.")
        return
    
    confirmar_senha = getpass.getpass("Confirmar senha: ")
    if senha != confirmar_senha:
        print("❌ Senhas não coincidem.")
        return
    
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        
        # Verificar se email já existe
        cur.execute('SELECT id FROM usuarios WHERE email = %s', (email,))
        existe = cur.fetchone()
        if existe:
            print("❌ Email já cadastrado.")
            cur.close()
            conn.close()
            return
        
        # Criar usuário
        senha_hash = generate_password_hash(senha)
        cur.execute(
            'INSERT INTO usuarios (nome, email, senha, tipo) VALUES (%s, %s, %s, %s)',
            (nome, email, senha_hash, tipo)
        )
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Usuário {nome} criado com sucesso!")

def alterar_senha():
    """Altera a senha de um usuário."""
    print("\n🔑 Alterar senha de usuário:")
    
    email = input("Email do usuário: ").strip()
    if not email:
        print("❌ Email é obrigatório.")
        return
    
    with app.app_context():
        conn = get_db()
        cur = conn.cursor(row_factory=dict_row)
        
        # Verificar se usuário existe
        cur.execute('SELECT id, nome FROM usuarios WHERE email = %s', (email,))
        usuario = cur.fetchone()
        if not usuario:
            print("❌ Usuário não encontrado.")
            cur.close()
            conn.close()
            return
        
        print(f"Usuário encontrado: {usuario['nome']}")
        
        nova_senha = getpass.getpass("Nova senha: ")
        if not nova_senha:
            print("❌ Senha é obrigatória.")
            cur.close()
            conn.close()
            return
        
        confirmar_senha = getpass.getpass("Confirmar nova senha: ")
        if nova_senha != confirmar_senha:
            print("❌ Senhas não coincidem.")
            cur.close()
            conn.close()
            return
        
        # Atualizar senha
        senha_hash = generate_password_hash(nova_senha)
        cur.execute('UPDATE usuarios SET senha = %s WHERE email = %s', (senha_hash, email))
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Senha alterada com sucesso para {usuario['nome']}!")

def main():
    """Menu principal."""
    if not os.getenv('DATABASE_URL'):
        print("❌ ERRO: Variável de ambiente DATABASE_URL não está configurada!")
        print("Configure a DATABASE_URL antes de executar este script.")
        sys.exit(1)
    
    while True:
        print("\n" + "="*50)
        print("🔧 GERENCIADOR DE USUÁRIOS")
        print("="*50)
        print("1. Listar usuários")
        print("2. Criar usuário")
        print("3. Alterar senha")
        print("4. Sair")
        print("-"*50)
        
        opcao = input("Escolha uma opção (1-4): ").strip()
        
        if opcao == '1':
            listar_usuarios()
        elif opcao == '2':
            criar_usuario()
        elif opcao == '3':
            alterar_senha()
        elif opcao == '4':
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida. Tente novamente.")

if __name__ == '__main__':
    main()
