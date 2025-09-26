import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Home, BarChart3, Calendar, Users, Menu, X } from 'lucide-react';

const Sidebar = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const navItems = [
    { to: '/', icon: Home, label: 'Dashboard' },
    { to: '/relatorios', icon: BarChart3, label: 'Relatórios' },
    { to: '/calendario', icon: Calendar, label: 'Calendário' },
    { to: '/clientes', icon: Users, label: 'Clientes' }
  ];

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={toggleMobileMenu}
          className="p-2 bg-white rounded-lg shadow-md hover:bg-gray-50 transition-colors"
        >
          {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={toggleMobileMenu}
        />
      )}

      {/* Sidebar */}
      <div className={`bg-white shadow-lg h-screen w-64 fixed left-0 top-0 overflow-y-auto z-40 transform transition-transform duration-300 ${
        isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0`}>
        {/* Logo/Brand */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
              <span className="text-white font-bold text-lg">CRM</span>
            </div>
            <h1 className="text-xl font-bold text-gray-900">AG CRM</h1>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col p-4">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setIsMobileMenuOpen(false)}
              className={({ isActive }) =>
                `flex items-center p-2.5 my-1 rounded-lg transition-colors duration-200 ${
                  isActive
                    ? 'bg-blue-100 text-blue-800 font-semibold'
                    : 'text-gray-600 hover:bg-gray-100'
                }`
              }
            >
              <Icon className="w-5 h-5 mr-3" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="absolute bottom-0 w-full p-4 border-t border-gray-200">
          <div className="text-center">
            <p className="text-xs text-gray-500">Sistema de Gestão</p>
            <p className="text-xs text-gray-400">Versão 1.1</p>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
