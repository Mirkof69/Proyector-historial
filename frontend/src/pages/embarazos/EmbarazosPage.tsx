// Página Principal de Embarazos
import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Tag, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { EmbarazosService } from '../../services/api';
import { Embarazo } from '../../types';

const EmbarazosPage: React.FC = () => {
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
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card 
        title="Gestión de Embarazos"
        extra={
          <Button type="primary" icon={<PlusOutlined />}>
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
