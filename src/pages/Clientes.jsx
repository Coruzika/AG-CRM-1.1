import React from 'react';
import { PlusCircle, FilePenLine, Trash2 } from 'lucide-react';

const Clientes = () => {
  // Dados mockados para simular clientes
  const clientes = [
    {
      id: 1,
      nome: 'João Silva',
      cpf: '123.456.789-00',
      telefone: '(11) 99999-9999',
      cidade: 'São Paulo'
    },
    {
      id: 2,
      nome: 'Maria Santos',
      cpf: '987.654.321-00',
      telefone: '(21) 88888-8888',
      cidade: 'Rio de Janeiro'
    },
    {
      id: 3,
      nome: 'Pedro Oliveira',
      cpf: '456.789.123-00',
      telefone: '(31) 77777-7777',
      cidade: 'Belo Horizonte'
    },
    {
      id: 4,
      nome: 'Ana Costa',
      cpf: '789.123.456-00',
      telefone: '(41) 66666-6666',
      cidade: 'Curitiba'
    },
    {
      id: 5,
      nome: 'Carlos Ferreira',
      cpf: '321.654.987-00',
      telefone: '(51) 55555-5555',
      cidade: 'Porto Alegre'
    }
  ];

  const handleEditar = (clienteId) => {
    console.log('Editar cliente:', clienteId);
    // TODO: Implementar navegação para edição
  };

  const handleExcluir = (clienteId, clienteNome) => {
    if (window.confirm(`Tem certeza que deseja excluir o cliente "${clienteNome}"?`)) {
      console.log('Excluir cliente:', clienteId);
      // TODO: Implementar exclusão
    }
  };

  const handleAdicionar = () => {
    console.log('Adicionar novo cliente');
    // TODO: Implementar navegação para adicionar
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Clientes</h1>
        <button
          onClick={handleAdicionar}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <PlusCircle className="w-5 h-5" />
          Adicionar Cliente
        </button>
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nome
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  CPF
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Telefone
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cidade
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {clientes.map((cliente) => (
                <tr key={cliente.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {cliente.nome}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {cliente.cpf}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {cliente.telefone}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {cliente.cidade}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEditar(cliente.id)}
                        className="flex items-center gap-1 text-blue-600 hover:text-blue-900 transition-colors"
                        title="Editar"
                      >
                        <FilePenLine className="w-4 h-4" />
                        Editar
                      </button>
                      <button
                        onClick={() => handleExcluir(cliente.id, cliente.nome)}
                        className="flex items-center gap-1 text-red-600 hover:text-red-900 transition-colors"
                        title="Excluir"
                      >
                        <Trash2 className="w-4 h-4" />
                        Excluir
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Estado vazio (caso não haja clientes) */}
      {clientes.length === 0 && (
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Nenhum cliente cadastrado
          </h3>
          <p className="text-gray-500 mb-4">
            Comece adicionando seu primeiro cliente ao sistema.
          </p>
          <button
            onClick={handleAdicionar}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors mx-auto"
          >
            <PlusCircle className="w-5 h-5" />
            Adicionar Cliente
          </button>
        </div>
      )}
    </div>
  );
};

export default Clientes;
