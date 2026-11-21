import React from 'react';
import { Row, Col, Card, Statistic } from 'antd';

interface StatsCardsProps {
  stats: {
    total: number;
    conGestas: number;
    conPartos: number;
    conAbortos: number;
  };
}

const StatsCards: React.FC<StatsCardsProps> = ({ stats }) => (
  <Row gutter={[16, 16]}>
    <Col xs={12} md={6}>
      <Card className="stat-card"><Statistic title="Total Registros" value={stats.total} /></Card>
    </Col>
    <Col xs={12} md={6}>
      <Card className="stat-card"><Statistic title="Con Gestas" value={stats.conGestas} /></Card>
    </Col>
    <Col xs={12} md={6}>
      <Card className="stat-card"><Statistic title="Con Partos" value={stats.conPartos} /></Card>
    </Col>
    <Col xs={12} md={6}>
      <Card className="stat-card"><Statistic title="Con Abortos" value={stats.conAbortos} /></Card>
    </Col>
  </Row>
);

export default StatsCards;
