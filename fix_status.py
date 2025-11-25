import os
import sys
from app import app, get_db
from psycopg.rows import dict_row

def corrigir_parcelas():
    print('--- Iniciando correção de status das parcelas ---')
    
    with app.app_context():
        conn = get_db()
        cur = conn.cursor(row_factory=dict_row)
        
        # Busca parcelas pendentes que têm algum valor pago
        cur.execute("""
            SELECT * FROM parcelas 
            WHERE status != 'Pago' AND valor_pago > 0
        """)
        parcelas = cur.fetchall()
        
        corrigidas = 0
        
        for p in parcelas:
            valor_devido = p['valor'] + (p['multa_manual'] or 0)
            valor_pago = p['valor_pago'] or 0
            
            # Verifica se já está pago (com margem de tolerância de 5 centavos para erros de arredondamento)
            if valor_pago >= (valor_devido - 0.05):
                print(f"Corrigindo Parcela ID {p['id']}: Pago R${valor_pago} / Devido R${valor_devido}")
                
                # Atualiza status para Pago
                cur.execute("""
                    UPDATE parcelas 
                    SET status = 'Pago', atualizado_em = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (p['id'],))
                
                # Verifica se a cobrança pai deve ser quitada também
                cobranca_id = p['cobranca_id']
                cur.execute("""
                    SELECT COUNT(*) as total, 
                           SUM(CASE WHEN status = 'Pago' THEN 1 ELSE 0 END) as pagas 
                    FROM parcelas 
                    WHERE cobranca_id = %s
                """, (cobranca_id,))
                status_geral = cur.fetchone()
                
                # Se agora todas estão pagas (considerando a que acabamos de atualizar + 1)
                # Nota: o SELECT acima pode ainda não ver o update atual dependendo da transação, 
                # então forçamos a verificação
                if status_geral['total'] == (status_geral['pagas'] + 1):
                    cur.execute("""
                        UPDATE cobrancas 
                        SET status = 'Pago', data_pagamento = CURRENT_DATE, atualizado_em = CURRENT_TIMESTAMP 
                        WHERE id = %s
                    """, (cobranca_id,))
                    print(f"-> Cobrança {cobranca_id} também foi quitada automaticamente.")
                
                corrigidas += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        print('------------------------------------------------')
        print(f"Concluído! Total de parcelas corrigidas: {corrigidas}")

if __name__ == '__main__':
    corrigir_parcelas()