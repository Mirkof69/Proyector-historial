/**
 * =============================================================================
 * LAYOUT PRINCIPAL
 * =============================================================================
 * Layout con Sidebar y Header para el sistema
 * =============================================================================
 */

import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Typography, Space, Badge } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  TeamOutlined,
  HeartOutlined,
  MedicineBoxOutlined,
  CalculatorOutlined,
  FileTextOutlined,
  SettingOutlined,
  LogoutOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  FundOutlined,
  ExperimentOutlined,
  CalendarOutlined,
  MedicineBoxFilled,
  BarChartOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../../services/authService';
import './MainLayout.css';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const currentUser = authService.getCurrentUser();

  const handleLogout = async () => {
    await authService.logout();
    navigate('/login');
  };

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/dashboard/pacientes',
      icon: <UserOutlined />,
      label: 'Pacientes',
    },
    {
      key: '/dashboard/embarazos',
      icon: <HeartOutlined />,
      label: 'Embarazos',
    },
    {
      key: '/dashboard/controles',
      icon: <MedicineBoxOutlined />,
      label: 'Controles Prenatales',
    },
    {
      key: '/dashboard/ecografias',
      icon: <FundOutlined />,
      label: 'Ecografías',
    },
    {
      key: '/dashboard/laboratorio',
      icon: <ExperimentOutlined />,
      label: 'Laboratorio',
    },
    {
      key: '/dashboard/citas',
      icon: <CalendarOutlined />,
      label: 'Citas',
    },
    {
      key: '/dashboard/partos',
      icon: <MedicineBoxFilled />,
      label: 'Partos',
    },
    {
      key: '/dashboard/calculadoras',
      icon: <CalculatorOutlined />,
      label: 'Calculadoras FMF',
    },
    {
      key: '/dashboard/calculadoras-avanzadas',
      icon: <BarChartOutlined />,
      label: 'Calculadoras Avanzadas',
    },
    {
      key: '/dashboard/reportes',
      icon: <FileTextOutlined />,
      label: 'Reportes',
    },
    {
      key: '/dashboard/usuarios',
      icon: <TeamOutlined />,
      label: 'Usuarios',
    },
  ];

  const userMenu = {
    items: [
      {
        key: 'profile',
        icon: <UserOutlined />,
        label: 'Mi Perfil',
        onClick: () => navigate('/dashboard/perfil'),
      },
      {
        key: 'settings',
        icon: <SettingOutlined />,
        label: 'Configuración',
        onClick: () => navigate('/dashboard/configuracion'),
      },
      {
        type: 'divider' as const,
      },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: 'Cerrar Sesión',
        onClick: handleLogout,
        danger: true,
      },
    ],
  };

  return (
    <Layout className="main-layout">
      {/* SIDEBAR */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="main-sider"
        width={250}
      >
        <div className="logo-container">
          <HeartOutlined className="logo-icon" />
          {!collapsed && (
            <Text strong className="logo-text">
              Fetal Medical
            </Text>
          )}
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>

      <Layout>
        {/* HEADER */}
        <Header className="main-header">
          <div className="header-left">
            {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
              className: 'trigger',
              onClick: () => setCollapsed(!collapsed),
            })}
            <Text strong className="page-title">
              Sistema de Historial Médico Obstétrico
            </Text>
          </div>

          <Space size="large" className="header-right">
            <Badge count={5} className="notification-badge">
              <BellOutlined style={{ fontSize: 20 }} />
            </Badge>

            <Dropdown menu={userMenu} placement="bottomRight">
              <div className="user-info">
                <Avatar icon={<UserOutlined />} />
                <div className="user-details">
                  <Text strong>{currentUser?.nombre} {currentUser?.apellido}</Text>
                  <Text type="secondary" className="user-role">
                    {currentUser?.rol?.toUpperCase()}
                  </Text>
                </div>
              </div>
            </Dropdown>
          </Space>
        </Header>

        {/* CONTENT */}
        <Content className="main-content">
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
