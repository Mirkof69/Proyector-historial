// Página Principal de Embarazos
import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Tag, message, Space, Popconfirm } from 'antd';
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { EmbarazosService } from '../../services/api';
import { Embarazo } from '../../types';

const EmbarazosPage: React.FC = () => {
  const navigate = useNavigate();
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchEmbarazos();
  }, []);

  const fetchEmbarazos = async () => {
    setLoading(true);
    try {
      const response = await EmbarazosService.getAll();
      setEmbarazos(response.data.results || response.data);
    } catch (error) {
      message.error('Error al cargar embarazos');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await EmbarazosService.delete(id);
      message.success('Embarazo eliminado exitosamente');
      fetchEmbarazos();
    } catch (error) {
      message.error('Error al eliminar embarazo');
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Paciente',
      dataIndex: 'paciente_nombre',
      key: 'paciente_nombre',
    },
    {
      title: 'Gesta',
      dataIndex: 'numero_gesta',
      key: 'numero_gesta',
    },
    {
      title: 'FUM',
      dataIndex: 'fecha_ultima_menstruacion',
      key: 'fecha_ultima_menstruacion',
    },
    {
      title: 'FPP',
      dataIndex: 'fecha_probable_parto',
      key: 'fecha_probable_parto',
    },
    {
      title: 'Riesgo',
      dataIndex: 'riesgo_embarazo',
      key: 'riesgo_embarazo',
      render: (riesgo: string) => {
        const colors = {
          bajo: 'green',
          medio: 'orange',
          alto: 'red',
        };
        return <Tag color={colors[riesgo as keyof typeof colors]}>{riesgo.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => (
        <Tag color={estado === 'activo' ? 'blue' : 'default'}>{estado.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: Embarazo) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            onClick={() => navigate(`/embarazos/${record.id}`)}
          />
          <Button
            icon={<EditOutlined />}
            onClick={() => navigate(`/embarazos/${record.id}/edit`)}
          />
          <Popconfirm
            title="¿Está seguro de eliminar este embarazo?"
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
        title="Gestión de Embarazos"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/embarazos/new')}
          >
            Nuevo Embarazo
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={embarazos}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default EmbarazosPage;
