import React, { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import ptBrLocale from '@fullcalendar/core/locales/pt-br';

// FullCalendar v6 injeta estilos automaticamente - não é necessário importar CSS

const CalendarioVencimentos = () => {
  const [events, setEvents] = useState([]);
  const [estatisticas, setEstatisticas] = useState(null);
  const [proximosVencimentos, setProximosVencimentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentData, setPaymentData] = useState({
    valor_pago: 0,
    forma_pagamento: 'Dinheiro',
    observacoes: ''
  });

  // Carregar dados iniciais
  useEffect(() => {
    carregarDados();
  }, []);

  const carregarDados = async () => {
    setLoading(true);
    try {
      const [eventosResponse, statsResponse] = await Promise.all([
        fetch('/api/calendario/eventos'),
        fetch('/api/calendario/estatisticas')
      ]);

      const eventos = await eventosResponse.json();
      const stats = await statsResponse.json();

      setEvents(eventos);
      setEstatisticas(stats);
      setProximosVencimentos(stats.proximos_vencimentos);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  // Manipulador para clique em evento
  const handleEventClick = (clickInfo) => {
    const evento = clickInfo.event;
    const props = evento.extendedProps;
    
    setSelectedEvent({
      id: evento.id,
      title: evento.title,
      start: evento.start,
      ...props
    });
  };

  // Processar pagamento
  const processarPagamento = async () => {
    if (!selectedEvent) return;

    try {
      const response = await fetch(`/api/calendario/pagar/${selectedEvent.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(paymentData)
      });

      const result = await response.json();

      if (result.success) {
        alert('Pagamento registrado com sucesso!');
        setShowPaymentModal(false);
        setSelectedEvent(null);
        carregarDados(); // Recarregar dados
      } else {
        alert('Erro: ' + result.message);
      }
    } catch (error) {
      console.error('Erro ao processar pagamento:', error);
      alert('Erro ao processar pagamento');
    }
  };


  // Converter eventos para formato do FullCalendar
  const eventosCalendario = events.map(evento => ({
    id: evento.id.toString(),
    title: evento.title,
    start: evento.start,
    backgroundColor: evento.backgroundColor,
    borderColor: evento.borderColor,
    textColor: evento.textColor,
    extendedProps: evento.extendedProps
  }));

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-xl p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando calendário...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-t-xl shadow-xl p-6 text-center">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            📅 Calendário de Vencimentos
          </h1>
          <p className="text-gray-600">
            Visualize e gerencie as datas de vencimento das cobranças
          </p>
        </div>

        {/* Estatísticas */}
        {estatisticas && (
          <div className="bg-white shadow-xl p-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg p-6 text-center">
                <div className="text-3xl font-bold">{estatisticas.contadores.pagas}</div>
                <div className="text-lg font-medium">Pagas</div>
                <div className="text-sm opacity-90">
                  R$ {estatisticas.valores.pagas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg p-6 text-center">
                <div className="text-3xl font-bold">{estatisticas.contadores.vencidas}</div>
                <div className="text-lg font-medium">Vencidas</div>
                <div className="text-sm opacity-90">
                  R$ {estatisticas.valores.vencidas.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg p-6 text-center">
                <div className="text-3xl font-bold">{estatisticas.contadores.a_pagar}</div>
                <div className="text-lg font-medium">A Pagar</div>
                <div className="text-sm opacity-90">
                  R$ {estatisticas.valores.a_pagar.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-gray-500 to-gray-600 text-white rounded-lg p-6 text-center">
                <div className="text-3xl font-bold">{estatisticas.contadores.canceladas}</div>
                <div className="text-lg font-medium">Canceladas</div>
                <div className="text-sm opacity-90">-</div>
              </div>
            </div>
          </div>
        )}

        {/* Legenda */}
        <div className="bg-white shadow-xl p-6">
          <div className="flex flex-wrap justify-center gap-8">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-green-500"></div>
              <span className="text-gray-700 font-medium">Pagas</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-red-500"></div>
              <span className="text-gray-700 font-medium">Vencidas</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-blue-500"></div>
              <span className="text-gray-700 font-medium">A Pagar</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-gray-500"></div>
              <span className="text-gray-700 font-medium">Canceladas</span>
            </div>
          </div>
        </div>

        {/* Calendário */}
        <div className="bg-white shadow-xl rounded-lg p-6 mb-6">
          <FullCalendar
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
            initialView="dayGridMonth"
            locale={ptBrLocale}
            headerToolbar={{
              left: 'prev,next today',
              center: 'title',
              right: 'dayGridMonth,dayGridWeek,timeGridDay'
            }}
            buttonText={{
              today: 'Hoje',
              month: 'Mês',
              week: 'Semana',
              day: 'Dia'
            }}
            events={eventosCalendario}
            eventClick={handleEventClick}
            height="auto"
            dayMaxEvents={3}
            moreLinkClick="popover"
            eventDisplay="block"
            dayHeaderFormat={{
              weekday: 'short'
            }}
          />
        </div>

        {/* Próximos Vencimentos */}
        <div className="bg-white shadow-xl rounded-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">
            ⏰ Próximos Vencimentos (7 dias)
          </h3>
          
          {proximosVencimentos.length === 0 ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-yellow-800">
                <i className="fas fa-info-circle mr-2"></i>
                Nenhum vencimento nos próximos 7 dias.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {proximosVencimentos.map((vencimento, index) => {
                const dataVenc = new Date(vencimento.data_vencimento);
                const hoje = new Date();
                const diasRestantes = Math.ceil((dataVenc - hoje) / (1000 * 60 * 60 * 24));
                
                return (
                  <div key={index} className="bg-gray-50 rounded-lg p-4 border-l-4 border-yellow-400">
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="font-semibold text-gray-800">{vencimento.cliente_nome}</h4>
                        <p className="text-sm text-gray-600">{vencimento.descricao}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-red-600">
                          R$ {vencimento.valor.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                        </div>
                        <div className="text-sm text-gray-500">
                          {dataVenc.toLocaleDateString('pt-BR')}
                        </div>
                        <div className={`text-xs font-medium ${
                          diasRestantes <= 1 ? 'text-red-600' : 'text-yellow-600'
                        }`}>
                          {diasRestantes === 0 ? 'Vence hoje' : 
                           diasRestantes === 1 ? 'Vence amanhã' : 
                           `${diasRestantes} dias`}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Modal de Detalhes */}
        {selectedEvent && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-800">Detalhes da Cobrança</h2>
                  <button
                    onClick={() => setSelectedEvent(null)}
                    className="text-gray-500 hover:text-gray-700 text-2xl"
                  >
                    ×
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Cliente:</label>
                    <div className="p-3 bg-gray-50 rounded-lg font-semibold">
                      {selectedEvent.cliente_nome}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Descrição:</label>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      {selectedEvent.descricao}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Valor Original:</label>
                      <div className="p-3 bg-gray-50 rounded-lg font-semibold">
                        R$ {selectedEvent.valor_original.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Valor Total:</label>
                      <div className="p-3 bg-red-50 rounded-lg font-semibold text-red-600">
                        R$ {selectedEvent.valor_total.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                      </div>
                    </div>
                  </div>

                  {(selectedEvent.multa > 0 || selectedEvent.juros > 0) && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Multa:</label>
                        <div className="p-3 bg-gray-50 rounded-lg">
                          R$ {selectedEvent.multa.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                        </div>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Juros:</label>
                        <div className="p-3 bg-gray-50 rounded-lg">
                          R$ {selectedEvent.juros.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status:</label>
                      <div className={`p-3 rounded-lg font-semibold ${
                        selectedEvent.status === 'Pago' ? 'bg-green-100 text-green-800' :
                        selectedEvent.status === 'Pendente' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {selectedEvent.status}
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Dias de Atraso:</label>
                      <div className={`p-3 rounded-lg font-semibold ${
                        selectedEvent.dias_atraso > 0 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'
                      }`}>
                        {selectedEvent.dias_atraso > 0 ? `${selectedEvent.dias_atraso} dias` : 'Em dia'}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Telefone:</label>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        {selectedEvent.cliente_telefone || 'Não informado'}
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email:</label>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        {selectedEvent.cliente_email || 'Não informado'}
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-center space-x-4 pt-6">
                    {selectedEvent.status === 'Pendente' && (
                      <button
                        onClick={() => {
                          setPaymentData({
                            valor_pago: selectedEvent.valor_total,
                            forma_pagamento: 'Dinheiro',
                            observacoes: ''
                          });
                          setShowPaymentModal(true);
                        }}
                        className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                      >
                        💳 Registrar Pagamento
                      </button>
                    )}
                    <button
                      onClick={() => setSelectedEvent(null)}
                      className="bg-gray-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-600 transition-colors"
                    >
                      ✕ Fechar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal de Pagamento */}
        {showPaymentModal && selectedEvent && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold text-gray-800">Registrar Pagamento</h2>
                  <button
                    onClick={() => setShowPaymentModal(false)}
                    className="text-gray-500 hover:text-gray-700 text-2xl"
                  >
                    ×
                  </button>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <p className="text-blue-800">
                    <i className="fas fa-info-circle mr-2"></i>
                    Registrando pagamento para: <strong>{selectedEvent.cliente_nome}</strong>
                  </p>
                </div>

                <form onSubmit={(e) => {
                  e.preventDefault();
                  processarPagamento();
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Valor a Pagar:
                      </label>
                      <input
                        type="number"
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        value={paymentData.valor_pago}
                        onChange={(e) => setPaymentData({
                          ...paymentData,
                          valor_pago: parseFloat(e.target.value) || 0
                        })}
                        step="0.01"
                        min="0"
                        required
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Valor total: R$ {selectedEvent.valor_total.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Forma de Pagamento:
                      </label>
                      <select
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        value={paymentData.forma_pagamento}
                        onChange={(e) => setPaymentData({
                          ...paymentData,
                          forma_pagamento: e.target.value
                        })}
                        required
                      >
                        <option value="Dinheiro">Dinheiro</option>
                        <option value="PIX">PIX</option>
                        <option value="Cartão de Débito">Cartão de Débito</option>
                        <option value="Cartão de Crédito">Cartão de Crédito</option>
                        <option value="Transferência">Transferência Bancária</option>
                        <option value="Boleto">Boleto</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Observações:
                      </label>
                      <textarea
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        rows="3"
                        value={paymentData.observacoes}
                        onChange={(e) => setPaymentData({
                          ...paymentData,
                          observacoes: e.target.value
                        })}
                        placeholder="Observações sobre o pagamento (opcional)"
                      />
                    </div>
                  </div>

                  <div className="flex justify-center space-x-4 mt-6">
                    <button
                      type="submit"
                      className="bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
                    >
                      ✅ Confirmar Pagamento
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowPaymentModal(false)}
                      className="bg-gray-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-600 transition-colors"
                    >
                      ✕ Cancelar
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CalendarioVencimentos;
