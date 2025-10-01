import React from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import './index.css';
import Layout from './components/Layout';
import Dashboard from './Dashboard';
import Relatorios from './Relatorios';
import CalendarioVencimentos from './components/CalendarioVencimentos';
import Clientes from './pages/Clientes';

function App() {
  console.log('🚀 App carregado, hash atual:', window.location.hash);
  
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="relatorios" element={<Relatorios />} />
            <Route path="calendario" element={<CalendarioVencimentos />} />
            <Route path="clientes" element={<Clientes />} />
          </Route>
        </Routes>
      </div>
    </Router>
  );
}

export default App;
