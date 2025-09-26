// Dados mock para testar o dashboard quando a API não estiver disponível

export const mockKPIs = {
  totalLoaned: 150000.00,
  totalReceived: 75000.00,
  totalPending: 75000.00,
  interestRevenue: 5230.50
};

export const mockMonthlyEvolution = [
  { month: 'Janeiro', loaned: 25000, received: 15000 },
  { month: 'Fevereiro', loaned: 30000, received: 20000 },
  { month: 'Março', loaned: 35000, received: 25000 },
  { month: 'Abril', loaned: 28000, received: 22000 },
  { month: 'Maio', loaned: 32000, received: 28000 },
  { month: 'Junho', loaned: 40000, received: 30000 }
];

export const mockInstallmentsStatus = [
  { name: 'Pagas', value: 45 },
  { name: 'A pagar', value: 32 },
  { name: 'Vencidas', value: 8 }
];

export const mockTopClients = [
  { clientName: 'João Silva', totalValue: 15000 },
  { clientName: 'Maria Santos', totalValue: 12500 },
  { clientName: 'Pedro Costa', totalValue: 11000 },
  { clientName: 'Ana Oliveira', totalValue: 9500 },
  { clientName: 'Carlos Lima', totalValue: 8500 }
];

export const mockDelinquents = [
  {
    clientName: 'João Silva',
    clientCpf: '12345678900',
    overdueInstallments: 3,
    totalDue: 1550.75
  },
  {
    clientName: 'Maria Santos',
    clientCpf: '98765432100',
    overdueInstallments: 2,
    totalDue: 1200.00
  },
  {
    clientName: 'Pedro Costa',
    clientCpf: '45678912300',
    overdueInstallments: 1,
    totalDue: 850.50
  },
  {
    clientName: 'Ana Oliveira',
    clientCpf: '32165498700',
    overdueInstallments: 4,
    totalDue: 2100.00
  }
];

export const mockDueSoon = [
  {
    clientName: 'João Silva',
    clientCpf: '12345678900',
    dueDate: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // amanhã
    amount: 500.00
  },
  {
    clientName: 'Maria Santos',
    clientCpf: '98765432100',
    dueDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // depois de amanhã
    amount: 750.00
  },
  {
    clientName: 'Pedro Costa',
    clientCpf: '45678912300',
    dueDate: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    amount: 650.00
  },
  {
    clientName: 'Ana Oliveira',
    clientCpf: '32165498700',
    dueDate: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    amount: 800.00
  },
  {
    clientName: 'Carlos Lima',
    clientCpf: '78912345600',
    dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    amount: 900.00
  }
];
