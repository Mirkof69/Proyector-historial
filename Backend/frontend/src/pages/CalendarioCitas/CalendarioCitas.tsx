/**
 * =============================================================================
 * CALENDARIO DE CITAS - VISTA MENSUAL
 * =============================================================================
 * Vista de calendario completo con todas las citas
 * - Vista mensual interactiva
 * - Citas agrupadas por día
 * - Código de colores por tipo y estado
 * - Modal de detalle al hacer clic
 * - Navegación entre meses
 * - Conexión: GET /citas/
 * =============================================================================
 */

import React, { useState, useEffect, useReducer, useCallback, useMemo } from 'react';
import {
  Card,
  Calendar,
  Badge,
  Modal,
  List,
  Button,
  Space,
  Tag,
  Typography,
  Row,
  Col,
  Select,
  Alert,
  Tooltip,
  Spin,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import type { Dayjs } from 'dayjs';
import type { BadgeProps } from 'antd';
import {
  CalendarOutlined,
  ClockCircleOutlined,
  UserOutlined,
  ArrowLeftOutlined,
  PlusOutlined,
  ReloadOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import locale from 'antd/es/calendar/locale/es_ES';
import { citasService, Cita } from '../../services/citasService';
import { FRONTEND_ROUTES } from '../../config/routes';
import './CalendarioCitas.css';

const { Title, Text } = Typography;
const { Option } = Select;

dayjs.locale('es');

interface CitaDelDia {
  id: number;
  hora: string;
  paciente: string;
  tipo: string;
  estado: string;
  motivo: string;
}

interface CalendarioState {
  loading: boolean;
  citas: Cita[];
  citasFiltradas: Cita[];
  modalVisible: boolean;
  citasDelDiaSeleccionado: CitaDelDia[];
  diaSeleccionado: Dayjs;
  filtroEstado: string;
  filtroTipo: string;
  mesActual: Dayjs;
}

type CalendarioAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_CITAS'; payload: Cita[] }
  | { type: 'SET_CITAS_FILTRADAS'; payload: Cita[] }
  | { type: 'SET_MODAL_VISIBLE'; payload: boolean }
  | { type: 'SET_DIA_SELECCIONADO'; payload: CitaDelDia[] }
  | { type: 'SET_FILTRO_ESTADO'; payload: string }
  | { type: 'SET_FILTRO_TIPO'; payload: string }
  | { type: 'SET_MES_ACTUAL'; payload: Dayjs }
  | { type: 'CLEAR_FILTERS' };

const initialCalendarioState: CalendarioState = {
  loading: false,
  citas: [],
  citasFiltradas: [],
  modalVisible: false,
  citasDelDiaSeleccionado: [],
  diaSeleccionado: dayjs(),
  filtroEstado: '',
  filtroTipo: '',
  mesActual: dayjs(),
};

function calendarioReducer(state: CalendarioState, action: CalendarioAction): CalendarioState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_CITAS':
      return { ...state, citas: action.payload, loading: false };
    case 'SET_CITAS_FILTRADAS':
      return { ...state, citasFiltradas: action.payload };
    case 'SET_MODAL_VISIBLE':
      return { ...state, modalVisible: action.payload };
    case 'SET_DIA_SELECCIONADO':
      return { ...state, citasDelDiaSeleccionado: action.payload };
    case 'SET_FILTRO_ESTADO':
      return { ...state, filtroEstado: action.payload };
    case 'SET_FILTRO_TIPO':
      return { ...state, filtroTipo: action.payload };
    case 'SET_MES_ACTUAL':
      return { ...state, mesActual: action.payload };
    case 'CLEAR_FILTERS':
      return { ...state, filtroEstado: '', filtroTipo: '' };
    default:
      return state;
  }
}

const getEstadoBadge = (estado: string): BadgeProps['status'] => {
  const estados: Record<string, BadgeProps['status']> = {
    pendiente: 'warning',
    confirmada: 'processing',
    completada: 'success',
    cancelada: 'error',
  };
  return estados[estado] || 'default';
};

const getEstadoColor = (estado: string): string => {
  const colores: Record<string, string> = {
    pendiente: '#faad14',
    confirmada: '#1890ff',
    completada: '#52c41a',
    cancelada: '#ff4d4f',
  };
  return colores[estado] || '#d9d9d9';
};

