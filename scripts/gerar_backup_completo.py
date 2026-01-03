#!/usr/bin/env python3
"""
Script para gerar backup completo de todos os dados existentes no banco de dados.
Este script lê todos os registros das tabelas principais e os grava no arquivo
finanflow_backup.jsonl no formato JSON Lines compatível com o sistema de logs.

Execute apenas uma vez para popular o arquivo de backup com dados históricos.
"""

import os
import sys
import json
from datetime import datetime, date
from psycopg.rows import dict_row

# Adicionar o diretório raiz ao path para importar o app
# Isso garante que o script encontre o app.py mesmo estando em scripts/
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Importar diretamente do arquivo app.py usando importlib
# Isso evita conflito com o pacote app/ (pasta)
import importlib.util
app_path = os.path.join(root_dir, 'app.py')

if not os.path.exists(app_path):
    raise FileNotFoundError(f"Arquivo app.py não encontrado em: {app_path}")

spec = importlib.util.spec_from_file_location('app_module', app_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

# Acessar app e get_db do módulo carregado
app = app_module.app
get_db = app_module.get_db

# Configuração do arquivo de backup (mesmo do logger_backup.py)
# Usar caminho absoluto baseado no diretório raiz
BACKUP_FILE = os.path.join(root_dir, 'finanflow_backup.jsonl')


def write_log_entry(log_data: dict):
    """
    Escreve uma entrada de log no arquivo JSON Lines.
    
    Args:
        log_data: Dicionário contendo os dados do log
    """
    try:
        # Garantir que o diretório existe
        backup_dir = os.path.dirname(BACKUP_FILE) if os.path.dirname(BACKUP_FILE) else '.'
        if backup_dir and not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        # Abrir arquivo em modo append ('a') para nunca sobrescrever histórico
        with open(BACKUP_FILE, 'a', encoding='utf-8') as f:
            # Escrever uma linha JSON por vez (formato JSON Lines)
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            f.flush()  # Garantir que os dados são escritos imediatamente
    except Exception as e:
        print(f"ERRO ao escrever log de backup: {str(e)}")


def format_timestamp(dt):
    """
    Formata um datetime ou date para string ISO format.
    
    Args:
        dt: datetime, date object ou None
        
    Returns:
        String ISO format ou None
    """
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        return dt.isoformat()
    if isinstance(dt, date):
        # Converter date para datetime para manter compatibilidade
        return datetime.combine(dt, datetime.min.time()).isoformat()
    return str(dt)


def get_timestamp_from_record(record, field_name='criado_em'):
    """
    Obtém o timestamp de um registro, usando o campo especificado ou datetime atual.
    
    Args:
        record: Dicionário com os dados do registro
        field_name: Nome do campo de timestamp (padrão: 'criado_em')
        
    Returns:
        String ISO format do timestamp
    """
    if field_name in record and record[field_name]:
        timestamp = format_timestamp(record[field_name])
        if timestamp:
            return timestamp
    return datetime.now().isoformat()


def sanitize_changes(changes: dict) -> dict:
    """
    Remove senhas e outros dados sensíveis do dicionário de mudanças.
    Também converte objetos datetime/date para strings JSON-serializáveis.
    
    Args:
        changes: Dicionário com os dados
        
    Returns:
        Dicionário sanitizado e serializável
    """
    sanitized = {}
    for key, value in changes.items():
        # Remover senhas por segurança
        if key == 'senha':
            sanitized[key] = '[REDACTED]'
        # Converter datetime/date para strings
        elif isinstance(value, (datetime, date)):
            sanitized[key] = format_timestamp(value)
        # Manter outros valores como estão
        else:
            sanitized[key] = value
    return sanitized


def backup_table(table_name: str, entity_name: str, batch_size: int = 1000):
    """
    Faz backup de uma tabela completa.
    
    Args:
        table_name: Nome da tabela no banco de dados
        entity_name: Nome da entidade para o log (ex: 'Cliente', 'Cobrança')
        batch_size: Tamanho do lote para paginação (padrão: 1000)
    """
    conn = get_db()
    cur = conn.cursor(row_factory=dict_row)
    
    try:
        # Contar total de registros
        cur.execute(f'SELECT COUNT(*) as total FROM {table_name}')
        total = cur.fetchone()['total']
        
        if total == 0:
            print(f"  ✓ {entity_name}: Nenhum registro encontrado.")
            return
        
        print(f"  → {entity_name}: {total} registro(s) encontrado(s). Processando...")
        
        # Processar em lotes para não estourar memória
        offset = 0
        processed = 0
        
        while offset < total:
            # Buscar lote de registros
            query = f'SELECT * FROM {table_name} ORDER BY id LIMIT %s OFFSET %s'
            cur.execute(query, (batch_size, offset))
            records = cur.fetchall()
            
            if not records:
                break
            
            # Processar cada registro
            for record in records:
                # Converter registro para dict (já está como dict_row, mas garantir)
                record_dict = dict(record)
                
                # Obter timestamp (usar criado_em se existir)
                timestamp = get_timestamp_from_record(record_dict)
                
                # Sanitizar dados (remover senhas, etc)
                changes = sanitize_changes(record_dict)
                
                # Criar entrada de log
                log_entry = {
                    'timestamp': timestamp,
                    'user_id': None,  # Não temos user_id para dados históricos
                    'action': 'SNAPSHOT',  # Ação especial para backup completo
                    'entity': entity_name,
                    'changes': changes,
                    'route': '/backup/complete',  # Rota fictícia para identificar backup
                    'method': 'SNAPSHOT'
                }
                
                # Escrever no arquivo
                write_log_entry(log_entry)
                processed += 1
                
                # Mostrar progresso a cada 50 registros
                if processed % 50 == 0:
                    print(f"    Processando {entity_name}: {processed}/{total}...")
            
            offset += batch_size
        
        print(f"  ✓ {entity_name}: {processed} registro(s) processado(s) com sucesso!")
        
    except Exception as e:
        print(f"  ✗ ERRO ao processar {entity_name}: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()


def main():
    """
    Função principal que executa o backup completo.
    """
    print("=" * 60)
    print("GERADOR DE BACKUP COMPLETO - FinanFlow CRM")
    print("=" * 60)
    print()
    
    # Verificar se DATABASE_URL está configurada
    if not os.getenv('DATABASE_URL'):
        print("❌ ERRO: Variável de ambiente DATABASE_URL não está configurada!")
        print("Configure a DATABASE_URL antes de executar o script.")
        sys.exit(1)
    
    # Executar dentro do contexto da aplicação Flask
    with app.app_context():
        print("📦 Iniciando backup completo...")
        print()
        
        # Lista de tabelas para fazer backup
        # Ordem importa: primeiro tabelas que não dependem de outras
        tables_to_backup = [
            ('usuarios', 'Usuário'),
            ('clientes', 'Cliente'),
            ('cobrancas', 'Cobrança'),
            ('parcelas', 'Parcela'),
            ('pagamentos', 'Pagamento'),
        ]
        
        total_tables = len(tables_to_backup)
        current_table = 0
        
        try:
            for table_name, entity_name in tables_to_backup:
                current_table += 1
                print(f"[{current_table}/{total_tables}] Processando {entity_name}...")
                backup_table(table_name, entity_name)
                print()
            
            print("=" * 60)
            print("✅ BACKUP COMPLETO FINALIZADO COM SUCESSO!")
            print("=" * 60)
            print(f"📄 Arquivo de backup: {BACKUP_FILE}")
            print()
            print("Todos os dados históricos foram exportados para o arquivo de backup.")
            print("O sistema de logs em tempo real continuará adicionando novos registros.")
            
        except Exception as e:
            print()
            print("=" * 60)
            print("❌ ERRO DURANTE O BACKUP")
            print("=" * 60)
            print(f"Erro: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()

