import React from 'react';
import { Form, Input, Alert, Button, Typography } from 'antd';
import type { FormInstance } from 'antd';
import { KeyOutlined, SafetyOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { TotpForm } from './loginTypes';

const { Title, Paragraph } = Typography;

interface PasoTotpProps {
  form: FormInstance<TotpForm>;
  loading: boolean;
  onFinish: (values: TotpForm) => void;
  onBack: () => void;
}

const PasoTotp: React.FC<PasoTotpProps> = ({ form, loading, onFinish, onBack }) => (
  <>
    <div className="login-form-header">
      <div className="login-icon-circle" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <KeyOutlined />
      </div>
      <Title level={3} className="login-title">
        Verificación de Dos Factores
      </Title>
      <Paragraph className="login-subtitle">
        Ingrese el código de 6 dígitos de su aplicación autenticadora
        (Google Authenticator, Authy, etc.)
      </Paragraph>
    </div>

    <Alert
      message="Código caduca en 30 segundos"
      description="Si el código expiró, espere el siguiente y vuelva a intentarlo."
      type="warning"
      showIcon
      style={{ marginBottom: 20, borderRadius: 8 }}
    />

    <Form<TotpForm>
      form={form}
      layout="vertical"
      onFinish={onFinish}
      className="login-form"
    >
      <Form.Item
        name="totp_code"
        label="Código de Autenticación (6 dígitos)"
        rules={[
          { required: true, message: 'Por favor ingrese el código TOTP.' },
          { pattern: /^\d{6}$/, message: 'El código debe ser exactamente 6 dígitos numéricos.' },
        ]}
      >
        <Input
          prefix={<KeyOutlined />}
          placeholder="000000"
          maxLength={6}
          size="large"
          autoComplete="one-time-code"
          inputMode="numeric"
          pattern="\d{6}"
          style={{
            letterSpacing: '0.05em',
            fontSize: '1.4rem',
            fontWeight: 700,
            textAlign: 'center',
          }}
          disabled={loading}
          onChange={(e) => {
            const val = e.target.value.replace(/\D/g, '');
            if (val.length === 6) {
              form.setFieldValue('totp_code', val);
              setTimeout(() => form.submit(), 100);
            }
          }}
        />
      </Form.Item>

      <Form.Item style={{ marginBottom: 12 }}>
        <Button
          type="primary"
          htmlType="submit"
          icon={<SafetyOutlined />}
          size="large"
          block
          loading={loading}
          className="login-submit-button"
        >
          {loading ? 'Verificando...' : 'Verificar Código'}
        </Button>
      </Form.Item>

      <Button
        type="text"
        icon={<ArrowLeftOutlined />}
        block
        onClick={onBack}
        disabled={loading}
        style={{ color: 'var(--color-text-secondary, #888)' }}
      >
        Volver al inicio de sesión
      </Button>
    </Form>
  </>
);

export default PasoTotp;
