import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './index.css';
import Dashboard from './Dashboard';
import CalendarioVencimentos from './components/CalendarioVencimentos';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/calendario" element={<CalendarioVencimentos />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
