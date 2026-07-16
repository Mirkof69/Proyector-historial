import React from 'react';
import {
  WarningOutlined, ClockCircleOutlined, ExclamationCircleOutlined, BellOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { AlertaMedica } from '../../services/reportesService';

export interface AlertasState {
  alertas: AlertaMedica[];
  loading: boolean;
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
  const colors: any = {
    baja: 'blue',
    media: 'orange',
    alta: 'red',
    critica: 'magenta',
    emergencia: 'red'
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
    { name: 'Baja', value: counts.baja, color: '#1890ff' },
    { name: 'Media', value: counts.media, color: '#fa8c16' },
    { name: 'Alta', value: counts.alta, color: '#f5222d' },
    { name: 'Crítica', value: counts.critica, color: '#eb2f96' }
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
