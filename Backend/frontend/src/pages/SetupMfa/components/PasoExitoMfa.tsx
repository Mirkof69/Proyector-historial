import React from 'react';
import { Typography, Button } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

interface PasoExitoMfaProps {
  onIrDashboard: () => void;
}

const PasoExitoMfa: React.FC<PasoExitoMfaProps> = ({ onIrDashboard }) => (
  <div style={{ textAlign: 'center', padding: '20px 0' }}>
    <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 16 }} />
    <Title level={3} style={{ color: '#52c41a' }}>¡MFA Activado!</Title>
    <Paragraph>
      Su cuenta ahora está protegida con autenticación de dos factores.
      Será redirigido al sistema en unos segundos…
    </Paragraph>
    <Button
      type="primary"
      size="large"
      onClick={onIrDashboard}
      style={{ marginTop: 16 }}
    >
      Ir al Dashboard
    </Button>
  </div>
);

export default PasoExitoMfa;
