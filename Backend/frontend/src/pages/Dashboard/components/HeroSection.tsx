import React from 'react';
import { Badge, Button, Typography, Space } from 'antd';
import { LoginOutlined, RocketOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

interface HeroSectionProps {
  onLogin: () => void;
  onScrollToFeatures: () => void;
}

const HeroSection: React.FC<HeroSectionProps> = ({ onLogin, onScrollToFeatures }) => (
  <div className="hero-section">
    <div className="hero-content">
      <Badge.Ribbon text="Sistema Profesional" color="purple">
        <div className="hero-text-container">
          <Title level={1} className="hero-title">
            Sistema Integral de
            <br />
            <span className="highlight">Historias Clínicas</span>
            <br />
            Gineco-Obstétricas
          </Title>
          <Paragraph className="hero-description">
            Plataforma profesional para el seguimiento prenatal con tecnología
            avalada por la <strong>Fetal Medicine Foundation</strong>. Gestiona
            pacientes, embarazos y controles con{' '}
            <strong>alertas médicas automáticas</strong> y{' '}
            <strong>15+ calculadoras clínicas validadas</strong>.
          </Paragraph>
          <Space size="large" className="hero-buttons">
            <Button
              type="primary"
              size="large"
              icon={<LoginOutlined />}
              onClick={onLogin}
            >
              Acceder al Sistema
            </Button>
            <Button
              size="large"
              icon={<RocketOutlined />}
              onClick={onScrollToFeatures}
            >
              Conocer Más
            </Button>
          </Space>
          <div className="hero-badges">
            <span className="badge">100% Validación FMF</span>
            <span className="badge">Cumple Ley 3871</span>
            <span className="badge">Acceso 24/7</span>
            <span className="badge">Multi-usuario</span>
          </div>
        </div>
      </Badge.Ribbon>
    </div>
  </div>
);

export default HeroSection;
