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

const getSeveridadIcon = (severidad: string) => {
  switch (severidad) {
    case 'critica': return <ExclamationCircleOutlined />;
    case 'alta': return <WarningOutlined />;
    case 'media': return <ClockCircleOutlined />;
    case 'baja': return <BellOutlined />;
    default: return <BellOutlined />;
  }
};

interface AlertaMedica {
  id: number;
  paciente: number;
  paciente_nombre: string;
  paciente_id_clinico?: string;
  tipo_alerta: string;
  severidad: 'baja' | 'media' | 'alta' | 'critica';
  mensaje: string;
  descripcion?: string;
  resuelta: boolean;
  fecha_creacion: string;
  fecha_resolucion?: string;
  resuelto_por?: string;
  modulo_origen?: string;
  valores_referencia?: string;
}

const renderPieLabel = ({ name, percent }: { name: string; percent: number }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`;

const AlertasMedicas: React.FC = () => {
  const { message } = useAntdApp();
  const navigate = useNavigate();
  const [alertas, setAlertas] = useState<AlertaMedica[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAlerta, setSelectedAlerta] = useState<AlertaMedica | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [filterSeveridad, setFilterSeveridad] = useState<string>('all');
  const [filterEstado, setFilterEstado] = useState<string>('all');
  const [dateRange, setDateRange] = useState<any>(null);
  const [modalNuevaAlerta, setModalNuevaAlerta] = useState(false);
  const mountedRef = useRef(false);
  useEffect(() => { mountedRef.current = true; }, []);
  const filtrosAvanzadosVisibleRef = useRef(false);
  const [form] = Form.useForm();

  const handleCrearAlerta = useCallback((values: any) => {
    const now = new Date().toISOString();
    const nuevaAlerta: AlertaMedica = {
      id: alertas.length + 1,
      paciente: parseInt(values.paciente),
      paciente_nombre: values.paciente_nombre,
      paciente_id_clinico: values.paciente_id_clinico,
      tipo_alerta: values.tipo_alerta,
      severidad: values.severidad,
      mensaje: values.mensaje,
      descripcion: values.descripcion,
      resuelta: false,
      fecha_creacion: now,
      modulo_origen: values.modulo_origen,
      valores_referencia: values.valores_referencia
    };
    setAlertas(prev => [nuevaAlerta, ...prev]);
    message.success('Alerta creada correctamente');
    setModalNuevaAlerta(false);
    form.resetFields();
  }, [alertas.length, form]);

  const cargarAlertas = useCallback(async () => {
    setLoading(true);
    try {
      // Datos de ejemplo más completos
      const datosEjemplo: AlertaMedica[] = [
        {
          id: 1,
          paciente: 1,
          paciente_nombre: 'María García López',
          paciente_id_clinico: 'PAC-001',
          tipo_alerta: 'Presión Arterial Alta',
          severidad: 'critica',
          mensaje: 'Presión arterial 180/110 mmHg - Riesgo de preeclampsia severa',
          descripcion: 'Paciente en semana 34 de gestación. Requiere atención inmediata.',
          resuelta: false,
          fecha_creacion: '2024-12-18T08:30:00',
          modulo_origen: 'Triaje',
          valores_referencia: 'Normal: <140/90 mmHg'
        },
        {
          id: 2,
          paciente: 2,
          paciente_nombre: 'Carmen Rodríguez Pérez',
          paciente_id_clinico: 'PAC-002',
          tipo_alerta: 'Glucemia Elevada',
          severidad: 'alta',
          mensaje: 'Glucosa en ayunas: 145 mg/dL - Posible diabetes gestacional',
          descripcion: 'Realizar test de tolerancia oral a la glucosa',
          resuelta: false,
          fecha_creacion: '2024-12-18T09:15:00',
          modulo_origen: 'Laboratorio',
          valores_referencia: 'Normal: <105 mg/dL'
        },
        {
          id: 3,
          paciente: 3,
          paciente_nombre: 'Ana Martínez Silva',
          paciente_id_clinico: 'PAC-003',
          tipo_alerta: 'Hemoglobina Baja',
          severidad: 'media',
          mensaje: 'Hemoglobina: 9.2 g/dL - Anemia moderada',
          descripcion: 'Indicar suplemento de hierro',
          resuelta: true,
          fecha_creacion: '2024-12-17T14:20:00',
          fecha_resolucion: '2024-12-17T16:00:00',
          resuelto_por: 'Dr. Juan Pérez',
          modulo_origen: 'Laboratorio',
          valores_referencia: 'Normal: >11 g/dL'
        },
        {
          id: 4,
          paciente: 4,
          paciente_nombre: 'Laura Fernández Torres',
          paciente_id_clinico: 'PAC-004',
          tipo_alerta: 'Proteínas en Orina',
          severidad: 'alta',
          mensaje: 'Proteinuria: 350 mg/24h - Signo de preeclampsia',
          descripcion: 'Monitoreo cercano de presión arterial y función renal',
          resuelta: false,
          fecha_creacion: '2024-12-18T10:00:00',
          modulo_origen: 'Laboratorio',
          valores_referencia: 'Normal: <300 mg/24h'
        },
        {
          id: 5,
          paciente: 5,
          paciente_nombre: 'Patricia Gómez Ruiz',
          paciente_id_clinico: 'PAC-005',
          tipo_alerta: 'Peso Materno Bajo',
          severidad: 'media',
          mensaje: 'Ganancia de peso insuficiente: +3 kg en 20 semanas',
          descripcion: 'Evaluación nutricional requerida',
          resuelta: true,
          fecha_creacion: '2024-12-16T11:30:00',
          fecha_resolucion: '2024-12-17T09:00:00',
          resuelto_por: 'Dra. María González',
          modulo_origen: 'Control Prenatal',
          valores_referencia: 'Esperado: +5-9 kg a las 20 semanas'
        },
        {
          id: 6,
          paciente: 6,
          paciente_nombre: 'Isabel López Castro',
          paciente_id_clinico: 'PAC-006',
          tipo_alerta: 'Plaquetas Bajas',
          severidad: 'alta',
          mensaje: 'Plaquetas: 85,000/μL - Trombocitopenia',
          descripcion: 'Descartar síndrome HELLP',
          resuelta: false,
          fecha_creacion: '2024-12-18T11:45:00',
          modulo_origen: 'Laboratorio',
          valores_referencia: 'Normal: >150,000/μL'
        },
        {
          id: 7,
          paciente: 7,
          paciente_nombre: 'Rosa Sánchez Morales',
          paciente_id_clinico: 'PAC-007',
          tipo_alerta: 'Vacuna Vencida',
          severidad: 'baja',
          mensaje: 'Vacuna Tdap pendiente - Debe aplicarse antes de semana 36',
          descripcion: 'Actualmente en semana 33',
          resuelta: true,
          fecha_creacion: '2024-12-15T13:00:00',
          fecha_resolucion: '2024-12-17T14:30:00',
          resuelto_por: 'Enf. Carlos Ramírez',
          modulo_origen: 'Vacunas',
          valores_referencia: 'Aplicar entre semanas 27-36'
        },
        {
          id: 8,
          paciente: 8,
          paciente_nombre: 'Elena Díaz Jiménez',
          paciente_id_clinico: 'PAC-008',
          tipo_alerta: 'Líquido Amniótico Bajo',
          severidad: 'alta',
          mensaje: 'ILA: 4 cm - Oligohidramnios',
          descripcion: 'Requiere evaluación Doppler fetal',
          resuelta: false,
          fecha_creacion: '2024-12-18T12:15:00',
          modulo_origen: 'Ecografía',
          valores_referencia: 'Normal: 8-18 cm'
        }
      ];
      setAlertas(datosEjemplo);
      message.success(`${datosEjemplo.length} alertas cargadas`);
    } catch (error) {
      message.error('Error al cargar alertas');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarAlertas();
  }, [cargarAlertas]);

  const filteredAlertas = useMemo(() => {
    let filtered = [...alertas];

    // Filtro por texto
    if (searchText) {
      filtered = filtered.filter(alerta =>
        alerta.paciente_nombre.toLowerCase().includes(searchText.toLowerCase()) ||
        alerta.tipo_alerta.toLowerCase().includes(searchText.toLowerCase()) ||
        alerta.mensaje.toLowerCase().includes(searchText.toLowerCase())
      );
    }

    // Filtro por severidad
    if (filterSeveridad !== 'all') {
      filtered = filtered.filter(alerta => alerta.severidad === filterSeveridad);
    }

    // Filtro por estado
    if (filterEstado !== 'all') {
      const resuelta = filterEstado === 'resuelta';
      filtered = filtered.filter(alerta => alerta.resuelta === resuelta);
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

  const getSeveridadColor = (severidad: string) => {
    const colors: any = {
      baja: 'blue',
      media: 'orange',
      alta: 'red',
      critica: 'magenta'
    };
    return colors[severidad] || 'default';
  };

  const marcarResuelta = (id: number) => {
    Modal.confirm({
      title: '¿Marcar como resuelta?',
      content: '¿Está seguro de que desea marcar esta alerta como resuelta?',
      okText: 'Sí, marcar',
      cancelText: 'Cancelar',
      onOk: () => {
        const updatedAlertas = alertas.map(alerta =>
          alerta.id === id
            ? { ...alerta, resuelta: true, fecha_resolucion: new Date().toISOString() }
            : alerta
        );
        setAlertas(updatedAlertas);
        message.success('Alerta marcada como resuelta');
      }
    });
  };

  // Datos para gráficas
  const getSeveridadData = () => {
    const counts = {
      baja: alertas.filter(a => a.severidad === 'baja').length,
      media: alertas.filter(a => a.severidad === 'media').length,
      alta: alertas.filter(a => a.severidad === 'alta').length,
      critica: alertas.filter(a => a.severidad === 'critica').length
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
    const resueltas = alertas.filter(a => a.resuelta && a.fecha_resolucion);
    return resueltas.map(alerta => {
      const inicio = dayjs(alerta.fecha_creacion);
      const fin = dayjs(alerta.fecha_resolucion);
      const horas = fin.diff(inicio, 'hour', true);
      return {
        tipo: alerta.tipo_alerta.substring(0, 15) + '...',
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
      render: (nombre: string, record: AlertaMedica) => (
        <div>
          <div style={{ fontWeight: 500 }}>{nombre}</div>
          <div style={{ fontSize: 12, color: '#999' }}>{record.paciente_id_clinico}</div>
        </div>
      )
    },
    {
      title: 'Tipo de Alerta',
      dataIndex: 'tipo_alerta',
      key: 'tipo',
      render: (tipo: string) => (
        <Tag icon={<BellOutlined />}>{tipo}</Tag>
      )
    },
    {
      title: 'Severidad',
      dataIndex: 'severidad',
      key: 'severidad',
      render: (sev: string) => (
        <Badge
          count={sev.toUpperCase()}
          style={{
            backgroundColor: getSeveridadColor(sev),
            fontWeight: 'bold'
          }}
        />
      ),
      sorter: (a: AlertaMedica, b: AlertaMedica) => {
        const orden = { baja: 1, media: 2, alta: 3, critica: 4 };
        return (orden[a.severidad] || 0) - (orden[b.severidad] || 0);
      }
    },
    {
      title: 'Mensaje',
      dataIndex: 'mensaje',
      key: 'mensaje',
      ellipsis: true
    },
    {
      title: 'Módulo Origen',
      dataIndex: 'modulo_origen',
      key: 'modulo',
      render: (modulo: string) => (
        <Tag color="cyan">{modulo || 'N/A'}</Tag>
      )
    },
    {
      title: 'Estado',
      dataIndex: 'resuelta',
      key: 'estado',
      render: (resuelta: boolean) => (
        resuelta ? (
          <Badge status="success" text="Resuelta" />
        ) : (
          <Badge status="error" text="Pendiente" />
        )
      ),
      filters: [
        { text: 'Pendiente', value: false },
        { text: 'Resuelta', value: true }
      ],
      onFilter: (value: any, record: AlertaMedica) => record.resuelta === value
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
              setSelectedAlerta(record);
              setDrawerVisible(true);
            }}
          >
            Detalle
          </Button>
          {!record.resuelta && (
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
  const alertasPendientes = alertas.filter(a => !a.resuelta).length;
  const alertasCriticas = alertas.filter(a => a.severidad === 'critica' && !a.resuelta).length;
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
            onChange={e => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
          <Select
            value={filterSeveridad}
            onChange={setFilterSeveridad}
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
            onChange={setFilterEstado}
            style={{ width: 150 }}
          >
            <Select.Option value="all">Todos los estados</Select.Option>
            <Select.Option value="pendiente">Pendientes</Select.Option>
            <Select.Option value="resuelta">Resueltas</Select.Option>
          </Select>
          <RangePicker
            value={dateRange}
            onChange={setDateRange}
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
            onClick={() => setModalNuevaAlerta(true)}
          >
            Nueva Alerta
          </Button>
          <Button
            icon={<FilterOutlined />}
            onClick={() => { filtrosAvanzadosVisibleRef.current = !filtrosAvanzadosVisibleRef.current; }}
          >
            Filtros Avanzados
          </Button>
          {filteredAlertas.length > 0 && filteredAlertas.some(a => !a.resuelta) && (
            <Button
              type="default"
              icon={<CheckCircleOutlined />}
              onClick={() => {
                Modal.confirm({
                  title: '¿Marcar todas como resueltas?',
                  content: '¿Está seguro de marcar todas las alertas pendientes como resueltas?',
                  okText: 'Sí',
                  cancelText: 'No',
                  onOk: () => {
                    const updated = alertas.map(a => ({ ...a, resuelta: true }));
                    setAlertas(updated);
                    message.success('Todas las alertas marcadas como resueltas');
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
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalNuevaAlerta(true)}>
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
              rowClassName={(record) => !record.resuelta && record.severidad === 'critica' ? 'alerta-critica-row' : ''}
            />
          )}
        </Spin>
      </Card>

      {/* Drawer de Detalle */}
      <Drawer
        title="Detalle de Alerta"
        placement="right"
        width={600}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedAlerta && (
          <div>
            <Descriptions column={1} bordered>
              <Descriptions.Item label="ID Alerta">#{selectedAlerta.id}</Descriptions.Item>
              <Descriptions.Item label="Paciente">
                <strong>{selectedAlerta.paciente_nombre}</strong>
                <br />
                <small>{selectedAlerta.paciente_id_clinico}</small>
              </Descriptions.Item>
              <Descriptions.Item label="Tipo de Alerta">{selectedAlerta.tipo_alerta}</Descriptions.Item>
              <Descriptions.Item label="Severidad">
                <Tag color={getSeveridadColor(selectedAlerta.severidad)}>
                  {selectedAlerta.severidad.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Módulo Origen">{selectedAlerta.modulo_origen || 'N/A'}</Descriptions.Item>
              <Descriptions.Item label="Mensaje">{selectedAlerta.mensaje}</Descriptions.Item>
              <Descriptions.Item label="Descripción">{selectedAlerta.descripcion || 'Sin descripción adicional'}</Descriptions.Item>
              <Descriptions.Item label="Valores de Referencia">{selectedAlerta.valores_referencia || 'N/A'}</Descriptions.Item>
              <Descriptions.Item label="Estado">
                {selectedAlerta.resuelta ? (
                  <Badge status="success" text="Resuelta" />
                ) : (
                  <Badge status="error" text="Pendiente" />
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Fecha de Creación">
                {dayjs(selectedAlerta.fecha_creacion).format('DD/MM/YYYY HH:mm:ss')}
              </Descriptions.Item>
              {selectedAlerta.resuelta && (
                <>
                  <Descriptions.Item label="Fecha de Resolución">
                    {dayjs(selectedAlerta.fecha_resolucion).format('DD/MM/YYYY HH:mm:ss')}
                  </Descriptions.Item>
                  <Descriptions.Item label="Resuelto Por">
                    {selectedAlerta.resuelto_por || 'N/A'}
                  </Descriptions.Item>
                </>
              )}
            </Descriptions>

            {!selectedAlerta.resuelta && (
              <div style={{ marginTop: 24 }}>
                <Space style={{ width: '100%' }} direction="vertical">
                  <Button
                    type="primary"
                    icon={<CheckOutlined />}
                    onClick={() => {
                      marcarResuelta(selectedAlerta.id);
                      setDrawerVisible(false);
                    }}
                    block
                  >
                    Marcar como Resuelta
                  </Button>
                  <Button
                    icon={<CloseOutlined />}
                    onClick={() => setDrawerVisible(false)}
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
                        <p style={{ fontSize: 12 }}>Origen: {selectedAlerta.modulo_origen}</p>
                      </>
                    ),
                  },
                  ...(selectedAlerta.resuelta
                    ? [
                        {
                          color: 'green',
                          children: (
                            <>
                              <p><strong>Alerta Resuelta</strong></p>
                              <p style={{ fontSize: 12, color: '#999' }}>
                                {dayjs(selectedAlerta.fecha_resolucion).format('DD/MM/YYYY HH:mm:ss')}
                              </p>
                              <p style={{ fontSize: 12 }}>Por: {selectedAlerta.resuelto_por}</p>
                            </>
                          ),
                        },
                      ]
                    : []),
                ]}
              />
            </div>

            {/* Botón para ver paciente */}
            <div style={{ marginTop: 24 }}>
              <Button
                type="dashed"
                block
                onClick={() => navigate(`/dashboard/pacientes/${selectedAlerta.paciente}`)}
              >
                Ver Expediente del Paciente
              </Button>
            </div>
          </div>
        )}
      </Drawer>

      {/* Modal para Nueva Alerta */}
      <Modal
        title="Crear Nueva Alerta Médica"
        open={modalNuevaAlerta}
        onCancel={() => {
          setModalNuevaAlerta(false);
          form.resetFields();
        }}
        onOk={() => {
          form.validateFields().then(handleCrearAlerta);
        }}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="paciente_nombre" label="Nombre del Paciente" rules={[{ required: true }]}>
            <Input placeholder="Nombre completo" />
          </Form.Item>
          <Form.Item name="paciente_id_clinico" label="ID Clínico" rules={[{ required: true }]}>
            <Input placeholder="PAC-XXX" />
          </Form.Item>
          <Form.Item name="paciente" label="ID Paciente" rules={[{ required: true }]}>
            <Input type="number" placeholder="ID numérico" />
          </Form.Item>
          <Form.Item name="tipo_alerta" label="Tipo de Alerta" rules={[{ required: true }]}>
            <Input placeholder="Ej: Presión Arterial Alta" />
          </Form.Item>
          <Form.Item name="severidad" label="Severidad" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="baja">Baja</Select.Option>
              <Select.Option value="media">Media</Select.Option>
              <Select.Option value="alta">Alta</Select.Option>
              <Select.Option value="critica">Crítica</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="mensaje" label="Mensaje" rules={[{ required: true }]}>
            <Input.TextArea rows={2} placeholder="Mensaje principal de la alerta" />
          </Form.Item>
          <Form.Item name="descripcion" label="Descripción">
            <Input.TextArea rows={3} placeholder="Descripción detallada (opcional)" />
          </Form.Item>
          <Form.Item name="modulo_origen" label="Módulo Origen">
            <Select>
              <Select.Option value="Triaje">Triaje</Select.Option>
              <Select.Option value="Laboratorio">Laboratorio</Select.Option>
              <Select.Option value="Control Prenatal">Control Prenatal</Select.Option>
              <Select.Option value="Ecografía">Ecografía</Select.Option>
              <Select.Option value="Vacunas">Vacunas</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="valores_referencia" label="Valores de Referencia">
            <Input placeholder="Ej: Normal: <140/90 mmHg" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AlertasMedicas;
