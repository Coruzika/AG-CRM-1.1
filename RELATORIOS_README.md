# Dashboard de Relatórios - Sistema de Gestão de Empréstimos

## Visão Geral

Este dashboard de Business Intelligence foi desenvolvido para fornecer insights visuais sobre o sistema de gestão de empréstimos, permitindo aos administradores monitorar KPIs, analisar tendências e gerenciar inadimplência.

## Funcionalidades Principais

### 📊 KPIs (Key Performance Indicators)
- **Total Emprestado**: Valor total dos empréstimos concedidos
- **Total Recebido**: Valor total já recebido dos clientes
- **Total Pendente**: Valor ainda pendente de recebimento
- **Receita de Juros**: Valor gerado através de juros

### 📈 Gráficos e Visualizações
1. **Evolução Mensal**: Gráfico de linha mostrando tendências de empréstimos e recebimentos
2. **Status das Parcelas**: Gráfico de pizza com distribuição de parcelas (pagas, a pagar, vencidas)
3. **Top 5 Clientes**: Gráfico de barras dos clientes com maior volume de empréstimos

### 📋 Tabelas de Gestão
1. **Clientes Inadimplentes**: Lista de clientes com parcelas vencidas
2. **Parcelas a Vencer**: Parcelas próximas do vencimento com alertas de urgência

### 🔍 Filtros e Interatividade
- Filtros por período (data inicial e final)
- Filtros rápidos (últimos 7, 30, 90 dias, último ano)
- Filtro por cliente específico
- Ordenação e busca nas tabelas

### 📄 Exportação
- Exportação em PDF e Excel
- Relatórios personalizados por período
- Download direto dos arquivos

## Arquitetura Técnica

### Componentes Principais

```
src/
├── Relatorios.jsx                 # Componente principal do dashboard
├── services/
│   └── api.js                    # Serviço de integração com API
├── components/
│   ├── FiltrosGlobais.jsx        # Componente de filtros
│   ├── CardsKPIs.jsx             # Cards de métricas principais
│   ├── GraficoEvolucaoMensal.jsx # Gráfico de linha
│   ├── GraficoStatusParcelas.jsx # Gráfico de pizza
│   ├── GraficoTopClientes.jsx    # Gráfico de barras
│   ├── TabelaInadimplentes.jsx   # Tabela de inadimplentes
│   ├── TabelaVencimentos.jsx     # Tabela de vencimentos
│   ├── LoadingSpinner.jsx        # Componente de loading
│   └── ErrorMessage.jsx          # Componente de erro
└── data/
    └── mockData.js               # Dados mock para desenvolvimento
```

### Tecnologias Utilizadas

- **React 18**: Framework principal
- **Recharts**: Biblioteca de gráficos
- **Axios**: Cliente HTTP para API
- **Tailwind CSS**: Framework de estilização
- **React Router**: Navegação entre páginas

## Integração com API

### Endpoints da API

O dashboard consome os seguintes endpoints:

```
GET /api/reports/kpis?startDate={date}&endDate={date}
GET /api/reports/monthly-evolution?startDate={date}&endDate={date}
GET /api/reports/installments-status?startDate={date}&endDate={date}
GET /api/reports/top-clients?limit=5&startDate={date}&endDate={date}
GET /api/reports/delinquents?startDate={date}&endDate={date}
GET /api/reports/due-soon?startDate={date}&endDate={date}
GET /api/reports/{type}/export?format={pdf|xlsx}&startDate={date}&endDate={date}
```

### Formato dos Dados

#### KPIs
```json
{
  "totalLoaned": 150000.00,
  "totalReceived": 75000.00,
  "totalPending": 75000.00,
  "interestRevenue": 5230.50
}
```

#### Evolução Mensal
```json
[
  { "month": "Janeiro", "loaned": 25000, "received": 15000 },
  { "month": "Fevereiro", "loaned": 30000, "received": 20000 }
]
```

#### Clientes Inadimplentes
```json
[
  {
    "clientName": "João Silva",
    "clientCpf": "123.456.789-00",
    "overdueInstallments": 3,
    "totalDue": 1550.75
  }
]
```

## Modo de Desenvolvimento

O sistema inclui dados mock para desenvolvimento e teste quando a API não está disponível:

- Os dados mock são carregados automaticamente se a API falhar
- Simula delays realistas de rede
- Permite desenvolvimento offline completo

## Como Usar

### 1. Acesso ao Dashboard
- Navegue para `/relatorios` no sistema
- Ou clique no botão "📊 Relatórios" no dashboard principal

### 2. Aplicar Filtros
- Use os filtros de data para definir o período
- Aplique filtros rápidos para períodos comuns
- Filtre por cliente específico se necessário

### 3. Visualizar Dados
- Os KPIs são exibidos no topo
- Gráficos mostram tendências e distribuições
- Tabelas listam detalhes específicos

### 4. Exportar Relatórios
- Use os botões de exportação em PDF ou Excel
- Os relatórios incluem dados filtrados
- Downloads são iniciados automaticamente

## Responsividade

O dashboard é totalmente responsivo:
- **Desktop**: Layout em grid com múltiplas colunas
- **Tablet**: Layout adaptado com 2 colunas
- **Mobile**: Layout em coluna única otimizado

## Performance

- Carregamento assíncrono de dados
- Estados de loading para melhor UX
- Tratamento de erros robusto
- Otimização de re-renders com React hooks

## Configuração

### Variáveis de Ambiente
```env
REACT_APP_API_URL=http://localhost:5000
```

### Customização
- Cores e temas podem ser ajustados no Tailwind CSS
- Componentes são modulares e reutilizáveis
- Fácil adição de novos gráficos e métricas

## Próximos Passos

1. **Integração com Backend**: Conectar com API real
2. **Autenticação**: Implementar controle de acesso
3. **Notificações**: Alertas em tempo real
4. **Relatórios Customizados**: Permitir criação de relatórios personalizados
5. **Dashboard Interativo**: Adicionar mais interatividade aos gráficos

## Suporte

Para dúvidas ou problemas:
1. Verifique se a API está rodando
2. Confirme as variáveis de ambiente
3. Verifique o console do navegador para erros
4. Use os dados mock para testar funcionalidades

---

**Desenvolvido com ❤️ para otimizar a gestão de empréstimos**
