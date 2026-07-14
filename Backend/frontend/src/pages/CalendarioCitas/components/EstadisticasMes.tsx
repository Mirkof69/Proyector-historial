import React from 'react';
import { Row, Col, Card, Typography } from 'antd';
import {
  CalendarOutlined, ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, WarningOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

interface EstadisticasMesProps {
  total: number;
  pendientes: number;
  confirmadas: number;
  completadas: number;
  canceladas: number;
  atrasadas: number;
}

const StatCard: React.FC<{ icon: React.ReactNode; value: number; label: string; color?: string }> = ({ icon, value, label, color }) => (
  <Col xs={12} sm={8} md={4}>
    <Card size="small" style={{ textAlign: 'center' }}>
      {icon}
      <div style={{ marginTop: 8 }}>
        <Text strong style={{ fontSize: 18, color }}>{value}</Text>
        <br />
        <Text type="secondary" style={{ fontSize: 12 }}>{label}</Text>
      </div>
    </Card>
  </Col>
);

const EstadisticasMes: React.FC<EstadisticasMesProps> = ({ total, pendientes, confirmadas, completadas, canceladas, atrasadas }) => (
  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
    <StatCard icon={<CalendarOutlined style={{ fontSize: 24, color: '#1890ff' }} />} value={total} label="Total" />
    <StatCard icon={<ClockCircleOutlined style={{ fontSize: 24, color: '#faad14' }} />} value={pendientes} label="Pendientes" color="#faad14" />
    <StatCard icon={<CheckCircleOutlined style={{ fontSize: 24, color: '#1890ff' }} />} value={confirmadas} label="Confirmadas" color="#1890ff" />
    <StatCard icon={<CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />} value={completadas} label="Completadas" color="#52c41a" />
    <StatCard icon={<CloseCircleOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />} value={canceladas} label="Canceladas" color="#ff4d4f" />
    <StatCard icon={<WarningOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />} value={atrasadas} label="Atrasadas" color="#ff4d4f" />
  </Row>
);

export default EstadisticasMes;
