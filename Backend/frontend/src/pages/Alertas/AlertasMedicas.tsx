import React, { useState, useEffect, useMemo, useCallback, lazy, Suspense, useRef } from 'react';
import {
  Card, Table, Tag, Badge, Button, Space, Input, Select,
  Empty, Row, Col, Statistic, Drawer, Descriptions, Timeline, DatePicker,
  Modal, Form, Spin
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  WarningOutlined, CheckCircleOutlined, ClockCircleOutlined,
  SearchOutlined, PlusOutlined, ReloadOutlined, FilterOutlined,
  BellOutlined, ExclamationCircleOutlined, SafetyOutlined,
  FileTextOutlined, CheckOutlined, CloseOutlined
} from '@ant-design/icons';
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })) as any);
const PieChart = lazy(() => import('recharts').then(m => ({ default: m.PieChart })) as any);
const Pie = lazy(() => import('recharts').then(m => ({ default: m.Pie })) as any);
const Cell = lazy(() => import('recharts').then(m => ({ default: m.Cell })) as any);
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })) as any);
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })) as any);
const BarChart = lazy(() => import('recharts').then(m => ({ default: m.BarChart })) as any);
const Bar = lazy(() => import('recharts').then(m => ({ default: m.Bar })) as any);
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })) as any);
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })) as any);
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })) as any);
const LineChart = lazy(() => import('recharts').then(m => ({ default: m.LineChart })) as any);
const Line = lazy(() => import('recharts').then(m => ({ default: m.Line })) as any);
import { useNavigate } from 'react-router-dom';
import { reportesService, AlertaMedica } from '../../services/reportesService';
import dayjs from 'dayjs';
import './AlertasMedicas.css';

const { RangePicker } = DatePicker;

// Memoized icon instances
const WARNING_ICON_MEMO = <WarningOutlined />;
const CHECK_CIRCLE_ICON_MEMO = <CheckCircleOutlined />;
const CLOCK_ICON_MEMO = <ClockCircleOutlined />;
const SEARCH_ICON_MEMO = <SearchOutlined />;
const PLUS_ICON_MEMO = <PlusOutlined />;
const RELOAD_ICON_MEMO = <ReloadOutlined />;
const FILTER_ICON_MEMO = <FilterOutlined />;
const BELL_ICON_MEMO = <BellOutlined />;

const getSeveridadIcon = (prioridad: string) => {
  switch (prioridad) {
    case 'critica':
    case 'emergencia': return <ExclamationCircleOutlined />;
    case 'alta': return <WarningOutlined />;
    case 'media': return <ClockCircleOutlined />;
    case 'baja': return <BellOutlined />;
    default: return <BellOutlined />;
  }
};

