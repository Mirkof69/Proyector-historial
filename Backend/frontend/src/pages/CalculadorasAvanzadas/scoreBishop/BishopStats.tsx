import React from 'react';
import { Row, Col, Card, Statistic } from 'antd';
import { HistoryOutlined, TrophyOutlined } from '@ant-design/icons';

interface BishopStatsProps {
  total: number;
  promedio: number | string;
  tasaFavorable: number | string;
  ultimoScore: number;
}

const BishopStats: React.FC<BishopStatsProps> = ({ total, promedio, tasaFavorable, ultimoScore }) => (
  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic title="Total Evaluaciones" value={total} prefix={<HistoryOutlined />} valueStyle={{ color: '#1890ff' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic title="Promedio Score" value={promedio} suffix="/ 13" valueStyle={{ color: '#722ed1' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic title="Tasa Favorable" value={tasaFavorable} suffix="%" prefix={<TrophyOutlined />} valueStyle={{ color: '#52c41a' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Último Score"
          value={ultimoScore}
          suffix="puntos"
          valueStyle={{ color: ultimoScore >= 8 ? '#52c41a' : '#fa8c16' }}
        />
      </Card>
    </Col>
  </Row>
);

export default BishopStats;
