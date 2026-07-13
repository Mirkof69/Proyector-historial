import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Tag, Button, Space, Typography, Alert, Spin } from 'antd';
import { ReloadOutlined, ExperimentOutlined, WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import { laboratorioService, ResultadoLaboratorio } from '../../services/laboratorioService';

const { Text } = Typography;

const ResultadosLaboratorio: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [resultados, setResultados] = useState<ResultadoLaboratorio[]>([]);
  const [loading, setLoading] = useState(false);

  const cargarResultados = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await laboratorioService.obtenerResultados(Number(id));
      setResultados(Array.isArray(data) ? data : []);
    } catch {
      setResultados([]);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    cargarResultados();
  }, [cargarResultados]);

  const criticos = resultados.filter(r => r.es_critico);
  const anormales = resultados.filter(r => !r.es_normal && !r.es_critico);

  const columns = [
    { title: 'Parámetro', dataIndex: 'parametro_nombre', key: 'parametro', render: (v: string) => <Text strong>{v}</Text> },
    { title: 'Valor Numérico', dataIndex: 'valor_numerico', key: 'numerico', render: (v: number) => v != null ? v : '-' },
    { title: 'Valor Texto', dataIndex: 'valor_texto', key: 'texto', render: (v: string) => v || '-' },
    { title: 'Unidad', dataIndex: 'unidad', key: 'unidad', render: (v: string) => v || '-' },
    { title: 'Rango Referencia', dataIndex: 'rango_referencia', key: 'rango', render: (v: string) => v || '-' },
    {
      title: 'Estado', key: 'estado',
      render: (_: unknown, r: ResultadoLaboratorio) => {
        if (r.es_critico) return <Tag color="magenta" icon={<WarningOutlined />}>CRÍTICO</Tag>;
        if (!r.es_normal) return <Tag color="orange" icon={<WarningOutlined />}>ANORMAL</Tag>;
        return <Tag color="green" icon={<CheckCircleOutlined />}>NORMAL</Tag>;
      },
    },
  ];

  if (!id) {
    return (
      <Card title="Resultados de Laboratorio">
        <Alert message="Seleccione un examen" description="Navegue a un detalle de laboratorio para ver sus resultados." type="info" showIcon />
      </Card>
    );
  }

  return (
    <Card
      title={<span><ExperimentOutlined style={{ marginRight: 8 }} />Resultados de Laboratorio</span>}
      extra={<Button icon={<ReloadOutlined />} onClick={cargarResultados} loading={loading}>Recargar</Button>}
    >
      {criticos.length > 0 && (
        <Alert message={`${criticos.length} resultado(s) crítico(s) detectados`} type="error" showIcon style={{ marginBottom: 16 }} />
      )}
      {anormales.length > 0 && (
        <Alert message={`${anormales.length} resultado(s) anormal(es) detectados`} type="warning" showIcon style={{ marginBottom: 16 }} />
      )}
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={resultados}
          rowKey={(r) => r.id || r.valor_referencia}
          pagination={false}
          locale={{ emptyText: 'No hay resultados registrados' }}
          bordered
        />
      </Spin>
    </Card>
  );
};

export default ResultadosLaboratorio;
