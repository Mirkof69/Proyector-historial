import React from 'react';
import { Tag } from 'antd';
import { CheckCircleOutlined, ReloadOutlined, ClockCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';

interface EstadoTagProps {
  estado: string;
}

const EstadoTag: React.FC<EstadoTagProps> = ({ estado }) => {
  switch (estado) {
    case 'TERMINADO': return <Tag icon={<CheckCircleOutlined />} color="success">TERMINADO</Tag>;
    case 'PROCESANDO': return <Tag icon={<ReloadOutlined spin />} color="processing">PROCESANDO</Tag>;
    case 'PENDIENTE': return <Tag icon={<ClockCircleOutlined />} color="warning">EN COLA</Tag>;
    case 'FALLIDO': return <Tag icon={<CloseCircleOutlined />} color="error">FALLIDO</Tag>;
    default: return <Tag color="default">{estado}</Tag>;
  }
};

export default EstadoTag;
