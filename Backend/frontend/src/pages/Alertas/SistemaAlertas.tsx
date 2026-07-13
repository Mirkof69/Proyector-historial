/**
 * =============================================================================
 * SISTEMA DE ALERTAS MÉDICAS - DASHBOARD COMPLETO
 * =============================================================================
 * Centro de control de alertas médicas con notificaciones en tiempo real
 * =============================================================================
 */

import React, { useReducer, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import {Card, Row, Col, Badge, List, Tag, Button, Space, Modal,
  Statistic, Empty, Spin, Divider,
  Select, Input, DatePicker, Tabs, Alert, Avatar, Tooltip} from "antd";
import {
  BellOutlined, WarningOutlined, CheckCircleOutlined,
  ClockCircleOutlined, ExclamationCircleOutlined,
  MedicineBoxOutlined, UserOutlined,
  FireOutlined, AlertOutlined, InfoCircleOutlined,
  SyncOutlined, FilterOutlined, SearchOutlined,
  CloseCircleOutlined, CalendarOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { reportesService, AlertaMedica as AlertaMedicaReal } from '../../services/reportesService';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import es from 'dayjs/locale/es';

dayjs.extend(relativeTime);
dayjs.locale(es);

const { Option } = Select;
const { Search } = Input;
const { RangePicker } = DatePicker;

// Tipo de vista usado por esta pantalla: misma forma que el modelo real
// AlertaMedica del backend (reportes/models.py), con "tipo" reutilizado
// para el filtro de prioridad y "categoria"/"notas" derivados de campos reales.
interface AlertaMedica {
  id: number;
  titulo: string;
  descripcion: string;
  tipo: 'critica' | 'alta' | 'media' | 'baja' | 'info';
  prioridad: string;
  paciente_id?: number;
  paciente_nombre?: string | null;
  estado: 'activa' | 'en_proceso' | 'resuelta' | 'descartada';
  fecha_creacion: string;
  fecha_resolucion?: string;
  categoria: string;
  asignado_a?: string;
  notas?: string;
}

const mapEstadoReal = (estado: AlertaMedicaReal['estado']): AlertaMedica['estado'] => {
  if (estado === 'revisada' || estado === 'escalada') return 'en_proceso';
  if (estado === 'resuelta') return 'resuelta';
  if (estado === 'descartada') return 'descartada';
  return 'activa';
};

const mapEstadoVistaABackend = (estado: AlertaMedica['estado']): AlertaMedicaReal['estado'] | '' => {
  if (estado === 'en_proceso') return 'revisada';
  return estado || '';
};

const mapTipoReal = (prioridad: AlertaMedicaReal['prioridad']): AlertaMedica['tipo'] => {
  if (prioridad === 'critica' || prioridad === 'emergencia') return 'critica';
  if (prioridad === 'alta') return 'alta';
  if (prioridad === 'media') return 'media';
  return 'baja';
};

const mapAlertaReal = (alerta: AlertaMedicaReal): AlertaMedica => ({
  id: alerta.id,
  titulo: alerta.titulo,
  descripcion: alerta.descripcion || '',
  tipo: mapTipoReal(alerta.prioridad),
  prioridad: alerta.prioridad_display || alerta.prioridad,
  paciente_id: alerta.paciente_id,
  paciente_nombre: alerta.paciente_nombre,
  estado: mapEstadoReal(alerta.estado),
  fecha_creacion: alerta.fecha_creacion,
  fecha_resolucion: alerta.fecha_resolucion,
  categoria: alerta.modulo_origen_display || alerta.modulo_origen,
  notas: alerta.comentario_resolucion || alerta.comentario_revision || undefined,
});

interface AlertState {
  alertas: AlertaMedica[];
  loading: boolean;
  filtroTipo: string;
  filtroEstado: string;
  busqueda: string;
  alertaSeleccionada: AlertaMedica | null;
  modalVisible: boolean;
  rangoFechas: [dayjs.Dayjs | null, dayjs.Dayjs | null];
  vistaActiva: string;
}

type AlertAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ALERTAS'; payload: AlertaMedica[] }
  | { type: 'SET_FILTRO_TIPO'; payload: string }
  | { type: 'SET_FILTRO_ESTADO'; payload: string }
  | { type: 'SET_BUSQUEDA'; payload: string }
  | { type: 'SET_ALERTA_SELECCIONADA'; payload: AlertaMedica | null }
  | { type: 'SET_MODAL_VISIBLE'; payload: boolean }
  | { type: 'SET_RANGO_FECHAS'; payload: [dayjs.Dayjs | null, dayjs.Dayjs | null] }
  | { type: 'SET_VISTA_ACTIVA'; payload: string }
  | { type: 'CLEAR_FILTERS' };

const initialAlertState: AlertState = {
  alertas: [],
  loading: false,
  filtroTipo: '',
  filtroEstado: 'activa',
  busqueda: '',
  alertaSeleccionada: null,
  modalVisible: false,
  rangoFechas: [null, null],
  vistaActiva: 'todas',
};

function alertReducer(state: AlertState, action: AlertAction): AlertState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ALERTAS':
      return { ...state, alertas: action.payload, loading: false };
    case 'SET_FILTRO_TIPO':
      return { ...state, filtroTipo: action.payload };
    case 'SET_FILTRO_ESTADO':
      return { ...state, filtroEstado: action.payload };
    case 'SET_BUSQUEDA':
      return { ...state, busqueda: action.payload };
    case 'SET_ALERTA_SELECCIONADA':
      return { ...state, alertaSeleccionada: action.payload };
    case 'SET_MODAL_VISIBLE':
      return { ...state, modalVisible: action.payload };
    case 'SET_RANGO_FECHAS':
      return { ...state, rangoFechas: action.payload };
    case 'SET_VISTA_ACTIVA':
      return { ...state, vistaActiva: action.payload };
    case 'CLEAR_FILTERS':
      return { ...state, filtroTipo: '', filtroEstado: '', busqueda: '', rangoFechas: [null, null] };
    default:
      return state;
  }
}

