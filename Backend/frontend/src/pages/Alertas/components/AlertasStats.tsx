import React from 'react';
import { Card, Statistic } from 'antd';
import { BellOutlined, FireOutlined, AlertOutlined, SyncOutlined } from '@ant-design/icons';

interface AlertasStatsProps {
  stats: { total: number; criticas: number; activas: number; enProceso: number; resueltas: number };
}

const AlertasStats: React.FC<AlertasStatsProps> = ({ stats }) => (
  <div className="alertas-page__cifras">
    <Card size="small">
      <Statistic title={<><BellOutlined />Total Alertas</>} value={stats.total} />
    </Card>
    <Card size="small" className={stats.criticas > 0 ? 'alertas-page__cifra--peligro' : undefined}>
      <Statistic title={<><FireOutlined />Alertas Críticas</>} value={stats.criticas} />
    </Card>
    <Card size="small" className={stats.activas > 0 ? 'alertas-page__cifra--aviso' : undefined}>
      <Statistic title={<><AlertOutlined />Activas</>} value={stats.activas} />
    </Card>
    <Card size="small">
      <Statistic title={<><SyncOutlined />En Proceso</>} value={stats.enProceso} />
    </Card>
  </div>
);

export default AlertasStats;
