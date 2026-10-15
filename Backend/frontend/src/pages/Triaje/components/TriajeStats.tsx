import React from 'react';
import { Row, Col, Card, Statistic } from 'antd';
import {
  DashboardOutlined, ClockCircleOutlined, CheckCircleOutlined,
  AlertOutlined, HeartOutlined,
} from '@ant-design/icons';

interface TriajeStatsProps {
  total: number;
  pendiente: number;
  completado: number;
  urgente: number;
  presionAlta: number;
}

const Etiqueta: React.FC<{ icono: React.ReactNode; texto: string }> = ({ icono, texto }) => (
  <span className="stat-card__etiqueta">{icono}{texto}</span>
);

// Tarjetas de cifras del contrato: superficie + borde; color semántico solo
// cuando la cifra es un estado (urgentes, presión alta).
const TriajeStats: React.FC<TriajeStatsProps> = ({ total, pendiente, completado, urgente, presionAlta }) => (
  <Row gutter={[16, 16]}>
    <Col xs={12} sm={8} md={4}>
      <Card className="stat-card">
        <Statistic title={<Etiqueta icono={<DashboardOutlined />} texto="Total" />} value={total} />
      </Card>
    </Col>
    <Col xs={12} sm={8} md={4}>
      <Card className="stat-card">
        <Statistic title={<Etiqueta icono={<ClockCircleOutlined />} texto="Pendientes" />} value={pendiente} />
      </Card>
    </Col>
    <Col xs={12} sm={8} md={4}>
      <Card className="stat-card">
        <Statistic title={<Etiqueta icono={<CheckCircleOutlined />} texto="Completados" />} value={completado} />
      </Card>
    </Col>
    <Col xs={12} sm={8} md={4}>
      <Card className={`stat-card${urgente > 0 ? ' cifra--peligro' : ''}`}>
        <Statistic title={<Etiqueta icono={<AlertOutlined />} texto="Urgentes" />} value={urgente} />
      </Card>
    </Col>
    <Col xs={12} sm={8} md={4}>
      <Card className={`stat-card${presionAlta > 0 ? ' cifra--aviso' : ''}`}>
        <Statistic title={<Etiqueta icono={<HeartOutlined />} texto="Presión Alta" />} value={presionAlta} />
      </Card>
    </Col>
  </Row>
);

export default TriajeStats;
