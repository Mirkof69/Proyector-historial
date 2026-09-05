import React from 'react';
import { Drawer, Avatar, Typography, Divider, Descriptions, Badge, Tag } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { Usuario } from '../../../services/usuariosService';
import { configuracionDeRol } from '../../../config/roles';

const { Title, Text } = Typography;

const userIcon = <UserOutlined />;

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
          <Avatar size={100} src={usuario.foto_url} icon={userIcon} style={{ backgroundColor: configuracionDeRol(usuario.rol).color }} />
          <Title level={4} style={{ marginTop: 16 }}>{usuario.nombre_completo}</Title>
          {/* `configuracionDeRol` siempre devuelve un nombre. Antes esto era
              `ROLES_CONFIG[rol]?.nombre` sin alternativa, y para enfermera,
              laboratorista y recepcion pintaba una etiqueta VACIA: parecia que
              la usuaria no tuviera rol asignado. */}
          <Tag color={configuracionDeRol(usuario.rol).color} icon={configuracionDeRol(usuario.rol).icono}>
            {configuracionDeRol(usuario.rol).nombre}
          </Tag>
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
