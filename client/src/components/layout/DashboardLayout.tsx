import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Navbar } from './Navbar';
import { Footer } from './Footer';

export const DashboardLayout: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { pathname } = useLocation();
  const isDocumentWorkspace = pathname.startsWith('/document/');

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <main className={`flex-1 w-full ${isDocumentWorkspace ? 'max-w-[1440px]' : 'max-w-7xl'} mx-auto px-4 sm:px-6 lg:px-8 py-8`}>
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};

export const RootLayout: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};
