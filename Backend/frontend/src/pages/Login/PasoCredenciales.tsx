import React from 'react';
import { Form, Input, Space, Checkbox, Button, Divider, Typography } from 'antd';
import type { FormInstance } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined, SafetyOutlined } from '@ant-design/icons';
import { CredentialsForm } from './loginTypes';

const { Title, Paragraph, Text } = Typography;

interface PasoCredencialesProps {
  form: FormInstance<CredentialsForm>;
  loading: boolean;
  onFinish: (values: CredentialsForm) => void;
  onForgotPassword: () => void;
}

const PasoCredenciales: React.FC<PasoCredencialesProps> = ({ form, loading, onFinish, onForgotPassword }) => (
  <>
    <div className="login-form-header">
      <div className="login-icon-circle">
        <LoginOutlined />
      </div>
      <Title level={2} className="login-title">Iniciar Sesión</Title>
      <Paragraph className="login-subtitle">
        Acceda al Sistema de Historias Clínicas Gineco-Obstétricas
      </Paragraph>
    </div>

    <Form<CredentialsForm>
      form={form}
      layout="vertical"
      onFinish={onFinish}
      className="login-form"
      initialValues={{ remember: true }}
    >
      <Form.Item
        name="email"
        label="Email"
        rules={[
          { required: true, message: 'Por favor ingrese su email.' },
          { type: 'email', message: 'Formato de email inválido.' },
        ]}
      >
        <Input
          prefix={<UserOutlined />}
          placeholder="ejemplo@fetalmedical.com"
          autoComplete="email"
          size="large"
          disabled={loading}
        />
      </Form.Item>

      <Form.Item
        name="password"
        label="Contraseña"
        rules={[
          { required: true, message: 'Por favor ingrese su contraseña.' },
          { min: 4, message: 'La contraseña debe tener al menos 4 caracteres.' },
        ]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="Ingrese su contraseña"
          autoComplete="current-password"
          size="large"
          disabled={loading}
        />
      </Form.Item>

      <Form.Item>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Form.Item name="remember" valuePropName="checked" noStyle>
            <Checkbox disabled={loading}>Recordarme</Checkbox>
          </Form.Item>
          <Button type="link" size="small" onClick={onForgotPassword} disabled={loading}>
            ¿Olvidó su contraseña?
          </Button>
        </Space>
      </Form.Item>

      <Form.Item style={{ marginBottom: 0 }}>
        <Button
          type="primary"
          htmlType="submit"
          icon={<LoginOutlined />}
          size="large"
          block
          loading={loading}
          className="login-submit-button"
        >
          {loading ? 'Verificando...' : 'Iniciar Sesión'}
        </Button>
      </Form.Item>

      <Divider />
      <div className="login-info-footer">
        <Text type="secondary" style={{ fontSize: 12 }}>
          <SafetyOutlined /> Acceso exclusivo para personal médico autorizado
        </Text>
      </div>
    </Form>
  </>
);

export default PasoCredenciales;
