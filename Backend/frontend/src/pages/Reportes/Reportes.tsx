/* eslint-disable react-doctor/prefer-dynamic-import */
/**
 * =============================================================================
 * REPORTES - DASHBOARD Y GESTIÓN
 * =============================================================================
 * Dashboard completo con estadísticas, gráficos y gestión de reportes
 * =============================================================================
 */

/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card, Table, Button, Space, Input, Select, DatePicker, Tag, Tooltip,
  Modal, Row, Col, Statistic, Empty, Typography, Spin, Tabs
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  EyeOutlined, DownloadOutlined, PlusOutlined,
  SearchOutlined, FilterOutlined, ReloadOutlined, FileTextOutlined,
  FilePdfOutlined, FileExcelOutlined, BarChartOutlined,
  ExclamationCircleOutlined, CalendarOutlined, ClockCircleOutlined,
  CheckCircleOutlined, MedicineBoxOutlined, UserOutlined,
  WarningOutlined, RiseOutlined, FallOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { reportesService, Reporte, DashboardKPIs } from '../../services/reportesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import DateRangeSelector, { DateRange } from '../../components/DateRangeSelector';
import './Reportes.css';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Title, Text, Paragraph } = Typography;

// Colores para gráficos
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const calcularPorcentaje = (valor: number, total: number) => {
  if (total === 0) return 0;
  return ((valor / total) * 100).toFixed(1);
};

const RenderKPIs: React.FC<{ kpis: DashboardKPIs | null }> = ({ kpis }) => {
  if (!kpis) return null;


  const totalPacientes = kpis.kpis?.pacientes_activos?.valor || 0;
  const totalEmbarazos = kpis.kpis?.embarazos_activos?.valor || 0;
  const citasCompletadas = kpis.kpis?.citas_dia?.completadas || 0;
  const citasTotal = kpis.kpis?.citas_dia?.valor || 1;
  const tasaCompletadas = calcularPorcentaje(citasCompletadas, citasTotal);

  return (
    <div className="reportes-kpi-grid">
      <div className="reportes-kpi-card reportes-kpi-card--pacientes">
        <div className="reportes-kpi-card__header">
          <div className="reportes-kpi-card__icon">
            <UserOutlined />
          </div>
          <div className={`reportes-kpi-card__trend reportes-kpi-card__trend--${kpis.kpis?.pacientes_activos?.tendencia}`}>
            {kpis.kpis?.pacientes_activos?.tendencia === 'up' ? <RiseOutlined /> : <FallOutlined />}
            {Math.abs(kpis.kpis?.pacientes_activos?.variacion_mes || 0)}%
          </div>
        </div>
        <div className="reportes-kpi-card__value">{totalPacientes.toLocaleString()}</div>
        <div className="reportes-kpi-card__label">Pacientes Activos</div>
        <div className="reportes-kpi-card__meta">
          Variaci&oacute;n: {kpis.kpis?.pacientes_activos?.variacion_mes > 0 ? '+' : ''}{kpis.kpis?.pacientes_activos?.variacion_mes}%
        </div>
      </div>

      <div className="reportes-kpi-card reportes-kpi-card--embarazos">
        <div className="reportes-kpi-card__header">
          <div className="reportes-kpi-card__icon">
            <MedicineBoxOutlined />
          </div>
          <div className={`reportes-kpi-card__trend reportes-kpi-card__trend--${kpis.kpis?.embarazos_activos?.tendencia}`}>
            {kpis.kpis?.embarazos_activos?.tendencia === 'up' ? <RiseOutlined /> : <FallOutlined />}
            {Math.abs(kpis.kpis?.embarazos_activos?.variacion_mes || 0)}%
          </div>
        </div>
        <div className="reportes-kpi-card__value">{totalEmbarazos.toLocaleString()}</div>
        <div className="reportes-kpi-card__label">Embarazos Activos</div>
        <div className="reportes-kpi-card__meta">
          Variaci&oacute;n: {kpis.kpis?.embarazos_activos?.variacion_mes > 0 ? '+' : ''}{kpis.kpis?.embarazos_activos?.variacion_mes}%
        </div>
      </div>

      <div className="reportes-kpi-card reportes-kpi-card--partos">
        <div className="reportes-kpi-card__header">
          <div className="reportes-kpi-card__icon">
            <CheckCircleOutlined />
          </div>
          <div className="reportes-kpi-card__trend reportes-kpi-card__trend--up">
            <CalendarOutlined /> {tasaCompletadas}%
          </div>
        </div>
        <div className="reportes-kpi-card__value">
          {citasCompletadas}/{citasTotal}
        </div>
        <div className="reportes-kpi-card__label">Citas Completadas</div>
        <div className="reportes-kpi-card__meta">
          Tasa de completitud: {tasaCompletadas}%
        </div>
      </div>

      <div className="reportes-kpi-card reportes-kpi-card--alertas">
        <div className="reportes-kpi-card__header">
          <div className="reportes-kpi-card__icon">
            <WarningOutlined />
          </div>
          <div className="reportes-kpi-card__trend">
            Pendientes
          </div>
        </div>
        <div className="reportes-kpi-card__value">{kpis.alertas?.embarazos_alto_riesgo || 0}</div>
        <div className="reportes-kpi-card__label">Alto Riesgo</div>
        <div className="reportes-kpi-card__meta">
          Requieren atención inmediata
        </div>
      </div>
    </div>
  );
};

