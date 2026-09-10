import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface AuthContextType {
  isAuthenticated: boolean;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem('isAuth') === 'true';
  });

  useEffect(() => {
    // Listen for unauthorized events to automatically logout
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener('unauthorized', handleUnauthorized);
    return () => window.removeEventListener('unauthorized', handleUnauthorized);
  }, []);

  const login = () => {
    setIsAuthenticated(true);
    localStorage.setItem('isAuth', 'true');
  };

  const logout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('isAuth');
    void apiClient.post('/auth/logout').catch(() => undefined);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
