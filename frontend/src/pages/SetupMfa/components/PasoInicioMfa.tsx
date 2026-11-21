import React from 'react';
import { Alert, Typography, Space, Button } from 'antd';
import { QrcodeOutlined } from '@ant-design/icons';

const { Paragraph } = Typography;

interface PasoInicioMfaProps {
  loading: boolean;
  onComenzar: () => void;
}

const PasoInicioMfa: React.FC<PasoInicioMfaProps> = ({ loading, onComenzar }) => (
  <div className="setup-mfa__paso">
    <Alert
      message="¿Por qué necesito MFA?"
      description="Como médico o administrador, accede a datos clínicos sensibles. MFA añade una segunda capa de seguridad que protege a sus pacientes."
      type="info"
      showIcon
      className="setup-mfa__bloque"
    />
    <Paragraph>
      Necesitará instalar <strong>Google Authenticator</strong> o <strong>Authy</strong> en su teléfono.
    </Paragraph>
    <Space direction="vertical" className="setup-mfa__ancho">
      <Button
        type="primary"
        size="large"
        block
        icon={<QrcodeOutlined />}
        loading={loading}
        onClick={onComenzar}
      >
        Comenzar configuración
      </Button>
    </Space>
  </div>
);

export default PasoInicioMfa;
