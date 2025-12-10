from app import app, get_db
from datetime import date
from psycopg.rows import dict_row

def corrigir_datas_festivas():
    print("--- Iniciando correção de datas festivas ---")
    
    with app.app_context():
        conn = get_db()
        cur = conn.cursor(row_factory=dict_row)
        
        # Busca todas as parcelas pendentes
        cur.execute("SELECT id, data_vencimento FROM parcelas WHERE status = 'Pendente'")
        parcelas = cur.fetchall()
        
        alteradas = 0
        
        for p in parcelas:
            data_orig = p['data_vencimento']
            nova_data = None
            
            # Regra para Natal (24 e 25 -> 26)
            if data_orig.month == 12 and data_orig.day in [24, 25]:
                nova_data = date(data_orig.year, 12, 26)
            
            # Regra para Ano Novo (31/12 -> 02/01 do próximo ano)
            elif data_orig.month == 12 and data_orig.day == 31:
                nova_data = date(data_orig.year + 1, 1, 2)
                
            # Regra para Ano Novo (01/01 -> 02/01 do mesmo ano)
            elif data_orig.month == 1 and data_orig.day == 1:
                nova_data = date(data_orig.year, 1, 2)
            
            # Se encontrou uma data para corrigir
            if nova_data:
                print(f"Parcela {p['id']}: Mudando de {data_orig} para {nova_data}")
                cur.execute(
                    "UPDATE parcelas SET data_vencimento = %s WHERE id = %s",
                    (nova_data, p['id'])
                )
                
                # Se alterou a data, precisa atualizar a cobrança pai também se for a data dela
                cur.execute(
                    "UPDATE cobrancas SET data_vencimento = %s WHERE id = (SELECT cobranca_id FROM parcelas WHERE id = %s) AND data_vencimento = %s",
                    (nova_data, p['id'], data_orig)
                )
                alteradas += 1
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"--- Concluído! {alteradas} parcelas foram corrigidas. ---")

if __name__ == "__main__":
    corrigir_datas_festivas()