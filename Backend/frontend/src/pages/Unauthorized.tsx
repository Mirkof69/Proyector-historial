import React from 'react';
import { Result, Button, Typography, Alert } from 'antd';
import { useNavigate } from 'react-router-dom';
import {
  LockOutlined,
  SafetyCertificateOutlined,
  LogoutOutlined,
  HomeOutlined
} from '@ant-design/icons';
import { authService } from '../services/authService';

import './NotFound.css';

const { Paragraph, Text } = Typography;

const lockIcon = <LockOutlined className="pagina-estado__icono-403" />;
const safetyCertIcon = <SafetyCertificateOutlined />;

const unauthorizedSubTitle = (user: { nombre?: string; rol?: string } | null) => (
  <div className="pagina-estado__texto">
    <Paragraph>
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
      className="pagina-estado__aviso"
    />
  </div>
);

const Unauthorized: React.FC = () => {
  const navigate = useNavigate();
  const user = authService.getCurrentUser(); // Asumimos que esto devuelve { rol: 'enfermero', ... }

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  return (
    <div className="pagina-estado page-container">
      <div className="pagina-estado__tarjeta">
        <Result
          status="error"
          icon={lockIcon}
          title={<span className="pagina-estado__titulo-403">Acceso Restringido (403)</span>}
          subTitle={unauthorizedSubTitle(user)}
          extra={
            <div className="pagina-estado__acciones">
              <Button
                type="primary"
                icon={<HomeOutlined />}
                onClick={() => navigate('/')}
              >
                Ir al Dashboard
              </Button>

              <Button
                icon={<LogoutOutlined />}
                onClick={handleLogout}
              >
                Cerrar Sesión
              </Button>
            </div>
          }
        />

        <div className="pagina-estado__pie">
          Si crees que esto es un error, contacta al Administrador del Sistema.
          <br />
          Ref: SEC-403-ACCESS-DENIED
        </div>
      </div>
    </div>
  );
};

export default Unauthorized;
