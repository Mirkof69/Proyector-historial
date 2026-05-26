import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import {
  CalendarOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  UserOutlined,
  WarningOutlined,
} from '@ant-design/icons';

interface CitasStatsProps {
  estadisticas: {
    total: number;
    agendadas: number;
    confirmadas: number;
    en_espera: number;
    hoy: number;
    atrasadas: number;
  };
}

const CitasStats: React.FC<CitasStatsProps> = ({ estadisticas }) => (
  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card hoverable>
        <Statistic
          title="Total Citas"
          value={estadisticas.total}
          prefix={<CalendarOutlined />}
          valueStyle={{ color: '#1890ff' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card hoverable>
        <Statistic
          title="Por Confirmar"
          value={estadisticas.agendadas}
          valueStyle={{ color: '#faad14' }}
          prefix={<ClockCircleOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card hoverable>
        <Statistic
          title="Confirmadas"
          value={estadisticas.confirmadas}
          valueStyle={{ color: '#1890ff' }}
          prefix={<CheckCircleOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card hoverable>
        <Statistic
          title="En Espera"
          value={estadisticas.en_espera}
          valueStyle={{ color: '#faad14' }}
          prefix={<UserOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card hoverable>
        <Statistic
          title="Hoy"
          value={estadisticas.hoy}
          valueStyle={{ color: '#722ed1' }}
          prefix={<CalendarOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={4}>
      <Card hoverable>
        <Statistic
          title="Atrasadas"
          value={estadisticas.atrasadas}
          valueStyle={{ color: '#ff4d4f' }}
          prefix={<WarningOutlined />}
        />
      </Card>
    </Col>
  </Row>
);

export default CitasStats;
