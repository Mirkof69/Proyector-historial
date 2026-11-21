import React from 'react';
import { Card, Statistic } from 'antd';
import {
  ClockCircleOutlined, BellOutlined, ExclamationCircleOutlined, SafetyOutlined,
} from '@ant-design/icons';

interface AlertasMedicasStatsProps {
  totalAlertas: number;
  alertasPendientes: number;
  alertasCriticas: number;
  alertasHoy: number;
}

const AlertasMedicasStats: React.FC<AlertasMedicasStatsProps> = ({
  totalAlertas, alertasPendientes, alertasCriticas, alertasHoy,
}) => (
  <div className="alertas-page__cifras">
    <Card size="small">
      <Statistic title={<><BellOutlined />Total Alertas</>} value={totalAlertas} />
    </Card>
    <Card size="small" className={alertasPendientes > 0 ? 'alertas-page__cifra--aviso' : undefined}>
      <Statistic title={<><ClockCircleOutlined />Pendientes</>} value={alertasPendientes} />
    </Card>
    <Card size="small" className={alertasCriticas > 0 ? 'alertas-page__cifra--peligro' : undefined}>
      <Statistic title={<><ExclamationCircleOutlined />Críticas</>} value={alertasCriticas} />
    </Card>
    <Card size="small">
      <Statistic title={<><SafetyOutlined />Hoy</>} value={alertasHoy} />
    </Card>
  </div>
);

export default AlertasMedicasStats;
