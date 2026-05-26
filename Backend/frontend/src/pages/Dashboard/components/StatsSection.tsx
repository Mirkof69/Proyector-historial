import React from 'react';
import { Card, Row, Col, Typography } from 'antd';

const { Title, Text } = Typography;

interface StatItem {
  value: string;
  label: string;
}

const stats: StatItem[] = [
  { value: '100%', label: 'Validación FMF' },
  { value: '15+', label: 'Calculadoras Clínicas' },
  { value: '24/7', label: 'Acceso en Tiempo Real' },
  { value: '100+', label: 'Funcionalidades API' },
];

const StatsSection: React.FC = () => (
  <div className="stats-section">
    <div className="section-container">
      <Row gutter={[24, 24]}>
        {stats.map((stat) => (
          <Col xs={24} sm={12} md={6} key={stat.label}>
            <Card className="stat-card">
              <Title level={2}>{stat.value}</Title>
              <Text>{stat.label}</Text>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  </div>
);

export default StatsSection;
