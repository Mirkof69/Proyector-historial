import React from 'react';
import { Layout, Button, Typography, Space, Divider } from 'antd';
import { HeartOutlined, LoginOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { FRONTEND_ROUTES } from '../../../config/routes';

const { Header } = Layout;
const { Title } = Typography;

interface LandingHeaderProps {
  onLogin: () => void;
  onScrollToSection: (sectionId: string) => void;
}

const LandingHeader: React.FC<LandingHeaderProps> = ({ onLogin, onScrollToSection }) => (
  <Header className="landing-header">
    <div className="landing-header-content">
      <div className="logo-container">
        <HeartOutlined className="logo-icon" />
        <Title level={3} className="logo-text">
          Fetal Medical Foundation
        </Title>
      </div>
      <Space size="large" className="header-nav">
        <Button type="link" onClick={() => onScrollToSection('features')}>
          Características
        </Button>
        <Button type="link" onClick={() => onScrollToSection('calculadoras')}>
          Calculadoras
        </Button>
        <Button type="link" onClick={() => onScrollToSection('beneficios')}>
          Beneficios
        </Button>
        <Divider type="vertical" />
        <Button
          type="primary"
          size="large"
          icon={<LoginOutlined />}
          onClick={onLogin}
          className="btn-login"
        >
          Iniciar Sesión
        </Button>
      </Space>
    </div>
  </Header>
);

export default LandingHeader;
