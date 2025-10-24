import React, { useState } from 'react';
import { Layout, Menu, Button } from 'antd';
import {
  UserOutlined,
  MedicineBoxOutlined,
  HeartOutlined,
  CalculatorOutlined,
  LogoutOutlined,
  DashboardOutlined
} from '@ant-design/icons';
import { authService } from '../services/authService';
import Pacientes from './Pacientes';
import Embarazos from './Embarazos';
import Controles from './Controles';
import Calculadoras from './Calculadoras';

const { Header, Sider, Content } = Layout;

interface DashboardProps {
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const user = authService.getCurrentUser();
  const [selectedMenu, setSelectedMenu] = useState('dashboard');

  const handleLogout = () => {
    authService.logout();
    onLogout();
  };

  const renderContent = () => {
    switch (selectedMenu) {
      case 'pacientes':
        return <Pacientes />;
      case 'embarazos':
        return <Embarazos />;
      case 'controles':
        return <Controles />;
      case 'calculadoras':
        return <Calculadoras />;
      case 'dashboard':
      default:
        return (
          <div style={{ padding: 24, background: '#fff' }}>
            <h1>Bienvenido al Sistema de Historial Clínico</h1>
            <p>Selecciona una opción del menú para comenzar.</p>
          </div>
        );
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" breakpoint="lg" collapsedWidth="0">
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'white',
          fontSize: '18px',
          fontWeight: 'bold'
        }}>
          Historial Clínico
        </div>
        <Menu 
          theme="dark" 
          mode="inline" 
          selectedKeys={[selectedMenu]}
          onClick={({ key }) => setSelectedMenu(key)}
        >
          <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
            Dashboard
          </Menu.Item>
          <Menu.Item key="pacientes" icon={<UserOutlined />}>
            Pacientes
          </Menu.Item>
          <Menu.Item key="embarazos" icon={<HeartOutlined />}>
            Embarazos
          </Menu.Item>
          <Menu.Item key="controles" icon={<MedicineBoxOutlined />}>
            Controles
          </Menu.Item>
          <Menu.Item key="calculadoras" icon={<CalculatorOutlined />}>
            Calculadoras
          </Menu.Item>
        </Menu>
      </Sider>
      
      <Layout>
        <Header style={{ 
          background: '#fff', 
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: 0 }}>Dashboard</h2>
          <div>
            <span style={{ marginRight: 16 }}>
              {user?.nombre} ({user?.rol})
            </span>
            <Button 
              icon={<LogoutOutlined />} 
              onClick={handleLogout}
            >
              Cerrar Sesión
            </Button>
          </div>
        </Header>
        
        <Content style={{ margin: '24px 16px 0' }}>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
};

export default Dashboard;