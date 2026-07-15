import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
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
  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
    <Col xs={24} sm={12} md={6}>
      <Card className="stat-card">
        <Statistic
          title="Total Alertas"
          value={totalAlertas}
          prefix={<BellOutlined />}
          valueStyle={{ color: '#1890ff' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="stat-card">
        <Statistic
          title="Pendientes"
          value={alertasPendientes}
          prefix={<ClockCircleOutlined />}
          valueStyle={{ color: '#fa8c16' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="stat-card">
        <Statistic
          title="Críticas"
          value={alertasCriticas}
          prefix={<ExclamationCircleOutlined />}
          valueStyle={{ color: '#f5222d' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="stat-card">
        <Statistic
          title="Hoy"
          value={alertasHoy}
          prefix={<SafetyOutlined />}
          valueStyle={{ color: '#52c41a' }}
        />
      </Card>
    </Col>
  </Row>
);

export default AlertasMedicasStats;
