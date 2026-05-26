import React from 'react';
import { Result, Button, Typography, Card, Alert } from 'antd';
import { useNavigate } from 'react-router-dom';
import {
  LockOutlined,
  SafetyCertificateOutlined,
  LogoutOutlined,
  HomeOutlined
} from '@ant-design/icons';
import { authService } from '../services/authService';

const lockIcon = <LockOutlined style={{ color: '#ff4d4f' }} />;
const safetyCertIcon = <SafetyCertificateOutlined />;

const unauthorizedSubTitle = (user: { nombre?: string; rol?: string } | null) => (
  <div style={{ margin: '20px 0' }}>
    <Paragraph style={{ fontSize: 16 }}>
      Lo sentimos, <strong>{user?.nombre || 'Usuario'}</strong>. No tienes los permisos necesarios para acceder a esta sección.
    </Paragraph>

    <Alert
      message="Permisos Insuficientes"
      description={
        <span>
          Tu rol actual es <Text code>{user?.rol?.toUpperCase() || 'INVITADO'}</Text>.
          Esta página requiere privilegios de <strong>ADMINISTRADOR</strong> o <strong>MÉDICO TITULAR</strong>.
        </span>
      }
      type="error"
      showIcon
      icon={safetyCertIcon}
      style={{ textAlign: 'left', maxWidth: 500, margin: '0 auto' }}
    />
  </div>
);

const { Paragraph, Text } = Typography;

const Unauthorized: React.FC = () => {
  const navigate = useNavigate();
  const user = authService.getCurrentUser(); // Asumimos que esto devuelve { rol: 'enfermero', ... }

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  return (
    <div className="unauthorized-container animate-fade-in" style={{
      height: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-gradient(135deg, #fff1f0 0%, #fff 100%)' // Fondo rojizo sutil para alerta
    }}>
      <Card
        variant="borderless"
        style={{
          maxWidth: 700,
          width: '90%',
          borderRadius: 16,
          boxShadow: '0 10px 30px rgba(255, 77, 79, 0.15)', // Sombra rojiza
          textAlign: 'center',
          borderTop: '6px solid #ff4d4f'
        }}
      >
        <Result
          status="403"
          icon={lockIcon}
          title={<span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>Acceso Restringido (403)</span>}
          subTitle={unauthorizedSubTitle(user)}
          extra={
            <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 20 }}>
              <Button
                type="primary"
                size="large"
                icon={<HomeOutlined />}
                onClick={() => navigate('/')}
                style={{ minWidth: 150, background: '#ff4d4f', borderColor: '#ff4d4f' }}
              >
                Ir al Dashboard
              </Button>

              <Button
                size="large"
                icon={<LogoutOutlined />}
                onClick={handleLogout}
              >
                Cerrar Sesión
              </Button>
            </div>
          }
        />

        <div style={{ marginTop: 30 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Si crees que esto es un error, contacta al Administrador del Sistema.
            <br />
            Ref: SEC-403-ACCESS-DENIED
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default Unauthorized;