interface RenderChartsProps {
  kpis: DashboardKPIs | null;
  compositionData: any[];
  stackedBarData: any[];
  distributionData: any;
}
const RenderCharts: React.FC<RenderChartsProps> = ({ kpis, compositionData, stackedBarData, distributionData }) => {
  if (!kpis) return null;
  return (
    <div className="reportes-charts-grid" style={{ maxHeight: '600px', overflowY: 'auto', overflowX: 'hidden' }}>
      <div className="reportes-chart-card">
        <div className="reportes-chart-card__header">
          <div className="reportes-chart-card__title">Tendencia de Partos</div>
          <div className="reportes-chart-card__subtitle">Últimos 12 meses - Total: {kpis?.tendencias?.partos_ultimo_anio?.reduce((sum, item) => sum + (item.total || 0), 0) || 0}</div>
        </div>
        <div className="reportes-chart-card__body">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={kpis?.tendencias?.partos_ultimo_anio}>
              <defs>
                <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} /><stop offset="95%" stopColor="#8884d8" stopOpacity={0} /></linearGradient>
                <linearGradient id="colorCesareas" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#ffc658" stopOpacity={0.8} /><stop offset="95%" stopColor="#ffc658" stopOpacity={0} /></linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0e0e0" />
              <XAxis dataKey="mes" stroke="#666" style={{ fontSize: 12 }} />
              <YAxis stroke="#666" style={{ fontSize: 12 }} />
              <RechartsTooltip contentStyle={TOOLTIP_CONTENT_STYLE} formatter={TOOLTIP_FORMATTER} />
              <Legend wrapperStyle={{ paddingTop: 10 }} />
              <Area type="monotone" dataKey="total" stroke="#8884d8" fillOpacity={1} fill="url(#colorTotal)" name="Total Partos" animationDuration={800} />
              <Area type="monotone" dataKey="cesareas" stroke="#ffc658" fill="url(#colorCesareas)" fillOpacity={0.6} name="Cesáreas" animationDuration={800} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="reportes-chart-card">
        <div className="reportes-chart-card__header">
          <div className="reportes-chart-card__title">Citas de la Semana</div>
          <div className="reportes-chart-card__subtitle">Total: {kpis?.tendencias?.citas_ultima_semana?.reduce((sum, item) => sum + (item.total || 0), 0) || 0}</div>
        </div>
        <div className="reportes-chart-card__body">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={kpis?.tendencias?.citas_ultima_semana}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0e0e0" />
              <XAxis dataKey="dia" stroke="#666" style={{ fontSize: 12 }} />
              <YAxis stroke="#666" style={{ fontSize: 12 }} />
              <RechartsTooltip contentStyle={TOOLTIP_CONTENT_STYLE} formatter={TOOLTIP_FORMATTER} />
              <Legend wrapperStyle={{ paddingTop: 10 }} />
              <Bar dataKey="completadas" fill="#82ca9d" name="Completadas" radius={BAR_RADIUS} animationDuration={800} />
              <Bar dataKey="canceladas" fill="#ff8042" name="Canceladas" radius={BAR_RADIUS} animationDuration={800} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      {compositionData && compositionData.length > 0 && (
        <div className="reportes-chart-card">
          <div className="reportes-chart-card__header"><div className="reportes-chart-card__title">Composición del Sistema</div><div className="reportes-chart-card__subtitle">Distribución porcentual de registros</div></div>
          <div className="reportes-chart-card__body">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={compositionData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} fill="#8884d8" dataKey="value" label={renderPieLabel} animationDuration={800}>
                  {compositionData.map((entry: any) => (<Cell key={entry.name} fill={['#4caf50', '#9c27b0', '#ff9800', '#2196f3'][compositionData.indexOf(entry) % 4]} />))}
                </Pie>
                <RechartsTooltip contentStyle={{ backgroundColor: '#fff', borderColor: '#ddd', borderRadius: 8 }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
      {stackedBarData && stackedBarData.length > 0 && (
        <div className="reportes-chart-card">
          <div className="reportes-chart-card__header"><div className="reportes-chart-card__title">Comparativa Mensual</div><div className="reportes-chart-card__subtitle">Últimos 12 meses - Actividad del sistema</div></div>
          <div className="reportes-chart-card__body">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stackedBarData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0e0e0" />
                <XAxis dataKey="month" stroke="#666" style={{ fontSize: 12 }} /><YAxis stroke="#666" style={{ fontSize: 12 }} />
                <RechartsTooltip contentStyle={{ backgroundColor: '#fff', borderColor: '#ddd', borderRadius: 8 }} />
                <Legend wrapperStyle={{ paddingTop: 10 }} />
                <Bar dataKey="embarazos" stackId="a" fill="#9c27b0" name="Embarazos" /><Bar dataKey="controles" stackId="a" fill="#4caf50" name="Controles" /><Bar dataKey="partos" stackId="a" fill="#ff9800" name="Partos" /><Bar dataKey="citas" stackId="a" fill="#2196f3" name="Citas" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
      {distributionData && distributionData.data && distributionData.data.length > 0 && (
        <div className="reportes-chart-card">
          <div className="reportes-chart-card__header"><div className="reportes-chart-card__title">Distribución de Edades</div><div className="reportes-chart-card__subtitle">Promedio: {distributionData.stats.mean} años | Total: {distributionData.stats.count} pacientes</div></div>
          <div className="reportes-chart-card__body">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={distributionData.data}>
                <defs><linearGradient id="colorAge" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#8b1fa2" stopOpacity={0.8} /><stop offset="95%" stopColor="#8b1fa2" stopOpacity={0.1} /></linearGradient></defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0e0e0" />
                <XAxis dataKey="age" stroke="#666" label={{ value: 'Edad (años)', position: 'insideBottom', offset: -5 }} /><YAxis stroke="#666" label={{ value: 'Cantidad', angle: -90, position: 'insideLeft' }} />
                <RechartsTooltip contentStyle={{ backgroundColor: '#fff', borderColor: '#ddd', borderRadius: 8 }} />
                <Area type="monotone" dataKey="count" stroke="#8b1fa2" fillOpacity={1} fill="url(#colorAge)" name="Pacientes" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

interface RenderHistoryProps {
  reportes: Reporte[];
  busqueda: string;
  filtroTipo: string;
  loading: boolean;
  setBusqueda: (v: string) => void;
  setFiltroTipo: (v: string) => void;
}
const RenderHistory: React.FC<RenderHistoryProps> = ({ reportes, busqueda, filtroTipo, loading, setBusqueda, setFiltroTipo }) => {
  const navigate = useNavigate();
  const { message } = useAntdApp();
  return (
  <div className="reportes-history">
    <div className="reportes-history__header" style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <Title level={4}>Historial de Reportes</Title>
        <Text type="secondary">Consulte y descargue reportes generados anteriormente</Text>
      </div>
      <Space>
        <Input placeholder="Buscar reporte…" prefix={<SearchOutlined />} value={busqueda} onChange={e => setBusqueda(e.target.value)} style={{ width: 250 }} />
        <Select placeholder="Filtrar por tipo" style={{ width: 180 }} value={filtroTipo} onChange={setFiltroTipo} allowClear>
          <Option value="pacientes">Pacientes</Option>
          <Option value="embarazos">Embarazos</Option>
          <Option value="partos">Partos</Option>
          <Option value="controles">Controles</Option>
          <Option value="laboratorio">Laboratorio</Option>
          <Option value="citas">Citas</Option>
        </Select>
      </Space>
    </div>
    <Table
      dataSource={reportes.filter(r =>
        (r.tipo_reporte_nombre?.toLowerCase().includes(busqueda.toLowerCase())) &&
        (!filtroTipo || r.tipo_reporte_nombre?.toLowerCase().includes(filtroTipo.toLowerCase()))
      )}
      locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay reportes generados todavía" /> }}
      loading={loading}
      rowKey="id"
      columns={[
        { title: 'Reporte', dataIndex: 'tipo_reporte_nombre', key: 'tipo_reporte_nombre', render: (text, record) => (<Space>{record.formato === 'pdf' ? <FilePdfOutlined style={{ color: '#ff4d4f' }} /> : <FileExcelOutlined style={{ color: '#52c41a' }} />}<Text strong>{text || 'Reporte sin tipo'}</Text></Space>) },
        { title: 'Fecha', dataIndex: 'fecha_solicitud', key: 'fecha_solicitud', render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY HH:mm') },
        { title: 'Estado', dataIndex: 'estado', key: 'estado', render: (estado: string, record) => (<Tag color={estado === 'completado' ? 'success' : estado === 'error' ? 'error' : 'processing'}>{record.estado_display || estado.toUpperCase()}</Tag>) },
        { title: 'Acciones', key: 'acciones', render: (_, record) => (
          <Space>
            <Tooltip title="Ver Detalles">
              <Button icon={<EyeOutlined />} size="small" onClick={() => navigate(`${FRONTEND_ROUTES.DASHBOARD.REPORTES}/${record.id}`)} />
            </Tooltip>
            <Tooltip title="Descargar">
              <Button
                icon={<DownloadOutlined />}
                size="small"
                type="primary"
                disabled={record.estado !== 'completado'}
                onClick={async () => {
                  try {
                    const blob = await reportesService.downloadReporte(record.id);
                    reportesService.descargarArchivo(blob, `reporte_${record.id}.${record.formato === 'pdf' ? 'pdf' : 'xlsx'}`);
                  } catch {
                    message.error('Error al descargar el reporte');
                  }
                }}
              />
            </Tooltip>
          </Space>
        ) }
      ]}
    />
  </div>
  );
};

const RenderGenerator: React.FC<{ onGenerateReporte: (tipo: string) => void }> = ({ onGenerateReporte }) => (
  <div className="reportes-generator">
    <div className="reportes-generator__header">
      <div className="reportes-generator__title">Generador de Reportes</div>
      <div className="reportes-generator__subtitle">Seleccione el tipo de reporte y los parámetros para generar un nuevo documento</div>
    </div>
      <div className="reportes-type-selector">
        <button type="button" className="reportes-type-option" onClick={() => onGenerateReporte('pacientes')} onKeyDown={(e) => { if(e.key === 'Enter' || e.key === ' ') onGenerateReporte('pacientes'); }}><div className="reportes-type-option__icon"><UserOutlined /></div><div className="reportes-type-option__label">Pacientes</div></button>
        <button type="button" className="reportes-type-option" onClick={() => onGenerateReporte('embarazos')} onKeyDown={(e) => { if(e.key === 'Enter' || e.key === ' ') onGenerateReporte('embarazos'); }}><div className="reportes-type-option__icon"><MedicineBoxOutlined /></div><div className="reportes-type-option__label">Embarazos</div></button>
        <button type="button" className="reportes-type-option" onClick={() => onGenerateReporte('partos')} onKeyDown={(e) => { if(e.key === 'Enter' || e.key === ' ') onGenerateReporte('partos'); }}><div className="reportes-type-option__icon"><CheckCircleOutlined /></div><div className="reportes-type-option__label">Partos</div></button>
        <button type="button" className="reportes-type-option" onClick={() => onGenerateReporte('financiero')} onKeyDown={(e) => { if(e.key === 'Enter' || e.key === ' ') onGenerateReporte('financiero'); }}><div className="reportes-type-option__icon"><BarChartOutlined /></div><div className="reportes-type-option__label">Financiero</div></button>
      </div>
  </div>
);

const TOOLTIP_CONTENT_STYLE = { backgroundColor: '#fff', borderColor: '#ddd', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.15)' };
const TOOLTIP_FORMATTER = (value: any) => [value, ''];
const BAR_RADIUS: [number, number, number, number] = [4, 4, 0, 0];
const renderPieLabel = (entry: any) => `${entry.name}: ${entry.percentage}%`;

const ReportesPage: React.FC = () => {
  const { message } = useAntdApp();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [reportes, setReportes] = useState<Reporte[]>([]);
  const [periodo, setPeriodo] = useState<'semana' | 'mes' | 'anio'>('mes');
  const dateRangeRef = useRef<DateRange | null>(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [currentTime, setCurrentTime] = useState<Date>(new Date());

  // Estados para filtros de historial
  const [busqueda, setBusqueda] = useState('');
  const [filtroTipo, setFiltroTipo] = useState<string>('');

  // Estados para gráficos profesionales
  const [compositionData, setCompositionData] = useState<any[]>([]);
  const [stackedBarData, setStackedBarData] = useState<any[]>([]);
  const [distributionData, setDistributionData] = useState<any>(null);

  const cargarDatos = useCallback(async () => {
    setLoading(true);
    try {
      // Cargar KPIs y Dashboard
      const kpisData = await reportesService.obtenerDashboardKPIs();
      setKpis(kpisData);
      setLastUpdate(new Date());

      // Cargar datos de gráficos profesionales
      const [composition, stackedBar, distribution] = await Promise.all([
        reportesService.obtenerCompositionChart(),
        reportesService.obtenerStackedBarChart(12),
        reportesService.obtenerDistributionChart()
      ]);

      setCompositionData(composition);
      setStackedBarData(stackedBar);
      setDistributionData(distribution);

      // Cargar historial de reportes generados
      const reportesData = await reportesService.getReportes({ page_size: 10 });
      setReportes(reportesData);

    } catch (error: any) {
      message.error(`Error al cargar el dashboard: ${error.response?.data?.detail || error.message || 'Error desconocido'}`);
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    cargarDatos();

    // Auto-refresh cada 30 segundos si está habilitado
    let interval: NodeJS.Timeout | null = null;
    if (autoRefresh) {
      interval = setInterval(() => {
        cargarDatos();
      }, 30000); // 30 segundos
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [periodo, autoRefresh, cargarDatos]);

  // Reloj en tiempo real - actualiza cada segundo
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleGenerarReporte = (tipo: string) => {
    // Navegar a la página de generación o abrir modal
    message.info(`Iniciando generación de reporte: ${tipo}`);
    navigate(`${FRONTEND_ROUTES.DASHBOARD.REPORTES}/generar?tipo=${tipo}`);
  };

  const handleDateRangeChange = (range: DateRange) => {
    dateRangeRef.current = range;
    // Recargar datos cuando cambia el rango
    cargarDatos();
  };

  const handleExportPDF = async () => {
    if (!dateRangeRef.current) {
      message.warning('Por favor seleccione un rango de fechas');
      return;
    }

    setExportLoading(true);
    try {
      await reportesService.downloadAndSavePDFEnhanced({
        start_date: dateRangeRef.current!.startDate,
        end_date: dateRangeRef.current!.endDate
      });
      message.success('¡PDF descargado exitosamente!');
    } catch (error) {
      message.error('Error al descargar el PDF');
    } finally {
      setExportLoading(false);
    }
  };

  const handleExportExcel = async () => {
    if (!dateRangeRef.current) {
      message.warning('Por favor seleccione un rango de fechas');
      return;
    }

    setExportLoading(true);
    try {
      await reportesService.downloadAndSaveExcel({
        start_date: dateRangeRef.current!.startDate,
        end_date: dateRangeRef.current!.endDate
      });
      message.success('¡Excel descargado exitosamente!');
    } catch (error) {
      message.error('Error al descargar el Excel');
    } finally {
      setExportLoading(false);
    }
  };

  return (
    <div className="reportes-container fade-in">
      <div className="reportes-dashboard-header">
        <div className="reportes-dashboard-header__content">
          <div>
            <div className="reportes-dashboard-header__title">Panel de Reportes y Estadísticas</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
              <span>Visualice el estado del sistema y genere reportes detallados</span>

              {/* Reloj en tiempo real */}
              <Tag color="cyan" icon={<ClockCircleOutlined />} style={{ fontSize: 14, padding: '4px 12px' }}>
                {currentTime.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </Tag>

              {lastUpdate && (
                <Tag color="blue" icon={<ClockCircleOutlined />}>
                  Actualizado: {dayjs(lastUpdate).format('HH:mm:ss')}
                </Tag>
              )}
              <Button
                size="small"
                type={autoRefresh ? 'primary' : 'default'}
                icon={<ReloadOutlined spin={autoRefresh} />}
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
              </Button>
            </div>
          </div>
          <div className="reportes-dashboard-header__actions">
            <Button
              type="primary"
              icon={<FilePdfOutlined />}
              onClick={handleExportPDF}
              loading={exportLoading}
              size="large"
            >
              Descargar PDF
            </Button>
            <Button
              type="default"
              icon={<FileExcelOutlined />}
              onClick={handleExportExcel}
              loading={exportLoading}
              size="large"
              style={{ marginLeft: 8 }}
            >
              Descargar Excel
            </Button>
          </div>
        </div>
      </div>

      {/* Date Range Selector */}
      <div style={{ marginBottom: 24 }}>
        <DateRangeSelector
          onChange={handleDateRangeChange}
          defaultPreset="month"
          showCompare={false}
        />
      </div>

      {loading && !kpis ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" tip="Cargando estadísticas…"><div /></Spin>
        </div>
      ) : (
        <Tabs
          defaultActiveKey="1"
          className="reportes-tabs"
          items={[
            {
              key: '1',
              label: (
                <span>
                  <BarChartOutlined /> Dashboard
                </span>
              ),
              children: (
                <>
                  <RenderKPIs kpis={kpis} />
                  <RenderCharts kpis={kpis} compositionData={compositionData} stackedBarData={stackedBarData} distributionData={distributionData} />
                  <RenderGenerator onGenerateReporte={handleGenerarReporte} />
                </>
              ),
            },
            {
              key: '2',
              label: (
                <span>
                  <ClockCircleOutlined /> Historial
                </span>
              ),
              children: (
                <Card>
                  <RenderHistory reportes={reportes} busqueda={busqueda} filtroTipo={filtroTipo} loading={loading} setBusqueda={setBusqueda} setFiltroTipo={setFiltroTipo} />
                </Card>
              ),
            },
          ]}
        />
      )}
    </div>
  );
};

export default ReportesPage;
