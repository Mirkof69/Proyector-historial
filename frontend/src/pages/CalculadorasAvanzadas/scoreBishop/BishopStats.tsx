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
  <Row gutter={[16, 16]} className="calc-fila-stats">
    <Col xs={24} sm={12} md={6}>
      <Card className="calc-stat-card">
        <Statistic title="Total Evaluaciones" value={total} prefix={<HistoryOutlined />} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="calc-stat-card">
        <Statistic title="Promedio Score" value={promedio} suffix="/ 13" />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="calc-stat-card">
        <Statistic title="Tasa Favorable" value={tasaFavorable} suffix="%" prefix={<TrophyOutlined />} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="calc-stat-card">
        <Statistic
          title="Último Score"
          value={ultimoScore}
          suffix="puntos"
          valueStyle={{ color: ultimoScore >= 8 ? 'var(--color-exito)' : 'var(--color-aviso)' }}
        />
      </Card>
    </Col>
  </Row>
);

export default BishopStats;
