import React from 'react';
import { Alert } from 'antd';
import { WarningOutlined, CalendarOutlined } from '@ant-design/icons';

interface CitasAlertsProps {
  atrasadas: number;
  hoy: number;
}

const CitasAlerts: React.FC<CitasAlertsProps> = ({ atrasadas, hoy }) => (
  <>
    {atrasadas > 0 && (
      <Alert
        message="⚠️ Atención: Citas Atrasadas"
        description={`Hay ${atrasadas} cita${atrasadas > 1 ? 's' : ''} pendiente${atrasadas > 1 ? 's' : ''} o confirmada${atrasadas > 1 ? 's' : ''} que ya pasaron su fecha programada.`}
        type="error"
        showIcon
        icon={<WarningOutlined />}
        closable
        style={{ marginBottom: 16 }}
      />
    )}
    {hoy > 0 && (
      <Alert
        message={`📅 Citas de Hoy: ${hoy}`}
        description="Hay citas programadas para el día de hoy. Revise el calendario."
        type="info"
        showIcon
        icon={<CalendarOutlined />}
        closable
        style={{ marginBottom: 16 }}
      />
    )}
  </>
);

export default CitasAlerts;
