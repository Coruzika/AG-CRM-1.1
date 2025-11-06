import sys
from app import app, get_db
from werkzeug.security import generate_password_hash


def resetar_senha(username, nova_senha):
    """
    Encontra um utilizador pelo 'email' ou 'nome' e define uma nova senha.
    O parâmetro 'username' pode ser o email ou o nome do utilizador.
    """
    # Garante que estamos no contexto da aplicação para aceder à base de dados
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        
        # Tentar buscar primeiro por email (identificador único)
        cur.execute('SELECT id, nome, email FROM usuarios WHERE email = %s', (username,))
        utilizador = cur.fetchone()
        
        # Se não encontrou por email, tentar buscar por nome
        if not utilizador:
            cur.execute('SELECT id, nome, email FROM usuarios WHERE nome = %s', (username,))
            utilizador = cur.fetchone()
        
        if utilizador:
            # Fazer hash da nova senha
            senha_hash = generate_password_hash(nova_senha)
            
            # Atualizar a senha no banco de dados
            cur.execute('UPDATE usuarios SET senha = %s WHERE id = %s', (senha_hash, utilizador[0]))
            conn.commit()
            
            print(f"Sucesso: A senha para o utilizador '{utilizador[1]}' (email: {utilizador[2]}) foi redefinida.")
        else:
            print(f"Erro: Utilizador '{username}' não encontrado (tentou buscar por email e por nome).")
        
        cur.close()
        conn.close()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python reset_password.py <username> <nova_senha>")
        print("\nNota: 'username' pode ser o email ou o nome do utilizador.")
        print("Exemplo: python reset_password.py admin@sistema.com nova_senha123")
        print("Exemplo: python reset_password.py admin nova_senha123")
        sys.exit(1)

    username_arg = sys.argv[1]
    nova_senha_arg = sys.argv[2]

    resetar_senha(username_arg, nova_senha_arg)

