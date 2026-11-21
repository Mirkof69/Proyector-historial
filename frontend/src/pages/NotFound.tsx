import React, { useEffect, useState, useMemo } from 'react';
import { Result, Button, Typography, Divider } from 'antd';
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
  <Title level={1} className="pagina-estado__codigo">
    404
  </Title>
);

const getNotFoundSubTitle = (pathname: string) => (
  <div className="pagina-estado__texto">
    <Title level={3}>¡Ups! Página no encontrada</Title>
    <Text type="secondary">
      Lo sentimos, la ruta <code>{pathname}</code> no existe en el sistema.
    </Text>
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
    <div className="pagina-estado page-container">
      <div className="pagina-estado__tarjeta">
        <Result
          status="404"
          title={notFoundTitle}
          subTitle={notFoundSubTitle as React.ReactNode}
          extra={
            <div className="pagina-estado__extra">
              <div className="pagina-estado__acciones">
                <Button
                  type="primary"
                  icon={<HomeOutlined />}
                  onClick={() => navigate('/')}
                >
                  Ir al Inicio ({countdown}s)
                </Button>

                <Button
                  icon={<ArrowLeftOutlined />}
                  onClick={() => navigate(-1)}
                >
                  Volver Atrás
                </Button>
              </div>

              <Divider dashed>¿Buscas algo específico?</Divider>

              <Paragraph type="secondary">
                Si necesitas ayuda para encontrar lo que buscas, puedes usar los enlaces rápidos de abajo o contactar con soporte técnico.
              </Paragraph>

              {/* Enlaces rápidos de ayuda */}
              <div className="pagina-estado__acciones">
                <Button type="link" icon={<SearchOutlined />} onClick={() => navigate('/dashboard/pacientes')}>
                  Buscar Paciente
                </Button>
                <Button type="link" icon={<BugOutlined />} onClick={() => navigate('/dashboard/ayuda')}>
                  Reportar Error
                </Button>
              </div>
            </div>
          }
        />

        <div className="pagina-estado__pie texto-mono" suppressHydrationWarning>
          System ID: 404-NF-Route-Exception • {timestamp}
        </div>
      </div>
    </div>
  );
};

export default NotFound;
