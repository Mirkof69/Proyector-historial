import React, { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Statistic, Spin, Button, DatePicker, Space, Empty } from 'antd';
import {
  TeamOutlined, HeartOutlined, AlertOutlined, CalendarOutlined,
  ReloadOutlined, MedicineBoxOutlined, FileTextOutlined,
  FilePdfOutlined, FileExcelOutlined,
} from '@ant-design/icons';
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, Legend,
} from 'recharts';
import dayjs, { Dayjs } from 'dayjs';
import statisticsService from '../services/statisticsService';
import { useAntdApp } from '../hooks/useMessage';

const { RangePicker } = DatePicker;

const PIE_COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2'];

interface AllStatsState {
  dashboard: {
    total_pacientes: number;
    nuevos_pacientes: number;
    embarazos_activos: number;
    embarazos_alto_riesgo: number;
    controles_mes: number;
    citas_pendientes: number;
    citas_hoy: number;
    partos_mes: number;
  } | null;
  embarazos: {
    total_embarazos: number;
    por_riesgo: Array<{ clasificacion_riesgo: string; total: number }>;
    por_trimestre: { primer_trimestre: number; segundo_trimestre: number; tercer_trimestre: number };
    edad_promedio: number;
  } | null;
  citas: {
    por_estado: Array<{ estado: string; total: number }>;
    tasa_asistencia: number;
    tasa_cancelacion: number;
  } | null;
  partos: {
    total_partos: number;
    por_tipo: Array<{ tipo_parto: string; total: number }>;
    con_complicaciones: number;
    sin_complicaciones: number;
    partos_mensuales: Array<{ mes: string; total: number }>;
  } | null;
}

