import React from 'react';
import { Typography, Card, Row, Col } from 'antd';

const { Title, Paragraph, Text } = Typography;

interface Beneficio {
  icon: React.ReactNode;
  titulo: string;
  descripcion: string;
}

interface BeneficiosSectionProps {
  beneficios: Beneficio[];
}

const BeneficiosSection: React.FC<BeneficiosSectionProps> = ({ beneficios }) => (
  <div id="beneficios" className="beneficios-section">
    <div className="section-container">
      <div className="section-header">
        <Title level={2} className="section-title" style={{ color: '#fff' }}>
          Beneficios del Sistema
        </Title>
        <Paragraph
          className="section-description"
          style={{ color: 'rgba(255,255,255,0.9)' }}
        >
          Tecnología que transforma la atención prenatal
        </Paragraph>
      </div>
      <Row gutter={[24, 24]} style={{ marginTop: 50 }}>
        {beneficios.map((beneficio) => (
          <Col xs={24} sm={12} md={6} key={beneficio.titulo}>
            <Card className="beneficio-card">
              <div className="beneficio-icon">{beneficio.icon}</div>
              <Title level={4} style={{ marginTop: 16 }}>
                {beneficio.titulo}
              </Title>
              <Text>{beneficio.descripcion}</Text>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  </div>
);

export default BeneficiosSection;