const getTipoConfig = (tipo: string) => {
  const configs: Record<string, { icon: React.ReactElement; color: string; text: string }> = {
    'critica': { icon: <FireOutlined />, color: '#f5222d', text: 'Crítica' },
    'alta': { icon: <WarningOutlined />, color: '#fa8c16', text: 'Alta' },
    'media': { icon: <ExclamationCircleOutlined />, color: '#faad14', text: 'Media' },
    'baja': { icon: <InfoCircleOutlined />, color: '#1890ff', text: 'Baja' },
    'info': { icon: <BellOutlined />, color: '#52c41a', text: 'Información' },
  };
  return configs[tipo] || configs['info'];
};

const getEstadoConfig = (estado: string) => {
  const configs: Record<string, { icon: React.ReactElement; color: string; text: string }> = {
    'activa': { icon: <AlertOutlined />, color: 'error', text: 'Activa' },
    'en_proceso': { icon: <SyncOutlined spin />, color: 'processing', text: 'En Proceso' },
    'resuelta': { icon: <CheckCircleOutlined />, color: 'success', text: 'Resuelta' },
    'descartada': { icon: <CloseCircleOutlined />, color: 'default', text: 'Descartada' },
  };
  return configs[estado] || configs['activa'];
};

const SistemaAlertas: React.FC = () => {
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const [state, dispatch] = useReducer(alertReducer, initialAlertState);
  const { alertas, loading, filtroTipo, filtroEstado, busqueda, alertaSeleccionada, modalVisible, rangoFechas, vistaActiva } = state;

  useEffect(() => {
    cargarAlertas();
    // Simular actualizaciones en tiempo real
    const interval = setInterval(() => {
      cargarAlertas();
    }, 30000); // Actualizar cada 30 segundos

    return () => clearInterval(interval);
  }, []);

  const cargarAlertas = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const data = await reportesService.listarAlertas();
      dispatch({ type: 'SET_ALERTAS', payload: data.map(mapAlertaReal) });
    } catch (error) {
      message.error('Error cargando alertas');
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const alertasFiltradas = alertas.filter(alerta => {
    const matchTipo = !filtroTipo || alerta.tipo === filtroTipo;
    const matchEstado = !filtroEstado || alerta.estado === filtroEstado;
    const matchBusqueda = !busqueda ||
      alerta.titulo.toLowerCase().includes(busqueda.toLowerCase()) ||
      alerta.paciente_nombre?.toLowerCase().includes(busqueda.toLowerCase()) ||
      alerta.descripcion.toLowerCase().includes(busqueda.toLowerCase());

    // Filtro por rango de fechas usando RangePicker
    const matchFecha = !rangoFechas[0] || !rangoFechas[1] ||
      (dayjs(alerta.fecha_creacion).isAfter(rangoFechas[0]) &&
       dayjs(alerta.fecha_creacion).isBefore(rangoFechas[1]));

    // Filtro por vista de tabs
    const matchVista = vistaActiva === 'todas' ||
      (vistaActiva === 'criticas' && alerta.tipo === 'critica') ||
      (vistaActiva === 'altas' && alerta.tipo === 'alta') ||
      (vistaActiva === 'medias' && alerta.tipo === 'media') ||
      (vistaActiva === 'bajas' && (alerta.tipo === 'baja' || alerta.tipo === 'info'));

    return matchTipo && matchEstado && matchBusqueda && matchFecha && matchVista;
  });

  const stats = {
    total: alertas.length,
    criticas: alertas.filter(a => a.tipo === 'critica').length,
    activas: alertas.filter(a => a.estado === 'activa').length,
    enProceso: alertas.filter(a => a.estado === 'en_proceso').length,
    resueltas: alertas.filter(a => a.estado === 'resuelta').length,
  };

  const handleVerDetalle = (alerta: AlertaMedica) => {
    dispatch({ type: 'SET_ALERTA_SELECCIONADA', payload: alerta });
    dispatch({ type: 'SET_MODAL_VISIBLE', payload: true });
  };

  const handleResolverAlerta = async (id: number) => {
    try {
      await reportesService.marcarAlertaResuelta(id);
      message.success('Alerta resuelta');
      cargarAlertas();
      dispatch({ type: 'SET_MODAL_VISIBLE', payload: false });
    } catch (error) {
      message.error('Error resolviendo alerta');
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Header con estadísticas */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Alertas"
              value={stats.total}
              prefix={<BellOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Alertas Críticas"
              value={stats.criticas}
              prefix={<FireOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Activas"
              value={stats.activas}
              prefix={<AlertOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="En Proceso"
              value={stats.enProceso}
              prefix={<SyncOutlined spin />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filtros */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col xs={24} md={8}>
            <Search
              placeholder="Buscar alertas..."
              value={busqueda}
              onChange={(e) => dispatch({ type: 'SET_BUSQUEDA', payload: e.target.value })}
              prefix={<SearchOutlined />}
              allowClear
            />
          </Col>
          <Col xs={24} md={5}>
            <Select
              placeholder="Tipo de Alerta"
              value={filtroTipo}
              onChange={(val) => dispatch({ type: 'SET_FILTRO_TIPO', payload: val })}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="critica">
                <FireOutlined /> Crítica
              </Option>
              <Option value="alta">
                <WarningOutlined /> Alta
              </Option>
              <Option value="media">
                <ExclamationCircleOutlined /> Media
              </Option>
              <Option value="baja">
                <InfoCircleOutlined /> Baja
              </Option>
              <Option value="info">
                <BellOutlined /> Información
              </Option>
            </Select>
          </Col>
          <Col xs={24} md={5}>
            <Select
              placeholder="Estado"
              value={filtroEstado}
              onChange={(val) => dispatch({ type: 'SET_FILTRO_ESTADO', payload: val })}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value="activa">Activas</Option>
              <Option value="en_proceso">En Proceso</Option>
              <Option value="resuelta">Resueltas</Option>
              <Option value="descartada">Descartadas</Option>
            </Select>
          </Col>
          <Col xs={24} md={6}>
            <Space>
              <Tooltip title="Actualizar alertas en tiempo real">
                <Button
                  icon={<SyncOutlined />}
                  onClick={cargarAlertas}
                  loading={loading}
                >
                  Actualizar
                </Button>
              </Tooltip>
              <Tooltip title="Limpiar todos los filtros">
                <Button
                  icon={<FilterOutlined />}
                  onClick={() => dispatch({ type: 'CLEAR_FILTERS' })}
                >
                  Limpiar
                </Button>
              </Tooltip>
            </Space>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <RangePicker
              style={{ width: '100%' }}
              placeholder={['Fecha inicio', 'Fecha fin']}
              value={rangoFechas}
              onChange={(dates) => dispatch({ type: 'SET_RANGO_FECHAS', payload: dates || [null, null] })}
              format="DD/MM/YYYY"
            />
          </Col>
        </Row>
      </Card>

      {/* Lista de Alertas con Tabs */}
      <Card
        title={
          <Space>
            <BellOutlined />
            <span>Alertas Médicas</span>
            <Badge count={alertasFiltradas.length} showZero />
          </Space>
        }
      >
        <Tabs
          activeKey={vistaActiva}
          onChange={(key) => dispatch({ type: 'SET_VISTA_ACTIVA', payload: key })}
          items={[
            {
              key: 'todas',
              label: (
                <Tooltip title="Ver todas las alertas">
                  <span>
                    <BellOutlined /> Todas ({alertas.length})
                  </span>
                </Tooltip>
              ),
              children: null,
            },
            {
              key: 'criticas',
              label: (
                <Tooltip title="Alertas que requieren atención inmediata">
                  <span>
                    <FireOutlined /> Críticas ({alertas.filter(a => a.tipo === 'critica').length})
                  </span>
                </Tooltip>
              ),
              children: null,
            },
            {
              key: 'altas',
              label: (
                <Tooltip title="Alertas de alta prioridad">
                  <span>
                    <WarningOutlined /> Altas ({alertas.filter(a => a.tipo === 'alta').length})
                  </span>
                </Tooltip>
              ),
              children: null,
            },
            {
              key: 'medias',
              label: (
                <Tooltip title="Alertas de prioridad media">
                  <span>
                    <ExclamationCircleOutlined /> Medias ({alertas.filter(a => a.tipo === 'media').length})
                  </span>
                </Tooltip>
              ),
              children: null,
            },
            {
              key: 'bajas',
              label: (
                <Tooltip title="Alertas de baja prioridad e informativas">
                  <span>
                    <InfoCircleOutlined /> Bajas/Info ({alertas.filter(a => a.tipo === 'baja' || a.tipo === 'info').length})
                  </span>
                </Tooltip>
              ),
              children: null,
            },
          ]}
        />

        <Spin spinning={loading}>
          {alertasFiltradas.length === 0 ? (
            <Empty description="No hay alertas que mostrar" />
          ) : (
            <List
              itemLayout="vertical"
              dataSource={alertasFiltradas}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total) => `Total ${total} alertas`,
              }}
              renderItem={alerta => {
                const tipoConfig = getTipoConfig(alerta.tipo);
                const estadoConfig = getEstadoConfig(alerta.estado);

                return (
                  <List.Item
                    key={alerta.id}
                    extra={
                      <Space direction="vertical" align="end">
                        <Tag
                          icon={tipoConfig.icon}
                          style={{
                            backgroundColor: tipoConfig.color,
                            color: 'white',
                            border: 'none',
                          }}
                        >
                          {tipoConfig.text}
                        </Tag>
                        <Tag color={estadoConfig.color} icon={estadoConfig.icon}>
                          {estadoConfig.text}
                        </Tag>
                        <Tooltip title="Ver detalle completo de la alerta">
                          <Button
                            type="primary"
                            size="small"
                            onClick={() => handleVerDetalle(alerta)}
                          >
                            Ver Detalle
                          </Button>
                        </Tooltip>
                      </Space>
                    }
                  >
                    <List.Item.Meta
                      avatar={
                        <Avatar
                          style={{
                            backgroundColor: tipoConfig.color,
                          }}
                          icon={tipoConfig.icon}
                        />
                      }
                      title={
                        <Space>
                          <strong>{alerta.titulo}</strong>
                          <Tag>{alerta.categoria}</Tag>
                        </Space>
                      }
                      description={
                        <Space direction="vertical" size="small">
                          <div>{alerta.descripcion}</div>
                          {alerta.paciente_nombre && (
                            <div>
                              <UserOutlined /> Paciente: {alerta.paciente_nombre}
                            </div>
                          )}
                          {alerta.asignado_a && (
                            <div>
                              <MedicineBoxOutlined /> Asignado a: {alerta.asignado_a}
                            </div>
                          )}
                          <div>
                            <ClockCircleOutlined /> {dayjs(alerta.fecha_creacion).fromNow()}
                          </div>
                        </Space>
                      }
                    />
                  </List.Item>
                );
              }}
            />
          )}
        </Spin>
      </Card>

      {/* Panel de Análisis por Categoría usando TabPane */}
      <Card
        title={
          <Space>
            <InfoCircleOutlined />
            <span>Análisis Detallado por Categoría</span>
          </Space>
        }
        style={{ marginTop: 24 }}
      >
        <Tabs
          defaultActiveKey="signos_vitales"
          type="card"
          items={[
            {
              key: 'signos_vitales',
              label: (
                <span>
                  <MedicineBoxOutlined /> Signos Vitales ({alertas.filter(a => a.categoria === 'Signos Vitales').length})
                </span>
              ),
              children: (
                <List
                  dataSource={alertas.filter(a => a.categoria === 'Signos Vitales')}
                  renderItem={alerta => (
                    <List.Item key={alerta.id}>
                      <List.Item.Meta
                        avatar={<Avatar style={{ backgroundColor: getTipoConfig(alerta.tipo).color }} icon={getTipoConfig(alerta.tipo).icon} />}
                        title={alerta.titulo}
                        description={`${alerta.paciente_nombre || 'Sin paciente'} - ${alerta.descripcion}`}
                      />
                      <Tag color={getEstadoConfig(alerta.estado).color}>{alerta.estado}</Tag>
                    </List.Item>
                  )}
                />
              )
            },
            {
              key: 'controles',
              label: (
                <span>
                  <CalendarOutlined /> Controles ({alertas.filter(a => a.categoria === 'Control Prenatal').length})
                </span>
              ),
              children: (
                <List
                  dataSource={alertas.filter(a => a.categoria === 'Control Prenatal')}
                  renderItem={alerta => (
                    <List.Item key={alerta.id}>
                      <List.Item.Meta
                        avatar={<Avatar style={{ backgroundColor: getTipoConfig(alerta.tipo).color }} icon={getTipoConfig(alerta.tipo).icon} />}
                        title={alerta.titulo}
                        description={`${alerta.paciente_nombre || 'Sin paciente'} - ${alerta.descripcion}`}
                      />
                      <Tag color={getEstadoConfig(alerta.estado).color}>{alerta.estado}</Tag>
                    </List.Item>
                  )}
                />
              )
            },
            {
              key: 'riesgos',
              label: (
                <span>
                  <WarningOutlined /> Riesgos ({alertas.filter(a => a.categoria === 'Riesgo Obstétrico').length})
                </span>
              ),
              children: (
                <List
                  dataSource={alertas.filter(a => a.categoria === 'Riesgo Obstétrico')}
                  renderItem={alerta => (
                    <List.Item key={alerta.id}>
                      <List.Item.Meta
                        avatar={<Avatar style={{ backgroundColor: getTipoConfig(alerta.tipo).color }} icon={getTipoConfig(alerta.tipo).icon} />}
                        title={alerta.titulo}
                        description={`${alerta.paciente_nombre || 'Sin paciente'} - ${alerta.descripcion}`}
                      />
                      <Tag color={getEstadoConfig(alerta.estado).color}>{alerta.estado}</Tag>
                    </List.Item>
                  )}
                />
              )
            },
            {
              key: 'otras',
              label: (
                <span>
                  <BellOutlined /> Otras ({alertas.filter(a => !['Signos Vitales', 'Control Prenatal', 'Riesgo Obstétrico'].includes(a.categoria)).length})
                </span>
              ),
              children: (
                <List
                  dataSource={alertas.filter(a => !['Signos Vitales', 'Control Prenatal', 'Riesgo Obstétrico'].includes(a.categoria))}
                  renderItem={alerta => (
                    <List.Item key={alerta.id}>
                      <List.Item.Meta
                        avatar={<Avatar style={{ backgroundColor: getTipoConfig(alerta.tipo).color }} icon={getTipoConfig(alerta.tipo).icon} />}
                        title={alerta.titulo}
                        description={`${alerta.paciente_nombre || 'Sin paciente'} - ${alerta.descripcion}`}
                      />
                      <Tag color={getEstadoConfig(alerta.estado).color}>{alerta.estado}</Tag>
                    </List.Item>
                  )}
                />
              )
            }
          ]}
        />
      </Card>

      {/* Modal de Detalle */}
      <Modal
        title={
          <Space>
            <AlertOutlined />
            Detalle de Alerta
          </Space>
        }
        open={modalVisible}
        onCancel={() => dispatch({ type: 'SET_MODAL_VISIBLE', payload: false })}
        footer={[
          <Button key="close" onClick={() => dispatch({ type: 'SET_MODAL_VISIBLE', payload: false })}>
            Cerrar
          </Button>,
          alertaSeleccionada?.estado === 'activa' && (
            <Button
              key="resolver"
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={() => alertaSeleccionada && handleResolverAlerta(alertaSeleccionada.id)}
            >
              Resolver Alerta
            </Button>
          ),
        ]}
        width={700}
      >
        {alertaSeleccionada && (
          <div>
            <Alert
              message={alertaSeleccionada.titulo}
              description={alertaSeleccionada.descripcion}
              type={alertaSeleccionada.tipo === 'critica' ? 'error' : alertaSeleccionada.tipo === 'alta' ? 'warning' : 'info'}
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Divider orientation="left">Información del Paciente</Divider>
            <Row gutter={16}>
              <Col span={12}>
                <p><strong>Nombre:</strong> {alertaSeleccionada.paciente_nombre || 'N/A'}</p>
              </Col>
              <Col span={12}>
                <p>
                  <strong>ID:</strong> {alertaSeleccionada.paciente_id || 'N/A'}
                  {alertaSeleccionada.paciente_id && (
                    <Button
                      type="link"
                      size="small"
                      onClick={() => navigate(`/dashboard/pacientes/${alertaSeleccionada.paciente_id}`)}
                    >
                      Ver Paciente
                    </Button>
                  )}
                </p>
              </Col>
            </Row>

            <Divider orientation="left">Detalles de la Alerta</Divider>
            <Row gutter={16}>
              <Col span={12}>
                <p><strong>Categoría:</strong> {alertaSeleccionada.categoria}</p>
              </Col>
              <Col span={12}>
                <p><strong>Prioridad:</strong> {alertaSeleccionada.prioridad}</p>
              </Col>
              <Col span={12}>
                <p><strong>Creada:</strong> {dayjs(alertaSeleccionada.fecha_creacion).format('DD/MM/YYYY HH:mm')}</p>
              </Col>
              <Col span={12}>
                <p><strong>Asignado a:</strong> {alertaSeleccionada.asignado_a || 'Sin asignar'}</p>
              </Col>
            </Row>

            {alertaSeleccionada.notas && (
              <>
                <Divider orientation="left">Notas</Divider>
                <p>{alertaSeleccionada.notas}</p>
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default SistemaAlertas;
