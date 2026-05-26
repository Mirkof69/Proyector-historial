import React from 'react';
import { Row, Col, Card, Statistic } from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  HistoryOutlined,
  MedicineBoxOutlined,
  RiseOutlined
} from '@ant-design/icons';

interface EvolucionesStatsProps {
  stats: {
    total: number;
    hoy: number;
    semana: number;
    consultas: number;
    urgencias: number;
  };
}

const EvolucionesStats: React.FC<EvolucionesStatsProps> = ({ stats }) => (
  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
    <Col xs={12} md={6} lg={4}>
      <Card hoverable className="stat-card-premium blue">
        <Statistic title="Total Notas" value={stats.total} prefix={<FileTextOutlined />} />
      </Card>
    </Col>
    <Col xs={12} md={6} lg={4}>
      <Card hoverable className="stat-card-premium green">
        <Statistic title="Registros Hoy" value={stats.hoy} prefix={<CheckCircleOutlined />} />
      </Card>
    </Col>
    <Col xs={12} md={6} lg={4}>
      <Card hoverable className="stat-card-premium orange">
        <Statistic title="Esta Semana" value={stats.semana} prefix={<HistoryOutlined />} />
      </Card>
    </Col>
    <Col xs={12} md={6} lg={4}>
      <Card hoverable className="stat-card-premium purple">
        <Statistic title="Consultas" value={stats.consultas} prefix={<MedicineBoxOutlined />} />
      </Card>
    </Col>
    <Col xs={12} md={6} lg={4}>
      <Card hoverable className="stat-card-premium red">
        <Statistic title="Urgencias" value={stats.urgencias} prefix={<RiseOutlined />} />
      </Card>
    </Col>
    <Col xs={12} md={6} lg={4}>
      <Card hoverable className="stat-card-premium cyan">
        <Statistic
          title="Efectividad"
          value={((stats.total / (stats.total || 1)) * 100).toFixed(0)}
          suffix="%"
          prefix={<RiseOutlined />}
        />
      </Card>
    </Col>
  </Row>
);

export default EvolucionesStats;
