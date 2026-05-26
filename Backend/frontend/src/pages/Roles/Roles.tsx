import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Space, Tag, Switch } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, SafetyOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

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
      const datosEjemplo: Rol[] = [
        {
          id: 1,
          nombre: 'Administrador',
          descripcion: 'Acceso completo al sistema',
          permisos: ['all'],
          activo: true
        },
        {
          id: 2,
          nombre: 'Médico',
          descripcion: 'Acceso a pacientes y controles',
          permisos: ['view_paciente', 'add_control', 'view_embarazo'],
          activo: true
        },
        {
          id: 3,
          nombre: 'Enfermera',
          descripcion: 'Acceso a triaje y signos vitales',
          permisos: ['view_paciente', 'add_triaje', 'view_cita'],
          activo: true
        }
      ];
      setRoles(datosEjemplo);
      message.success('Roles cargados');
    } catch (error) {
      message.error('Error al cargar roles');
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    cargarRoles();
  }, [cargarRoles]);

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
      render: (activo: boolean) => <Switch checked={activo} />
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: Rol) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/dashboard/roles/${record.id}`)} />
          <Button size="small" icon={<EditOutlined />} onClick={() => navigate(`/dashboard/roles/${record.id}/editar`)} />
          <Button size="small" danger icon={<DeleteOutlined />} />
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
