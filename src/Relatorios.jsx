import React, { useState, useEffect, useCallback } from 'react';
import { reportsAPI } from './services/api';
import FiltrosGlobais from './components/FiltrosGlobais';
import CardsKPIs from './components/CardsKPIs';
import GraficoEvolucaoMensal from './components/GraficoEvolucaoMensal';
import GraficoStatusParcelas from './components/GraficoStatusParcelas';
import GraficoTopClientes from './components/GraficoTopClientes';
import TabelaInadimplentes from './components/TabelaInadimplentes';
import TabelaVencimentos from './components/TabelaVencimentos';
import LoadingSpinner from './components/LoadingSpinner';

const Relatorios = () => {
  // Estados para filtros
  const [filtros, setFiltros] = useState({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 dias atrás
    endDate: new Date().toISOString().split('T')[0], // hoje
    clienteSelecionado: null
  });

  // Estados para dados da API
  const [kpisData, setKpisData] = useState(null);
  const [monthlyEvolutionData, setMonthlyEvolutionData] = useState(null);
  const [installmentsStatusData, setInstallmentsStatusData] = useState(null);
  const [topClientsData, setTopClientsData] = useState(null);
  const [delinquentsData, setDelinquentsData] = useState(null);
  const [dueSoonData, setDueSoonData] = useState(null);

  // Estados para loading e erro
  const [loadingStates, setLoadingStates] = useState({
    kpis: false,
    monthlyEvolution: false,
    installmentsStatus: false,
    topClients: false,
    delinquents: false,
    dueSoon: false
  });

  const [errorStates, setErrorStates] = useState({
    kpis: null,
    monthlyEvolution: null,
    installmentsStatus: null,
    topClients: null,
    delinquents: null,
    dueSoon: null
  });

  // Função para atualizar loading state
  const updateLoadingState = (key, isLoading) => {
    setLoadingStates(prev => ({ ...prev, [key]: isLoading }));
  };

  // Função para atualizar error state
  const updateErrorState = (key, error) => {
    setErrorStates(prev => ({ ...prev, [key]: error }));
  };

  // Função para buscar dados da API
  const fetchData = useCallback(async () => {
    const { startDate, endDate } = filtros;

    try {
      // Buscar KPIs
      updateLoadingState('kpis', true);
      updateErrorState('kpis', null);
      try {
        const kpis = await reportsAPI.getKPIs(startDate, endDate);
        setKpisData(kpis);
      } catch (error) {
        updateErrorState('kpis', error.message);
      }
      updateLoadingState('kpis', false);

      // Buscar evolução mensal
      updateLoadingState('monthlyEvolution', true);
      updateErrorState('monthlyEvolution', null);
      try {
        const monthly = await reportsAPI.getMonthlyEvolution(startDate, endDate);
        setMonthlyEvolutionData(monthly);
      } catch (error) {
        updateErrorState('monthlyEvolution', error.message);
      }
      updateLoadingState('monthlyEvolution', false);

      // Buscar status das parcelas
      updateLoadingState('installmentsStatus', true);
      updateErrorState('installmentsStatus', null);
      try {
        const status = await reportsAPI.getInstallmentsStatus(startDate, endDate);
        setInstallmentsStatusData(status);
      } catch (error) {
        updateErrorState('installmentsStatus', error.message);
      }
      updateLoadingState('installmentsStatus', false);

      // Buscar top clientes
      updateLoadingState('topClients', true);
      updateErrorState('topClients', null);
      try {
        const topClients = await reportsAPI.getTopClients(5, startDate, endDate);
        setTopClientsData(topClients);
      } catch (error) {
        updateErrorState('topClients', error.message);
      }
      updateLoadingState('topClients', false);

      // Buscar inadimplentes
      updateLoadingState('delinquents', true);
      updateErrorState('delinquents', null);
      try {
        const delinquents = await reportsAPI.getDelinquents(startDate, endDate);
        setDelinquentsData(delinquents);
      } catch (error) {
        updateErrorState('delinquents', error.message);
      }
      updateLoadingState('delinquents', false);

      // Buscar vencimentos
      updateLoadingState('dueSoon', true);
      updateErrorState('dueSoon', null);
      try {
        const dueSoon = await reportsAPI.getDueSoon(startDate, endDate);
        setDueSoonData(dueSoon);
      } catch (error) {
        updateErrorState('dueSoon', error.message);
      }
      updateLoadingState('dueSoon', false);

    } catch (error) {
      console.error('Erro ao buscar dados:', error);
    }
  }, [filtros]);

  // Função para lidar com mudanças nos filtros
  const handleFilterChange = (novosFiltros) => {
    setFiltros(prev => ({ ...prev, ...novosFiltros }));
  };

  // Função para exportar relatório
  const handleExport = async (reportType, format = 'pdf') => {
    try {
      const { startDate, endDate } = filtros;
      const response = await reportsAPI.exportReport(reportType, format, startDate, endDate);
      
      // Criar link de download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${reportType}_${startDate}_${endDate}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erro ao exportar relatório:', error);
      alert('Erro ao exportar relatório. Tente novamente.');
    }
  };

  // Buscar dados quando o componente monta ou filtros mudam
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Verificar se algum dado está carregando
  const isAnyLoading = Object.values(loadingStates).some(loading => loading);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard de Relatórios</h1>
              <p className="mt-2 text-gray-600">
                Business Intelligence - Gestão de Empréstimos
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => handleExport('delinquents', 'pdf')}
                className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                📄 Exportar PDF
              </button>
              <button
                onClick={() => handleExport('delinquents', 'xlsx')}
                className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                📊 Exportar Excel
              </button>
            </div>
          </div>
        </div>

        {/* Filtros */}
        <div className="mb-8">
          <FiltrosGlobais 
            filtros={filtros}
            onFilterChange={handleFilterChange}
            isLoading={isAnyLoading}
          />
        </div>

        {/* Loading global */}
        {isAnyLoading && (
          <div className="mb-8">
            <LoadingSpinner message="Carregando dados do dashboard..." />
          </div>
        )}

        {/* Grid principal */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* KPIs - Ocupam toda a largura */}
          <div className="lg:col-span-12">
            <CardsKPIs 
              data={kpisData}
              isLoading={loadingStates.kpis}
              error={errorStates.kpis}
            />
          </div>

          {/* Gráfico de Evolução Mensal */}
          <div className="lg:col-span-8">
            <GraficoEvolucaoMensal 
              data={monthlyEvolutionData}
              isLoading={loadingStates.monthlyEvolution}
              error={errorStates.monthlyEvolution}
            />
          </div>

          {/* Gráfico de Status das Parcelas */}
          <div className="lg:col-span-4">
            <GraficoStatusParcelas 
              data={installmentsStatusData}
              isLoading={loadingStates.installmentsStatus}
              error={errorStates.installmentsStatus}
            />
          </div>

          {/* Gráfico de Top Clientes */}
          <div className="lg:col-span-6">
            <GraficoTopClientes 
              data={topClientsData}
              isLoading={loadingStates.topClients}
              error={errorStates.topClients}
            />
          </div>

          {/* Tabela de Inadimplentes */}
          <div className="lg:col-span-6">
            <TabelaInadimplentes 
              data={delinquentsData}
              isLoading={loadingStates.delinquents}
              error={errorStates.delinquents}
              onExport={handleExport}
            />
          </div>

          {/* Tabela de Vencimentos */}
          <div className="lg:col-span-12">
            <TabelaVencimentos 
              data={dueSoonData}
              isLoading={loadingStates.dueSoon}
              error={errorStates.dueSoon}
              onExport={handleExport}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Relatorios;
