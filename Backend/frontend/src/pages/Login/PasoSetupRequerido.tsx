import React from 'react';
import { Result, Button } from 'antd';
import { QrcodeOutlined, ArrowLeftOutlined } from '@ant-design/icons';

interface PasoSetupRequeridoProps {
  setupMessage: string;
  onSetup: () => void;
  onBack: () => void;
}

const PasoSetupRequerido: React.FC<PasoSetupRequeridoProps> = ({ setupMessage, onSetup, onBack }) => (
  <Result
    icon={<QrcodeOutlined style={{ color: '#fa8c16' }} />}
    title="Configuración MFA Requerida"
    subTitle={
      setupMessage ||
      'Su rol requiere autenticación de dos factores. Configure MFA para acceder al sistema.'
    }
    extra={[
      <Button
        key="setup"
        type="primary"
        size="large"
        icon={<QrcodeOutlined />}
        onClick={onSetup}
      >
        Configurar Google Authenticator
      </Button>,
      <Button
        key="back"
        icon={<ArrowLeftOutlined />}
        onClick={onBack}
      >
        Volver
      </Button>,
    ]}
  />
);

export default PasoSetupRequerido;
