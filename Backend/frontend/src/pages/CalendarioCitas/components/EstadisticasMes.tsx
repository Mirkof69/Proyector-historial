import React from 'react';
import { Card, Statistic } from 'antd';
import {
  CalendarOutlined, ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined,
} from '@ant-design/icons';

interface EstadisticasMesProps {
  total: number;
  pendientes: number;
  confirmadas: number;
  completadas: number;
  canceladas: number;
  atrasadas: number;
}

/** Tarjeta de cifra; `peligro` solo cuando la cifra es un estado a atender. */
const StatCard: React.FC<{ icon: React.ReactNode; value: number; label: string; peligro?: boolean }> = ({ icon, value, label, peligro }) => (
  <Card size="small" className={peligro && value > 0 ? 'calendario-page__cifra--peligro' : undefined}>
    <Statistic title={<>{icon}{label}</>} value={value} />
  </Card>
);

const EstadisticasMes: React.FC<EstadisticasMesProps> = ({ total, pendientes, confirmadas, completadas, canceladas, atrasadas }) => (
  <div className="calendario-page__cifras">
    <StatCard icon={<CalendarOutlined />} value={total} label="Total" />
    <StatCard icon={<ClockCircleOutlined />} value={pendientes} label="Pendientes" />
    <StatCard icon={<CheckCircleOutlined />} value={confirmadas} label="Confirmadas" />
    <StatCard icon={<CheckCircleOutlined />} value={completadas} label="Completadas" />
    <StatCard icon={<CloseCircleOutlined />} value={canceladas} label="Canceladas" />
    <StatCard icon={<WarningOutlined />} value={atrasadas} label="Atrasadas" peligro />
  </div>
);

export default EstadisticasMes;
