import React from 'react';
import { Card, Button, Typography, Space } from 'antd';
import { HeartOutlined, LoginOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

interface FinalCTAProps {
  onLogin: () => void;
}

const FinalCTA: React.FC<FinalCTAProps> = ({ onLogin }) => (
  <div className="final-cta-section">
    <div className="section-container">
      <Card className="final-cta-card">
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <HeartOutlined style={{ fontSize: 64, color: '#ff4d4f' }} />
            <Title level={2} style={{ marginTop: 24 }}>
              Comienza a Transformar tu Atención Prenatal
            </Title>
            <Paragraph style={{ fontSize: 18, maxWidth: 700, margin: '0 auto' }}>
              Únete a los profesionales de la salud que confían en nuestro sistema
              para brindar la mejor atención materno-fetal
            </Paragraph>
          </div>
          <div style={{ textAlign: 'center' }}>
            <Button
              type="primary"
              size="large"
              icon={<LoginOutlined />}
              onClick={onLogin}
              style={{ height: 50, fontSize: 16, padding: '0 50px' }}
            >
              Acceder al Sistema
            </Button>
          </div>
          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">
              ¿Necesitas más información? Contacta con el administrador del
              sistema
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  </div>
);

export default FinalCTA;
