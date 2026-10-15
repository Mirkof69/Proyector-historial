import React from 'react';
import { Alert, Typography, Space, Button, Spin } from 'antd';
import { MobileOutlined, CopyOutlined, ReloadOutlined, KeyOutlined } from '@ant-design/icons';
import type { MfaSetupResponse } from '../../../services/authService';

const { Paragraph, Text } = Typography;

interface PasoQrMfaProps {
  loading: boolean;
  setupData: MfaSetupResponse | null;
  onRegenerar: () => void;
  onContinuar: () => void;
  onCopySecret: () => void;
}

const PasoQrMfa: React.FC<PasoQrMfaProps> = ({ loading, setupData, onRegenerar, onContinuar, onCopySecret }) => {
  if (loading) {
    return (
      <div className="setup-mfa__paso setup-mfa__cargando">
        <Spin size="large" />
        <Paragraph>Generando código QR seguro…</Paragraph>
      </div>
    );
  }

  if (!setupData) return null;

  return (
    <div className="setup-mfa__paso">
      <Alert
        message="Paso 1: Escanee el código QR"
        description="Abra Google Authenticator → toque + → Escanear código QR."
        type="success"
        showIcon
        className="setup-mfa__bloque"
      />

      {/* QR Image */}
      {/* La imagen trae su propio fondo blanco y margen de silencio (qrcode.make) */}
      <div className="setup-mfa__qr">
        <img
          src={setupData.qr_code}
          alt="QR Code MFA"
        />
      </div>

      {/* Clave manual */}
      <Paragraph type="secondary" className="setup-mfa__ayuda">
        <MobileOutlined /> ¿No puede escanear? Use el código manual:
      </Paragraph>
      <div className="setup-mfa__secreto">
        <Text code>
          {setupData.secret}
        </Text>
        <Button
          size="small"
          icon={<CopyOutlined />}
          onClick={onCopySecret}
          type="text"
        />
      </div>

      <Space>
        <Button icon={<ReloadOutlined />} onClick={onRegenerar}>
          Regenerar QR
        </Button>
        <Button
          type="primary"
          icon={<KeyOutlined />}
          onClick={onContinuar}
        >
          Ya escaneé el QR →
        </Button>
      </Space>
    </div>
  );
};

export default PasoQrMfa;
