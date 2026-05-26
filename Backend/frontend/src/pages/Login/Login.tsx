/**
 * =============================================================================
 * PÁGINA DE LOGIN — SISTEMA CLÍNICO PERINATAL
 * =============================================================================
 * Flujo de autenticación de dos pasos:
 *   Paso 1: email + contraseña → POST /usuarios/login/
 *   Paso 2 (si mfa_required): código TOTP de 6 dígitos → reenvío con totp_code
 *   Si mfa_setup_required: redirigir a página de configuración MFA
 * =============================================================================
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Layout,
  Card,
  Form,
  Input,
  Button,
  Typography,
  Divider,
  Space,
  message,
  Alert,
  Checkbox,
  Steps,
  Result,
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  LoginOutlined,
  HeartOutlined,
  ArrowLeftOutlined,
  SafetyOutlined,
  CheckCircleOutlined,
  MedicineBoxOutlined,
  TeamOutlined,
  KeyOutlined,
  QrcodeOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../../services/authService';
import type { LoginFlowResult } from '../../services/authService';
import { useAuth } from '../../hooks/useAuth';
import { FRONTEND_ROUTES } from '../../config/routes';
import './Login.css';

const { Header, Content } = Layout;
const { Title, Paragraph, Text } = Typography;

// ─────────────────────────────────────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────────────────────────────────────

type LoginStep = 'credentials' | 'totp' | 'setup_required';

interface CredentialsForm {
  email: string;
  password: string;
  remember?: boolean;
}

interface TotpForm {
  totp_code: string;
}

interface LocationState {
  from?: string;
}

interface LoginProps {
  onLoginSuccess?: () => void;
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENTE PRINCIPAL
// ─────────────────────────────────────────────────────────────────────────────

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [credForm] = Form.useForm<CredentialsForm>();
  const [totpForm] = Form.useForm<TotpForm>();

  const [step, setStep] = useState<LoginStep>('credentials');
  const [loading, setLoading] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const [setupMessage, setSetupMessage] = useState('');

  // Guardamos las credenciales para el paso 2 (nunca van a localStorage)
  const pendingCredentials = useRef<{ email: string; password: string } | null>(null);

  const { refreshAuth } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;
  const fromPath = state?.from || FRONTEND_ROUTES.DASHBOARD.HOME;

  // Redirigir si ya está autenticado
  useEffect(() => {
    if (authService.isAuthenticated()) {
      navigate(FRONTEND_ROUTES.DASHBOARD.HOME, { replace: true });
    }
  }, [navigate]);

  // ─────────────────────────────────────────────────────────────────────────
  // PASO 1: email + contraseña
  // ─────────────────────────────────────────────────────────────────────────

  const onSubmitCredentials = async (values: CredentialsForm) => {
    setLoading(true);
    setConnectionError(false);

    try {
      const result: LoginFlowResult = await authService.loginStep1({
        email: values.email,
        password: values.password,
      });

      if (values.remember) {
        localStorage.setItem('remember_me', 'true');
      } else {
        localStorage.removeItem('remember_me');
      }

      if (result.success) {
        // Login directo (sin MFA)
        handleLoginSuccess(result.user);
        return;
      }

      if ('setupRequired' in result && result.setupRequired) {
        // Médico/admin sin MFA configurado
        pendingCredentials.current = { email: values.email, password: values.password };
        setSetupMessage(result.mensaje);
        setStep('setup_required');
        return;
      }

      if ('mfaRequired' in result && result.mfaRequired) {
        // El backend pide el código TOTP
        pendingCredentials.current = { email: values.email, password: values.password };
        setStep('totp');
        message.info({
          content: 'Ingrese el código de 6 dígitos de su aplicación autenticadora.',
          duration: 3,
          icon: <KeyOutlined />,
        });
      }

    } catch (error: any) {
      handleLoginError(error);
    } finally {
      setLoading(false);
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  // PASO 2: código TOTP
  // ─────────────────────────────────────────────────────────────────────────

  const onSubmitTotp = async (values: TotpForm) => {
    if (!pendingCredentials.current) {
      setStep('credentials');
      return;
    }

    setLoading(true);
    try {
      const result = await authService.loginStep2({
        ...pendingCredentials.current,
        totp_code: values.totp_code.replace(/\s/g, ''),
      });

      handleLoginSuccess(result.user);
    } catch (error: any) {
      const status = error?.response?.status;

      if (status === 401) {
        message.error({ content: 'Código MFA inválido o expirado. Inténtelo de nuevo.', duration: 4 });
        totpForm.resetFields();
      } else {
        handleLoginError(error);
      }
    } finally {
      setLoading(false);
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  // HELPERS
  // ─────────────────────────────────────────────────────────────────────────

  const handleLoginSuccess = (user: any) => {
    const nombre = user?.nombre || user?.email || 'usuario';
    const apellido = user?.apellido_paterno ? ` ${user.apellido_paterno}` : '';
    message.success({ content: `Bienvenido/a ${nombre}${apellido}`, duration: 2 });
    refreshAuth(); // Sincroniza isAuthenticated en el contexto React
    if (onLoginSuccess) onLoginSuccess();
    pendingCredentials.current = null;
    setTimeout(() => navigate(fromPath, { replace: true }), 300);
  };

  const handleLoginError = (error: any) => {
    let errorMessage = 'No se pudo iniciar sesión. Revise sus datos.';

    if (error?.response) {
      const status = error.response.status;
      const data = error.response.data;

      if (status === 401) {
        errorMessage = 'Email o contraseña incorrectos.';
      } else if (status === 400) {
        errorMessage = data?.error || data?.detail || 'Datos inválidos.';
      } else if (status === 403 && data?.mfa_setup_required) {
        // Manejado en onSubmitCredentials — no llegar aquí
        return;
      } else if (status === 403) {
        errorMessage = data?.mensaje || 'Acceso denegado. Contacte al administrador.';
      } else if (status === 423) {
        errorMessage = 'Cuenta bloqueada temporalmente por múltiples intentos fallidos.';
      } else if (status >= 500) {
        errorMessage = 'Error del servidor. Intente nuevamente más tarde.';
        setConnectionError(true);
      } else if (data?.error) {
        errorMessage = data.error;
      } else if (data?.detail) {
        errorMessage = data.detail;
      }
    } else if (error?.request) {
      errorMessage = 'No se pudo conectar al servidor. Verifique su conexión a internet.';
      setConnectionError(true);
    } else if (error?.message) {
      errorMessage = error.message;
    }

    message.error({ content: errorMessage, duration: 4 });
  };

  const handleBackToCredentials = () => {
    setStep('credentials');
    pendingCredentials.current = null;
    totpForm.resetFields();
  };

  const handleForgotPassword = () => {
    message.info({ content: 'La recuperación de contraseña estará disponible próximamente.', duration: 3 });
  };

  const handleGoToHome = () => navigate(FRONTEND_ROUTES.LANDING);

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────────────────

  return (
    <Layout className="login-layout">
      {/* HEADER */}
      <Header className="login-header">
        <div className="login-header-left">
          <HeartOutlined className="login-logo-icon" />
          <span className="login-logo-text">Fetal Medical Foundation</span>
        </div>
        <div className="login-header-right">
          <Button
            type="text"
            className="login-back-button"
            icon={<ArrowLeftOutlined />}
            onClick={handleGoToHome}
          >
            Volver al Inicio
          </Button>
        </div>
      </Header>

      {/* CONTENIDO PRINCIPAL */}
      <Content className="login-content">
        {connectionError && (
          <Alert
            message="Problema de Conexión"
            description="No se pudo conectar con el servidor. Verifique que el backend esté en ejecución."
            type="error"
            showIcon
            closable
            onClose={() => setConnectionError(false)}
            style={{ maxWidth: 900, margin: '0 auto 20px' }}
          />
        )}

        <div className="login-container">
          {/* ── COLUMNA IZQUIERDA: FORMULARIO ── */}
          <Card className="login-card login-card-form" variant="borderless">

            {/* Indicador de pasos cuando está en modo MFA */}
            {step !== 'credentials' && (
              <Steps
                current={step === 'totp' ? 1 : 2}
                size="small"
                style={{ marginBottom: 24 }}
                items={[
                  { title: 'Credenciales', icon: <UserOutlined /> },
                  { title: 'Verificación MFA', icon: <KeyOutlined /> },
                ]}
              />
            )}

            {/* ── PASO 1: Credenciales ── */}
            {step === 'credentials' && (
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
                  form={credForm}
                  layout="vertical"
                  onFinish={onSubmitCredentials}
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
                      <Button type="link" size="small" onClick={handleForgotPassword} disabled={loading}>
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
            )}

            {/* ── PASO 2: Código TOTP ── */}
            {step === 'totp' && (
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
                  form={totpForm}
                  layout="vertical"
                  onFinish={onSubmitTotp}
                  className="login-form"
                >
                  <Form.Item
                    name="totp_code"
                    label="Código de Autenticación (6 dígitos)"
                    rules={[
                      { required: true, message: 'Por favor ingrese el código TOTP.' },
                      {
                        pattern: /^\d{6}$/,
                        message: 'El código debe ser exactamente 6 dígitos numéricos.',
                      },
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
                        // Auto-submit cuando tiene 6 dígitos
                        const val = e.target.value.replace(/\D/g, '');
                        if (val.length === 6) {
                          totpForm.setFieldValue('totp_code', val);
                          setTimeout(() => totpForm.submit(), 100);
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
                    onClick={handleBackToCredentials}
                    disabled={loading}
                    style={{ color: 'var(--color-text-secondary, #888)' }}
                  >
                    Volver al inicio de sesión
                  </Button>
                </Form>
              </>
            )}

            {/* ── ESTADO: MFA Setup requerido ── */}
            {step === 'setup_required' && (
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
                    onClick={() => navigate('/setup-mfa', {
                      state: { credentials: pendingCredentials.current }
                    })}
                  >
                    Configurar Google Authenticator
                  </Button>,
                  <Button
                    key="back"
                    icon={<ArrowLeftOutlined />}
                    onClick={handleBackToCredentials}
                  >
                    Volver
                  </Button>,
                ]}
              />
            )}
          </Card>

          {/* ── COLUMNA DERECHA: PANEL INFORMATIVO ── */}
          <Card className="login-card login-card-info" variant="borderless">
            <div className="login-info-header">
              <SafetyOutlined className="login-info-main-icon" />
              <div>
                <Title level={4} className="login-info-title">Sistema Clínico Seguro</Title>
                <Paragraph className="login-info-subtitle">
                  Plataforma profesional para la gestión integral de historias clínicas
                  gineco-obstétricas con autenticación de dos factores.
                </Paragraph>
              </div>
            </div>

            <Divider />

            <Space direction="vertical" size="large" className="login-info-list">
              <div className="login-info-item">
                <div className="login-info-icon success">
                  <CheckCircleOutlined />
                </div>
                <div>
                  <Text strong>Acceso Controlado con MFA</Text>
                  <br />
                  <Text type="secondary">
                    Médicos y administradores requieren Google Authenticator para acceder.
                  </Text>
                </div>
              </div>

              <div className="login-info-item">
                <div className="login-info-icon info">
                  <MedicineBoxOutlined />
                </div>
                <div>
                  <Text strong>Gestión Completa</Text>
                  <br />
                  <Text type="secondary">
                    Pacientes, embarazos, controles prenatales, ecografías, laboratorios e IA.
                  </Text>
                </div>
              </div>

              <div className="login-info-item">
                <div className="login-info-icon warning">
                  <TeamOutlined />
                </div>
                <div>
                  <Text strong>Equipo Médico Colaborativo</Text>
                  <br />
                  <Text type="secondary">
                    Médicos, enfermeras y personal clínico con historial compartido seguro.
                  </Text>
                </div>
              </div>

              <div className="login-info-item">
                <div className="login-info-icon neutral">
                  <LockOutlined />
                </div>
                <div>
                  <Text strong>Confidencialidad Total</Text>
                  <br />
                  <Text type="secondary">
                    Cifrado AES-256, auditoría completa. Cumple Ley 3871.
                  </Text>
                </div>
              </div>
            </Space>

            {step === 'totp' && (
              <>
                <Divider />
                <Alert
                  message="¿Cómo obtener el código?"
                  description={
                    <ol style={{ paddingLeft: 16, margin: 0 }}>
                      <li>Abra Google Authenticator en su teléfono</li>
                      <li>Busque la cuenta "Fetal Medical Bolivia"</li>
                      <li>Ingrese el código de 6 dígitos que aparece</li>
                    </ol>
                  }
                  type="info"
                  showIcon
                  icon={<KeyOutlined />}
                />
              </>
            )}

            <Divider />
            <div className="login-support-info">
              <Text type="secondary" style={{ fontSize: 12 }}>
                Si tiene problemas para acceder, contacte al administrador del sistema.
              </Text>
            </div>
          </Card>
        </div>
      </Content>
    </Layout>
  );
};

export default Login;
