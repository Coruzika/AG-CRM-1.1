# Sistema de Navegação - AG CRM

## Visão Geral

O sistema de navegação foi implementado com um componente Sidebar responsivo que utiliza React Router DOM para navegação entre páginas. O sistema é totalmente responsivo e funciona tanto em desktop quanto em dispositivos móveis.

## Componentes Implementados

### 1. Sidebar.jsx
Componente principal de navegação lateral com as seguintes características:

- **Navegação com NavLink**: Utiliza `NavLink` do React Router DOM para navegação
- **Estados ativos**: Destaque visual do item de menu ativo
- **Responsividade**: Menu colapsável em dispositivos móveis
- **Ícones**: Utiliza ícones da biblioteca Lucide React
- **Animações**: Transições suaves e efeitos hover

#### Itens de Menu:
- **Dashboard** (`/`) - Página principal
- **Relatórios** (`/relatorios`) - Dashboard de BI
- **Calendário** (`/calendario`) - Calendário de vencimentos
- **Clientes** (`/clientes`) - Gestão de clientes

### 2. Layout.jsx
Componente wrapper que organiza o layout geral:

- **Estrutura flexível**: Sidebar fixo + conteúdo principal
- **Responsividade**: Adaptação para diferentes tamanhos de tela
- **Outlet**: Renderiza o conteúdo das rotas filhas

### 3. App.js (Atualizado)
Estrutura de rotas aninhadas:

```jsx
<Routes>
  <Route path="/" element={<Layout />}>
    <Route index element={<Dashboard />} />
    <Route path="relatorios" element={<Relatorios />} />
    <Route path="calendario" element={<CalendarioVencimentos />} />
  </Route>
</Routes>
```

## Características Técnicas

### Navegação com NavLink
```jsx
<NavLink
  to="/relatorios"
  className={({ isActive }) =>
    `flex items-center p-2.5 my-1 rounded-lg transition-colors duration-200 ${
      isActive
        ? 'bg-blue-100 text-blue-800 font-semibold'
        : 'text-gray-600 hover:bg-gray-100'
    }`
  }
>
  <BarChart3 className="w-5 h-5 mr-3" />
  Relatórios
</NavLink>
```

### Responsividade
- **Desktop (lg+)**: Sidebar sempre visível
- **Mobile (<lg)**: Sidebar colapsável com botão hamburger
- **Overlay**: Fundo escuro quando menu mobile está aberto

### Estados Visuais
- **Normal**: Texto cinza com hover em cinza claro
- **Ativo**: Fundo azul claro, texto azul escuro e negrito
- **Hover**: Transição suave de cores

## Estrutura de Arquivos

```
src/
├── components/
│   ├── Sidebar.jsx          # Componente de navegação lateral
│   └── Layout.jsx           # Layout principal com sidebar
├── App.js                   # Rotas e estrutura principal
├── Dashboard.jsx           # Página principal (sem navegação inline)
└── Relatorios.jsx          # Página de relatórios
```

## Funcionalidades Implementadas

### ✅ Navegação Funcional
- Links funcionais entre todas as páginas
- Navegação programática com React Router
- URLs limpos e amigáveis

### ✅ Feedback Visual
- Destaque do item ativo
- Efeitos hover suaves
- Ícones consistentes

### ✅ Responsividade
- Menu colapsável em mobile
- Botão hamburger funcional
- Overlay para fechar menu

### ✅ Acessibilidade
- Navegação por teclado
- Contraste adequado
- Semântica HTML correta

## Como Usar

### 1. Navegação Básica
- Clique nos itens do menu para navegar
- O item ativo é destacado automaticamente

### 2. Navegação Mobile
- Clique no ícone de menu (☰) no canto superior esquerdo
- Clique em qualquer item para navegar e fechar o menu
- Clique no overlay escuro para fechar o menu

### 3. Adicionar Novos Itens
Para adicionar um novo item de menu:

1. **Adicione o ícone** na importação:
```jsx
import { Home, BarChart3, Calendar, Users, NovoIcone } from 'lucide-react';
```

2. **Adicione ao array navItems**:
```jsx
const navItems = [
  { to: '/', icon: Home, label: 'Dashboard' },
  { to: '/relatorios', icon: BarChart3, label: 'Relatórios' },
  { to: '/nova-pagina', icon: NovoIcone, label: 'Nova Página' }
];
```

3. **Crie a rota** no App.js:
```jsx
<Route path="nova-pagina" element={<NovaPagina />} />
```

## Personalização

### Cores
As cores podem ser personalizadas alterando as classes Tailwind:

- **Ativo**: `bg-blue-100 text-blue-800`
- **Hover**: `hover:bg-gray-100`
- **Normal**: `text-gray-600`

### Ícones
Substitua os ícones importando outros da biblioteca Lucide React:
```jsx
import { Home, BarChart3, Calendar, Users, Settings, Help } from 'lucide-react';
```

### Layout
O layout pode ser ajustado no componente Layout.jsx:
- Largura do sidebar: `w-64` (256px)
- Margem do conteúdo: `lg:ml-64`

## Troubleshooting

### Menu não aparece em mobile
- Verifique se as classes Tailwind estão corretas
- Confirme que o z-index está adequado

### Navegação não funciona
- Verifique se as rotas estão definidas no App.js
- Confirme que os componentes estão importados

### Estilos não aplicados
- Verifique se o Tailwind CSS está configurado
- Confirme se as classes estão sendo aplicadas corretamente

---

**Sistema de navegação implementado com sucesso! 🎉**
