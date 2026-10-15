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
  <Row gutter={[16, 16]}>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card className="stat-card">
        <Statistic
          title="Embarazos"
          value={stats.totalEmbarazos}
          prefix={<MedicineBoxOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card className="stat-card">
        <Statistic
          title="Activos"
          value={stats.embarazosActivos}
          prefix={<HeartOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card className="stat-card">
        <Statistic
          title="Triajes"
          value={stats.totalTriajes}
          prefix={<DashboardOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card className="stat-card">
        <Statistic
          title="Notas Médicas"
          value={stats.totalNotas}
          prefix={<FileTextOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card className="stat-card">
        <Statistic
          title="Vacunas"
          value={stats.totalVacunas}
          prefix={<SafetyOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={8} lg={4}>
      <Card className="stat-card">
        <Statistic
          title="Completas"
          value={stats.vacunasCompletas}
          prefix={<SafetyOutlined />}
        />
      </Card>
    </Col>
  </Row>
);

export default DetallePacienteStats;