const Statistics: React.FC = () => {
  const { message } = useAntdApp();
  const [data, setData] = useState<AllStatsState>({ dashboard: null, embarazos: null, citas: null, partos: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [rango, setRango] = useState<[Dayjs, Dayjs] | null>(null);

  const filtrosActuales = rango
    ? { start_date: rango[0].format('YYYY-MM-DD'), end_date: rango[1].format('YYYY-MM-DD') }
    : undefined;

  const descargar = async (tipo: 'pdf' | 'excel') => {
    setExporting(true);
    try {
      const blob = tipo === 'pdf'
        ? await statisticsService.downloadPDF(filtrosActuales)
        : await statisticsService.downloadExcel(filtrosActuales);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `estadisticas_${dayjs().format('YYYYMMDD_HHmmss')}.${tipo === 'pdf' ? 'pdf' : 'xlsx'}`;
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
      message.success(`Estadísticas exportadas a ${tipo.toUpperCase()}`);
    } catch {
      message.error(`No se pudo exportar a ${tipo.toUpperCase()}`);
    } finally {
      setExporting(false);
    }
  };

  const cargar = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const filters = rango
        ? { start_date: rango[0].format('YYYY-MM-DD'), end_date: rango[1].format('YYYY-MM-DD') }
        : undefined;
      const all = await statisticsService.getAllStatistics(filters);
      setData(all);
    } catch {
      setError(true);
      setData({ dashboard: null, embarazos: null, citas: null, partos: null });
    } finally {
      setLoading(false);
    }
  }, [rango]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  const { dashboard, embarazos, citas, partos } = data;

  const porTrimestreData = embarazos ? [
    { name: '1er trimestre', total: embarazos.por_trimestre.primer_trimestre },
    { name: '2do trimestre', total: embarazos.por_trimestre.segundo_trimestre },
    { name: '3er trimestre', total: embarazos.por_trimestre.tercer_trimestre },
  ] : [];

  return (
    <div style={{ padding: 24 }}>
      <Space style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>Estadísticas del Sistema</h2>
        <Space>
          <RangePicker
            value={rango}
            onChange={(v) => setRango(v as [Dayjs, Dayjs] | null)}
            placeholder={['Desde', 'Hasta']}
          />
          <Button icon={<FilePdfOutlined />} onClick={() => descargar('pdf')} loading={exporting}>PDF</Button>
          <Button icon={<FileExcelOutlined />} onClick={() => descargar('excel')} loading={exporting}>Excel</Button>
          <Button icon={<ReloadOutlined />} onClick={cargar} loading={loading}>Recargar</Button>
        </Space>
      </Space>

      <Spin spinning={loading}>
        {error ? (
          <Empty description="No se pudieron cargar las estadísticas. Verifique la conexión con el servidor." />
        ) : (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Card><Statistic title="Total pacientes" value={dashboard?.total_pacientes ?? 0} prefix={<TeamOutlined />} /></Card>
              </Col>
              <Col span={6}>
                <Card><Statistic title="Embarazos activos" value={dashboard?.embarazos_activos ?? 0} prefix={<HeartOutlined />} /></Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="Embarazos de alto riesgo"
                    value={dashboard?.embarazos_alto_riesgo ?? 0}
                    prefix={<AlertOutlined />}
                    valueStyle={{ color: (dashboard?.embarazos_alto_riesgo ?? 0) > 0 ? '#ff4d4f' : undefined }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card><Statistic title="Citas hoy" value={dashboard?.citas_hoy ?? 0} prefix={<CalendarOutlined />} /></Card>
              </Col>
            </Row>

            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Card><Statistic title="Nuevos pacientes" value={dashboard?.nuevos_pacientes ?? 0} /></Card>
              </Col>
              <Col span={6}>
                <Card><Statistic title="Controles del mes" value={dashboard?.controles_mes ?? 0} /></Card>
              </Col>
              <Col span={6}>
                <Card><Statistic title="Citas pendientes" value={dashboard?.citas_pendientes ?? 0} /></Card>
              </Col>
              <Col span={6}>
                <Card><Statistic title="Partos del mes" value={dashboard?.partos_mes ?? 0} prefix={<MedicineBoxOutlined />} /></Card>
              </Col>
            </Row>

            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Card title="Embarazos por trimestre">
                  {porTrimestreData.some(d => d.total > 0) ? (
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={porTrimestreData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis allowDecimals={false} />
                        <Tooltip />
                        <Bar dataKey="total" fill="#1890ff" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : <Empty description="Sin datos de embarazos en el período" />}
                </Card>
              </Col>
              <Col span={12}>
                <Card title="Citas por estado">
                  {citas && citas.por_estado.length > 0 ? (
                    <ResponsiveContainer width="100%" height={260}>
                      <PieChart>
                        <Pie data={citas.por_estado} dataKey="total" nameKey="estado" outerRadius={90} label>
                          {citas.por_estado.map((entry, i) => (
                            <Cell key={entry.estado} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : <Empty description="Sin citas registradas en el período" />}
                </Card>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Card title="Partos por tipo">
                  {partos && partos.por_tipo.length > 0 ? (
                    <ResponsiveContainer width="100%" height={260}>
                      <PieChart>
                        <Pie data={partos.por_tipo} dataKey="total" nameKey="tipo_parto" outerRadius={90} label>
                          {partos.por_tipo.map((entry, i) => (
                            <Cell key={entry.tipo_parto} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : <Empty description="Sin partos registrados en el período" />}
                </Card>
              </Col>
              <Col span={12}>
                <Card title={<span><FileTextOutlined style={{ marginRight: 8 }} />Partos mensuales</span>}>
                  {partos && partos.partos_mensuales.length > 0 ? (
                    <ResponsiveContainer width="100%" height={260}>
                      <LineChart data={partos.partos_mensuales}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="mes" />
                        <YAxis allowDecimals={false} />
                        <Tooltip />
                        <Line type="monotone" dataKey="total" stroke="#722ed1" strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : <Empty description="Sin datos mensuales de partos" />}
                </Card>
              </Col>
            </Row>
          </>
        )}
      </Spin>
    </div>
  );
};

export default Statistics;
