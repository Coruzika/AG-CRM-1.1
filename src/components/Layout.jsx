import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const Layout = () => {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content */}
      <div className="flex-1 lg:ml-64 overflow-y-auto">
        <main className="h-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
