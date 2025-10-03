# Central de Relatórios - Sistema CRM

## Visão Geral

A Central de Relatórios é uma funcionalidade integrada ao sistema CRM que permite extrair dados importantes em formato CSV para análise externa. Implementada completamente em Flask com templates HTML, oferece uma interface limpa e consistente com o resto da aplicação.

## Funcionalidades Disponíveis

### 📋 Relatório de Clientes
- Exporta lista completa de todos os clientes cadastrados
- Inclui dados pessoais, contato e data de cadastro
- Formato: CSV com encoding UTF-8

### 📊 Relatório de Cobranças
- Exporta histórico completo de todas as cobranças
- Inclui valores, status, datas e informações do cliente
- Formato: CSV com encoding UTF-8

## Arquitetura Implementada

```
templates/
├── relatorios.html          # Interface principal da central
└── base.html               # Layout base usado por todos os templates

app.py                      # Rotas Flask implementadas:
├── /relatorios             # Página principal
├── /relatorios/clientes    # Exportação de clientes
└── /relatorios/cobrancas   # Exportação de cobranças
```

## Tecnologias Utilizadas

- **Flask**: Framework web Python
- **PostgreSQL**: Banco de dados principal
- **Jinja2**: Engine de templates HTML
- **Bootstrap 5**: Framework CSS para interface
- **Cursors**: Biblioteca para manipulação de CSV

## Como Usar

1. **Acesso**: Clique em "Relatórios" na barra de navegação
2. **Seleção**: Escolha o tipo de relatório desejado
3. **Download**: Clique em "Gerar Relatório" para baixar o CSV
4. **Análise**: Abra o arquivo em Excel ou Google Sheets

## Recursos da Interface

### 📈 Estatísticas Rápidas
- Total de clientes cadastrados
- Cobranças pendentes e vencidas
- Valor total a receber
- Atualizações em tempo real

### 🎨 Design Consistente
- Integração perfeita com layout existente
- Ícones Font Awesome para melhor UX
- Responsivo para dispositivos móveis
- Loading states durante geração de relatórios

## Recursos de Segurança

- **Autenticação**: Acesso restrito a usuários logados
- **Autorização**: Verificação de sessão em todas as rotas
- **Validação**: Tratamento de erros com flash messages
- **Sanitização**: Escape adequado de dados CSV

## Formatos de Saída

### Clientes (CSV)
```
ID,Nome,CPF/CNPJ,Telefone,Email,Cidade,Data de Cadastro
1,João Silva,123.456.789-00,(11) 99999-9999,joao@email.com,São Paulo,2024-01-15
```

### Cobranças (CSV)
```
ID,Cliente,Descrição,Valor Original,Valor Total,Data Vencimento,Status,Data Criação
1,João Silva,Empréstimo pessoal,R$ 1.000,00,R$ 1.100,00,15/02/2024,Pendente,01/01/2024
```

## Troubleshooting

### Problemas Comuns

1. **Erro ao gerar relatório**
   - Verifique conexão com banco de dados
   - Confirme permissões de usuário
   - Valide sessão ativa

2. **Download não funciona**
   - Limpe cache do navegador
   - Verifique bloqueadores de popup
   - Teste em navegador diferente

3. **Interface quebrada**
   - Certifique-se de usar templates corretos
   - Verifique se extends "base.html"
   - Confirme carregamento do Bootstrap

## Customizações Futuras

### Possíveis Melhorias
- Filtros por data nos relatórios
- Formatos adicionais (Excel, PDF)
- Agendamento de relatórios
- Dashboard com gráficos
- Backup automático dos dados

### Como Extender
1. Adicione nova rota em `app.py`
2. Crie formulário correspondente em `relatorios.html`
3. Implemente lógica de exportação
4. Teste e documente nova funcionalidade

## Desenvolvimento

### Estrutura de Arquivos
```
AG CRM 1.1/
├── app.py                      # Flask app principal
├── templates/
│   ├── base.html              # Layout base
│   └── relatorios.html        # Central de relatórios
├── requirements.txt            # Dependências Python
└── README.md                  # Documentação geral
```

### Variáveis de Ambiente
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your-secret-key-here
```

---

*Documentação atualizada para versão Flask pura - Dezembro 2024*