import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import { BellOutlined, FireOutlined, AlertOutlined, SyncOutlined } from '@ant-design/icons';

interface AlertStats {
  total: number;
  criticas: number;
  activas: number;
  enProceso: number;
  resueltas: number;
}

interface AlertStatsCardsProps {
  stats: AlertStats;
}

const AlertStatsCards: React.FC<AlertStatsCardsProps> = ({ stats }) => (
  <Row gutter={16} style={{ marginBottom: 24 }}>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic title="Total Alertas" value={stats.total} prefix={<BellOutlined />} valueStyle={{ color: '#1890ff' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic title="Alertas Críticas" value={stats.criticas} prefix={<FireOutlined />} valueStyle={{ color: '#f5222d' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic title="Activas" value={stats.activas} prefix={<AlertOutlined />} valueStyle={{ color: '#fa8c16' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic title="En Proceso" value={stats.enProceso} prefix={<SyncOutlined spin />} valueStyle={{ color: '#1890ff' }} />
      </Card>
    </Col>
  </Row>
);

export default AlertStatsCards;
