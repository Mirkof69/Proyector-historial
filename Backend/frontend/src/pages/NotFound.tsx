import React, { useEffect, useState, useMemo } from 'react';
import { Result, Button, Typography, Row, Col, Card, Divider, Space } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  HomeOutlined,
  ArrowLeftOutlined,
  BugOutlined,
  SearchOutlined
} from '@ant-design/icons';
import './NotFound.css';

const { Text, Title, Paragraph } = Typography;

const notFoundTitle = (
  <Title level={1} style={{ color: 'var(--text-secondary)', marginBottom: 0 }}>
    404
  </Title>
);

const getNotFoundSubTitle = (pathname: string) => (
  <div style={{ marginBottom: 24 }}>
    <Title level={3}>¡Ups! Página no encontrada</Title>
    <Text type="secondary" style={{ fontSize: 16 }}>
      Lo sentimos, la ruta <code>{pathname}</code> no existe en el sistema.
    </Text>
    <br />
    <Text type="secondary">
      Es posible que el enlace esté roto o que la página haya sido movida.
    </Text>
  </div>
);

const NotFound: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [countdown, setCountdown] = useState(10);
  const [timestamp] = useState<string>(() => new Date().toISOString());

  const notFoundSubTitle = useMemo(() => getNotFoundSubTitle(location.pathname), [location]);

  // Cuenta regresiva: el updater se mantiene puro (sin efectos secundarios,
  // React puede llamarlo más de una vez). La navegación al llegar a 0 se hace
  // en un efecto aparte que observa el contador.
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => (prev <= 1 ? 0 : prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (countdown <= 0) {
      navigate('/'); // Volver al inicio automáticamente
    }
  }, [countdown, navigate]);

  return (
    <div className="not-found-container animate-fade-in" style={{
      height: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
    }}>
      <Card
        variant="borderless"
        style={{
          maxWidth: 800,
          width: '90%',
          borderRadius: 16,
          boxShadow: '0 10px 30px rgba(0,0,0,0.08)',
          textAlign: 'center',
          padding: '40px 20px'
        }}
      >
        <Result
          status="404"
          title={notFoundTitle}
          subTitle={notFoundSubTitle as React.ReactNode}
          extra={
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Space size="middle" wrap style={{ justifyContent: 'center' }}>
                <Button
                  type="primary"
                  size="large"
                  icon={<HomeOutlined />}
                  onClick={() => navigate('/')}
                  style={{ minWidth: 160, borderRadius: 6 }}
                >
                  Ir al Inicio ({countdown}s)
                </Button>

                <Button
                  size="large"
                  icon={<ArrowLeftOutlined />}
                  onClick={() => navigate(-1)}
                  style={{ minWidth: 160, borderRadius: 6 }}
                >
                  Volver Atrás
                </Button>
              </Space>

              <Divider dashed style={{ margin: '24px 0' }}>¿Buscas algo específico?</Divider>

              <Paragraph type="secondary" style={{ marginBottom: 16, fontSize: 13 }}>
                Si necesitas ayuda para encontrar lo que buscas, puedes usar los enlaces rápidos de abajo o contactar con soporte técnico.
              </Paragraph>

              {/* Enlaces rápidos de ayuda */}
              <Row gutter={[16, 16]} justify="center">
                <Col xs={24} sm={8}>
                  <Button block type="link" icon={<SearchOutlined />} onClick={() => navigate('/dashboard/pacientes')}>
                    Buscar Paciente
                  </Button>
                </Col>
                <Col xs={24} sm={8}>
                  <Button block type="link" icon={<BugOutlined />} onClick={() => navigate('/dashboard/ayuda')}>
                    Reportar Error
                  </Button>
                </Col>
              </Row>
            </Space>
          }
        />

        <div style={{ marginTop: 40, color: '#bfbfbf', fontSize: 12 }} suppressHydrationWarning>
          System ID: 404-NF-Route-Exception • {timestamp}
        </div>
      </Card>
    </div>
  );
};

export default NotFound;
