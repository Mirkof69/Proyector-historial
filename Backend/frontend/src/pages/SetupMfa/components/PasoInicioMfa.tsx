import React from 'react';
import { Alert, Typography, Space, Button } from 'antd';
import { QrcodeOutlined } from '@ant-design/icons';

const { Paragraph } = Typography;

interface PasoInicioMfaProps {
  loading: boolean;
  onComenzar: () => void;
}

const PasoInicioMfa: React.FC<PasoInicioMfaProps> = ({ loading, onComenzar }) => (
  <div style={{ textAlign: 'center' }}>
    <Alert
      message="¿Por qué necesito MFA?"
      description="Como médico o administrador, accede a datos clínicos sensibles. MFA añade una segunda capa de seguridad que protege a sus pacientes."
      type="info"
      showIcon
      style={{ marginBottom: 24, textAlign: 'left' }}
    />
    <Paragraph>
      Necesitará instalar <strong>Google Authenticator</strong> o <strong>Authy</strong> en su teléfono.
    </Paragraph>
    <Space direction="vertical" style={{ width: '100%' }}>
      <Button
        type="primary"
        size="large"
        block
        icon={<QrcodeOutlined />}
        loading={loading}
        onClick={onComenzar}
        style={{ borderRadius: 8 }}
      >
        Comenzar configuración
      </Button>
    </Space>
  </div>
);

export default PasoInicioMfa;
