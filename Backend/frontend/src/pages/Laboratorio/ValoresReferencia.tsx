import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Space, Tag, Typography, Alert } from 'antd';
import { ReloadOutlined, ExperimentOutlined } from '@ant-design/icons';
import { laboratorioService, ValorReferencia } from '../../services/laboratorioService';

const { Title, Text } = Typography;

const ValoresReferencia: React.FC = () => {
  const [valores, setValores] = useState<ValorReferencia[]>([]);
  const [loading, setLoading] = useState(false);

  const cargarValores = useCallback(async () => {
    setLoading(true);
    try {
      const data = await laboratorioService.getValoresReferencia();
      setValores(Array.isArray(data) ? data : []);
    } catch {
      setValores([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarValores();
  }, [cargarValores]);

  const columns = [
    { title: 'Parámetro', dataIndex: 'parametro', key: 'parametro', render: (v: string) => <Text strong>{v}</Text> },
    { title: 'Valor Mínimo', dataIndex: 'valor_minimo', key: 'min', render: (v: number) => v != null ? v : '-' },
    { title: 'Valor Máximo', dataIndex: 'valor_maximo', key: 'max', render: (v: number) => v != null ? v : '-' },
    { title: 'Valor Normal', dataIndex: 'valor_normal', key: 'normal', render: (v: string) => v || '-' },
    { title: 'Unidad', dataIndex: 'unidad', key: 'unidad' },
    {
      title: 'Rango Normal', dataIndex: 'rango_normal', key: 'rango',
      render: (v: string) => v ? <Tag color="green">{v}</Tag> : '-',
    },
    {
      title: 'Crítico Bajo', dataIndex: 'es_critico_bajo', key: 'critico_bajo',
      render: (v: number) => v != null ? <Tag color="red">{v}</Tag> : '-',
    },
    {
      title: 'Crítico Alto', dataIndex: 'es_critico_alto', key: 'critico_alto',
      render: (v: number) => v != null ? <Tag color="red">{v}</Tag> : '-',
    },
    { title: 'Condición', dataIndex: 'condicion', key: 'condicion', render: (v: string) => v || '-' },
  ];

  return (
    <Card
      title={<span><ExperimentOutlined style={{ marginRight: 8 }} />Valores de Referencia</span>}
      extra={<Button icon={<ReloadOutlined />} onClick={cargarValores} loading={loading}>Recargar</Button>}
    >
      <Alert
        message="Valores de referencia para exámenes de laboratorio"
        description="Estos rangos son referenciales y pueden variar según el laboratorio y la población."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      <Table
        columns={columns}
        dataSource={valores}
        rowKey={(r) => r.id || r.parametro}
        loading={loading}
        pagination={{ pageSize: 20 }}
        locale={{ emptyText: 'No hay valores de referencia registrados' }}
      />
    </Card>
  );
};

export default ValoresReferencia;
