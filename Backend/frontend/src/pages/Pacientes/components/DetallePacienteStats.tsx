import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import {
  DashboardOutlined, MedicineBoxOutlined, HeartOutlined, FileTextOutlined, SafetyOutlined,
} from '@ant-design/icons';

interface DetallePacienteStatsProps {
  stats: {
    totalEmbarazos: number;
    embarazosActivos: number;
    totalTriajes: number;
    totalNotas: number;
    totalVacunas: number;
    vacunasCompletas: number;
  };
}

const DetallePacienteStats: React.FC<DetallePacienteStatsProps> = ({ stats }) => (
  <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card>
        <Statistic
          title="Embarazos"
          value={stats.totalEmbarazos}
          prefix={<MedicineBoxOutlined />}
          valueStyle={{ color: '#1890ff' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card>
        <Statistic
          title="Activos"
          value={stats.embarazosActivos}
          prefix={<HeartOutlined />}
          valueStyle={{ color: '#52c41a' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card>
        <Statistic
          title="Triajes"
          value={stats.totalTriajes}
          prefix={<DashboardOutlined />}
          valueStyle={{ color: '#faad14' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card>
        <Statistic
          title="Notas Médicas"
          value={stats.totalNotas}
          prefix={<FileTextOutlined />}
          valueStyle={{ color: '#722ed1' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card>
        <Statistic
          title="Vacunas"
          value={stats.totalVacunas}
          prefix={<SafetyOutlined />}
          valueStyle={{ color: '#13c2c2' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card>
        <Statistic
          title="Completas"
          value={stats.vacunasCompletas}
          prefix={<SafetyOutlined />}
          valueStyle={{ color: '#52c41a' }}
        />
      </Card>
    </Col>
  </Row>
);

export default DetallePacienteStats;
