import React from 'react';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';

const TabelaInadimplentes = ({ data, isLoading, error, onExport }) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Clientes Inadimplentes</h3>
        <ErrorMessage message={error} />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Clientes Inadimplentes</h3>
          <div className="text-sm text-gray-500">Nenhum cliente inadimplente</div>
        </div>
        <div className="flex items-center justify-center h-32 bg-gray-50 rounded-lg">
          <p className="text-gray-500">Todos os clientes estão em dia! 🎉</p>
        </div>
      </div>
    );
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatCPF = (cpf) => {
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  };

  const getStatusBadge = (installments) => {
    if (installments <= 1) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          1 parcela vencida
        </span>
      );
    } else if (installments <= 3) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
          {installments} parcelas vencidas
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          {installments} parcelas vencidas
        </span>
      );
    }
  };

  const totalInadimplencia = data.reduce((sum, cliente) => sum + cliente.totalDue, 0);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Clientes Inadimplentes</h3>
          <p className="text-sm text-gray-500 mt-1">
            {data.length} cliente{data.length !== 1 ? 's' : ''} com parcelas vencidas
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onExport('delinquents', 'pdf')}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
          >
            📄 PDF
          </button>
          <button
            onClick={() => onExport('delinquents', 'xlsx')}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors"
          >
            📊 Excel
          </button>
        </div>
      </div>

      {/* Resumo */}
      <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-red-800">Total em Inadimplência:</span>
          <span className="text-lg font-bold text-red-900">{formatCurrency(totalInadimplencia)}</span>
        </div>
      </div>

      {/* Tabela */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cliente
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                CPF
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Valor Total
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ações
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((cliente, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {cliente.clientName}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">
                    {formatCPF(cliente.clientCpf)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(cliente.overdueInstallments)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {formatCurrency(cliente.totalDue)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button className="text-blue-600 hover:text-blue-900 mr-3">
                    Contatar
                  </button>
                  <button className="text-green-600 hover:text-green-900">
                    Renegociar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Estatísticas */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-sm text-gray-600">Total de Clientes</p>
            <p className="text-lg font-semibold text-gray-900">{data.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Parcelas Vencidas</p>
            <p className="text-lg font-semibold text-gray-900">
              {data.reduce((sum, cliente) => sum + cliente.overdueInstallments, 0)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Valor Médio</p>
            <p className="text-lg font-semibold text-gray-900">
              {formatCurrency(totalInadimplencia / data.length)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TabelaInadimplentes;