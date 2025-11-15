// ===========================================
// CONTEXT DE AUTENTICACIÓN
// ===========================================

import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { Usuario } from '../types';
import { AuthService } from '../services/api';

interface AuthContextType {
  user: Usuario | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (user: Usuario) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<Usuario | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Cargar usuario de localStorage al iniciar
    const loadUser = () => {
      const currentUser = AuthService.getCurrentUser();
      setUser(currentUser);
      setIsLoading(false);
    };

    loadUser();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await AuthService.login(username, password);
      setUser(response.user);
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await AuthService.logout();
    } finally {
      setUser(null);
    }
  };

  const updateUser = (updatedUser: Usuario) => {
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

