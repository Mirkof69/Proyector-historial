import React from 'react';
import { Card, Statistic } from 'antd';
import { UserOutlined, HeartOutlined, WarningOutlined, CalendarOutlined } from '@ant-design/icons';

interface DashboardStats {
  total_pacientes: number;
  pacientes_nuevos_mes: number;
  embarazos_activos: number;
  embarazos_riesgo_alto: number;
  citas_hoy_count: number;
}

interface DashboardStatsCardsProps {
  stats: DashboardStats;
}

const DashboardStatsCards: React.FC<DashboardStatsCardsProps> = ({ stats }) => (
  <div className="dashboard-stats-grid">
    <Card className="stat-card blue-gradient">
      <Statistic
        title={<span style={{ color: '#fff' }}>Total Pacientes</span>}
        value={stats.total_pacientes}
        valueStyle={{ color: '#fff' }}
        prefix={<UserOutlined />}
        suffix={<span style={{ fontSize: 12, opacity: 0.8 }}>+{stats.pacientes_nuevos_mes} este mes</span>}
      />
      <div className="stat-icon-bg"><UserOutlined /></div>
    </Card>

    <Card className="stat-card purple-gradient">
      <Statistic
        title={<span style={{ color: '#fff' }}>Embarazos Activos</span>}
        value={stats.embarazos_activos}
        valueStyle={{ color: '#fff' }}
        prefix={<HeartOutlined />}
      />
      <div className="stat-icon-bg"><HeartOutlined /></div>
    </Card>

    <Card className="stat-card orange-gradient">
      <Statistic
        title={<span style={{ color: '#fff' }}>Riesgo Alto</span>}
        value={stats.embarazos_riesgo_alto}
        valueStyle={{ color: '#fff' }}
        prefix={<WarningOutlined />}
      />
      <div className="stat-icon-bg"><WarningOutlined /></div>
    </Card>

    <Card className="stat-card green-gradient">
      <Statistic
        title={<span style={{ color: '#fff' }}>Citas para Hoy</span>}
        value={stats.citas_hoy_count}
        valueStyle={{ color: '#fff' }}
        prefix={<CalendarOutlined />}
      />
      <div className="stat-icon-bg"><CalendarOutlined /></div>
    </Card>
  </div>
);

export default DashboardStatsCards;
