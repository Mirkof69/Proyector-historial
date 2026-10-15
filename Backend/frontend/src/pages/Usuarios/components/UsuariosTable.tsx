import React from 'react';
import { Empty, Table, Avatar, Space, Tag, Tooltip, Switch, Button, Popconfirm, Typography } from 'antd';
import { UserOutlined, MailOutlined, PhoneOutlined, EyeOutlined, EditOutlined, KeyOutlined, DeleteOutlined, CheckCircleOutlined, StopOutlined, SafetyOutlined } from '@ant-design/icons';
import { Usuario } from '../../../services/usuariosService';
import { configuracionDeRol } from '../../../config/roles';

const { Text } = Typography;

const userIcon = <UserOutlined />;
const eyeIcon = <EyeOutlined />;
const editIcon = <EditOutlined />;
const keyIcon = <KeyOutlined />;
const deleteIcon = <DeleteOutlined />;
const checkCircleIcon = <CheckCircleOutlined />;
const stopIcon = <StopOutlined />;
const mfaIcon = <SafetyOutlined />;

interface UsuariosTableProps {
  usuarios: Usuario[];
  loading: boolean;
  onVisualizar: (usuario: Usuario) => void;
  onEditar: (usuario: Usuario) => void;
  onCambiarPassword: (usuario: Usuario) => void;
  onEliminar: (id: number) => void;
  onToggleActivo: (usuario: Usuario) => void;
  onRestablecerMfa: (usuario: Usuario) => void;
}

const UsuariosTable: React.FC<UsuariosTableProps> = ({
  usuarios,
  loading,
  onVisualizar,
  onEditar,
  onCambiarPassword,
  onEliminar,
  onToggleActivo,
  onRestablecerMfa
}) => {
  const columnas = [
    {
      title: 'Avatar',
      dataIndex: 'foto_url',
      key: 'foto_url',
      width: 80,
      render: (foto_url: string | null) => (
        <Avatar size={40} src={foto_url} icon={userIcon} className="usuarios-page__avatar" />
      ),
    },
    {
      title: 'Nombre Completo',
      dataIndex: 'nombre_completo',
      key: 'nombre_completo',
      render: (_: any, record: Usuario) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.nombre_completo || `${record.nombre} ${record.apellido_paterno}`}</Text>
          <Text type="secondary" className="usuarios-page__iniciales">{record.iniciales || ''}</Text>
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      render: (email: string) => (<Space><MailOutlined /><Text>{email}</Text></Space>),
    },
    {
      title: 'Rol',
      dataIndex: 'rol',
      key: 'rol',
      render: (rol: string, record: Usuario) => {
        const config = configuracionDeRol(rol);
        return (
          <Space direction="vertical" size={2}>
            <Tag icon={config.icono}>{config.nombre}</Tag>
            {record.cargo_nombre && <Text type="secondary">{record.cargo_nombre}</Text>}
          </Space>
        );
      },
    },
    {
      title: 'Especialidad',
      dataIndex: 'especialidad',
      key: 'especialidad',
      render: (especialidad: string) => especialidad || '-',
    },
    {
      title: 'Teléfono',
      dataIndex: 'telefono',
      key: 'telefono',
      render: (telefono: string) => (telefono ? (<Space><PhoneOutlined /><Text>{telefono}</Text></Space>) : '-'),
    },
    {
      title: 'Estado',
      dataIndex: 'activo',
      key: 'activo',
      render: (activo: boolean, record: Usuario) => (
        <Tooltip title={activo ? 'Click para desactivar' : 'Click para activar'}>
          <Switch checked={activo} onChange={() => onToggleActivo(record)} checkedChildren={checkCircleIcon} unCheckedChildren={stopIcon} />
        </Tooltip>
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as const,
      width: 240,
      render: (_: any, record: Usuario) => (
        <Space>
          <Tooltip title="Ver detalles"><Button type="text" icon={eyeIcon} onClick={() => onVisualizar(record)} /></Tooltip>
          <Tooltip title="Editar"><Button type="text" icon={editIcon} onClick={() => onEditar(record)} /></Tooltip>
          <Tooltip title="Cambiar contraseña"><Button type="text" icon={keyIcon} onClick={() => onCambiarPassword(record)} /></Tooltip>
          <Popconfirm title="¿Restablecer el MFA?" description="Para quien perdió o cambió el celular: al entrar configurará Google Authenticator de nuevo." onConfirm={() => onRestablecerMfa(record)} okText="Restablecer" cancelText="Cancelar">
            <Tooltip title="Restablecer MFA (celular perdido)"><Button type="text" icon={mfaIcon} aria-label="Restablecer MFA" /></Tooltip>
          </Popconfirm>
          <Popconfirm title="¿Eliminar usuario?" description="Esta acción no se puede deshacer" onConfirm={() => onEliminar(record.id!)} okText="Eliminar" cancelText="Cancelar" okButtonProps={{ danger: true }}>
            <Tooltip title="Eliminar"><Button type="text" danger icon={deleteIcon} /></Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columnas}
      dataSource={usuarios}
      locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay usuarios registrados" /> }}
      rowKey="id"
      loading={loading}
      pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `Total: ${total} usuarios` }}
      scroll={{ x: 1200 }}
    />
  );
};

export default UsuariosTable;
