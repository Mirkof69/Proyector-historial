/**
 * =============================================================================
 * PÁGINA DE LOGIN — SISTEMA CLÍNICO PERINATAL
 * =============================================================================
 * Flujo de autenticación de dos pasos:
 *   Paso 1: email + contraseña → POST /usuarios/login/
 *   Paso 2 (si mfa_required): código TOTP de 6 dígitos → reenvío con totp_code
 *   Si mfa_setup_required: redirigir a página de configuración MFA
 * Los pasos y el panel informativo viven en ./PasoCredenciales, ./PasoTotp,
 * ./PasoSetupRequerido y ./LoginInfoPanel.
 * =============================================================================
 */

import React, { useState, useEffect, useRef } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { Layout, Card, Form, Steps, Alert, Button } from "antd";
import {
  UserOutlined, HeartOutlined, ArrowLeftOutlined, KeyOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../../services/authService';
import type { LoginFlowResult } from '../../services/authService';
import { useAuth } from '../../hooks/useAuth';
import { FRONTEND_ROUTES } from '../../config/routes';
import { LoginStep, CredentialsForm, TotpForm, LocationState } from './loginTypes';
import PasoCredenciales from './PasoCredenciales';
import PasoTotp from './PasoTotp';
import PasoSetupRequerido from './PasoSetupRequerido';
import LoginInfoPanel from './LoginInfoPanel';
import './Login.css';

const { Header, Content } = Layout;

interface LoginProps {
  onLoginSuccess?: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const { message } = useAntdApp();
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
        handleLoginSuccess(result.user);
        return;
      }

      if ('setupRequired' in result && result.setupRequired) {
        pendingCredentials.current = { email: values.email, password: values.password };
        setSetupMessage(result.mensaje);
        setStep('setup_required');
        return;
      }

      if ('mfaRequired' in result && result.mfaRequired) {
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
    refreshAuth();
    if (onLoginSuccess) onLoginSuccess();
    pendingCredentials.current = null;
    setTimeout(() => navigate(fromPath, { replace: true }), 300);
  };

  const handleLoginError = (error: any) => {
    let errorMessage = 'No se pudo iniciar sesión. Revise sus datos.';

    if (error?.response) {
      const status = error.response.status;
      const data = error.response?.data;

      if (status === 401) {
        errorMessage = 'Email o contraseña incorrectos.';
      } else if (status === 400) {
        errorMessage = data?.error || data?.detail || 'Datos inválidos.';
      } else if (status === 403 && data?.mfa_setup_required) {
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

            {step === 'credentials' && (
              <PasoCredenciales
                form={credForm}
                loading={loading}
                onFinish={onSubmitCredentials}
                onForgotPassword={handleForgotPassword}
              />
            )}

            {step === 'totp' && (
              <PasoTotp
                form={totpForm}
                loading={loading}
                onFinish={onSubmitTotp}
                onBack={handleBackToCredentials}
              />
            )}

            {step === 'setup_required' && (
              <PasoSetupRequerido
                setupMessage={setupMessage}
                onSetup={() => navigate('/setup-mfa', { state: { credentials: pendingCredentials.current } })}
                onBack={handleBackToCredentials}
              />
            )}
          </Card>

          {/* ── COLUMNA DERECHA: PANEL INFORMATIVO ── */}
          <LoginInfoPanel showTotpHelp={step === 'totp'} />
        </div>
      </Content>
    </Layout>
  );
};

export default Login;
