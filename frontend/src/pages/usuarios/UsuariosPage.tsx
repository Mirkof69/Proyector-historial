// Página Principal de Usuarios
import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Tag, message, Space, Popconfirm } from 'antd';
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { UsuariosService } from '../../services/api';
import { Usuario } from '../../types';

const UsuariosPage: React.FC = () => {
  const navigate = useNavigate();
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchUsuarios();
  }, []);

  const fetchUsuarios = async () => {
    setLoading(true);
    try {
      const response = await UsuariosService.getAll();
      setUsuarios(response.data.results || response.data);
    } catch (error) {
      message.error('Error al cargar usuarios');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await UsuariosService.delete(id);
      message.success('Usuario eliminado exitosamente');
      fetchUsuarios();
    } catch (error) {
      message.error('Error al eliminar usuario');
    }
  };

  const columns = [
    {
      title: 'Usuario',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: 'Nombre Completo',
      dataIndex: 'nombre_completo',
      key: 'nombre_completo',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Rol',
      dataIndex: 'rol',
      key: 'rol',
      render: (rol: string) => {
        const colors = {
          administrador: 'red',
          medico: 'blue',
          enfermera: 'green',
          recepcionista: 'orange',
        };
        return <Tag color={colors[rol as keyof typeof colors]}>{rol.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => {
        const colors = {
          activo: 'green',
          inactivo: 'default',
          bloqueado: 'red',
        };
        return <Tag color={colors[estado as keyof typeof colors]}>{estado.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: Usuario) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            onClick={() => navigate(`/usuarios/${record.id}`)}
          />
          <Button
            icon={<EditOutlined />}
            onClick={() => navigate(`/usuarios/${record.id}/edit`)}
          />
          <Popconfirm
            title="¿Está seguro de eliminar este usuario?"
            onConfirm={() => handleDelete(record.id)}
            okText="Sí"
            cancelText="No"
          >
            <Button icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="Gestión de Usuarios"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/usuarios/new')}
          >
            Nuevo Usuario
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={usuarios}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default UsuariosPage;
