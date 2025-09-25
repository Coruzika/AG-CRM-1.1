# AG CRM - Dashboard com Gráfico de Parcelas

Este projeto contém um componente React `ParcelasPieChart` que utiliza Recharts para exibir um gráfico de pizza com as parcelas dos clientes.

## Características do Componente

- **Gráfico de Pizza**: Visualização clara das parcelas por status
- **Cores Personalizadas**: 
  - Verde para parcelas pagas
  - Azul para parcelas a pagar  
  - Vermelho para parcelas vencidas
- **Legendas**: Mostra o nome e percentual de cada categoria
- **Tooltip Interativo**: Exibe informações detalhadas ao passar o mouse
- **Design Responsivo**: Adapta-se a diferentes tamanhos de tela
- **Estilização com Tailwind**: Card moderno e centralizado

## Estrutura do Projeto

```
src/
├── components/
│   └── ParcelasPieChart.jsx    # Componente principal do gráfico
├── Dashboard.jsx                # Exemplo de uso no dashboard
├── App.js                       # Componente principal
├── index.js                     # Ponto de entrada
└── index.css                    # Estilos Tailwind
```

## Como Usar

### 1. Instalar Dependências

```bash
npm install
```

### 2. Executar o Projeto

```bash
npm start
```

### 3. Usar o Componente

```jsx
import ParcelasPieChart from './components/ParcelasPieChart';

// Dados no formato especificado
const data = [
  { name: 'Pagas', value: 5 },
  { name: 'A pagar', value: 3 },
  { name: 'Vencidas', value: 2 }
];

// Usar o componente
<ParcelasPieChart data={data} />
```

## Formato dos Dados

O componente espera receber um array de objetos com a seguinte estrutura:

```javascript
[
  { name: 'Pagas', value: 5 },      // Nome do status e quantidade
  { name: 'A pagar', value: 3 },
  { name: 'Vencidas', value: 2 }
]
```

## Funcionalidades

- **Percentuais Automáticos**: Calcula automaticamente os percentuais baseado nos valores
- **Tooltip Customizado**: Mostra quantidade e percentual ao passar o mouse
- **Legenda Personalizada**: Exibe cores e nomes das categorias
- **Labels no Gráfico**: Mostra percentuais diretamente nas fatias
- **Resumo Detalhado**: Lista todas as categorias com valores e percentuais
- **Design Moderno**: Card com sombra e bordas arredondadas

## Tecnologias Utilizadas

- **React 18**: Framework principal
- **Recharts**: Biblioteca para gráficos
- **Tailwind CSS**: Framework de estilização
- **PostCSS**: Processador CSS

## Exemplo Completo

O arquivo `Dashboard.jsx` contém um exemplo completo de como usar o componente, incluindo:

- Seleção de diferentes clientes
- Dados dinâmicos
- Cards de estatísticas
- Layout responsivo
- Interface moderna

## Personalização

Você pode personalizar as cores modificando o objeto `COLORS` no componente:

```javascript
const COLORS = {
  'Pagas': '#10B981',      // Verde
  'A pagar': '#3B82F6',    // Azul
  'Vencidas': '#EF4444'    // Vermelho
};
```
