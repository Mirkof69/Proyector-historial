/**
 * =============================================================================
 * DASHBOARD PRINCIPAL - LAYOUT WRAPPER
 * =============================================================================
 * Gestiona el layout principal y la verificación de sesión.
 * Las rutas ahora son manejadas centralmente en App.tsx.
 * =============================================================================
 */

import React, { useEffect } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { Spin } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import MainLayout from '../../components/layout/MainLayout';
import './DashboardHome.css';
import { authService } from '../../services/authService';
import { FRONTEND_ROUTES } from '../../config/routes';

interface DashboardProps {
  children?: React.ReactNode;
  onLogout?: () => void;
}

const loadingIcon = <LoadingOutlined style={{ fontSize: 48 }} spin />;

const Dashboard: React.FC<DashboardProps> = ({ children, onLogout }) => {
  const navigate = useNavigate();
  const loc = useLocation();
  const authenticated = authService.isAuthenticated();

  useEffect(() => {
    if (!authenticated) {
      navigate(FRONTEND_ROUTES.LOGIN, {
        replace: true,
        state: { from: loc.pathname }
      });
    }
  }, [authenticated, navigate, loc.pathname]);

  if (!authenticated) {
    return (
      <div className="dashboard-verificando">
        <Spin size="large" indicator={loadingIcon} />
        <div className="dashboard-verificando__texto">Cargando sistema…</div>
      </div>
    );
  }

  return (
    <MainLayout onLogout={onLogout}>
      {children || <Outlet />}
    </MainLayout>
  );
};

export default Dashboard;
