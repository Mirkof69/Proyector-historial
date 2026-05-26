import React from 'react';
import { Row, Col, Statistic } from 'antd';

interface StatsCardsProps {
  stats: {
    total: number;
    conGestas: number;
    conPartos: number;
    conAbortos: number;
  };
}

const StatsCards: React.FC<StatsCardsProps> = ({ stats }) => (
  <Row gutter={16} style={{ marginBottom: '24px' }}>
    <Col span={6}>
      <Statistic title="Total Registros" value={stats.total} />
    </Col>
    <Col span={6}>
      <Statistic title="Con Gestas" value={stats.conGestas} />
    </Col>
    <Col span={6}>
      <Statistic title="Con Partos" value={stats.conPartos} />
    </Col>
    <Col span={6}>
      <Statistic title="Con Abortos" value={stats.conAbortos} />
    </Col>
  </Row>
);

export default StatsCards;
