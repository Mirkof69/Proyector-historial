import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
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
      <Card>
        <Statistic
          title="Total Consultorios"
          value={stats.total}
          prefix={<HomeOutlined />}
          valueStyle={{ color: '#1890ff' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Disponibles"
          value={stats.disponibles}
          prefix={<CheckCircleOutlined />}
          valueStyle={{ color: '#52c41a' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="En Mantenimiento"
          value={stats.enMantenimiento}
          prefix={<ToolOutlined />}
          valueStyle={{ color: '#faad14' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Inactivos"
          value={stats.inactivos}
          prefix={<CloseCircleOutlined />}
          valueStyle={{ color: '#f5222d' }}
        />
      </Card>
    </Col>
  </Row>
);

export default ConsultoriosStats;
