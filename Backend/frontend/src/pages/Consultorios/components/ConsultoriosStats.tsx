import React from 'react';
import { Card, Row, Col } from 'antd';
import AnimatedStatistic from '../../../components/common/AnimatedStatistic';
import {
  HomeOutlined, ToolOutlined, CheckCircleOutlined, CloseCircleOutlined,
} from '@ant-design/icons';

interface ConsultoriosStatsProps {
  stats: {
    total: number;
    disponibles: number;
    enMantenimiento: number;
    inactivos: number;
  };
}

const ConsultoriosStats: React.FC<ConsultoriosStatsProps> = ({ stats }) => (
  <Row gutter={16} style={{ marginBottom: 16 }}>
    <Col xs={24} sm={12} md={6}>
      <Card className="stat-card">
        <AnimatedStatistic
          title="Total Consultorios"
          value={stats.total}
          prefix={<HomeOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="stat-card">
        <AnimatedStatistic
          title="Disponibles"
          value={stats.disponibles}
          prefix={<CheckCircleOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="stat-card">
        <AnimatedStatistic
          title="En Mantenimiento"
          value={stats.enMantenimiento}
          prefix={<ToolOutlined />}
          className={stats.enMantenimiento > 0 ? 'cifra--aviso' : undefined}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="stat-card">
        <AnimatedStatistic
          title="Inactivos"
          value={stats.inactivos}
          prefix={<CloseCircleOutlined />}
        />
      </Card>
    </Col>
  </Row>
);

export default ConsultoriosStats;
