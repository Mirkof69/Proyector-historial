// ===========================================
// APP PRINCIPAL - CONFIGURACIÓN DE RUTAS
// ===========================================

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/dashboard/Dashboard';
import './App.css';

const { Content } = Layout;

// Componente para proteger rutas
const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

// Componente principal de rutas
const AppRoutes: React.FC = () => {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Content>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Router>
  );
};

// App principal
const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
};

export default App;
