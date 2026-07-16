import React from 'react';
import { Card, Badge, Row, Col, Tag, Statistic } from 'antd';
import {
  BellOutlined,
  MailOutlined,
  PhoneOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

interface NotificacionesStatsProps {
  stats: { total: number; nuevas: number; alertas: number; info: number };
}

const NotificacionesStats: React.FC<NotificacionesStatsProps> = ({ stats }) => (
  <Row gutter={[16, 16]} className="notification-stats-row">
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Total Notificaciones"
          value={stats.total}
          prefix={<BellOutlined />}
          valueStyle={{ color: '#1890ff' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Badge count={stats.nuevas} overflowCount={99}>
        <Card style={{ width: '100%' }}>
          <Statistic
            title="No Leídas"
            value={stats.nuevas}
            prefix={<MailOutlined />}
            valueStyle={{ color: '#faad14' }}
          />
        </Card>
      </Badge>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Alertas Urgentes"
          value={stats.alertas}
          prefix={<PhoneOutlined />}
          valueStyle={{ color: '#ff4d4f' }}
          suffix={<Tag color="red">Urgente</Tag>}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Informativas"
          value={stats.info}
          prefix={<InfoCircleOutlined />}
          valueStyle={{ color: '#52c41a' }}
          suffix={<Tag color="green">Info</Tag>}
        />
      </Card>
    </Col>
  </Row>
);

export default NotificacionesStats;
