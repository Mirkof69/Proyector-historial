import React from 'react';
import { Typography, Card, Row, Col, Space, Divider, Button } from 'antd';
import { CalculatorOutlined, CheckCircleOutlined, LoginOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

interface Calculadora {
  nombre: string;
  categoria: string;
  color: string;
}

interface CalculadorasSectionProps {
  calculadoras: Calculadora[];
  onLogin: () => void;
}

const CalculadorasSection: React.FC<CalculadorasSectionProps> = ({ calculadoras, onLogin }) => (
  <div id="calculadoras" className="calculadoras-section">
    <div className="section-container">
      <div className="section-header">
        <Title level={2} className="section-title">
          <CalculatorOutlined /> 15+ Calculadoras Clínicas FMF
        </Title>
        <Paragraph className="section-description">
          Algoritmos validados científicamente para evaluación de riesgos y toma
          de decisiones basadas en evidencia
        </Paragraph>
      </div>
      <Row gutter={[16, 16]} style={{ marginTop: 50 }}>
        {calculadoras.map((calc) => (
          <Col xs={24} sm={12} md={8} key={calc.nombre}>
            <Card className="calculadora-card" size="small">
              <Space direction="vertical" size={4} style={{ width: '100%' }}>
                <Space>
                  <CheckCircleOutlined
                    style={{ color: calc.color, fontSize: 18 }}
                  />
                  <Text strong>{calc.nombre}</Text>
                </Space>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {calc.categoria}
                </Text>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
      <Divider style={{ margin: '60px 0 40px' }} />
      <div className="cta-container">
        <Title level={3}>¿Listo para empezar?</Title>
        <Paragraph>
          Accede al sistema con tus credenciales institucionales y comienza a
          gestionar historias clínicas digitales
        </Paragraph>
        <Button
          type="primary"
          size="large"
          icon={<LoginOutlined />}
          onClick={onLogin}
        >
          Iniciar Sesión Ahora
        </Button>
      </div>
    </div>
  </div>
);

export default CalculadorasSection;
