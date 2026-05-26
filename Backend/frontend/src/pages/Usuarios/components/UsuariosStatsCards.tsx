import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import { UserOutlined, CheckCircleOutlined, MedicineBoxOutlined } from '@ant-design/icons';

interface UsuariosStats {
  total: number;
  activos: number;
  medicos: number;
  enfermeros: number;
  administradores: number;
}

interface UsuariosStatsCardsProps {
  estadisticas: UsuariosStats;
}

const UsuariosStatsCards: React.FC<UsuariosStatsCardsProps> = ({ estadisticas }) => (
  <Row gutter={16} style={{ marginBottom: 24 }}>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic title="Total Usuarios" value={estadisticas.total} prefix={<UserOutlined />} valueStyle={{ color: '#1890ff' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic title="Activos" value={estadisticas.activos} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#52c41a' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic title="Médicos" value={estadisticas.medicos} prefix={<MedicineBoxOutlined />} valueStyle={{ color: '#3498db' }} />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic title="Enfermeros" value={estadisticas.enfermeros} prefix={<MedicineBoxOutlined />} valueStyle={{ color: '#2ecc71' }} />
      </Card>
    </Col>
  </Row>
);

export default UsuariosStatsCards;
