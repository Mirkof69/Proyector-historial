import React from 'react';
import { Typography, Button } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

interface PasoExitoMfaProps {
  onIrDashboard: () => void;
}

const PasoExitoMfa: React.FC<PasoExitoMfaProps> = ({ onIrDashboard }) => (
  <div className="setup-mfa__exito">
    <CheckCircleOutlined className="setup-mfa__exito-icono" />
    <Title level={3} type="success">¡MFA Activado!</Title>
    <Paragraph>
      Su cuenta ahora está protegida con autenticación de dos factores.
      Será redirigido al sistema en unos segundos…
    </Paragraph>
    <Button
      type="primary"
      size="large"
      onClick={onIrDashboard}
    >
      Ir al Dashboard
    </Button>
  </div>
);

export default PasoExitoMfa;
