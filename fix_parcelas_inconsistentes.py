"""
Script utilitário para corrigir parcelas que já foram pagas mas ainda estão
com status diferente de 'Pago' devido a comparações incorretas com floats.
"""

from psycopg.rows import dict_row

from app import app, get_db

TOLERANCIA = 0.05


def corrigir_parcelas():
    """Atualiza o status das parcelas quitadas considerando a tolerância."""
    with app.app_context():
        conn = get_db()
        cur = conn.cursor(row_factory=dict_row)

        cur.execute(
            """
            SELECT id, valor, valor_pago, multa_manual
            FROM parcelas
            WHERE status != 'Pago'
            """
        )
        parcelas = cur.fetchall()

        total_corrigidas = 0

        for parcela in parcelas:
            valor_base = parcela["valor"] or 0
            multa_manual = parcela.get("multa_manual") or 0
            valor_total_devido = valor_base + multa_manual
            valor_pago = parcela.get("valor_pago") or 0

            if valor_pago >= (valor_total_devido - TOLERANCIA):
                cur.execute(
                    """
                    UPDATE parcelas
                    SET status = 'Pago',
                        atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (parcela["id"],),
                )
                print(
                    f"Parcela ID {parcela['id']} corrigida: "
                    f"Valor Devido {valor_total_devido:.2f} | Valor Pago {valor_pago:.2f}"
                )
                total_corrigidas += 1

        conn.commit()
        cur.close()
        conn.close()

        print(f"Total de parcelas corrigidas: {total_corrigidas}")


if __name__ == "__main__":
    corrigir_parcelas()

