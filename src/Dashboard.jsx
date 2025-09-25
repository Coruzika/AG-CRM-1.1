import React, { useState } from 'react';
import ParcelasPieChart from './components/ParcelasPieChart';

const Dashboard = () => {
  // Dados de exemplo para o gráfico de parcelas
  const [parcelasData] = useState([
    { name: 'Pagas', value: 5 },
    { name: 'A pagar', value: 3 },
    { name: 'Vencidas', value: 2 }
  ]);

  // Dados de exemplo para diferentes clientes
  const [clientesData] = useState([
    {
      id: 1,
      nome: 'João Silva',
      parcelas: [
        { name: 'Pagas', value: 8 },
        { name: 'A pagar', value: 2 },
        { name: 'Vencidas', value: 1 }
      ]
    },
    {
      id: 2,
      nome: 'Maria Santos',
      parcelas: [
        { name: 'Pagas', value: 3 },
        { name: 'A pagar', value: 5 },
        { name: 'Vencidas', value: 0 }
      ]
    },
    {
      id: 3,
      nome: 'Pedro Costa',
      parcelas: [
        { name: 'Pagas', value: 12 },
        { name: 'A pagar', value: 1 },
        { name: 'Vencidas', value: 3 }
      ]
    }
  ]);

  const [clienteSelecionado, setClienteSelecionado] = useState(0);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header do Dashboard */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard CRM</h1>
          <p className="mt-2 text-gray-600">
            Visualização das parcelas dos clientes
          </p>
        </div>

        {/* Seletor de Cliente */}
        <div className="mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Selecionar Cliente
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {clientesData.map((cliente, index) => (
                <button
                  key={cliente.id}
                  onClick={() => setClienteSelecionado(index)}
                  className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                    clienteSelecionado === index
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <h3 className="font-medium text-gray-900">{cliente.nome}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {cliente.parcelas.reduce((sum, p) => sum + p.value, 0)} parcelas totais
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Gráfico Principal */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Gráfico de Pizza */}
          <div className="flex justify-center">
            <ParcelasPieChart data={clientesData[clienteSelecionado].parcelas} />
          </div>

          {/* Informações Detalhadas */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Detalhes - {clientesData[clienteSelecionado].nome}
            </h2>
            
            <div className="space-y-4">
              {clientesData[clienteSelecionado].parcelas.map((item, index) => {
                const total = clientesData[clienteSelecionado].parcelas.reduce((sum, p) => sum + p.value, 0);
                const percentage = ((item.value / total) * 100).toFixed(1);
                
                return (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div 
                        className={`w-4 h-4 rounded-full ${
                          item.name === 'Pagas' ? 'bg-green-500' :
                          item.name === 'A pagar' ? 'bg-blue-500' : 'bg-red-500'
                        }`}
                      />
                      <span className="font-medium text-gray-900">{item.name}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-bold text-gray-900">{item.value}</span>
                      <span className="text-sm text-gray-500 ml-2">({percentage}%)</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Resumo Geral */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="font-medium text-gray-900 mb-3">Resumo Geral</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {clientesData[clienteSelecionado].parcelas.find(p => p.name === 'Pagas')?.value || 0}
                  </div>
                  <div className="text-sm text-green-700">Pagas</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {clientesData[clienteSelecionado].parcelas.find(p => p.name === 'A pagar')?.value || 0}
                  </div>
                  <div className="text-sm text-blue-700">A Pagar</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Cards de Estatísticas Gerais */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Pagas</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {clientesData.reduce((sum, cliente) => 
                    sum + (cliente.parcelas.find(p => p.name === 'Pagas')?.value || 0), 0
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">A Pagar</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {clientesData.reduce((sum, cliente) => 
                    sum + (cliente.parcelas.find(p => p.name === 'A pagar')?.value || 0), 0
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Vencidas</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {clientesData.reduce((sum, cliente) => 
                    sum + (cliente.parcelas.find(p => p.name === 'Vencidas')?.value || 0), 0
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
