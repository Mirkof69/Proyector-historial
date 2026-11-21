import React from 'react';
import { Space, Button, Typography } from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
} from '@ant-design/icons';
import { EstadoCita } from '../../../services/citasService';
import { getEstadoTag } from '../utils/citasUtils';

interface DetalleCitaHeaderProps {
  citaId: number | undefined;
  estado: EstadoCita;
  onVolver: () => void;
  onEditar: () => void;
  editable: boolean;
  children?: React.ReactNode;
}

const DetalleCitaHeader: React.FC<DetalleCitaHeaderProps> = ({
  citaId,
  estado,
  onVolver,
  onEditar,
  editable,
  children,
}) => (
  <>
    <header className="citas-page__cabecera">
      <div>
        <Typography.Title level={2}>
          Detalle de Cita <span className="tabular-nums">#{citaId}</span>
          {getEstadoTag(estado)}
        </Typography.Title>
        <Typography.Text type="secondary">Datos de la cita, acciones rápidas e historial de cambios.</Typography.Text>
      </div>
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
    </header>
    {children}
  </>
);

export default DetalleCitaHeader;
