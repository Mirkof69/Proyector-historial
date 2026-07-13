import React from 'react';
import { Tag } from 'antd';
import {
  FilePdfOutlined, FileExcelOutlined, ReloadOutlined,
  CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined,
} from '@ant-design/icons';

export const EstadoTagReporte: React.FC<{ estado: string }> = ({ estado }) => {
  switch (estado) {
    case 'TERMINADO':
      return <Tag icon={<CheckCircleOutlined />} color="success">TERMINADO</Tag>;
    case 'PROCESANDO':
      return <Tag icon={<ReloadOutlined spin />} color="processing">PROCESANDO</Tag>;
    case 'PENDIENTE':
      return <Tag icon={<ClockCircleOutlined />} color="warning">EN COLA</Tag>;
    case 'FALLIDO':
      return <Tag icon={<CloseCircleOutlined />} color="error">FALLIDO</Tag>;
    default:
      return <Tag color="default">{estado}</Tag>;
  }
};

export const IconoFormatoReporte: React.FC<{ formato: string }> = ({ formato }) => (
  formato === 'PDF'
    ? <FilePdfOutlined style={{ fontSize: '24px', color: '#ff4d4f' }} />
    : <FileExcelOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
);
