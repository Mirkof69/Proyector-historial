import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Tag, Button, Typography, Alert, Spin } from 'antd';
import { ReloadOutlined, WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import './Laboratorio.css';
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
        if (r.es_critico) return <Tag color="error" icon={<WarningOutlined />}>CRÍTICO</Tag>;
        if (!r.es_normal) return <Tag color="warning" icon={<WarningOutlined />}>ANORMAL</Tag>;
        return <Tag color="success" icon={<CheckCircleOutlined />}>NORMAL</Tag>;
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
    <div className="laboratorio-page page-container">
      <header className="laboratorio-page__cabecera">
        <div>
          <Typography.Title level={2}>Resultados de Laboratorio</Typography.Title>
          <Typography.Text type="secondary">Valores medidos del examen y su comparación con el rango de referencia.</Typography.Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={cargarResultados} loading={loading}>Recargar</Button>
      </header>
    <Card>
      {criticos.length > 0 && (
        <Alert message={`${criticos.length} resultado(s) crítico(s) detectados`} type="error" showIcon className="laboratorio-separado" />
      )}
      {anormales.length > 0 && (
        <Alert message={`${anormales.length} resultado(s) anormal(es) detectados`} type="warning" showIcon className="laboratorio-separado" />
      )}
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={resultados}
          rowKey={(r) => r.id || r.valor_referencia}
          pagination={false}
          locale={{ emptyText: 'No hay resultados registrados' }}
        />
      </Spin>
    </Card>
    </div>
  );
};

export default ResultadosLaboratorio;
