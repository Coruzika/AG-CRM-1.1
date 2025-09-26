import React, { useState } from 'react';

const FiltrosGlobais = ({ filtros, onFilterChange, isLoading }) => {
  const [localFiltros, setLocalFiltros] = useState(filtros);

  const handleDateChange = (field, value) => {
    const novosFiltros = { ...localFiltros, [field]: value };
    setLocalFiltros(novosFiltros);
    onFilterChange(novosFiltros);
  };

  const handleClienteChange = (clienteId) => {
    const novosFiltros = { ...localFiltros, clienteSelecionado: clienteId };
    setLocalFiltros(novosFiltros);
    onFilterChange(novosFiltros);
  };

  const resetFilters = () => {
    const hoje = new Date().toISOString().split('T')[0];
    const trintaDiasAtras = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    const filtrosResetados = {
      startDate: trintaDiasAtras,
      endDate: hoje,
      clienteSelecionado: null
    };
    
    setLocalFiltros(filtrosResetados);
    onFilterChange(filtrosResetados);
  };

  const quickFilters = [
    { label: 'Últimos 7 dias', days: 7 },
    { label: 'Últimos 30 dias', days: 30 },
    { label: 'Últimos 90 dias', days: 90 },
    { label: 'Último ano', days: 365 }
  ];

  const applyQuickFilter = (days) => {
    const hoje = new Date();
    const dataInicio = new Date(hoje.getTime() - days * 24 * 60 * 60 * 1000);
    
    const novosFiltros = {
      ...localFiltros,
      startDate: dataInicio.toISOString().split('T')[0],
      endDate: hoje.toISOString().split('T')[0]
    };
    
    setLocalFiltros(novosFiltros);
    onFilterChange(novosFiltros);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Filtros</h2>
        <button
          onClick={resetFilters}
          disabled={isLoading}
          className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          Resetar
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Filtro de Data Inicial */}
        <div>
          <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-2">
            Data Inicial
          </label>
          <input
            type="date"
            id="startDate"
            value={localFiltros.startDate}
            onChange={(e) => handleDateChange('startDate', e.target.value)}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
        </div>

        {/* Filtro de Data Final */}
        <div>
          <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 mb-2">
            Data Final
          </label>
          <input
            type="date"
            id="endDate"
            value={localFiltros.endDate}
            onChange={(e) => handleDateChange('endDate', e.target.value)}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
        </div>

        {/* Filtro Rápido */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Filtros Rápidos
          </label>
          <select
            onChange={(e) => {
              if (e.target.value) {
                applyQuickFilter(parseInt(e.target.value));
                e.target.value = '';
              }
            }}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">Selecionar período</option>
            {quickFilters.map((filter) => (
              <option key={filter.days} value={filter.days}>
                {filter.label}
              </option>
            ))}
          </select>
        </div>

        {/* Filtro de Cliente */}
        <div>
          <label htmlFor="cliente" className="block text-sm font-medium text-gray-700 mb-2">
            Cliente (Opcional)
          </label>
          <input
            type="text"
            id="cliente"
            placeholder="Nome ou CPF do cliente"
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            onChange={(e) => handleClienteChange(e.target.value || null)}
          />
        </div>
      </div>

      {/* Informações do Período Selecionado */}
      <div className="mt-4 p-3 bg-blue-50 rounded-md">
        <p className="text-sm text-blue-800">
          <strong>Período selecionado:</strong> {localFiltros.startDate} até {localFiltros.endDate}
          {localFiltros.clienteSelecionado && (
            <span className="ml-2">
              | <strong>Cliente:</strong> {localFiltros.clienteSelecionado}
            </span>
          )}
        </p>
      </div>
    </div>
  );
};

export default FiltrosGlobais;
