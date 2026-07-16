import React from 'react';
import { Row, Col, Card, Statistic } from 'antd';
import { ExperimentOutlined, ExclamationCircleOutlined, WarningOutlined } from '@ant-design/icons';

interface LaboratorioStatsProps {
  total: number;
  solicitados: number;
  en_proceso: number;
  completados: number;
  con_anormales: number;
  con_criticos: number;
}

const LaboratorioStats: React.FC<LaboratorioStatsProps> = ({
  total, solicitados, en_proceso, completados, con_anormales, con_criticos,
}) => (
  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card>
        <Statistic title="Total Exámenes" value={total} prefix={<ExperimentOutlined />} valueStyle={{ color: '#722ed1' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card>
        <Statistic title="Solicitados" value={solicitados} valueStyle={{ color: '#fa8c16' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card>
        <Statistic title="En Proceso" value={en_proceso} valueStyle={{ color: '#1890ff' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card>
        <Statistic title="Completados" value={completados} valueStyle={{ color: '#52c41a' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card>
        <Statistic title="Con Anormales" value={con_anormales} valueStyle={{ color: '#faad14' }} prefix={<ExclamationCircleOutlined />} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card>
        <Statistic title="Con Críticos" value={con_criticos} valueStyle={{ color: '#ff4d4f' }} prefix={<WarningOutlined />} />
      </Card>
    </Col>
  </Row>
);

export default LaboratorioStats;
