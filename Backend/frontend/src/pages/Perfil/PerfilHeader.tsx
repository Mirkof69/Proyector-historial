import React from 'react';
import { Card, Row, Col, Avatar, Typography, Tag } from 'antd';
import { UserOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { Usuario } from './perfilTypes';

const { Title, Text } = Typography;

const PerfilHeader: React.FC<{ user: Usuario }> = ({ user }) => (
  <Card
    variant="borderless"
    className="shadow-md"
    style={{
      marginBottom: 24,
      background: 'var(--bg-card)',
    }}
  >
    <Row align="middle" gutter={24}>
      <Col xs={24} sm={6} style={{ textAlign: 'center' }}>
        <Avatar
          size={100}
          src={user.foto_url || undefined}
          icon={<UserOutlined />}
          style={{
            border: '4px solid var(--border-color)',
            boxShadow: '0 4px 10px rgba(0,0,0,0.3)',
          }}
        />
      </Col>
      <Col xs={24} sm={18} md={20}>
        <Title level={2} style={{ marginBottom: 0 }}>
          {user.nombre} {user.apellido_paterno}
        </Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          {user.email}
        </Text>
        <div style={{ marginTop: 12 }}>
          <Tag color="blue" icon={<SafetyCertificateOutlined />}>
            {user.rol?.toUpperCase() || 'USUARIO'}
          </Tag>
          {user.especialidad && (
            <Tag color="cyan">{user.especialidad}</Tag>
          )}
          <Tag color={user.activo ? 'green' : 'red'}>
            {user.activo ? 'CUENTA ACTIVA' : 'SUSPENDIDO'}
          </Tag>
        </div>
      </Col>
    </Row>
  </Card>
);

export default PerfilHeader;
