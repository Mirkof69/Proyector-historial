/* eslint-disable react-doctor/prefer-dynamic-import */
import React, { useState, useReducer, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Input,
  Space,
  Tag,
  DatePicker,
  Select,
  Row,
  Col,
  Badge,
  Tooltip,
  Empty,
  Drawer,
  Timeline,
  Alert,
  Divider,
  Descriptions,
  Typography
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  ExportOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  MedicineBoxOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  FilePdfOutlined,
  BarChartOutlined,
  UserOutlined,
  SafetyOutlined,
  FileSearchOutlined,
  PrinterOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { vacunasService, RegistroVacuna } from '../../services/vacunasService';
import { useAntdApp } from '../../hooks/useMessage';
import './Vacunas.css';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  ResponsiveContainer, PieChart, Pie, Cell,
  Tooltip as RechartsTooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';

dayjs.extend(relativeTime);

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Title, Text } = Typography;

// Interfaz extendida con información adicional para display
interface RegistroVacunaExtended extends RegistroVacuna {
  paciente_info?: { nombre_completo: string; id_clinico: string; edad?: number };
  tipo_vacuna_info?: { nombre: string; descripcion: string; dosis_requeridas: number };
  aplicada_por?: string;
  paciente_nombre?: string;
  tipo_vacuna_nombre?: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FF6B9D', '#C45AFF'];
const FULL_WIDTH_STYLE = { width: '100%' as const };
const AXIS_TICK_STYLE = { fill: '#64748b', fontSize: 12 };
const BAR_RADIUS: [number, number, number, number] = [4, 4, 0, 0];

// ── Estado de filtros (reducer a nivel de módulo: identidad estable) ─────────
interface FiltrosVacunasState {
  searchText: string;
  dateRange: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null;
  filtroVacuna: string;
  filtroEstado: string;
}

type FiltrosVacunasAction =
  | { type: 'SET_SEARCH'; payload: string }
  | { type: 'SET_DATE_RANGE'; payload: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null }
  | { type: 'SET_FILTRO_VACUNA'; payload: string }
  | { type: 'SET_FILTRO_ESTADO'; payload: string }
  | { type: 'LIMPIAR' };

const filtrosVacunasReducer = (state: FiltrosVacunasState, action: FiltrosVacunasAction): FiltrosVacunasState => {
  switch (action.type) {
    case 'SET_SEARCH': return { ...state, searchText: action.payload };
    case 'SET_DATE_RANGE': return { ...state, dateRange: action.payload };
    case 'SET_FILTRO_VACUNA': return { ...state, filtroVacuna: action.payload };
    case 'SET_FILTRO_ESTADO': return { ...state, filtroEstado: action.payload };
    case 'LIMPIAR': return { searchText: '', dateRange: null, filtroVacuna: 'todas', filtroEstado: 'todas' };
    default: return state;
  }
};

const Vacunas: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();

