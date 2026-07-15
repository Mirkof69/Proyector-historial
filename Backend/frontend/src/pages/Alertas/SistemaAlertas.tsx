/**
 * =============================================================================
 * SISTEMA DE ALERTAS MÉDICAS - DASHBOARD COMPLETO
 * =============================================================================
 * Centro de control de alertas médicas con notificaciones en tiempo real
 * =============================================================================
 */

import React, { useReducer, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { useNavigate } from 'react-router-dom';
import { reportesService } from '../../services/reportesService';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import es from 'dayjs/locale/es';
import {
  AlertaMedica, alertReducer, initialAlertState, mapAlertaReal,
} from './sistemaAlertasUtils';
import AlertasStats from './components/AlertasStats';
import AlertasFiltros from './components/AlertasFiltros';
import AlertasListado from './components/AlertasListado';
import AlertasCategorias from './components/AlertasCategorias';
import AlertaDetalleModal from './components/AlertaDetalleModal';

dayjs.extend(relativeTime);
dayjs.locale(es);

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
      <AlertasStats stats={stats} />

      {/* Filtros */}
      <AlertasFiltros
        busqueda={busqueda}
        filtroTipo={filtroTipo}
        filtroEstado={filtroEstado}
        rangoFechas={rangoFechas}
        loading={loading}
        dispatch={dispatch}
        cargarAlertas={cargarAlertas}
      />

      {/* Lista de Alertas con Tabs */}
      <AlertasListado
        alertas={alertas}
        alertasFiltradas={alertasFiltradas}
        vistaActiva={vistaActiva}
        loading={loading}
        dispatch={dispatch}
        handleVerDetalle={handleVerDetalle}
      />

      {/* Panel de Análisis por Categoría usando TabPane */}
      <AlertasCategorias alertas={alertas} />

      {/* Modal de Detalle */}
      <AlertaDetalleModal
        modalVisible={modalVisible}
        alertaSeleccionada={alertaSeleccionada}
        dispatch={dispatch}
        handleResolverAlerta={handleResolverAlerta}
        navigate={navigate}
      />
    </div>
  );
};

export default SistemaAlertas;
