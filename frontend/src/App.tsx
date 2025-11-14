/**
 * =============================================================================
 * APLICACIÓN PRINCIPAL
 * =============================================================================
 * Configuración de routing y autenticación
 * =============================================================================
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import esES from 'antd/locale/es_ES';

// Pages
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import RegistroPaciente from './pages/RegistroPaciente';
import Dashboard from './pages/Dashboard';

// Services
import { authService } from './services/authService';

// Componente para rutas protegidas
interface ProtectedRouteProps {
  children: React.ReactElement;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const isAuthenticated = authService.isAuthenticated();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

function App() {
  return (
    <ConfigProvider locale={esES}>
      <Router>
        <Routes>
          {/* Rutas Públicas */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<RegistroPaciente />} />

          {/* Rutas Protegidas */}
          <Route
            path="/dashboard/*"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          {/* Redirigir rutas no encontradas */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ConfigProvider>
  );
}

export default App;
