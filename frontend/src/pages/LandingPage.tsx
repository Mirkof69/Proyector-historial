/**
 * =============================================================================
 * LANDING PAGE - FETAL MEDICAL FOUNDATION
 * ============================================================================
 * Página de bienvenida con información del sistema
 * =============================================================================
 */

import React from 'react';
import { Layout, Button, Typography, Card, Row, Col, Space, Divider } from 'antd';
import {
  HeartOutlined,
  SafetyOutlined,
  BarChartOutlined,
  MedicineBoxOutlined,
  UserOutlined,
  CalendarOutlined,
  FundProjectionScreenOutlined,
  CheckCircleOutlined,
  LoginOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

const { Header, Content, Footer } = Layout;
const { Title, Paragraph, Text } = Typography;

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <HeartOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />,
      title: 'Seguimiento Prenatal',
      description: 'Control completo de embarazos con alertas médicas automáticas y evaluación de riesgos en tiempo real.',
    },
    {
      icon: <BarChartOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
      title: '15 Calculadoras FMF',
      description: 'Algoritmos validados de la Fetal Medicine Foundation para predicción de preeclampsia, trisomías, SGA y más.',
    },
    {
      icon: <SafetyOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
      title: 'Alertas Inteligentes',
      description: 'Sistema automático de detección de signos de alarma con clasificación por severidad y recomendaciones.',
    },
    {
      icon: <MedicineBoxOutlined style={{ fontSize: 48, color: '#722ed1' }} />,
      title: 'Historia Clínica Digital',
      description: 'Registro completo de pacientes, embarazos y controles prenatales con acceso instantáneo.',
    },
    {
      icon: <FundProjectionScreenOutlined style={{ fontSize: 48, color: '#fa8c16' }} />,
      title: 'Dashboard en Tiempo Real',
      description: 'Estadísticas y métricas actualizadas con visualizaciones interactivas para toma de decisiones.',
    },
    {
      icon: <TeamOutlined style={{ fontSize: 48, color: '#13c2c2' }} />,
      title: 'Gestión de Equipo',
      description: 'Control de usuarios, roles y permisos para médicos, enfermeros y personal administrativo.',
    },
  ];

  const calculadoras = [
    'Predicción de Preeclampsia',
    'Screening de Trisomías (21, 18, 13)',
    'Predicción de SGA (Pequeño para Edad Gestacional)',
    'Diabetes Gestacional',
    'Parto Pretérmino',
    'Peso Fetal Estimado',
    'Crecimiento Fetal',
    'Translucencia Nucal',
    'Doppler Fetal',
    'IP Arterias Uterinas',
    'Presión Arterial Media',
    'Biomarcadores (sFlt-1/PlGF)',
    'Índice de Shock',
    'Test No Estresante (NST)',
  ];

  return (
    <Layout className="landing-page">
      {/* HEADER */}
      <Header className="landing-header">
        <div className="landing-header-content">
          <div className="logo-container">
            <HeartOutlined className="logo-icon" />
            <Title level={3} className="logo-text">
              Fetal Medical Foundation
            </Title>
          </div>
          <Space size="large">
            <Button
              type="primary"
              size="large"
              icon={<LoginOutlined />}
              onClick={() => navigate('/login')}
              className="btn-login"
            >
              Iniciar Sesión
            </Button>
          </Space>
        </div>
      </Header>

      {/* HERO SECTION */}
      <Content>
        <div className="hero-section">
          <div className="hero-content">
            <Title level={1} className="hero-title">
              Sistema Integral de <br />
              <span className="highlight">Historial Médico Obstétrico</span>
            </Title>
            <Paragraph className="hero-description">
              Plataforma profesional para el seguimiento prenatal con tecnología de la
              <strong> Fetal Medicine Foundation</strong>. Gestiona pacientes, embarazos y controles
              con alertas médicas automáticas y 15 calculadoras clínicas validadas.
            </Paragraph>
            <Space size="large" className="hero-buttons">
              <Button
                type="primary"
                size="large"
                icon={<LoginOutlined />}
                onClick={() => navigate('/login')}
              >
                Acceder al Sistema
              </Button>
              <Button
                size="large"
                icon={<UserOutlined />}
                onClick={() => navigate('/registro')}
              >
                Registrarse como Paciente
              </Button>
            </Space>
          </div>
        </div>

        {/* FEATURES SECTION */}
        <div className="features-section">
          <div className="section-container">
            <Title level={2} className="section-title">
              Funcionalidades Principales
            </Title>
            <Paragraph className="section-description">
              Un sistema completo diseñado para profesionales de la salud
            </Paragraph>

            <Row gutter={[24, 24]} style={{ marginTop: 40 }}>
              {features.map((feature, index) => (
                <Col xs={24} sm={12} md={8} key={index}>
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

        {/* CALCULADORAS SECTION */}
        <div className="calculadoras-section">
          <div className="section-container">
            <Title level={2} className="section-title">
              15 Calculadoras Clínicas FMF
            </Title>
            <Paragraph className="section-description">
              Algoritmos validados científicamente para evaluación de riesgos
            </Paragraph>

            <Row gutter={[16, 16]} style={{ marginTop: 40 }}>
              {calculadoras.map((calc, index) => (
                <Col xs={24} sm={12} md={8} lg={6} key={index}>
                  <Card className="calculadora-card" size="small">
                    <Space>
                      <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 18 }} />
                      <Text strong>{calc}</Text>
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>

            <Divider />

            <div className="cta-container">
              <Title level={3}>¿Listo para empezar?</Title>
              <Paragraph>
                Accede al sistema con tus credenciales o regístrate como paciente
              </Paragraph>
              <Space size="large">
                <Button
                  type="primary"
                  size="large"
                  icon={<LoginOutlined />}
                  onClick={() => navigate('/login')}
                >
                  Iniciar Sesión
                </Button>
                <Button
                  size="large"
                  icon={<UserOutlined />}
                  onClick={() => navigate('/registro')}
                >
                  Registro de Pacientes
                </Button>
              </Space>
            </div>
          </div>
        </div>

        {/* STATS SECTION */}
        <div className="stats-section">
          <div className="section-container">
            <Row gutter={[24, 24]}>
              <Col xs={24} sm={12} md={6}>
                <Card className="stat-card">
                  <Title level={2}>100%</Title>
                  <Text>Validación FMF</Text>
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card className="stat-card">
                  <Title level={2}>15</Title>
                  <Text>Calculadoras Clínicas</Text>
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card className="stat-card">
                  <Title level={2}>24/7</Title>
                  <Text>Acceso en Tiempo Real</Text>
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card className="stat-card">
                  <Title level={2}>100+</Title>
                  <Text>Funcionalidades API</Text>
                </Card>
              </Col>
            </Row>
          </div>
        </div>
      </Content>

      {/* FOOTER */}
      <Footer className="landing-footer">
        <div className="footer-content">
          <Text>
            © 2025 <strong>Fetal Medical Foundation</strong> - Sistema de Historial Médico Obstétrico
          </Text>
          <Text type="secondary">
            Tecnología profesional para el cuidado prenatal
          </Text>
        </div>
      </Footer>
    </Layout>
  );
};

export default LandingPage;
