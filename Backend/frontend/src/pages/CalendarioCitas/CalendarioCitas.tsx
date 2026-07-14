/**
 * =============================================================================
 * CALENDARIO DE CITAS - VISTA MENSUAL
 * =============================================================================
 * Vista de calendario completo con todas las citas: vista mensual, citas por
 * día, código de colores, modal de detalle y navegación entre meses.
 * Stats, filtros/leyenda y modal viven en ./components.
 * =============================================================================
 */

import React, { useEffect, useReducer, useCallback, useMemo } from 'react';
import { Card, Calendar, Badge, Button, Space, Typography, Tooltip, Spin } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import type { Dayjs } from 'dayjs';
import { CalendarOutlined, ArrowLeftOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import locale from 'antd/es/calendar/locale/es_ES';
import { citasService } from '../../services/citasService';
import { FRONTEND_ROUTES } from '../../config/routes';
import {
  calendarioReducer, initialCalendarioState, esAtrasada, CitaDelDia,
} from './components/calendarioCitasUtils';
import EstadisticasMes from './components/EstadisticasMes';
import FiltrosLeyendaCitas from './components/FiltrosLeyendaCitas';
import ModalCitasDelDia from './components/ModalCitasDelDia';
import './CalendarioCitas.css';

const { Title, Text } = Typography;

dayjs.locale('es');

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
  const handleVolver = () => navigate(FRONTEND_ROUTES.DASHBOARD.CITAS);
  const handleNuevaCita = () => navigate(FRONTEND_ROUTES.DASHBOARD.CITAS_NUEVO);

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
    if (citasDelDia.length === 0) return null;

    const pendientes = citasDelDia.filter((c) => c.estado === 'pendiente').length;
    const confirmadas = citasDelDia.filter((c) => c.estado === 'confirmada').length;
    const completadas = citasDelDia.filter((c) => c.estado === 'completada').length;
    const canceladas = citasDelDia.filter((c) => c.estado === 'cancelada').length;

    return (
      <div className="calendar-day-content">
        <Space direction="vertical" size={2} style={{ width: '100%' }}>
          {pendientes > 0 && <Badge status="warning" text={`${pendientes} Pendiente${pendientes > 1 ? 's' : ''}`} style={{ fontSize: 12 }} />}
          {confirmadas > 0 && <Badge status="processing" text={`${confirmadas} Confirmada${confirmadas > 1 ? 's' : ''}`} style={{ fontSize: 12 }} />}
          {completadas > 0 && <Badge status="success" text={`${completadas} Completada${completadas > 1 ? 's' : ''}`} style={{ fontSize: 12 }} />}
          {canceladas > 0 && <Badge status="error" text={`${canceladas} Cancelada${canceladas > 1 ? 's' : ''}`} style={{ fontSize: 12 }} />}
        </Space>
      </div>
    );
  };

  const monthCellRender = (fecha: Dayjs) => {
    const citasDelMes = citasFiltradas.filter((cita) => dayjs(cita.fecha_cita).isSame(fecha, 'month'));
    if (citasDelMes.length === 0) return null;
    return (
      <div className="calendar-month-content">
        <Text strong>{citasDelMes.length} citas</Text>
      </div>
    );
  };

  // ==========================================================================
  // ESTADÍSTICAS DEL MES
  // ==========================================================================
  const citasDelMes = citasFiltradas.filter((cita) => dayjs(cita.fecha_cita).isSame(mesActual, 'month'));
  const estadisticas = {
    total: citasDelMes.length,
    pendientes: citasDelMes.filter((c) => c.estado === 'agendada' || c.estado === 'en_espera').length,
    confirmadas: citasDelMes.filter((c) => c.estado === 'confirmada').length,
    completadas: citasDelMes.filter((c) => c.estado === 'completada').length,
    canceladas: citasDelMes.filter((c) => c.estado === 'cancelada').length,
    atrasadas: citasDelMes.filter((c) => esAtrasada(c.fecha_cita, c.estado)).length,
  };

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
        <EstadisticasMes {...estadisticas} />

        <FiltrosLeyendaCitas
          filtroEstado={filtroEstado}
          filtroTipo={filtroTipo}
          onEstadoChange={(val) => dispatch({ type: 'SET_FILTRO_ESTADO', payload: val })}
          onTipoChange={(val) => dispatch({ type: 'SET_FILTRO_TIPO', payload: val })}
          onClearFilters={() => dispatch({ type: 'CLEAR_FILTERS' })}
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

      <ModalCitasDelDia
        open={modalVisible}
        dia={diaSeleccionado}
        citas={citasDelDiaSeleccionado}
        onClose={() => dispatch({ type: 'SET_MODAL_VISIBLE', payload: false })}
        onVerDetalle={handleVerDetalle}
      />
    </div>
  );
};

export default CalendarioCitas;