const getTipoColor = (tipo: string): string => {
  const colores: Record<string, string> = {
    control_prenatal: '#1890ff',
    ecografia: '#722ed1',
    consulta_general: '#13c2c2',
    emergencia: '#ff4d4f',
    seguimiento: '#52c41a',
    laboratorio: '#fa8c16',
    procedimiento: '#eb2f96',
  };
  return colores[tipo] || '#d9d9d9';
};

const esAtrasada = (fechaHora: string, estado: string): boolean => {
  return (
    dayjs(fechaHora).isBefore(dayjs()) &&
    (estado === 'pendiente' || estado === 'confirmada')
  );
};

const CalendarioCitas: React.FC = () => {
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const [state, dispatch] = useReducer(calendarioReducer, initialCalendarioState);
  const { loading, citas, modalVisible, citasDelDiaSeleccionado, diaSeleccionado, filtroEstado, filtroTipo, mesActual } = state;

  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================
  const cargarCitas = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const data = await citasService.getAll();
      dispatch({ type: 'SET_CITAS', payload: data });
      message.success(`${data.length} citas cargadas`);
    } catch (error) {
      message.error('Error al cargar las citas');
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [message]);

  useEffect(() => {
    cargarCitas();
  }, [cargarCitas]);

  const citasFiltradas = useMemo(() => {
    let resultado = [...citas];

    if (filtroEstado) {
      resultado = resultado.filter((cita) => cita.estado === filtroEstado);
    }

    if (filtroTipo) {
      resultado = resultado.filter((cita) => cita.tipo_cita === filtroTipo);
    }

    return resultado;
  }, [citas, filtroEstado, filtroTipo]);

  // ==========================================================================
  // HANDLERS
  // ==========================================================================
  const handleVolver = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.CITAS);
  };

  const handleNuevaCita = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.CITAS_NUEVO);
  };

  const handleVerDetalle = useCallback((citaId: number) => {
    dispatch({ type: 'SET_MODAL_VISIBLE', payload: false });
    navigate(FRONTEND_ROUTES.DASHBOARD.CITAS_DETALLE(citaId));
  }, [navigate]);

  const handlePanelChange = useCallback((value: Dayjs) => {
    dispatch({ type: 'SET_MES_ACTUAL', payload: value });
  }, []);

  // ==========================================================================
  // FUNCIONES AUXILIARES
  // ==========================================================================
  const getCitasDelDia = useCallback((fecha: Dayjs): CitaDelDia[] => {
    return citasFiltradas
      .filter((cita) => dayjs(cita.fecha_cita).isSame(fecha, 'day'))
      .sort((a, b) => dayjs(`${a.fecha_cita}T${a.hora_cita}`).unix() - dayjs(`${b.fecha_cita}T${b.hora_cita}`).unix())
      .map((cita) => ({
        id: cita.id!,
        hora: dayjs(`${cita.fecha_cita}T${cita.hora_cita}`).format('HH:mm'),
        paciente: cita.paciente_info?.nombre_completo || 'Sin nombre',
        tipo: cita.tipo_cita || 'No especificado',
        estado: cita.estado,
        motivo: cita.motivo || '',
      }));
  }, [citasFiltradas]);

  const handleDiaClick = useCallback((fecha: Dayjs) => {
    const citasDelDia = getCitasDelDia(fecha);
    dispatch({ type: 'SET_DIA_SELECCIONADO', payload: citasDelDia });
    if (citasDelDia.length > 0) {
      dispatch({ type: 'SET_MODAL_VISIBLE', payload: true });
    } else {
      message.info('No hay citas programadas para este día');
    }
  }, [getCitasDelDia, message]);

  // ==========================================================================
  // RENDER DEL CALENDARIO
  // ==========================================================================
  const dateCellRender = (fecha: Dayjs) => {
    const citasDelDia = getCitasDelDia(fecha);

    if (citasDelDia.length === 0) {
      return null;
    }

    // Contar citas por estado
    const pendientes = citasDelDia.filter((c) => c.estado === 'pendiente').length;
    const confirmadas = citasDelDia.filter((c) => c.estado === 'confirmada').length;
    const completadas = citasDelDia.filter((c) => c.estado === 'completada').length;
    const canceladas = citasDelDia.filter((c) => c.estado === 'cancelada').length;

    return (
      <div className="calendar-day-content">
        <Space direction="vertical" size={2} style={{ width: '100%' }}>
          {pendientes > 0 && (
            <Badge
              status="warning"
              text={`${pendientes} Pendiente${pendientes > 1 ? 's' : ''}`}
              style={{ fontSize: 12 }}
            />
          )}
          {confirmadas > 0 && (
            <Badge
              status="processing"
              text={`${confirmadas} Confirmada${confirmadas > 1 ? 's' : ''}`}
              style={{ fontSize: 12 }}
            />
          )}
          {completadas > 0 && (
            <Badge
              status="success"
              text={`${completadas} Completada${completadas > 1 ? 's' : ''}`}
              style={{ fontSize: 12 }}
            />
          )}
          {canceladas > 0 && (
            <Badge
              status="error"
              text={`${canceladas} Cancelada${canceladas > 1 ? 's' : ''}`}
              style={{ fontSize: 12 }}
            />
          )}
        </Space>
      </div>
    );
  };

  const monthCellRender = (fecha: Dayjs) => {
    const citasDelMes = citasFiltradas.filter((cita) =>
      dayjs(cita.fecha_cita).isSame(fecha, 'month')
    );

    if (citasDelMes.length === 0) {
      return null;
    }

    return (
      <div className="calendar-month-content">
        <Text strong>{citasDelMes.length} citas</Text>
      </div>
    );
  };

  // ==========================================================================
  // ESTADÍSTICAS DEL MES
  // ==========================================================================
  const getEstadisticasMes = () => {
    const citasDelMes = citasFiltradas.filter((cita) =>
      dayjs(cita.fecha_cita).isSame(mesActual, 'month')
    );

    return {
      total: citasDelMes.length,
      pendientes: citasDelMes.filter((c) => c.estado === 'agendada' || c.estado === 'en_espera').length,
      confirmadas: citasDelMes.filter((c) => c.estado === 'confirmada').length,
      completadas: citasDelMes.filter((c) => c.estado === 'completada').length,
      canceladas: citasDelMes.filter((c) => c.estado === 'cancelada').length,
      atrasadas: citasDelMes.filter((c) =>
        esAtrasada(c.fecha_cita, c.estado)
      ).length,
    };
  };

  const estadisticas = getEstadisticasMes();

  // ==========================================================================
  // RENDER PRINCIPAL
  // ==========================================================================
  return (
    <div className="calendario-citas-container">
      <Card
        title={
          <Space>
            <CalendarOutlined style={{ fontSize: 24, color: '#1890ff' }} />
            <Title level={3} style={{ margin: 0 }}>
              Calendario de Citas - {mesActual.format('MMMM YYYY')}
            </Title>
          </Space>
        }
        extra={
          <Space>
            <Tooltip title="Regresar a la vista anterior">
              <Button icon={<ArrowLeftOutlined />} onClick={handleVolver}>
                Volver
              </Button>
            </Tooltip>
            <Tooltip title="Recargar todas las citas del calendario">
              <Button icon={<ReloadOutlined />} onClick={cargarCitas}>
                Actualizar
              </Button>
            </Tooltip>
            <Tooltip title="Crear una nueva cita en el calendario">
              <Button type="primary" icon={<PlusOutlined />} onClick={handleNuevaCita}>
                Nueva Cita
              </Button>
            </Tooltip>
          </Space>
        }
      >
        {/* ESTADÍSTICAS DEL MES */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={12} sm={8} md={4}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <CalendarOutlined style={{ fontSize: 24, color: '#1890ff' }} />
              <div style={{ marginTop: 8 }}>
                <Text strong style={{ fontSize: 18 }}>
                  {estadisticas.total}
                </Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Total
                </Text>
              </div>
            </Card>
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <ClockCircleOutlined style={{ fontSize: 24, color: '#faad14' }} />
              <div style={{ marginTop: 8 }}>
                <Text strong style={{ fontSize: 18, color: '#faad14' }}>
                  {estadisticas.pendientes}
                </Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Pendientes
                </Text>
              </div>
            </Card>
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <CheckCircleOutlined style={{ fontSize: 24, color: '#1890ff' }} />
              <div style={{ marginTop: 8 }}>
                <Text strong style={{ fontSize: 18, color: '#1890ff' }}>
                  {estadisticas.confirmadas}
                </Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Confirmadas
                </Text>
              </div>
            </Card>
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
              <div style={{ marginTop: 8 }}>
                <Text strong style={{ fontSize: 18, color: '#52c41a' }}>
                  {estadisticas.completadas}
                </Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Completadas
                </Text>
              </div>
            </Card>
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <CloseCircleOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
              <div style={{ marginTop: 8 }}>
                <Text strong style={{ fontSize: 18, color: '#ff4d4f' }}>
                  {estadisticas.canceladas}
                </Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Canceladas
                </Text>
              </div>
            </Card>
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <WarningOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
              <div style={{ marginTop: 8 }}>
                <Text strong style={{ fontSize: 18, color: '#ff4d4f' }}>
                  {estadisticas.atrasadas}
                </Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Atrasadas
                </Text>
              </div>
            </Card>
          </Col>
        </Row>

        {/* FILTROS */}
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} md={8}>
            <Select
              placeholder="Filtrar por estado"
              style={{ width: '100%' }}
              value={filtroEstado}
              onChange={(val) => dispatch({ type: 'SET_FILTRO_ESTADO', payload: val })}
              allowClear
            >
              <Option value="pendiente">Pendiente</Option>
              <Option value="confirmada">Confirmada</Option>
              <Option value="completada">Completada</Option>
              <Option value="cancelada">Cancelada</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Select
              placeholder="Filtrar por tipo"
              style={{ width: '100%' }}
              value={filtroTipo}
              onChange={(val) => dispatch({ type: 'SET_FILTRO_TIPO', payload: val })}
              allowClear
            >
              <Option value="control_prenatal">Control Prenatal</Option>
              <Option value="ecografia">Ecografía</Option>
              <Option value="consulta_general">Consulta General</Option>
              <Option value="emergencia">Emergencia</Option>
              <Option value="seguimiento">Seguimiento</Option>
              <Option value="laboratorio">Laboratorio</Option>
              <Option value="procedimiento">Procedimiento</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Button
              icon={<FilterOutlined />}
              onClick={() => dispatch({ type: 'CLEAR_FILTERS' })}
              block
            >
              Limpiar Filtros
            </Button>
          </Col>
        </Row>

        {/* LEYENDA */}
        <Alert
          message="Leyenda del Calendario"
          description={
            <Space direction="vertical" size="small">
              <Space>
                <Badge status="warning" />
                <Text>Pendiente</Text>
                <Badge status="processing" />
                <Text>Confirmada</Text>
                <Badge status="success" />
                <Text>Completada</Text>
                <Badge status="error" />
                <Text>Cancelada</Text>
              </Space>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Haga clic en cualquier día para ver las citas programadas
              </Text>
            </Space>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        {/* CALENDARIO */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '100px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>Cargando calendario…</div>
          </div>
        ) : (
          <Calendar
            locale={locale}
            dateCellRender={dateCellRender}
            monthCellRender={monthCellRender}
            onSelect={handleDiaClick}
            onPanelChange={handlePanelChange}
            className="calendar-citas"
          />
        )}
      </Card>

      {/* MODAL DE CITAS DEL DÍA */}
      <Modal
        title={
          <Space>
            <CalendarOutlined />
            Citas del {diaSeleccionado.format('DD/MM/YYYY')}
          </Space>
        }
        open={modalVisible}
        onCancel={() => dispatch({ type: 'SET_MODAL_VISIBLE', payload: false })}
        footer={[
          <Button key="close" onClick={() => dispatch({ type: 'SET_MODAL_VISIBLE', payload: false })}>
            Cerrar
          </Button>,
        ]}
        width={700}
      >
        <List
          dataSource={citasDelDiaSeleccionado}
          renderItem={(cita) => (
            <List.Item
              actions={[
                <Button
                  type="link"
                  onClick={() => handleVerDetalle(cita.id)}
                  key="ver"
                >
                  Ver Detalle
                </Button>,
              ]}
            >
              <List.Item.Meta
                avatar={
                  <div
                    className="cita-avatar"
                    style={{
                      background: getEstadoColor(cita.estado),
                    }}
                  >
                    {cita.hora}
                  </div>
                }
                title={
                  <Space>
                    <UserOutlined />
                    <Text strong>{cita.paciente}</Text>
                    <Tag color={getTipoColor(cita.tipo)}>
                      {cita.tipo.replace('_', ' ').toUpperCase()}
                    </Tag>
                  </Space>
                }
                description={
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <Space>
                      <Badge status={getEstadoBadge(cita.estado)} />
                      <Text>{cita.estado.toUpperCase()}</Text>
                    </Space>
                    {cita.motivo && (
                      <Text type="secondary" ellipsis>
                        {cita.motivo}
                      </Text>
                    )}
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Modal>
    </div>
  );
};

export default CalendarioCitas;
