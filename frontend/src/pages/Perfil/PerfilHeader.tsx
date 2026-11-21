import React from 'react';
import { Avatar, Typography, Tag } from 'antd';
import { UserOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { Usuario } from './perfilTypes';

const { Title, Text } = Typography;

const PerfilHeader: React.FC<{ user: Usuario }> = ({ user }) => (
  <header className="perfil-page__cabecera">
    <Avatar
      size={88}
      src={user.foto_url || undefined}
      icon={<UserOutlined />}
      className="perfil-page__avatar"
    />
    <div className="perfil-page__datos">
      <Title level={2}>
        {user.nombre} {user.apellido_paterno}
      </Title>
      <Text type="secondary">
        {user.email}
      </Text>
      <div className="perfil-page__etiquetas">
        <Tag icon={<SafetyCertificateOutlined />}>
          {user.rol?.toUpperCase() || 'USUARIO'}
        </Tag>
        {user.especialidad && (
          <Tag>{user.especialidad}</Tag>
        )}
        <Tag color={user.activo ? 'success' : 'error'}>
          {user.activo ? 'CUENTA ACTIVA' : 'SUSPENDIDO'}
        </Tag>
      </div>
    </div>
  </header>
);

export default PerfilHeader;
