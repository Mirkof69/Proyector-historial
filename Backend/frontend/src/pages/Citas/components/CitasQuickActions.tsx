import React from 'react';
import { Space, Button } from 'antd';
import {
  CalendarOutlined,
  ClockCircleOutlined,
  FileExcelOutlined,
  ReloadOutlined,
  PlusOutlined,
} from '@ant-design/icons';

interface CitasQuickActionsProps {
  loading: boolean;
  canAdd: boolean;
  onVerCalendario: () => void;
  onGestionarHorarios: () => void;
  onExportExcel: () => void;
  onActualizar: () => void;
  onNuevaCita: () => void;
}

const CitasQuickActions: React.FC<CitasQuickActionsProps> = ({
  loading,
  canAdd,
  onVerCalendario,
  onGestionarHorarios,
  onExportExcel,
  onActualizar,
  onNuevaCita,
}) => (
  <Space>
    <Button icon={<CalendarOutlined />} onClick={onVerCalendario}>
      Ver Calendario
    </Button>
    <Button icon={<ClockCircleOutlined />} onClick={onGestionarHorarios}>
      Gestionar Horarios
    </Button>
    <Button icon={<FileExcelOutlined />} onClick={onExportExcel}>
      Exportar Excel
    </Button>
    <Button icon={<ReloadOutlined />} onClick={onActualizar} loading={loading}>
      Actualizar
    </Button>
    {canAdd && (
      <Button type="primary" icon={<PlusOutlined />} onClick={onNuevaCita}>
        Nueva Cita
      </Button>
    )}
  </Space>
);

export default CitasQuickActions;
