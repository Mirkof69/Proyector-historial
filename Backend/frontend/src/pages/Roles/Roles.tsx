import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Space, Tag, Switch, Popconfirm } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, SafetyOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import rolesService from '../../services/rolesService';

interface Rol {
  id: number;
  nombre: string;
  descripcion?: string;
  permisos: string[];
  activo: boolean;
}

const Roles: React.FC = () => {
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const [roles, setRoles] = useState<Rol[]>([]);
  const [loading, setLoading] = useState(false);



  const cargarRoles = useCallback(async () => {
    setLoading(true);
    try {
      const data = await rolesService.listar();
      setRoles(data);
    } catch (error) {
      message.error('Error al cargar roles');
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    cargarRoles();
  }, [cargarRoles]);

  const handleEliminarRol = async (id: number) => {
    try {
      await rolesService.eliminar(id);
      message.success('Rol eliminado correctamente');
      cargarRoles();
    } catch (error) {
      message.error('Error al eliminar el rol');
    }
  };

  const handleToggleActivo = async (record: Rol, activo: boolean) => {
    try {
      // El endpoint usa PUT (reemplazo completo), no PATCH: hay que mandar
      // el registro completo, no solo el campo que cambió.
      await rolesService.actualizar(record.id, { ...record, activo });
      setRoles(prev => prev.map(r => r.id === record.id ? { ...r, activo } : r));
      message.success(`Rol ${activo ? 'activado' : 'desactivado'} correctamente`);
    } catch (error) {
      message.error('Error al actualizar el estado del rol');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
    {
      title: 'Nombre',
      dataIndex: 'nombre',
      key: 'nombre',
      render: (nombre: string) => (
        <Space>
          <SafetyOutlined />
          <strong>{nombre}</strong>
        </Space>
      )
    },
    { title: 'Descripción', dataIndex: 'descripcion', key: 'descripcion' },
    {
      title: 'Permisos',
      dataIndex: 'permisos',
      key: 'permisos',
      render: (permisos: string[]) => (
        <Space wrap>
          {permisos.slice(0, 3).map(p => (
            <Tag key={p} color="blue">{p}</Tag>
          ))}
          {permisos.length > 3 && <Tag>+{permisos.length - 3} más</Tag>}
        </Space>
      )
    },
    {
      title: 'Activo',
      dataIndex: 'activo',
      key: 'activo',
      render: (activo: boolean, record: Rol) => (
        <Switch checked={activo} onChange={(checked) => handleToggleActivo(record, checked)} />
      )
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: Rol) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/dashboard/roles/${record.id}`)} />
          <Button size="small" icon={<EditOutlined />} onClick={() => navigate(`/dashboard/roles/${record.id}/editar`)} />
          <Popconfirm
            title="¿Eliminar este rol?"
            description="Esta acción no se puede deshacer."
            okText="Sí, eliminar"
            cancelText="Cancelar"
            onConfirm={() => handleEliminarRol(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1><SafetyOutlined /> Roles y Permisos</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/dashboard/roles/nuevo')}>
          Nuevo Rol
        </Button>
      </div>
      <Card>
        <Table columns={columns} dataSource={roles} loading={loading} rowKey="id" />
      </Card>
    </div>
  );
};

export default Roles;
