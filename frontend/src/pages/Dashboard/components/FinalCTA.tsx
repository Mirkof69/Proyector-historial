import React from 'react';
import { Card, Button, Typography } from 'antd';
import { HeartOutlined, LoginOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

interface FinalCTAProps {
  onLogin: () => void;
}

const FinalCTA: React.FC<FinalCTAProps> = ({ onLogin }) => (
  <div className="final-cta-section">
    <div className="section-container">
      <Card className="final-cta-card">
        <div className="final-cta-card__contenido">
          <span className="final-cta-card__icono"><HeartOutlined aria-hidden /></span>
          <Title level={2}>
            Comienza a Transformar tu Atención Prenatal
          </Title>
          <Paragraph>
            Únete a los profesionales de la salud que confían en nuestro sistema
            para brindar la mejor atención materno-fetal
          </Paragraph>
          <Button
            size="large"
            icon={<LoginOutlined />}
            onClick={onLogin}
          >
            Acceder al Sistema
          </Button>
          <Text type="secondary">
            ¿Necesitas más información? Contacta con el administrador del
            sistema
          </Text>
        </div>
      </Card>
    </div>
  </div>
);

export default FinalCTA;
