import React from 'react';
import { Card, Statistic } from 'antd';
import {
  CalendarOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  UserOutlined,
  WarningOutlined,
} from '@ant-design/icons';

interface CitasStatsProps {
  estadisticas: {
    total: number;
    agendadas: number;
    confirmadas: number;
    en_espera: number;
    hoy: number;
    atrasadas: number;
  };
}

const CitasStats: React.FC<CitasStatsProps> = ({ estadisticas }) => (
  <div className="citas-page__cifras">
    <Card size="small">
      <Statistic title={<><CalendarOutlined />Total Citas</>} value={estadisticas.total} />
    </Card>
    <Card size="small">
      <Statistic title={<><ClockCircleOutlined />Por Confirmar</>} value={estadisticas.agendadas} />
    </Card>
    <Card size="small">
      <Statistic title={<><CheckCircleOutlined />Confirmadas</>} value={estadisticas.confirmadas} />
    </Card>
    <Card size="small">
      <Statistic title={<><UserOutlined />En Espera</>} value={estadisticas.en_espera} />
    </Card>
    <Card size="small">
      <Statistic title={<><CalendarOutlined />Hoy</>} value={estadisticas.hoy} />
    </Card>
    <Card size="small" className={estadisticas.atrasadas > 0 ? 'citas-page__cifra--peligro' : undefined}>
      <Statistic title={<><WarningOutlined />Atrasadas</>} value={estadisticas.atrasadas} />
    </Card>
  </div>
);

export default CitasStats;
