import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../common/Button';
import { Scale, LogOut } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <Link to="/" className="flex items-center space-x-2 text-primary">
            <Scale className="h-6 w-6 text-accent" />
            <span className="font-bold text-xl tracking-tight">Legal<span className="text-accent">ze</span></span>
          </Link>
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" className="text-sm font-medium text-gray-700 hover:text-accent transition-colors">
                  Dashboard
                </Link>
                <Button variant="ghost" onClick={handleLogout} className="text-sm font-medium">
                  <LogOut className="h-4 w-4 mr-2" />
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm font-medium text-gray-700 hover:text-accent transition-colors">
                  Log in
                </Link>
                <Link to="/register">
                  <Button size="sm">Get Started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
