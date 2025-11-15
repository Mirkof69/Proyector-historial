// Página Principal de Partos
import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Tag, message, Space, Popconfirm } from 'antd';
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { PartosService } from '../../services/api';
import { Parto } from '../../types';

const PartosPage: React.FC = () => {
  const navigate = useNavigate();
  const [partos, setPartos] = useState<Parto[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchPartos();
  }, []);

  const fetchPartos = async () => {
    setLoading(true);
    try {
      const response = await PartosService.getAll();
      setPartos(response.data.results || response.data);
    } catch (error) {
      message.error('Error al cargar partos');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await PartosService.delete(id);
      message.success('Parto eliminado exitosamente');
      fetchPartos();
    } catch (error) {
      message.error('Error al eliminar parto');
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
      title: 'Fecha',
      dataIndex: 'fecha_parto',
      key: 'fecha_parto',
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_parto',
      key: 'tipo_parto',
      render: (tipo: string) => tipo.toUpperCase(),
    },
    {
      title: 'Vía',
      dataIndex: 'via_parto',
      key: 'via_parto',
      render: (via: string) => via.toUpperCase(),
    },
    {
      title: 'EG',
      key: 'edad_gestacional',
      render: (_: any, record: Parto) => 
        `${record.edad_gestacional_semanas}+${record.edad_gestacional_dias}`,
    },
    {
      title: 'Complicaciones',
      dataIndex: 'complicaciones',
      key: 'complicaciones',
      render: (complicaciones: boolean) => (
        <Tag color={complicaciones ? 'red' : 'green'}>
          {complicaciones ? 'SÍ' : 'NO'}
        </Tag>
      ),
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => {
        const colors = {
          en_curso: 'blue',
          finalizado: 'green',
          complicado: 'red',
        };
        return <Tag color={colors[estado as keyof typeof colors]}>{estado.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: Parto) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            onClick={() => navigate(`/partos/${record.id}`)}
          />
          <Button
            icon={<EditOutlined />}
            onClick={() => navigate(`/partos/${record.id}/edit`)}
          />
          <Popconfirm
            title="¿Está seguro de eliminar este parto?"
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
        title="Gestión de Partos"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/partos/new')}
          >
            Nuevo Parto
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={partos}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default PartosPage;