const renderPieLabel = ({ name, percent }: { name: string; percent: number }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`;

const getSeveridadColor = (prioridad: string) => {
  const colors: any = {
    baja: 'blue',
    media: 'orange',
    alta: 'red',
    critica: 'magenta',
    emergencia: 'red'
  };
  return colors[prioridad] || 'default';
};

const AlertasMedicas: React.FC = () => {
  const {modal,  message } = useAntdApp();
  const navigate = useNavigate();
  const [state, setState] = useState({
    alertas: [] as AlertaMedica[],
    loading: false,
    selectedAlerta: null as AlertaMedica | null,
    drawerVisible: false,
    searchText: '',
    filterSeveridad: 'all',
    filterEstado: 'all',
    dateRange: null as any,
    modalNuevaAlerta: false
  });
  const {
    alertas,
    loading,
    selectedAlerta,
    drawerVisible,
    searchText,
    filterSeveridad,
    filterEstado,
    dateRange,
    modalNuevaAlerta
  } = state;
  const mountedRef = useRef(false);
  useEffect(() => { mountedRef.current = true; }, []);
  const filtrosAvanzadosVisibleRef = useRef(false);
  const [form] = Form.useForm();

  const handleCrearAlerta = useCallback(async (values: any) => {
    try {
      await reportesService.crearAlerta({
        titulo: values.titulo,
        descripcion: values.descripcion,
        tipo: values.tipo,
        prioridad: values.prioridad,
        paciente_id: values.paciente_id ? parseInt(values.paciente_id, 10) : undefined,
        modulo_origen: values.modulo_origen,
        accion_recomendada: values.accion_recomendada,
        valor_actual: values.valor_actual,
        valor_umbral: values.valor_umbral,
      });
      message.success('Alerta creada correctamente');
      setState(prev => ({ ...prev, modalNuevaAlerta: false }));
      form.resetFields();
      cargarAlertas();
    } catch (error) {
      message.error('Error al crear la alerta');
    }
    // eslint-disable-next-line react-doctor/exhaustive-deps
  }, [form, message]);

  const cargarAlertas = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true }));
    try {
      const data = await reportesService.listarAlertas();
      setState(prev => ({ ...prev, alertas: data }));
    } catch (error) {
      message.error('Error al cargar alertas');
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [message]);

  useEffect(() => {
    cargarAlertas();
    // eslint-disable-next-line react-doctor/exhaustive-deps
  }, [cargarAlertas]);

  const filteredAlertas = useMemo(() => {
    let filtered = [...alertas];

    // Filtro por texto
    if (searchText) {
      filtered = filtered.filter(alerta =>
        (alerta.paciente_nombre || '').toLowerCase().includes(searchText.toLowerCase()) ||
        alerta.titulo.toLowerCase().includes(searchText.toLowerCase()) ||
        (alerta.descripcion || '').toLowerCase().includes(searchText.toLowerCase())
      );
    }

    // Filtro por prioridad
    if (filterSeveridad !== 'all') {
      filtered = filtered.filter(alerta => alerta.prioridad === filterSeveridad);
    }

    // Filtro por estado
    if (filterEstado !== 'all') {
      filtered = filtered.filter(alerta => alerta.estado === filterEstado);
    }

    // Filtro por rango de fechas
    if (dateRange && dateRange[0] && dateRange[1]) {
      filtered = filtered.filter(alerta => {
        const fecha = dayjs(alerta.fecha_creacion);
        return fecha.isAfter(dateRange[0]) && fecha.isBefore(dateRange[1]);
      });
    }

    return filtered;
  }, [alertas, searchText, filterSeveridad, filterEstado, dateRange]);

  const marcarResuelta = (id: number) => {
    modal.confirm({
      title: '¿Marcar como resuelta?',
      content: '¿Está seguro de que desea marcar esta alerta como resuelta?',
      okText: 'Sí, marcar',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await reportesService.marcarAlertaResuelta(id);
          message.success('Alerta marcada como resuelta');
          cargarAlertas();
        } catch (error) {
          message.error('Error al marcar la alerta como resuelta');
        }
      }
    });
  };

  // Datos para gráficas
  const getSeveridadData = () => {
    const counts = {
      baja: alertas.filter(a => a.prioridad === 'baja').length,
      media: alertas.filter(a => a.prioridad === 'media').length,
      alta: alertas.filter(a => a.prioridad === 'alta').length,
      critica: alertas.filter(a => a.prioridad === 'critica' || a.prioridad === 'emergencia').length
    };
    return [
      { name: 'Baja', value: counts.baja, color: '#1890ff' },
      { name: 'Media', value: counts.media, color: '#fa8c16' },
      { name: 'Alta', value: counts.alta, color: '#f5222d' },
      { name: 'Crítica', value: counts.critica, color: '#eb2f96' }
    ];
  };

  const getModuloData = () => {
    const modulos: any = {};
    alertas.forEach(alerta => {
      const modulo = alerta.modulo_origen || 'Otro';
      modulos[modulo] = (modulos[modulo] || 0) + 1;
    });
    return Object.keys(modulos).map(modulo => ({
      modulo,
      cantidad: modulos[modulo]
    }));
  };

  const getTiempoResolucionData = () => {
    const resueltas = alertas.filter(a => a.estado === 'resuelta' && a.fecha_resolucion);
    return resueltas.map(alerta => {
      const inicio = dayjs(alerta.fecha_creacion);
      const fin = dayjs(alerta.fecha_resolucion);
      const horas = fin.diff(inicio, 'hour', true);
      return {
        tipo: alerta.titulo.substring(0, 15) + '...',
        horas: Number(horas.toFixed(1))
      };
    });
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 70,
      sorter: (a: AlertaMedica, b: AlertaMedica) => a.id - b.id
    },
    {
      title: 'Paciente',
      dataIndex: 'paciente_nombre',
      key: 'paciente',
      render: (nombre: string | null) => nombre || '—'
    },
    {
      title: 'Título / Tipo',
      dataIndex: 'titulo',
      key: 'titulo',
      render: (titulo: string, record: AlertaMedica) => (
        <div>
          <div style={{ fontWeight: 500 }}>{titulo}</div>
          <Tag icon={<BellOutlined />}>{record.tipo_display || record.tipo}</Tag>
        </div>
      )
    },
    {
      title: 'Prioridad',
      dataIndex: 'prioridad',
      key: 'prioridad',
      render: (prioridad: string, record: AlertaMedica) => (
        <Badge
          count={record.prioridad_display || prioridad.toUpperCase()}
          style={{
            backgroundColor: getSeveridadColor(prioridad),
            fontWeight: 'bold'
          }}
        />
      ),
      sorter: (a: AlertaMedica, b: AlertaMedica) => {
        const orden: Record<string, number> = { baja: 1, media: 2, alta: 3, critica: 4, emergencia: 5 };
        return (orden[a.prioridad] || 0) - (orden[b.prioridad] || 0);
      }
    },
    {
      title: 'Descripción',
      dataIndex: 'descripcion',
      key: 'descripcion',
      ellipsis: true
    },
    {
      title: 'Módulo Origen',
      dataIndex: 'modulo_origen_display',
      key: 'modulo',
      render: (modulo: string, record: AlertaMedica) => (
        <Tag color="cyan">{modulo || record.modulo_origen}</Tag>
      )
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string, record: AlertaMedica) => {
        const status = estado === 'resuelta' ? 'success' : estado === 'descartada' ? 'default' : 'error';
        return <Badge status={status as any} text={record.estado_display || estado} />;
      },
      filters: [
        { text: 'Activa', value: 'activa' },
        { text: 'Revisada', value: 'revisada' },
        { text: 'Resuelta', value: 'resuelta' },
        { text: 'Descartada', value: 'descartada' },
        { text: 'Escalada', value: 'escalada' }
      ],
      onFilter: (value: any, record: AlertaMedica) => record.estado === value
    },
    {
      title: 'Fecha',
      dataIndex: 'fecha_creacion',
      key: 'fecha',
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY HH:mm'),
      sorter: (a: AlertaMedica, b: AlertaMedica) =>
        dayjs(a.fecha_creacion).unix() - dayjs(b.fecha_creacion).unix()
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: AlertaMedica) => (
        <Space>
          <Button
            type="link"
            icon={<FileTextOutlined />}
            onClick={() => {
              setState(prev => ({ ...prev, selectedAlerta: record, drawerVisible: true }));
            }}
          >
            Detalle
          </Button>
          {record.estado !== 'resuelta' && record.estado !== 'descartada' && (
            <Button
              type="link"
              icon={<CheckOutlined />}
              onClick={() => marcarResuelta(record.id)}
            >
              Resolver
            </Button>
          )}
        </Space>
      )
    }
  ];

  // Estadísticas
  const totalAlertas = alertas.length;
  const alertasPendientes = alertas.filter(a => a.estado === 'activa' || a.estado === 'revisada' || a.estado === 'escalada').length;
  const alertasCriticas = alertas.filter(a => (a.prioridad === 'critica' || a.prioridad === 'emergencia') && a.estado !== 'resuelta' && a.estado !== 'descartada').length;
  const alertasHoy = alertas.filter(a => dayjs(a.fecha_creacion).isSame(dayjs(), 'day')).length;

  return (
    <div className="alertas-page page-container" style={{ padding: 24 }} suppressHydrationWarning>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1><WarningOutlined style={{ color: '#fa8c16' }} /> Alertas Médicas</h1>
        <p style={{ color: '#666' }}>Monitoreo y gestión de alertas clínicas del sistema</p>
      </div>

      {/* Estadísticas */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="Total Alertas"
              value={totalAlertas}
              prefix={<BellOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="Pendientes"
              value={alertasPendientes}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="Críticas"
              value={alertasCriticas}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="stat-card">
            <Statistic
              title="Hoy"
              value={alertasHoy}
              prefix={<SafetyOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Gráficas */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} md={12}>
          <Card title="Alertas por Severidad" bordered={false}>
            <Suspense fallback={<div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={getSeveridadData()}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderPieLabel}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {getSeveridadData().map((entry) => (
                    <Cell key={`cell-${entry.name}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
            </Suspense>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="Alertas por Módulo" bordered={false}>
            <Suspense fallback={<div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getModuloData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="modulo" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="cantidad" fill="#1890ff" />
              </BarChart>
            </ResponsiveContainer>
            </Suspense>
          </Card>
        </Col>
      </Row>

      {getTiempoResolucionData().length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <Card title="Tiempo de Resolución (horas)" bordered={false}>
              <Suspense fallback={<div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>}>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={getTiempoResolucionData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="tipo" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="horas" stroke="#52c41a" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
            </Suspense>
            </Card>
          </Col>
        </Row>
      )}

      {/* Filtros */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input
            placeholder="Buscar por paciente, tipo o mensaje..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={e => setState(prev => ({ ...prev, searchText: e.target.value }))}
            style={{ width: 300 }}
          />
          <Select
            value={filterSeveridad}
            onChange={val => setState(prev => ({ ...prev, filterSeveridad: val }))}
            style={{ width: 150 }}
          >
            <Select.Option value="all">Todas las severidades</Select.Option>
            <Select.Option value="baja">Baja</Select.Option>
            <Select.Option value="media">Media</Select.Option>
            <Select.Option value="alta">Alta</Select.Option>
            <Select.Option value="critica">Crítica</Select.Option>
          </Select>
          <Select
            value={filterEstado}
            onChange={val => setState(prev => ({ ...prev, filterEstado: val }))}
            style={{ width: 150 }}
          >
            <Select.Option value="all">Todos los estados</Select.Option>
            <Select.Option value="activa">Activas</Select.Option>
            <Select.Option value="revisada">Revisadas</Select.Option>
            <Select.Option value="resuelta">Resueltas</Select.Option>
            <Select.Option value="descartada">Descartadas</Select.Option>
            <Select.Option value="escalada">Escaladas</Select.Option>
          </Select>
          <RangePicker
            value={dateRange}
            onChange={val => setState(prev => ({ ...prev, dateRange: val }))}
            format="DD/MM/YYYY"
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={cargarAlertas}
          >
            Recargar
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setState(prev => ({ ...prev, modalNuevaAlerta: true }))}
          >
            Nueva Alerta
          </Button>
          <Button
            icon={<FilterOutlined />}
            onClick={() => { filtrosAvanzadosVisibleRef.current = !filtrosAvanzadosVisibleRef.current; }}
          >
            Filtros Avanzados
          </Button>
          {filteredAlertas.length > 0 && filteredAlertas.some(a => a.estado !== 'resuelta' && a.estado !== 'descartada') && (
            <Button
              type="default"
              icon={<CheckCircleOutlined />}
              onClick={() => {
                modal.confirm({
                  title: '¿Marcar todas como resueltas?',
                  content: '¿Está seguro de marcar todas las alertas pendientes (filtradas) como resueltas?',
                  okText: 'Sí',
                  cancelText: 'No',
                  onOk: async () => {
                    const pendientes = filteredAlertas.filter(a => a.estado !== 'resuelta' && a.estado !== 'descartada');
                    try {
                      await Promise.all(pendientes.map(a => reportesService.marcarAlertaResuelta(a.id)));
                      message.success('Todas las alertas filtradas marcadas como resueltas');
                      cargarAlertas();
                    } catch (error) {
                      message.error('Error al marcar algunas alertas como resueltas');
                      cargarAlertas();
                    }
                  }
                });
              }}
            >
              Resolver Todas
            </Button>
          )}
        </Space>
      </Card>

      {/* Tabla */}
      <Card>
        <Spin spinning={loading} tip="Cargando alertas…">
          {filteredAlertas.length === 0 && !loading ? (
            <Empty
              description="No se encontraron alertas con los filtros aplicados"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setState(prev => ({ ...prev, modalNuevaAlerta: true }))}>
                Crear Primera Alerta
              </Button>
            </Empty>
          ) : (
            <Table
              columns={columns}
              dataSource={filteredAlertas}
              loading={false}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total) => `Total: ${total} alertas`
              }}
              rowClassName={(record) => record.estado === 'activa' && (record.prioridad === 'critica' || record.prioridad === 'emergencia') ? 'alerta-critica-row' : ''}
            />
          )}
        </Spin>
      </Card>

      {/* Drawer de Detalle */}
      <Drawer
        title="Detalle de Alerta"
        placement="right"
        width={600}
        onClose={() => setState(prev => ({ ...prev, drawerVisible: false }))}
        open={drawerVisible}
      >
        {selectedAlerta && (
          <div>
            <Descriptions column={1} bordered>
              <Descriptions.Item label="ID Alerta">#{selectedAlerta.id}</Descriptions.Item>
              <Descriptions.Item label="Título">{selectedAlerta.titulo}</Descriptions.Item>
              <Descriptions.Item label="Paciente">
                {selectedAlerta.paciente_nombre || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Tipo de Alerta">{selectedAlerta.tipo_display || selectedAlerta.tipo}</Descriptions.Item>
              <Descriptions.Item label="Prioridad">
                <Tag color={getSeveridadColor(selectedAlerta.prioridad)}>
                  {(selectedAlerta.prioridad_display || selectedAlerta.prioridad).toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Módulo Origen">{selectedAlerta.modulo_origen_display || selectedAlerta.modulo_origen}</Descriptions.Item>
              <Descriptions.Item label="Descripción">{selectedAlerta.descripcion}</Descriptions.Item>
              <Descriptions.Item label="Acción Recomendada">{selectedAlerta.accion_recomendada || 'Sin acción registrada'}</Descriptions.Item>
              <Descriptions.Item label="Valor Actual / Umbral">
                {selectedAlerta.valor_actual || '—'} / {selectedAlerta.valor_umbral || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Estado">
                <Badge
                  status={selectedAlerta.estado === 'resuelta' ? 'success' : selectedAlerta.estado === 'descartada' ? 'default' : 'error'}
                  text={selectedAlerta.estado_display || selectedAlerta.estado}
                />
              </Descriptions.Item>
              <Descriptions.Item label="Fecha de Creación">
                {dayjs(selectedAlerta.fecha_creacion).format('DD/MM/YYYY HH:mm:ss')}
              </Descriptions.Item>
              {selectedAlerta.estado === 'resuelta' && (
                <>
                  <Descriptions.Item label="Fecha de Resolución">
                    {selectedAlerta.fecha_resolucion ? dayjs(selectedAlerta.fecha_resolucion).format('DD/MM/YYYY HH:mm:ss') : '—'}
                  </Descriptions.Item>
                  <Descriptions.Item label="Comentario de Resolución">
                    {selectedAlerta.comentario_resolucion || '—'}
                  </Descriptions.Item>
                </>
              )}
            </Descriptions>

            {selectedAlerta.estado !== 'resuelta' && selectedAlerta.estado !== 'descartada' && (
              <div style={{ marginTop: 24 }}>
                <Space style={{ width: '100%' }} direction="vertical">
                  <Button
                    type="primary"
                    icon={<CheckOutlined />}
                    onClick={() => {
                      marcarResuelta(selectedAlerta.id);
                      setState(prev => ({ ...prev, drawerVisible: false }));
                    }}
                    block
                  >
                    Marcar como Resuelta
                  </Button>
                  <Button
                    icon={<CloseOutlined />}
                    onClick={() => setState(prev => ({ ...prev, drawerVisible: false }))}
                    block
                  >
                    Cerrar sin Resolver
                  </Button>
                </Space>
              </div>
            )}

            {/* Timeline de Historial */}
            <div style={{ marginTop: 32 }}>
              <h4>Historial de Actividad</h4>
              <Timeline
                items={[
                  {
                    color: 'blue',
                    children: (
                      <>
                        <p><strong>Alerta Creada</strong></p>
                        <p style={{ fontSize: 12, color: '#999' }}>
                          {dayjs(selectedAlerta.fecha_creacion).format('DD/MM/YYYY HH:mm:ss')}
                        </p>
                        <p style={{ fontSize: 12 }}>Origen: {selectedAlerta.modulo_origen_display || selectedAlerta.modulo_origen}</p>
                      </>
                    ),
                  },
                  ...(selectedAlerta.estado === 'resuelta'
                    ? [
                        {
                          color: 'green',
                          children: (
                            <>
                              <p><strong>Alerta Resuelta</strong></p>
                              <p style={{ fontSize: 12, color: '#999' }}>
                                {selectedAlerta.fecha_resolucion ? dayjs(selectedAlerta.fecha_resolucion).format('DD/MM/YYYY HH:mm:ss') : ''}
                              </p>
                            </>
                          ),
                        },
                      ]
                    : []),
                ]}
              />
            </div>

            {/* Botón para ver paciente */}
            {selectedAlerta.paciente_id && (
              <div style={{ marginTop: 24 }}>
                <Button
                  type="dashed"
                  block
                  onClick={() => navigate(`/dashboard/pacientes/${selectedAlerta.paciente_id}`)}
                >
                  Ver Expediente del Paciente
                </Button>
              </div>
            )}
          </div>
        )}
      </Drawer>

      {/* Modal para Nueva Alerta */}
      <Modal
        title="Crear Nueva Alerta Médica"
        open={modalNuevaAlerta}
        onCancel={() => {
          setState(prev => ({ ...prev, modalNuevaAlerta: false }));
          form.resetFields();
        }}
        onOk={() => {
          form.validateFields().then(handleCrearAlerta);
        }}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="titulo" label="Título" rules={[{ required: true }]}>
            <Input placeholder="Ej: Presión arterial alta" />
          </Form.Item>
          <Form.Item name="paciente_id" label="ID Paciente">
            <Input type="number" placeholder="ID numérico (opcional)" />
          </Form.Item>
          <Form.Item name="tipo" label="Tipo de Alerta" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="valor_critico">Valor crítico detectado</Select.Option>
              <Select.Option value="seguimiento_vencido">Seguimiento vencido</Select.Option>
              <Select.Option value="medicamento_contraindicado">Medicamento contraindicado</Select.Option>
              <Select.Option value="riesgo_alto">Riesgo alto detectado</Select.Option>
              <Select.Option value="resultado_anormal">Resultado anormal</Select.Option>
              <Select.Option value="cita_perdida">Cita perdida</Select.Option>
              <Select.Option value="protocolo_incumplido">Protocolo no seguido</Select.Option>
              <Select.Option value="auditoria">Requiere auditoría</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="prioridad" label="Prioridad" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="baja">Baja</Select.Option>
              <Select.Option value="media">Media</Select.Option>
              <Select.Option value="alta">Alta</Select.Option>
              <Select.Option value="critica">Crítica</Select.Option>
              <Select.Option value="emergencia">Emergencia</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="descripcion" label="Descripción" rules={[{ required: true }]}>
            <Input.TextArea rows={3} placeholder="Descripción detallada de la alerta" />
          </Form.Item>
          <Form.Item name="accion_recomendada" label="Acción Recomendada" rules={[{ required: true }]}>
            <Input.TextArea rows={2} placeholder="Qué debe hacer el equipo médico" />
          </Form.Item>
          <Form.Item name="modulo_origen" label="Módulo Origen" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="pacientes">Módulo de Pacientes</Select.Option>
              <Select.Option value="embarazos">Módulo de Embarazos</Select.Option>
              <Select.Option value="controles">Controles Prenatales</Select.Option>
              <Select.Option value="ecografias">Ecografías</Select.Option>
              <Select.Option value="laboratorio">Laboratorio</Select.Option>
              <Select.Option value="calculadoras">Calculadoras Médicas</Select.Option>
              <Select.Option value="partos">Partos</Select.Option>
              <Select.Option value="sistema">Sistema</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="valor_actual" label="Valor Actual">
            <Input placeholder="Ej: 150/95 mmHg" />
          </Form.Item>
          <Form.Item name="valor_umbral" label="Valor Umbral">
            <Input placeholder="Ej: Normal: <140/90 mmHg" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AlertasMedicas;
