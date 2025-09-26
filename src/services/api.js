import axios from 'axios';
import { 
  mockKPIs, 
  mockMonthlyEvolution, 
  mockInstallmentsStatus, 
  mockTopClients, 
  mockDelinquents, 
  mockDueSoon 
} from '../data/mockData';

// Configuração base da API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token de autenticação se necessário
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para tratamento de erros globais
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado ou inválido
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Função auxiliar para simular delay da API
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Função para tentar chamada real da API ou usar dados mock
const tryApiCall = async (apiCall, mockData, delayMs = 1000) => {
  try {
    const response = await apiCall();
    return response.data;
  } catch (error) {
    console.warn('API não disponível, usando dados mock:', error.message);
    await delay(delayMs); // Simula delay da API
    return mockData;
  }
};

// Serviços de Relatórios
export const reportsAPI = {
  // KPIs principais
  getKPIs: async (startDate, endDate) => {
    return tryApiCall(
      () => api.get('/api/reports/kpis', { params: { startDate, endDate } }),
      mockKPIs
    );
  },

  // Evolução mensal (gráfico de linha)
  getMonthlyEvolution: async (startDate, endDate) => {
    return tryApiCall(
      () => api.get('/api/reports/monthly-evolution', { params: { startDate, endDate } }),
      mockMonthlyEvolution
    );
  },

  // Status das parcelas (gráfico de pizza)
  getInstallmentsStatus: async (startDate, endDate) => {
    return tryApiCall(
      () => api.get('/api/reports/installments-status', { params: { startDate, endDate } }),
      mockInstallmentsStatus
    );
  },

  // Top clientes (gráfico de barras)
  getTopClients: async (limit = 5, startDate, endDate) => {
    return tryApiCall(
      () => api.get('/api/reports/top-clients', { params: { limit, startDate, endDate } }),
      mockTopClients
    );
  },

  // Clientes inadimplentes (tabela)
  getDelinquents: async (startDate, endDate) => {
    return tryApiCall(
      () => api.get('/api/reports/delinquents', { params: { startDate, endDate } }),
      mockDelinquents
    );
  },

  // Parcelas a vencer (tabela)
  getDueSoon: async (startDate, endDate) => {
    return tryApiCall(
      () => api.get('/api/reports/due-soon', { params: { startDate, endDate } }),
      mockDueSoon
    );
  },

  // Exportação de relatórios
  exportReport: async (reportType, format = 'pdf', startDate, endDate) => {
    try {
      const response = await api.get(`/api/reports/${reportType}/export`, {
        params: { format, startDate, endDate },
        responseType: 'blob'
      });
      return response;
    } catch (error) {
      console.warn('Exportação via API não disponível:', error.message);
      // Simular download de arquivo mock
      const mockContent = `Relatório ${reportType} - ${startDate} a ${endDate}`;
      const blob = new Blob([mockContent], { type: 'text/plain' });
      return { data: blob };
    }
  }
};

export default api;
