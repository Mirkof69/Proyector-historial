import React from 'react';
import {
  WarningOutlined, ClockCircleOutlined, ExclamationCircleOutlined, BellOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { AlertaMedica } from '../../services/reportesService';

export interface AlertasState {
  selectedAlerta: AlertaMedica | null;
  drawerVisible: boolean;
  searchText: string;
  filterSeveridad: string;
  filterEstado: string;
  dateRange: any;
  modalNuevaAlerta: boolean;
}

export const getSeveridadIcon = (prioridad: string) => {
  switch (prioridad) {
    case 'critica':
    case 'emergencia': return <ExclamationCircleOutlined />;
    case 'alta': return <WarningOutlined />;
    case 'media': return <ClockCircleOutlined />;
    case 'baja': return <BellOutlined />;
    default: return <BellOutlined />;
  }
};

export const renderPieLabel = ({ name, percent }: { name: string; percent: number }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`;

export const getSeveridadColor = (prioridad: string) => {
  // Color de Tag por token: la prioridad es un estado clínico.
  const colors: any = {
    baja: 'processing',
    media: 'warning',
    alta: 'error',
    critica: 'error',
    emergencia: 'error'
  };
  return colors[prioridad] || 'default';
};

// Datos para gráficas
export const getSeveridadData = (alertas: AlertaMedica[]) => {
  const counts = {
    baja: alertas.filter(a => a.prioridad === 'baja').length,
    media: alertas.filter(a => a.prioridad === 'media').length,
    alta: alertas.filter(a => a.prioridad === 'alta').length,
    critica: alertas.filter(a => a.prioridad === 'critica' || a.prioridad === 'emergencia').length
  };
  return [
    { name: 'Baja', value: counts.baja, color: 'var(--color-info)' },
    { name: 'Media', value: counts.media, color: 'var(--color-aviso)' },
    { name: 'Alta', value: counts.alta, color: 'var(--grafico-5)' },
    { name: 'Crítica', value: counts.critica, color: 'var(--color-peligro)' }
  ];
};

export const getModuloData = (alertas: AlertaMedica[]) => {
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

export const getTiempoResolucionData = (alertas: AlertaMedica[]) => {
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
