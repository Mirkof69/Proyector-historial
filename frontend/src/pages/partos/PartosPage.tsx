// Página Principal de Partos
import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Tag, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { PartosService } from '../../services/api';
import { Parto } from '../../types';

const PartosPage: React.FC = () => {
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
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card 
        title="Gestión de Partos"
        extra={
          <Button type="primary" icon={<PlusOutlined />}>
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
