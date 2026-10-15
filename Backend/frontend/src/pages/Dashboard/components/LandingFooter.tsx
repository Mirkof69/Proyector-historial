import React from 'react';
import { Layout, Typography, Space, Divider } from 'antd';
import { HeartOutlined } from '@ant-design/icons';

const { Footer } = Layout;
const { Text } = Typography;

const LandingFooter: React.FC = () => (
  <Footer className="landing-footer">
    <div className="footer-content">
      <Space direction="vertical" size="small" className="landing-ancho-completo">
        <Text strong className="landing-footer__marca">
          © 2025 <span className="landing-footer__marca-nombre">Fetal Medical Foundation</span>
        </Text>
        <Text>Sistema de Historias Clínicas Gineco-Obstétricas</Text>
        <Text type="secondary">
          Tecnología profesional para el cuidado prenatal | La Paz, Bolivia
        </Text>
        <Divider />
        <Text type="secondary" className="landing-footer__nota">
          Desarrollado con <HeartOutlined aria-label="amor" /> para mejorar la atención materno-fetal
        </Text>
      </Space>
    </div>
  </Footer>
);

export default LandingFooter;
