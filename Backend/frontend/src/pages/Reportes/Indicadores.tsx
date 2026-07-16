import React, { useState, useEffect, useCallback } from 'react';
import { Card, Tag, Typography, Spin, Table, Alert, Button, message } from 'antd';
import { BarChartOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined, DownloadOutlined } from '@ant-design/icons';
import api from '../../services/api';
import { exportarExcel } from '../../utils/excelExport';

const { Text } = Typography;

interface Indicador {
  id: number;
  nombre: string;
  codigo: string;
  categoria: string;
  categoria_display: string;
  valor_actual: number | null;
  unidad_medida: string;
  tendencia: 'subiendo' | 'bajando' | 'estable' | 'sin_datos';
  estado_vs_meta: 'optimo' | 'en_progreso' | 'bajo_minimo' | 'sin_datos';
  color_estado: string;
  icono?: string;
  orden_dashboard: number;
}

const estadoVsMetaConfig: Record<string, { color: string; icon: React.ReactElement; text: string }> = {
  optimo: { color: 'success', icon: <CheckCircleOutlined />, text: 'Óptimo' },
  en_progreso: { color: 'processing', icon: <WarningOutlined />, text: 'En Progreso' },
  bajo_minimo: { color: 'error', icon: <CloseCircleOutlined />, text: 'Bajo el Mínimo' },
  sin_datos: { color: 'default', icon: <WarningOutlined />, text: 'Sin Datos' },
};

const tendenciaConfig: Record<string, { color: string; text: string }> = {
  subiendo: { color: 'green', text: 'SUBIENDO' },
  bajando: { color: 'red', text: 'BAJANDO' },
  estable: { color: 'blue', text: 'ESTABLE' },
  sin_datos: { color: 'default', text: 'SIN DATOS' },
};

const Indicadores: React.FC = () => {
  const [indicadores, setIndicadores] = useState<Indicador[]>([]);
  const [loading, setLoading] = useState(false);

  const cargarIndicadores = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/reportes/dashboard-kpis/');
      const data = response.data?.results || response.data || [];
      setIndicadores(Array.isArray(data) ? data : []);
    } catch {
      setIndicadores([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarIndicadores();
  }, [cargarIndicadores]);

  const handleExportarExcel = () => {
    if (indicadores.length === 0) {
      message.warning('No hay indicadores para exportar');
      return;
    }
    exportarExcel(
      indicadores.map(i => ({
        nombre: i.nombre,
        categoria: i.categoria_display,
        valor_actual: i.unidad_medida ? `${i.valor_actual ?? '-'} ${i.unidad_medida}` : (i.valor_actual ?? '-'),
        estado_vs_meta: estadoVsMetaConfig[i.estado_vs_meta]?.text || i.estado_vs_meta,
        tendencia: tendenciaConfig[i.tendencia]?.text || i.tendencia,
      })),
      {
        nombre: 'Indicador',
        categoria: 'Categoría',
        valor_actual: 'Valor Actual',
        estado_vs_meta: 'Estado vs Meta',
        tendencia: 'Tendencia',
      },
      {
        filename: `indicadores_${new Date().toISOString().slice(0, 10)}.xlsx`,
        sheetName: 'Indicadores',
        title: 'Indicadores de Gestión',
      },
    );
    message.success('Indicadores exportados correctamente');
  };

  const columns = [
    { title: 'Indicador', dataIndex: 'nombre', key: 'nombre', render: (v: string) => <Text strong>{v}</Text> },
    { title: 'Categoría', dataIndex: 'categoria_display', key: 'categoria' },
    {
      title: 'Valor Actual', dataIndex: 'valor_actual', key: 'actual',
      render: (v: number | null, r: Indicador) => v === null ? '—' : `${v} ${r.unidad_medida || ''}`,
    },
    {
      title: 'Estado vs Meta', dataIndex: 'estado_vs_meta', key: 'estado_vs_meta',
      render: (v: string) => {
        const cfg = estadoVsMetaConfig[v] || estadoVsMetaConfig.sin_datos;
        return <Tag color={cfg.color} icon={cfg.icon}>{cfg.text}</Tag>;
      },
    },
    {
      title: 'Tendencia', dataIndex: 'tendencia', key: 'tendencia',
      render: (v: string) => {
        const cfg = tendenciaConfig[v] || tendenciaConfig.sin_datos;
        return <Tag color={cfg.color}>{cfg.text}</Tag>;
      },
    },
  ];

  return (
    <Card
      title={<span><BarChartOutlined style={{ marginRight: 8 }} />Indicadores de Gestión</span>}
      extra={<Button icon={<DownloadOutlined />} onClick={handleExportarExcel}>Exportar Excel</Button>}
    >
      {indicadores.length === 0 && !loading && (
        <Alert message="Sin indicadores" description="No hay indicadores registrados para el período actual." type="info" showIcon style={{ marginBottom: 16 }} />
      )}
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={indicadores}
          rowKey={(r) => r.id || r.nombre}
          pagination={false}
          locale={{ emptyText: 'No hay indicadores disponibles' }}
        />
      </Spin>
    </Card>
  );
};

export default Indicadores;
