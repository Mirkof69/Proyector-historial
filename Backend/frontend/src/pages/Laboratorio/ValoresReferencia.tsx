import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Tag, Typography, Alert } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import './Laboratorio.css';
import { laboratorioService, ValorReferencia } from '../../services/laboratorioService';

const { Text } = Typography;

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
      render: (v: string) => v ? <Tag color="success">{v}</Tag> : '-',
    },
    {
      title: 'Crítico Bajo', dataIndex: 'es_critico_bajo', key: 'critico_bajo',
      render: (v: number) => v != null ? <Tag color="error">{v}</Tag> : '-',
    },
    {
      title: 'Crítico Alto', dataIndex: 'es_critico_alto', key: 'critico_alto',
      render: (v: number) => v != null ? <Tag color="error">{v}</Tag> : '-',
    },
    { title: 'Condición', dataIndex: 'condicion', key: 'condicion', render: (v: string) => v || '-' },
  ];

  return (
    <div className="laboratorio-page page-container">
      <header className="laboratorio-page__cabecera">
        <div>
          <Typography.Title level={2}>Valores de Referencia</Typography.Title>
          <Typography.Text type="secondary">Rangos normales y críticos de cada parámetro de laboratorio.</Typography.Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={cargarValores} loading={loading}>Recargar</Button>
      </header>
    <Card>
      <Alert
        message="Valores de referencia para exámenes de laboratorio"
        description="Estos rangos son referenciales y pueden variar según el laboratorio y la población."
        type="info"
        showIcon
        className="laboratorio-separado"
      />
      <Table
        columns={columns}
        dataSource={valores}
        rowKey={(r) => r.id || r.parametro}
        loading={loading}
        pagination={{ defaultPageSize: 20 }}
        locale={{ emptyText: 'No hay valores de referencia registrados' }}
        scroll={{ x: 720 }}
      />
    </Card>
    </div>
  );
};

export default ValoresReferencia;
