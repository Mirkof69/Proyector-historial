import React from 'react';
import { Row, Col, Card, Statistic } from 'antd';
import {
  DashboardOutlined, ClockCircleOutlined, CheckCircleOutlined,
  AlertOutlined, HeartOutlined,
} from '@ant-design/icons';

interface TriajeStatsProps {
  total: number;
  pendiente: number;
  completado: number;
  urgente: number;
  presionAlta: number;
}

const TriajeStats: React.FC<TriajeStatsProps> = ({ total, pendiente, completado, urgente, presionAlta }) => (
  <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
    <Col xs={12} sm={8} md={4}>
      <Card className="blue-gradient stat-card">
        <Statistic title="Total" value={total} valueStyle={{ color: '#fff' }} />
        <DashboardOutlined className="stat-icon-bg" />
      </Card>
    </Col>
    <Col xs={12} sm={8} md={4}>
      <Card className="orange-gradient stat-card">
        <Statistic title="Pendientes" value={pendiente} valueStyle={{ color: '#fff' }} />
        <ClockCircleOutlined className="stat-icon-bg" />
      </Card>
    </Col>
    <Col xs={12} sm={8} md={4}>
      <Card className="green-gradient stat-card">
        <Statistic title="Completados" value={completado} valueStyle={{ color: '#fff' }} />
        <CheckCircleOutlined className="stat-icon-bg" />
      </Card>
    </Col>
    <Col xs={12} sm={8} md={4}>
      <Card className="purple-gradient stat-card" style={{ background: 'linear-gradient(120deg, #ff4d4f 0%, #ff7a45 100%)' }}>
        <Statistic title="Urgentes" value={urgente} valueStyle={{ color: '#fff' }} />
        <AlertOutlined className="stat-icon-bg" />
      </Card>
    </Col>
    <Col xs={12} sm={8} md={4}>
      <Card className="stat-card" style={{ background: 'linear-gradient(120deg, #13c2c2 0%, #1890ff 100%)' }}>
        <Statistic title="Presión Alta" value={presionAlta} valueStyle={{ color: '#fff' }} />
        <HeartOutlined className="stat-icon-bg" />
      </Card>
    </Col>
  </Row>
);

export default TriajeStats;
