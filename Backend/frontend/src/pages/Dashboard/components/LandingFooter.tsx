import React from 'react';
import { Layout, Typography, Space, Divider } from 'antd';

const { Footer } = Layout;
const { Text } = Typography;

const LandingFooter: React.FC = () => (
  <Footer className="landing-footer">
    <div className="footer-content">
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        <Text strong style={{ fontSize: 16 }}>
          © 2025 <span style={{ color: '#ff4d4f' }}>Fetal Medical Foundation</span>
        </Text>
        <Text>Sistema de Historias Clínicas Gineco-Obstétricas</Text>
        <Text type="secondary">
          Tecnología profesional para el cuidado prenatal | La Paz, Bolivia
        </Text>
        <Divider style={{ margin: '16px 0' }} />
        <Text type="secondary" style={{ fontSize: 12 }}>
          Desarrollado con ❤️ para mejorar la atención materno-fetal
        </Text>
      </Space>
    </div>
  </Footer>
);

export default LandingFooter;
