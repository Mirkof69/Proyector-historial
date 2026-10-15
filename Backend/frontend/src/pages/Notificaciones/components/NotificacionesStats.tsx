import React from 'react';
import { Card, Statistic } from 'antd';
import {
  BellOutlined,
  MailOutlined,
  PhoneOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

interface NotificacionesStatsProps {
  stats: { total: number; nuevas: number; alertas: number; info: number };
}

const NotificacionesStats: React.FC<NotificacionesStatsProps> = ({ stats }) => (
  <div className="notifications-page__cifras">
    <Card size="small">
      <Statistic title={<><BellOutlined />Total Notificaciones</>} value={stats.total} />
    </Card>
    <Card size="small" className={stats.nuevas > 0 ? 'notifications-page__cifra--aviso' : undefined}>
      <Statistic title={<><MailOutlined />No Leídas</>} value={stats.nuevas} />
    </Card>
    <Card size="small" className={stats.alertas > 0 ? 'notifications-page__cifra--peligro' : undefined}>
      <Statistic title={<><PhoneOutlined />Alertas Urgentes</>} value={stats.alertas} />
    </Card>
    <Card size="small">
      <Statistic title={<><InfoCircleOutlined />Informativas</>} value={stats.info} />
    </Card>
  </div>
);

export default NotificacionesStats;
