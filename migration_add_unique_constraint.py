import os
import sys
from app import app, get_db
from dotenv import load_dotenv
import psycopg
from psycopg.errors import UniqueViolation, ProgrammingError

def apply_migration():
    print('Iniciando migração: Adicionando restrição UNIQUE (cpf_cnpj) à tabela clientes...')
    load_dotenv()

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('ERRO: DATABASE_URL não encontrada. Configure o .env')
        sys.exit(1)

    try:
        with app.app_context():
            conn = get_db()
            cur = conn.cursor()
            
            # Verificar se a restrição já existe
            cur.execute("""
                SELECT 1 
                FROM pg_constraint 
                WHERE conname = 'clientes_cpf_cnpj_key' 
                AND conrelid = 'clientes'::regclass
            """)
            constraint_exists = cur.fetchone()
            
            if constraint_exists:
                print('AVISO: A restrição \'clientes_cpf_cnpj_key\' já existe. Nenhuma ação necessária.')
                cur.close()
                conn.close()
                return
            
            # Verificar se existem valores duplicados antes de adicionar a restrição
            cur.execute("""
                SELECT cpf_cnpj, COUNT(*) as count 
                FROM clientes 
                GROUP BY cpf_cnpj 
                HAVING COUNT(*) > 1
            """)
            duplicates = cur.fetchall()
            
            if duplicates:
                print('ERRO: Existem valores duplicados na coluna cpf_cnpj:')
                for dup in duplicates:
                    print(f"  - CPF/CNPJ: {dup[0]} (aparece {dup[1]} vezes)")
                print('\nPor favor, remova ou corrija os valores duplicados antes de executar esta migração.')
                cur.close()
                conn.close()
                sys.exit(1)
            
            # Este é o comando SQL que adiciona a restrição que falta
            sql_command = 'ALTER TABLE clientes ADD CONSTRAINT clientes_cpf_cnpj_key UNIQUE (cpf_cnpj);'
            print(f'Executando: {sql_command}')
            
            cur.execute(sql_command)
            conn.commit()
            
            print('SUCESSO: Restrição UNIQUE (cpf_cnpj) adicionada com sucesso!')
            
            cur.close()
            conn.close()
    except ProgrammingError as e:
        # Verificar se é erro de constraint já existe (código de erro PostgreSQL 42710)
        if 'already exists' in str(e).lower() or '42710' in str(e):
            print(f'AVISO: A restrição \'clientes_cpf_cnpj_key\' já existe. Nenhuma ação necessária.')
            print(f'Detalhes: {e}')
        else:
            # Re-raise se for outro tipo de ProgrammingError
            raise
    except UniqueViolation as e:
        print(f'ERRO: Não foi possível adicionar a restrição devido a valores duplicados existentes.')
        print(f'Detalhes: {e}')
        print('\nPor favor, remova ou corrija os valores duplicados antes de executar esta migração.')
        sys.exit(1)
    except Exception as e:
        print(f'ERRO ao aplicar migração: {e}')
        print('Se o erro for sobre valores duplicados, você deve limpá-los manualmente antes de executar esta migração.')
        sys.exit(1)
    finally:
        print('Script de migração concluído.')

if __name__ == '__main__':
    apply_migration()

