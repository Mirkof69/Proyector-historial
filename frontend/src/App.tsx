// ===========================================
// APP PRINCIPAL - CONFIGURACIÓN COMPLETA
// ===========================================

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  HeartOutlined,
  BabyCarriageOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/dashboard/Dashboard';
import PacientesPage from './pages/pacientes/PacientesPage';
import EmbarazosPage from './pages/embarazos/EmbarazosPage';
import PartosPage from './pages/partos/PartosPage';
import UsuariosPage from './pages/usuarios/UsuariosPage';
import './App.css';

const { Header, Content, Sider } = Layout;

// Componente para proteger rutas
const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

// Layout principal con menú
const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const currentPath = window.location.pathname;

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/pacientes',
      icon: <TeamOutlined />,
      label: 'Pacientes',
    },
    {
      key: '/embarazos',
      icon: <HeartOutlined />,
      label: 'Embarazos',
    },
    {
      key: '/partos',
      icon: <BabyCarriageOutlined />,
      label: 'Partos',
    },
    {
      key: '/usuarios',
      icon: <UserOutlined />,
      label: 'Usuarios',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible>
        <div style={{ padding: '16px', color: 'white', textAlign: 'center', fontSize: '16px', fontWeight: 'bold' }}>
          Sistema Médico
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[currentPath]}
          items={menuItems}
          onClick={({ key }) => window.location.href = key}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
            Bienvenido, {user?.nombre_completo}
          </div>
          <div>
            <a onClick={logout} style={{ cursor: 'pointer' }}>
              <LogoutOutlined /> Cerrar Sesión
            </a>
          </div>
        </Header>
        <Content style={{ margin: '24px 16px 0' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

// Componente principal de rutas
const AppRoutes: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Dashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/pacientes"
          element={
            <ProtectedRoute>
              <MainLayout>
                <PacientesPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/embarazos"
          element={
            <ProtectedRoute>
              <MainLayout>
                <EmbarazosPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/partos"
          element={
            <ProtectedRoute>
              <MainLayout>
                <PartosPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/usuarios"
          element={
            <ProtectedRoute>
              <MainLayout>
                <UsuariosPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
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
