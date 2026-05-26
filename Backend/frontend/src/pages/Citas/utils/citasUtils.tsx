import React from 'react';
import { Tag } from 'antd';
import {
  CalendarOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  MedicineBoxOutlined,
} from '@ant-design/icons';
import { EstadoCita } from '../../../services/citasService';

export const getEstadoTag = (estado: EstadoCita) => {
  const configs: Record<EstadoCita, { color: string; icon: React.ReactNode; text: string }> = {
    agendada: { color: 'blue', icon: <CalendarOutlined />, text: 'Agendada' },
    confirmada: { color: 'processing', icon: <CheckCircleOutlined />, text: 'Confirmada' },
    en_espera: { color: 'warning', icon: <ClockCircleOutlined />, text: 'En Espera' },
    en_consulta: { color: 'purple', icon: <MedicineBoxOutlined />, text: 'En Consulta' },
    completada: { color: 'success', icon: <CheckCircleOutlined />, text: 'Completada' },
    cancelada: { color: 'error', icon: <CloseCircleOutlined />, text: 'Cancelada' },
    no_asistio: { color: 'default', icon: <CloseCircleOutlined />, text: 'No Asistió' },
  };
  const config = configs[estado];
  return <Tag icon={config.icon} color={config.color}>{config.text}</Tag>;
};
