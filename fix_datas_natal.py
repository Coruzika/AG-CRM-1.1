#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Migração: Corrige datas de vencimento de parcelas que caem em datas bloqueadas.

Este script:
1. Busca todas as parcelas com status 'Pendente'
2. Verifica se alguma parcela cai nas datas proibidas:
   - Domingos (weekday == 6)
   - 24 de Dezembro
   - 25 de Dezembro
   - 31 de Dezembro
   - 01 de Janeiro
3. Se encontrar, calcula a nova data válida (usando a mesma lógica de pular dias)
4. Atualiza o banco de dados
5. Gera logs no terminal mostrando quais IDs foram alterados e para qual data
"""

import os
import sys
from datetime import datetime, timedelta, date
import psycopg
from psycopg.rows import dict_row

# Carregar variáveis de ambiente do arquivo .env se existir
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv não está instalado, usar apenas variáveis de ambiente do sistema

# Configuração do banco de dados
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ ERRO: Variável de ambiente DATABASE_URL não está configurada!")
    print("Configure a DATABASE_URL antes de executar o script.")
    sys.exit(1)

def is_data_bloqueada(data_obj):
    """
    Retorna True se a data for Domingo ou feriado de fim de ano bloqueado.
    Datas bloqueadas: Domingos, 24/12, 25/12, 31/12, 01/01.
    """
    # Garante que estamos trabalhando com objeto date
    if isinstance(data_obj, datetime):
        d = data_obj.date()
    else:
        d = data_obj

    # 1. Bloquear Domingos (6)
    if d.weekday() == 6:
        return True
    
    # 2. Bloquear Festas de Fim de Ano
    if (d.month == 12 and d.day in [24, 25, 31]) or \
       (d.month == 1 and d.day == 1):
        return True
        
    return False

def get_proximo_dia_util(data_obj):
    """
    Recebe uma data e retorna a próxima data válida (não bloqueada).
    Se a data for bloqueada, adiciona +1 dia e verifica novamente em loop
    até encontrar uma data válida.
    
    Datas bloqueadas: Domingos (weekday == 6), 24/12, 25/12, 31/12, 01/01.
    
    Args:
        data_obj: datetime ou date object
        
    Returns:
        date: Próxima data válida
    """
    # Garante que estamos trabalhando com objeto date
    if isinstance(data_obj, datetime):
        d = data_obj.date()
    else:
        d = data_obj
    
    # Loop até encontrar uma data válida
    while is_data_bloqueada(d):
        d += timedelta(days=1)
    
    return d

def get_db():
    """Abre uma nova conexão com o banco de dados PostgreSQL."""
    # Em ambientes gerenciados (ex.: Render), forçar SSL se não especificado
    db_url = DATABASE_URL
    if 'sslmode=' not in db_url and 'localhost' not in db_url and '127.0.0.1' not in db_url:
        separator = '&' if '?' in db_url else '?'
        db_url = f"{db_url}{separator}sslmode=require"
    
    conn = psycopg.connect(db_url)
    return conn

def corrigir_datas_parcelas():
    """
    Função principal que corrige as datas de vencimento das parcelas pendentes
    que caem em datas bloqueadas.
    """
    print("=" * 70)
    print("SCRIPT DE CORREÇÃO DE DATAS BLOQUEADAS")
    print("=" * 70)
    print()
    
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    try:
        # Buscar todas as parcelas com status 'Pendente'
        print("🔍 Buscando parcelas pendentes...")
        cur.execute("""
            SELECT id, cobranca_id, numero_parcela, data_vencimento, status
            FROM parcelas 
            WHERE status = 'Pendente'
            ORDER BY data_vencimento ASC
        """)
        parcelas = cur.fetchall()
        
        print(f"✅ Encontradas {len(parcelas)} parcelas pendentes.")
        print()
        
        # Lista para armazenar as correções
        correcoes = []
        
        # Verificar cada parcela
        print("🔍 Verificando datas bloqueadas...")
        for parcela in parcelas:
            data_vencimento = parcela['data_vencimento']
            
            # Garante que é um objeto date
            if isinstance(data_vencimento, datetime):
                data_venc = data_vencimento.date()
            else:
                data_venc = data_vencimento
            
            # Verifica se a data está bloqueada
            if is_data_bloqueada(data_venc):
                # Calcula a nova data válida
                nova_data = get_proximo_dia_util(data_venc)
                
                correcoes.append({
                    'id': parcela['id'],
                    'cobranca_id': parcela['cobranca_id'],
                    'numero_parcela': parcela['numero_parcela'],
                    'data_antiga': data_venc,
                    'data_nova': nova_data
                })
        
        if not correcoes:
            print("✅ Nenhuma parcela encontrada com data bloqueada. Tudo certo!")
            cur.close()
            conn.close()
            return
        
        print(f"⚠️  Encontradas {len(correcoes)} parcelas com datas bloqueadas.")
        print()
        print("=" * 70)
        print("CORREÇÕES A SEREM APLICADAS:")
        print("=" * 70)
        
        # Mostrar as correções que serão aplicadas
        for correcao in correcoes:
            print(f"Parcela ID {correcao['id']} (Cobrança {correcao['cobranca_id']}, Parcela #{correcao['numero_parcela']}):")
            print(f"  ❌ Data antiga: {correcao['data_antiga'].strftime('%d/%m/%Y')} ({correcao['data_antiga'].strftime('%A')})")
            print(f"  ✅ Data nova:   {correcao['data_nova'].strftime('%d/%m/%Y')} ({correcao['data_nova'].strftime('%A')})")
            print()
        
        # Confirmar antes de aplicar
        print("=" * 70)
        resposta = input("Deseja aplicar essas correções? (s/N): ").strip().lower()
        
        if resposta not in ['s', 'sim', 'y', 'yes']:
            print("❌ Operação cancelada pelo usuário.")
            cur.close()
            conn.close()
            return
        
        print()
        print("🔄 Aplicando correções...")
        
        # Aplicar as correções
        alteradas = 0
        for correcao in correcoes:
            try:
                # Atualizar a parcela
                cur.execute("""
                    UPDATE parcelas 
                    SET data_vencimento = %s, atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (correcao['data_nova'], correcao['id']))
                
                alteradas += 1
                print(f"✅ Parcela ID {correcao['id']} atualizada: {correcao['data_antiga'].strftime('%d/%m/%Y')} → {correcao['data_nova'].strftime('%d/%m/%Y')}")
                
            except Exception as e:
                print(f"❌ Erro ao atualizar parcela ID {correcao['id']}: {str(e)}")
        
        # Commit das alterações
        conn.commit()
        
        print()
        print("=" * 70)
        print(f"✅ CORREÇÃO CONCLUÍDA!")
        print(f"   Total de parcelas corrigidas: {alteradas}")
        print("=" * 70)
        
    except Exception as e:
        conn.rollback()
        print()
        print("=" * 70)
        print(f"❌ ERRO durante a execução: {str(e)}")
        print("=" * 70)
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    try:
        corrigir_datas_parcelas()
    except KeyboardInterrupt:
        print("\n\n❌ Operação interrompida pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {str(e)}")
        sys.exit(1)

