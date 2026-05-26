import React, { createContext, useState, useMemo, useCallback, ReactNode } from 'react';
import { authService, Usuario, LoginCredentials } from '../services/authService';

interface AuthContextType {
  user: Usuario | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => void;
  hasPermission: (permission: string) => boolean;
  getToken: () => string | null;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<Usuario | null>(() => {
    const isAuth = authService.isAuthenticated();
    return isAuth ? authService.getCurrentUser() : null;
  });
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => authService.isAuthenticated());

  const refreshAuth = useCallback(() => {
    const isAuth = authService.isAuthenticated();
    setIsAuthenticated(isAuth);
    setUser(isAuth ? authService.getCurrentUser() : null);
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    await authService.login(credentials);
    setIsAuthenticated(true);
    setUser(authService.getCurrentUser());
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setIsAuthenticated(false);
    setUser(null);
  }, []);

  const hasPermission = useCallback((permission: string) => {
    return authService.hasPermission(permission);
  }, []);

  const getToken = useCallback(() => {
    return authService.getToken();
  }, []);

  const contextValue = useMemo(() => ({ user, isAuthenticated, login, logout, refreshAuth, hasPermission, getToken }), [user, isAuthenticated, login, logout, refreshAuth, hasPermission, getToken]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};
