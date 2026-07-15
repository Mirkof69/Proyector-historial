import React from 'react';
import { Tag } from 'antd';
import {
  EyeOutlined, EditOutlined, DeleteOutlined, PlusOutlined, ReloadOutlined,
  CalendarOutlined, ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined,
  ExclamationCircleOutlined, UserOutlined, MedicineBoxOutlined, WarningOutlined,
  MoreOutlined, PhoneOutlined, BellOutlined, FileExcelOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { EstadoCita, TipoCita } from '../../services/citasService';

export interface EstadoCitaConfig {
  color: string;
  icon: React.ReactNode;
  text: string;
}

export interface EstadisticasCitas {
  total: number;
  agendadas: number;
  confirmadas: number;
  en_espera: number;
  en_consulta: number;
  completadas: number;
  canceladas: number;
  no_asistio: number;
  hoy: number;
  atrasadas: number;
  pendientes_confirmacion: number;
}

export const calendarIcon4 = <CalendarOutlined />;
export const clockCircleIcon4 = <ClockCircleOutlined />;
export const checkCircleIcon5 = <CheckCircleOutlined />;
export const closeCircleIcon2 = <CloseCircleOutlined />;
export const warningIcon3 = <WarningOutlined />;
export const userIcon2 = <UserOutlined />;
export const medicineBoxIcon2 = <MedicineBoxOutlined />;
export const moreIcon = <MoreOutlined />;
export const phoneIcon = <PhoneOutlined />;
export const bellIcon = <BellOutlined />;
export const fileExcelIcon2 = <FileExcelOutlined />;
export const eyeIcon3 = <EyeOutlined />;
export const editIcon3 = <EditOutlined />;
export const deleteIcon2 = <DeleteOutlined />;
export const plusIcon3 = <PlusOutlined />;
export const reloadIcon = <ReloadOutlined />;
export const exclamationIcon = <ExclamationCircleOutlined />;

export const getEstadoTag = (estado: EstadoCita) => {
  const configs: Record<EstadoCita, EstadoCitaConfig> = {
    agendada: {
      color: 'blue',
      icon: calendarIcon4,
      text: 'Agendada',
    },
    confirmada: {
      color: 'processing',
      icon: checkCircleIcon5,
      text: 'Confirmada',
    },
    en_espera: {
      color: 'warning',
      icon: clockCircleIcon4,
      text: 'En Espera',
    },
    en_consulta: {
      color: 'purple',
      icon: medicineBoxIcon2,
      text: 'En Consulta',
    },
    completada: {
      color: 'success',
      icon: checkCircleIcon5,
      text: 'Completada',
    },
    cancelada: {
      color: 'error',
      icon: closeCircleIcon2,
      text: 'Cancelada',
    },
    no_asistio: {
      color: 'default',
      icon: closeCircleIcon2,
      text: 'No Asistió',
    },
  };

  const config = configs[estado] || configs.agendada;
  return (
    <Tag icon={config.icon} color={config.color}>
      {config.text}
    </Tag>
  );
};

export const getTipoColor = (tipo: TipoCita): string => {
  const colores: Record<TipoCita, string> = {
    primera_vez: 'cyan',
    control: 'blue',
    urgencia: 'red',
    seguimiento: 'green',
  };
  return colores[tipo] || 'default';
};

export const getTipoTexto = (tipo: TipoCita): string => {
  const textos: Record<TipoCita, string> = {
    primera_vez: 'Primera Vez',
    control: 'Control',
    urgencia: 'Urgencia',
    seguimiento: 'Seguimiento',
  };
  return textos[tipo] || tipo;
};

export const esAtrasada = (fechaCita: string, estado: EstadoCita): boolean => {
  return (
    dayjs(fechaCita).isBefore(dayjs(), 'day') &&
    ['agendada', 'confirmada'].includes(estado)
  );
};

export const esHoy = (fechaCita: string): boolean => {
  return dayjs(fechaCita).isSame(dayjs(), 'day');
};
