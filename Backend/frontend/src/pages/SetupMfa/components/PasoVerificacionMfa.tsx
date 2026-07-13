import React from 'react';
import { Alert, Form, Input, Space, Button } from 'antd';
import type { FormInstance } from 'antd';
import { KeyOutlined, CheckCircleOutlined } from '@ant-design/icons';

export interface TotpConfirmForm {
  code: string;
}

interface PasoVerificacionMfaProps {
  form: FormInstance<TotpConfirmForm>;
  confirming: boolean;
  onConfirmCode: (values: TotpConfirmForm) => void;
  onVolver: () => void;
}

const PasoVerificacionMfa: React.FC<PasoVerificacionMfaProps> = ({ form, confirming, onConfirmCode, onVolver }) => (
  <>
    <Alert
      message="Paso 2: Ingrese el código de verificación"
      description="Abra Google Authenticator y escriba el código de 6 dígitos que aparece para 'Fetal Medical Bolivia'."
      type="info"
      showIcon
      style={{ marginBottom: 24 }}
    />

    <Form
      form={form}
      layout="vertical"
      onFinish={onConfirmCode}
    >
      <Form.Item
        name="code"
        label="Código de verificación"
        rules={[
          { required: true, message: 'Ingrese el código TOTP.' },
          { pattern: /^\d{6}$/, message: 'El código debe ser de 6 dígitos numéricos.' },
        ]}
      >
        <Input
          prefix={<KeyOutlined />}
          placeholder="000000"
          maxLength={6}
          size="large"
          inputMode="numeric"
          autoFocus={false}
          disabled={confirming}
          style={{
            letterSpacing: '0.05em',
            fontSize: '1.4rem',
            fontWeight: 700,
            textAlign: 'center',
          }}
          onChange={(e) => {
            const val = e.target.value.replace(/\D/g, '');
            if (val.length === 6) {
              form.setFieldValue('code', val);
              setTimeout(() => form.submit(), 100);
            }
          }}
        />
      </Form.Item>

      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
        <Button onClick={onVolver}>← Volver al QR</Button>
        <Button
          type="primary"
          htmlType="submit"
          icon={<CheckCircleOutlined />}
          loading={confirming}
          size="large"
        >
          {confirming ? 'Verificando...' : 'Activar MFA'}
        </Button>
      </Space>
    </Form>
  </>
);

export default PasoVerificacionMfa;
