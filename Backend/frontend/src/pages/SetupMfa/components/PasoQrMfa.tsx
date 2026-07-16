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
      <div style={{ textAlign: 'center', padding: 40 }}>
        <Spin size="large" />
        <Paragraph style={{ marginTop: 16 }}>Generando código QR seguro…</Paragraph>
      </div>
    );
  }

  if (!setupData) return null;

  return (
    <div style={{ textAlign: 'center' }}>
      <Alert
        message="Paso 1: Escanee el código QR"
        description="Abra Google Authenticator → toque + → Escanear código QR."
        type="success"
        showIcon
        style={{ marginBottom: 20, textAlign: 'left' }}
      />

      {/* QR Image */}
      <div style={{
        display: 'inline-block',
        padding: 12,
        background: '#fff',
        borderRadius: 12,
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        marginBottom: 20,
      }}>
        <img
          src={setupData.qr_code}
          alt="QR Code MFA"
          style={{ width: 200, height: 200, display: 'block' }}
        />
      </div>

      {/* Clave manual */}
      <Paragraph type="secondary" style={{ marginBottom: 8 }}>
        <MobileOutlined /> ¿No puede escanear? Use el código manual:
      </Paragraph>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        gap: 8, marginBottom: 24
      }}>
        <Text
          code
          style={{ fontSize: 13, letterSpacing: '0.05em', userSelect: 'all' }}
        >
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
          style={{ borderRadius: 8 }}
        >
          Ya escaneé el QR →
        </Button>
      </Space>
    </div>
  );
};

export default PasoQrMfa;
