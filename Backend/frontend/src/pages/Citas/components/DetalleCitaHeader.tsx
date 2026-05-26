import React from 'react';
import { Card, Space, Button } from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import { EstadoCita } from '../../../services/citasService';
import { getEstadoTag } from '../utils/citasUtils';

interface DetalleCitaHeaderProps {
  citaId: number | undefined;
  estado: EstadoCita;
  onVolver: () => void;
  onEditar: () => void;
  editable: boolean;
}

const DetalleCitaHeader: React.FC<DetalleCitaHeaderProps> = ({
  citaId,
  estado,
  onVolver,
  onEditar,
  editable,
}) => (
  <Card
    title={
      <Space>
        <CalendarOutlined style={{ fontSize: 24, color: '#1890ff' }} />
        <span style={{ fontSize: 20, fontWeight: 600 }}>Detalle de Cita #{citaId}</span>
        {getEstadoTag(estado)}
      </Space>
    }
    extra={
      <Space>
        <Button icon={<ArrowLeftOutlined />} onClick={onVolver}>
          Volver
        </Button>
        {editable && (
          <Button type="primary" icon={<EditOutlined />} onClick={onEditar}>
            Editar
          </Button>
        )}
      </Space>
    }
  />
);

export default DetalleCitaHeader;
