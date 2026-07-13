import React from 'react';
import { Drawer, Avatar, Typography, Divider, Descriptions, Badge, Tag } from 'antd';
import { UserOutlined, MedicineBoxOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { Usuario } from '../../../services/usuariosService';

const { Title, Text } = Typography;

const userIcon = <UserOutlined />;

interface ROLES_CONFIG_TYPE {
  nombre: string;
  color: string;
  icon: React.ReactNode;
}

const ROLES_CONFIG: Record<string, ROLES_CONFIG_TYPE> = {
  medico: { nombre: 'Médico', color: '#3498db', icon: <MedicineBoxOutlined /> },
  enfermero: { nombre: 'Enfermero', color: '#2ecc71', icon: <MedicineBoxOutlined /> },
  administrador: { nombre: 'Administrador', color: '#e74c3c', icon: <SafetyCertificateOutlined /> },
};

interface UsuarioDetailDrawerProps {
  usuario: Usuario | null;
  open: boolean;
  onClose: () => void;
}

const UsuarioDetailDrawer: React.FC<UsuarioDetailDrawerProps> = ({ usuario, open, onClose }) => {
  if (!usuario) return null;

  return (
    <Drawer title="Detalles del Usuario" width={600} open={open} onClose={onClose}>
      <div>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Avatar size={100} src={usuario.foto_url} icon={userIcon} style={{ backgroundColor: ROLES_CONFIG[usuario.rol]?.color }} />
          <Title level={4} style={{ marginTop: 16 }}>{usuario.nombre_completo}</Title>
          <Tag color={ROLES_CONFIG[usuario.rol]?.color}>{ROLES_CONFIG[usuario.rol]?.nombre}</Tag>
        </div>

        <Divider>Información Personal</Divider>
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="Email">{usuario.email}</Descriptions.Item>
          <Descriptions.Item label="Nombre">{usuario.nombre}</Descriptions.Item>
          <Descriptions.Item label="Apellido Paterno">{usuario.apellido_paterno}</Descriptions.Item>
          <Descriptions.Item label="Apellido Materno">{usuario.apellido_materno || '-'}</Descriptions.Item>
          <Descriptions.Item label="Teléfono">{usuario.telefono || '-'}</Descriptions.Item>
          <Descriptions.Item label="Especialidad">{usuario.especialidad || '-'}</Descriptions.Item>
        </Descriptions>

        <Divider>Estado</Divider>
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="Estado">
            <Badge status={usuario.activo ? 'success' : 'error'} text={usuario.activo ? 'Activo' : 'Inactivo'} />
          </Descriptions.Item>
          <Descriptions.Item label="Staff">{usuario.is_staff ? 'Sí' : 'No'}</Descriptions.Item>
          <Descriptions.Item label="Superusuario">{usuario.is_superuser ? 'Sí' : 'No'}</Descriptions.Item>
        </Descriptions>

        {usuario.descripcion && (
          <>
            <Divider>Descripción</Divider>
            <Text>{usuario.descripcion}</Text>
          </>
        )}
      </div>
    </Drawer>
  );
};

export default UsuarioDetailDrawer;