  const [vacunas, setVacunas] = useState<RegistroVacunaExtended[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [isDrawerVisible, setIsDrawerVisible] = useState<boolean>(false);
  const [selectedVacuna, setSelectedVacuna] = useState<RegistroVacunaExtended | null>(null);

  const [filtros, dispatchFiltros] = useReducer(filtrosVacunasReducer, {
    searchText: '',
    dateRange: null,
    filtroVacuna: 'todas',
    filtroEstado: 'todas',
  });

  const cargarVacunas = useCallback(async () => {
    try {
      setLoading(true);
      const response = await vacunasService.getRegistros({ page_size: 1000 });
      const data = response.results || response;

      if (Array.isArray(data)) {
        setVacunas(data as RegistroVacunaExtended[]);
      } else {
        setVacunas([]);
      }
    } catch (error) {
      message.error('Error al cargar el historial de inmunizaciones');
      setVacunas([]);
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    cargarVacunas();
  }, [cargarVacunas]);

  const filteredVacunas = useMemo(() => {
    let filtered = [...vacunas];

    if (filtros.searchText) {
      const searchLower = filtros.searchText.toLowerCase();
      filtered = filtered.filter(v =>
        v.paciente_info?.nombre_completo?.toLowerCase().includes(searchLower) ||
        v.tipo_vacuna_info?.nombre?.toLowerCase().includes(searchLower) ||
        v.paciente_nombre?.toLowerCase().includes(searchLower) ||
        v.tipo_vacuna_nombre?.toLowerCase().includes(searchLower) ||
        v.lote?.toLowerCase().includes(searchLower) ||
        v.laboratorio?.toLowerCase().includes(searchLower)
      );
    }

    if (filtros.dateRange && filtros.dateRange[0] && filtros.dateRange[1]) {
      const [start, end] = filtros.dateRange;
      filtered = filtered.filter(v => {
        const fecha = dayjs(v.fecha_aplicacion);
        return (fecha.isAfter(start.startOf('day')) || fecha.isSame(start.startOf('day'))) &&
          (fecha.isBefore(end.endOf('day')) || fecha.isSame(end.endOf('day')));
      });
    }

    if (filtros.filtroVacuna !== 'todas') {
      const filtroLower = filtros.filtroVacuna.toLowerCase();
      filtered = filtered.filter(v =>
        v.tipo_vacuna_info?.nombre?.toLowerCase().includes(filtroLower) ||
        v.tipo_vacuna_nombre?.toLowerCase().includes(filtroLower)
      );
    }

    if (filtros.filtroEstado !== 'todas') {
      if (filtros.filtroEstado === 'pendientes') {
        filtered = filtered.filter(v => v.proxima_dosis_fecha);
      } else if (filtros.filtroEstado === 'completas') {
        filtered = filtered.filter(v => !v.proxima_dosis_fecha);
      } else if (filtros.filtroEstado === 'vencidas') {
        filtered = filtered.filter(v =>
          v.proxima_dosis_fecha && dayjs(v.proxima_dosis_fecha).isBefore(dayjs().startOf('day'))
        );
      }
    }

    return filtered;
  }, [vacunas, filtros]);

  const stats = useMemo(() => {
    const total = filteredVacunas.length;
    const conProximaDosis = filteredVacunas.filter(v => v.proxima_dosis_fecha).length;
    const conReacciones = filteredVacunas.filter(v => v.reacciones_adversas).length;
    const esteMes = filteredVacunas.filter(v =>
      dayjs(v.fecha_aplicacion).isSame(dayjs(), 'month')
    ).length;

    const vencidas = filteredVacunas.filter(v =>
      v.proxima_dosis_fecha && dayjs(v.proxima_dosis_fecha).isBefore(dayjs().startOf('day'))
    ).length;

    const proximaSemana = filteredVacunas.filter(v =>
      v.proxima_dosis_fecha &&
      dayjs(v.proxima_dosis_fecha).isAfter(dayjs()) &&
      dayjs(v.proxima_dosis_fecha).isBefore(dayjs().add(7, 'days'))
    ).length;

    return { total, conProximaDosis, conReacciones, esteMes, vencidas, proximaSemana };
  }, [filteredVacunas]);

  const graficoPorTipo = useMemo(() => {
    const conteo: { [key: string]: number } = {};
    filteredVacunas.forEach(v => {
      const tipo = v.tipo_vacuna_info?.nombre || v.tipo_vacuna_nombre || 'Desconocido';
      conteo[tipo] = (conteo[tipo] || 0) + 1;
    });
    return Object.entries(conteo).map(([name, value]) => ({ name, value }));
  }, [filteredVacunas]);

  const graficoPorMes = useMemo(() => {
    const conteo: { [key: string]: number } = {};
    filteredVacunas.forEach(v => {
      const mes = dayjs(v.fecha_aplicacion).format('MMM YYYY');
      conteo[mes] = (conteo[mes] || 0) + 1;
    });
    return Object.entries(conteo).map(([mes, cantidad]) => ({ mes, cantidad }));
  }, [filteredVacunas]);

  // Handlers
  const handleNuevaVacuna = useCallback(() => {
    navigate('/dashboard/vacunas/nuevo');
  }, [navigate]);

  const handleVerDetalle = useCallback((id: number) => {
    navigate(`/dashboard/vacunas/${id}`);
  }, [navigate]);

  const handleEditar = useCallback((id: number) => {
    navigate(`/dashboard/vacunas/${id}/editar`);
  }, [navigate]);

  const handleEliminar = useCallback((vacuna: RegistroVacunaExtended) => {
    modal.confirm({
      title: 'Confirmar Eliminación',
      icon: <WarningOutlined style={{ color: 'red' }} />,
      content: `¿Desea eliminar el registro de vacunación de ${vacuna.tipo_vacuna_nombre || vacuna.tipo_vacuna_info?.nombre} para el paciente ${vacuna.paciente_nombre || vacuna.paciente_info?.nombre_completo}?`,
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await vacunasService.eliminarRegistro(vacuna.id);
          message.success('Registro de vacunación eliminado');
          cargarVacunas();
        } catch (error) {
          message.error('No se pudo eliminar el registro');
        }
      }
    });
  }, [modal, message, cargarVacunas]);

