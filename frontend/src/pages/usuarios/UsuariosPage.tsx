// Página Principal de Usuarios
import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Tag, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { UsuariosService } from '../../services/api';
import { Usuario } from '../../types';

const UsuariosPage: React.FC = () => {
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
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card 
        title="Gestión de Usuarios"
        extra={
          <Button type="primary" icon={<PlusOutlined />}>
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
