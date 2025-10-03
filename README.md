# FinanFlow

Sistema de gestão de cobranças com Flask e PostgreSQL.

## Configuração do Banco de Dados

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar PostgreSQL

#### Opção A: PostgreSQL Local
```bash
# Instalar PostgreSQL (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Criar banco de dados
sudo -u postgres createdb crm_ag

# Configurar variável de ambiente
export DATABASE_URL="postgresql://postgres:sua_senha@localhost:5432/crm_ag"
```

#### Opção B: Usar arquivo .env
Crie um arquivo `.env` na raiz do projeto:
```
DATABASE_URL=postgresql://postgres:sua_senha@localhost:5432/crm_ag
```

### 3. Inicializar o banco de dados
```bash
python init_db.py
```

### 4. Executar a aplicação
```bash
python app.py
```

## Deploy no Render.com

1. Conecte seu repositório GitHub ao Render
2. Configure as variáveis de ambiente:
   - `DATABASE_URL`: Será fornecida automaticamente pelo Render PostgreSQL
3. O Render executará automaticamente:
   - `pip install -r requirements.txt`
   - `python app.py`

## Usuários Padrão

O sistema cria automaticamente 3 usuários:

### 1. Administrador
- **Email**: admin@sistema.com
- **Senha**: admin123
- **Tipo**: admin (acesso total)

### 2. Operador
- **Email**: joao.operador@sistema.com
- **Senha**: operador123
- **Tipo**: operador (acesso limitado)

### 3. Gerente
- **Email**: maria.gerente@sistema.com
- **Senha**: gerente123
- **Tipo**: gerente (acesso intermediário)

## Estrutura do Banco

- `usuarios`: Usuários do sistema
- `clientes`: Dados dos clientes
- `cobrancas`: Cobranças e faturas
- `historico_pagamentos`: Histórico de pagamentos
- `notificacoes`: Notificações enviadas
- `configuracoes`: Configurações do sistema

## Scripts Adicionais

### Gerenciar Usuários
```bash
python manage_users.py
```
Permite:
- Listar todos os usuários
- Criar novos usuários
- Alterar senhas

## Comandos Úteis

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Conectar ao banco via psql
psql -U postgres -d crm_ag

# Listar tabelas
\dt

# Sair do psql
\q
```