  const handleVerCarnet = useCallback((vacuna: RegistroVacunaExtended) => {
    setSelectedVacuna(vacuna);
    setIsDrawerVisible(true);
  }, []);

  const getEstadoDosis = useCallback((vacuna: RegistroVacunaExtended) => {
    if (!vacuna.proxima_dosis_fecha) {
      return { tipo: 'completa', color: 'success', texto: 'Esquema Completo' };
    }

    const diasFaltantes = dayjs(vacuna.proxima_dosis_fecha).startOf('day').diff(dayjs().startOf('day'), 'days');

    if (diasFaltantes < 0) {
      return { tipo: 'vencida', color: 'error', texto: `Atrasada (${Math.abs(diasFaltantes)}d)` };
    } else if (diasFaltantes <= 7) {
      return { tipo: 'proxima', color: 'warning', texto: `En ${diasFaltantes} días` };
    }

    return { tipo: 'programada', color: 'processing', texto: 'Programada' };
  }, []);

  // Columnas de la tabla
  const columns: ColumnsType<RegistroVacunaExtended> = useMemo(() => [
    {
      title: 'Paciente',
      key: 'paciente',
      fixed: 'left',
      width: 250,
      render: (_, record) => (
        <Space size="middle">
          <Badge dot status={getEstadoDosis(record).color as any} offset={[-5, 30]}>
            <div className="avatar-placeholder" style={{ backgroundColor: '#f0f5ff', padding: '8px', borderRadius: '8px' }}>
              <UserOutlined style={{ color: '#1890ff', fontSize: '1.2em' }} />
            </div>
          </Badge>
          <div>
            <Text strong className="block">{record.paciente_info?.nombre_completo || record.paciente_nombre}</Text>
            <Text type="secondary" style={{ fontSize: '0.85em' }}>ID: {record.paciente_info?.id_clinico || '-'}</Text>
          </div>
        </Space>
      )
    },
    {
      title: 'Vacuna / Dosis',
      key: 'vacuna',
      width: 200,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.tipo_vacuna_info?.nombre || record.tipo_vacuna_nombre}</Text>
          <Space>
            <Tag color="cyan">Dosis {record.numero_dosis}</Tag>
            {record.tipo_vacuna_info?.dosis_requeridas && (
              <small style={{ color: '#999' }}>de {record.tipo_vacuna_info?.dosis_requeridas}</small>
            )}
          </Space>
        </Space>
      )
    },
    {
      title: 'Aplicación',
      dataIndex: 'fecha_aplicacion',
      key: 'fecha_aplicacion',
      width: 150,
      render: (fecha) => (
        <Space direction="vertical" size={0}>
          <Text>{dayjs(fecha).format('DD/MM/YYYY')}</Text>
          <Text type="secondary" style={{ fontSize: '0.8em' }}>{dayjs(fecha).fromNow()}</Text>
        </Space>
      )
    },
    {
      title: 'Programación',
      key: 'proxima',
      width: 180,
      render: (_, record) => {
        const estado = getEstadoDosis(record);
        return (
          <Space direction="vertical" size={2}>
            <Tag color={estado.color} style={{ borderRadius: '12px' }}>
              {estado.texto.toUpperCase()}
            </Tag>
            {record.proxima_dosis_fecha && (
              <Text strong style={{ fontSize: '0.9em' }}>
                {dayjs(record.proxima_dosis_fecha).format('DD/MM/YYYY')}
              </Text>
            )}
          </Space>
        );
      }
    },
    {
      title: 'Lote / Lab',
      key: 'logistica',
      width: 180,
      render: (_, record) => (
        <div>
          <div><Text type="secondary">L:</Text> {record.lote || '-'}</div>
          <div><Text type="secondary">Lab:</Text> {record.laboratorio || '-'}</div>
        </div>
      )
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right',
      width: 180,
      align: 'center',
      render: (_, record) => (
        <Space>
          <Tooltip title="Certificado">
            <Button
              type="text"
              icon={<FilePdfOutlined />}
              onClick={() => handleVerCarnet(record)}
              className="action-btn-pdf"
            />
          </Tooltip>
          <Tooltip title="Detalles">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleVerDetalle(record.id)}
              className="action-btn-view"
            />
          </Tooltip>
          <Tooltip title="Editar">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditar(record.id)}
              className="action-btn-edit"
            />
          </Tooltip>
          <Tooltip title="Eliminar">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleEliminar(record)}
              className="action-btn-delete"
            />
          </Tooltip>
        </Space>
      )
    }
  ], [handleVerCarnet, handleVerDetalle, handleEditar, handleEliminar, getEstadoDosis]);

  return (
    <div className="animate-fade-in" style={{ padding: '24px' }}>
      <Card className="shadow-card overflow-hidden">
        {/* HEADER SECTION */}
        <div className="blue-gradient-header" style={{ margin: '-24px -24px 24px -24px', padding: '32px' }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Space align="center" size="large">
                <div className="header-icon-container">
                  <MedicineBoxOutlined style={{ fontSize: '32px', color: '#fff' }} />
                </div>
                <div>
                  <Title level={2} style={{ color: '#fff', margin: 0 }}>Gestión de Vacunas e Inmunizaciones</Title>
                  <Text style={{ color: 'rgba(255,255,255,0.85)' }}>Control clínico de esquemas y cronogramas de vacunación</Text>
                </div>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button
                  size="large"
                  icon={<FileSearchOutlined />}
                  onClick={() => navigate('/dashboard/vacunas/tipos')}
                >
                  Catálogo
                </Button>
                <Button
                  type="primary"
                  size="large"
                  icon={<PlusOutlined />}
                  onClick={handleNuevaVacuna}
                  className="btn-success-gradient"
                >
                  Registrar Vacuna
                </Button>
                <Button
                  size="large"
                  icon={<ReloadOutlined />}
                  onClick={cargarVacunas}
                  loading={loading}
                />
              </Space>
            </Col>
          </Row>
        </div>

        {/* ALERTS SECTION */}
        {(stats.vencidas > 0 || stats.proximaSemana > 0) && (
          <Row gutter={16} style={{ marginBottom: 24 }}>
            {stats.vencidas > 0 && (
              <Col span={stats.proximaSemana > 0 ? 12 : 24}>
                <Alert
                  message={<Text strong>Dosis Retrasadas detectadas</Text>}
                  description={`${stats.vencidas} pacientes requieren atención inmediata por esquemas vencidos.`}
                  type="error"
                  showIcon
                  icon={<WarningOutlined className="status-pulse" />}
                  style={{ borderRadius: '8px' }}
                />
              </Col>
            )}
            {stats.proximaSemana > 0 && (
              <Col span={stats.vencidas > 0 ? 12 : 24}>
                <Alert
                  message={<Text strong>Próximas Dosis (7 días)</Text>}
                  description={`${stats.proximaSemana} dosis programadas para la siguiente semana.`}
                  type="warning"
                  showIcon
                  style={{ borderRadius: '8px' }}
                />
              </Col>
            )}
          </Row>
        )}

        {/* STATISTICS CARDS */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={12} md={6} lg={4}>
            <div className="stat-card-premium blue">
              <div className="stat-icon"><MedicineBoxOutlined /></div>
              <div className="stat-value">{stats.total}</div>
              <div className="stat-label">Total Aplicadas</div>
            </div>
          </Col>
          <Col xs={12} md={6} lg={4}>
            <div className="stat-card-premium green">
              <div className="stat-icon"><CalendarOutlined /></div>
              <div className="stat-value">{stats.esteMes}</div>
              <div className="stat-label">Este Mes</div>
            </div>
          </Col>
          <Col xs={12} md={6} lg={4}>
            <div className="stat-card-premium orange">
              <div className="stat-icon"><ClockCircleOutlined /></div>
              <div className="stat-value">{stats.conProximaDosis}</div>
              <div className="stat-label">Seguimientos</div>
            </div>
          </Col>
          <Col xs={12} md={6} lg={4}>
            <div className="stat-card-premium red">
              <div className="stat-icon"><WarningOutlined /></div>
              <div className="stat-value">{stats.vencidas}</div>
              <div className="stat-label">Vencidas</div>
            </div>
          </Col>
          <Col xs={12} md={6} lg={4}>
            <div className="stat-card-premium purple">
              <div className="stat-icon"><SafetyOutlined /></div>
              <div className="stat-value">{stats.conReacciones}</div>
              <div className="stat-label">Reacciones</div>
            </div>
          </Col>
          <Col xs={12} md={6} lg={4}>
            <div className="stat-card-premium cyan">
              <div className="stat-icon"><BarChartOutlined /></div>
              <div className="stat-value">{((stats.total / (stats.total + stats.vencidas || 1)) * 100).toFixed(0)}%</div>
              <div className="stat-label">Cobertura</div>
            </div>
          </Col>
        </Row>

        {/* FILTERS SECTION */}
        <div style={{ background: '#f8fafc', padding: '20px', borderRadius: '12px', marginBottom: 24, border: '1px solid #e2e8f0' }}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} lg={8}>
              <Input
                placeholder="Buscar por paciente, vacuna, lote o lab..."
                prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
                value={filtros.searchText}
                onChange={(e) => dispatchFiltros({ type: 'SET_SEARCH', payload: e.target.value })}
                size="large"
                className="custom-search"
                allowClear
              />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <RangePicker
                style={{ width: '100%' }}
                size="large"
                format="DD/MM/YYYY"
                value={filtros.dateRange}
                onChange={(dates) => dispatchFiltros({ type: 'SET_DATE_RANGE', payload: dates as any })}
              />
            </Col>
            <Col xs={12} sm={6} lg={5}>
              <Select
                style={FULL_WIDTH_STYLE}
                size="large"
                value={filtros.filtroVacuna}
                onChange={(val) => dispatchFiltros({ type: 'SET_FILTRO_VACUNA', payload: val })}
              >
                <Option value="todas">Todas las vacunas</Option>
                <Option value="covid">Refuerzos COVID</Option>
                <Option value="influenza">Influenza</Option>
                <Option value="hepatitis">Hepatitis B</Option>
              </Select>
            </Col>
            <Col xs={12} sm={6} lg={5}>
              <Select
                style={FULL_WIDTH_STYLE}
                size="large"
                value={filtros.filtroEstado}
                onChange={(val) => dispatchFiltros({ type: 'SET_FILTRO_ESTADO', payload: val })}
              >
                <Option value="todas">Todos los estados</Option>
                <Option value="pendientes">Pendientes</Option>
                <Option value="vencidas">Vencidas</Option>
                <Option value="completas">Esquema Completo</Option>
              </Select>
            </Col>
          </Row>
        </div>

        {/* CHARTS COLLAPSIBLE */}
        <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
          <Col xs={24} lg={14}>
            <Card title={<Space><BarChartOutlined /> Histórico de Aplicaciones</Space>} size="small" className="chart-card">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={graficoPorMes}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="mes" axisLine={false} tickLine={false} tick={AXIS_TICK_STYLE} />
                  <YAxis axisLine={false} tickLine={false} tick={AXIS_TICK_STYLE} />
                  <RechartsTooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  <Bar dataKey="cantidad" fill="#3b82f6" radius={BAR_RADIUS} barSize={40} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </Col>
          <Col xs={24} lg={10}>
            <Card title={<Space><SafetyOutlined /> Distribución por Inmunógeno</Space>} size="small" className="chart-card">
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={graficoPorTipo}
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {graficoPorTipo.map((entry) => (
                      <Cell key={`cell-${entry.name}`} fill={COLORS[graficoPorTipo.indexOf(entry) % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                  <Legend verticalAlign="bottom" height={36} />
                </PieChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>

        {/* TABLE SECTION */}
        <Table
          columns={columns}
          dataSource={filteredVacunas}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            className: "custom-pagination",
            showTotal: (total) => `Total ${total} inmunizaciones`
          }}
          className="premium-table"
          locale={{
            emptyText: (
              <Empty
                description="No hay vacunas registradas"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button type="primary" icon={<PlusOutlined />} onClick={handleNuevaVacuna}>
                  Registrar primera vacuna
                </Button>
              </Empty>
            )
          }}
        />
      </Card>

      {/* CARNET DRAWER */}
      <Drawer
        title={<Title level={4} style={{ margin: 0 }}><FilePdfOutlined /> Certificado Digital de Vacunación</Title>}
        placement="right"
        width={600}
        onClose={() => setIsDrawerVisible(false)}
        open={isDrawerVisible}
        className="carnet-drawer"
        extra={
          <Space>
            <Button icon={<PrinterOutlined />} onClick={() => window.print()}>Imprimir</Button>
            <Button type="primary" icon={<ExportOutlined />}>PDF</Button>
          </Space>
        }
      >
        {selectedVacuna && (
          <div className="carnet-content">
            <div className="carnet-header">
              <UserOutlined />
              <Title level={3}>{selectedVacuna.paciente_info?.nombre_completo || selectedVacuna.paciente_nombre}</Title>
              <Text type="secondary">Certificado de Inmunización Oficial</Text>
            </div>

            <Divider />

            <Descriptions title="Detalles del Paciente" column={1} bordered size="small">
              <Descriptions.Item label="ID Clínico">{selectedVacuna.paciente_info?.id_clinico}</Descriptions.Item>
              <Descriptions.Item label="Edad al momento">{selectedVacuna.paciente_info?.edad} años</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Descriptions title="Información de la Vacuna" column={1} bordered size="small">
              <Descriptions.Item label="Vacuna">
                <Text strong color="blue">{selectedVacuna.tipo_vacuna_info?.nombre || selectedVacuna.tipo_vacuna_nombre}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Dosis Nº">{selectedVacuna.numero_dosis}</Descriptions.Item>
              <Descriptions.Item label="Fecha Aplicación">{dayjs(selectedVacuna.fecha_aplicacion).format('DD [de] MMMM, YYYY')}</Descriptions.Item>
              <Descriptions.Item label="Laboratorio">{selectedVacuna.laboratorio}</Descriptions.Item>
              <Descriptions.Item label="Número de Lote">{selectedVacuna.lote}</Descriptions.Item>
              <Descriptions.Item label="Vía de Adm.">{selectedVacuna.via_administracion}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Title level={5}><ClockCircleOutlined /> Línea de Tiempo</Title>
            <Timeline
              items={[
                {
                  color: 'green',
                  children: (
                    <>
                      <Text strong>Vacuna aplicada</Text>
                      <br />
                      <Text type="secondary">
                        {dayjs(selectedVacuna.fecha_aplicacion).format('DD/MM/YYYY')}
                      </Text>
                    </>
                  ),
                },
                {
                  color: selectedVacuna.proxima_dosis_fecha ? 'blue' : 'gray',
                  children: selectedVacuna.proxima_dosis_fecha ? (
                    <>
                      <Text strong>Próxima dosis programada</Text>
                      <br />
                      <Text type="secondary">
                        {dayjs(selectedVacuna.proxima_dosis_fecha).format('DD/MM/YYYY')}
                      </Text>
                    </>
                  ) : (
                    <Text strong>Esquema de vacunación completo</Text>
                  ),
                },
              ]}
            />

            {selectedVacuna.reacciones_adversas && (
              <>
                <Divider />
                <Alert
                  message="Reacciones Adversas Reportadas"
                  description={selectedVacuna.reacciones_adversas}
                  type="warning"
                  showIcon
                  icon={<WarningOutlined />}
                />
              </>
            )}

            {selectedVacuna.observaciones && (
              <>
                <Divider />
                <Text strong>Observaciones:</Text>
                <p>{selectedVacuna.observaciones}</p>
              </>
            )}

            <Divider />
            <Space style={{ width: '100%', justifyContent: 'center' }}>
              <Button type="primary" icon={<FilePdfOutlined />} size="large">
                Descargar Certificado
              </Button>
              <Button icon={<EditOutlined />} size="large" onClick={() => handleEditar(selectedVacuna.id)}>
                Editar Registro
              </Button>
            </Space>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default Vacunas;
