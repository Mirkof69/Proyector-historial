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

const Etiqueta: React.FC<{ icono: React.ReactNode; texto: string }> = ({ icono, texto }) => (
  <span className="stat-card__etiqueta">{icono}{texto}</span>
);

const DashboardStatsCards: React.FC<DashboardStatsCardsProps> = ({ stats }) => (
  <div className="dashboard-stats-grid">
    <Card className="stat-card">
      <Statistic
        title={<Etiqueta icono={<UserOutlined />} texto="Total Pacientes" />}
        value={stats.total_pacientes}
        suffix={`+${stats.pacientes_nuevos_mes} este mes`}
      />
    </Card>

    <Card className="stat-card">
      <Statistic
        title={<Etiqueta icono={<HeartOutlined />} texto="Embarazos Activos" />}
        value={stats.embarazos_activos}
      />
    </Card>

    <Card className={`stat-card${stats.embarazos_riesgo_alto > 0 ? ' stat-card--peligro' : ''}`}>
      <Statistic
        title={<Etiqueta icono={<WarningOutlined />} texto="Riesgo Alto" />}
        value={stats.embarazos_riesgo_alto}
      />
    </Card>

    <Card className="stat-card">
      <Statistic
        title={<Etiqueta icono={<CalendarOutlined />} texto="Citas para Hoy" />}
        value={stats.citas_hoy_count}
      />
    </Card>
  </div>
);

export default DashboardStatsCards;
