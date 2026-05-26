import React from 'react';
import { Typography, Card, Row, Col } from 'antd';

const { Title, Paragraph } = Typography;

interface Feature {
  icon: React.ReactNode;
  title: string;
  description: string;
}

interface FeaturesSectionProps {
  features: Feature[];
}

const FeaturesSection: React.FC<FeaturesSectionProps> = ({ features }) => (
  <div id="features" className="features-section">
    <div className="section-container">
      <div className="section-header">
        <Title level={2} className="section-title">
          Funcionalidades Principales
        </Title>
        <Paragraph className="section-description">
          Un sistema completo diseñado específicamente para profesionales de la
          salud materna
        </Paragraph>
      </div>
      <Row gutter={[24, 24]} style={{ marginTop: 60 }}>
        {features.map((feature) => (
          <Col xs={24} sm={12} lg={8} key={feature.title}>
            <Card className="feature-card" hoverable>
              <div className="feature-icon">{feature.icon}</div>
              <Title level={4}>{feature.title}</Title>
              <Paragraph>{feature.description}</Paragraph>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  </div>
);

export default FeaturesSection;
