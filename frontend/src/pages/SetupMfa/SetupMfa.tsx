/**
 * =============================================================================
 * PÁGINA: CONFIGURACIÓN MFA — Google Authenticator
 * =============================================================================
 * Flujo:
 *   1. Pedir QR + secreto
 *   2. Usuario escanea QR con Google Authenticator
 *   3. Confirmar el primer código → activa MFA
 *   4. Redirigir al dashboard
 *
 * Dos accesos:
 *   - Con sesión (activar MFA voluntariamente): /mfa/setup/ y /mfa/confirm/.
 *   - Desde el login cuando el rol exige MFA (mfa_setup_required): todavía no
 *     hay sesión; se usa el token temporal del login con /mfa-setup-inicial/ y
 *     /mfa-confirmar-inicial/, que además abre la sesión.
 * =============================================================================
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { Layout, Card, Typography, Steps, Alert, Form, Divider, Tag } from "antd";
import {
  QrcodeOutlined,
  KeyOutlined,
  CheckCircleOutlined,
  SafetyOutlined,
  HeartOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';
import { useAuth } from '../../hooks/useAuth';
import type { MfaSetupResponse } from '../../services/authService';
import { FRONTEND_ROUTES } from '../../config/routes';
import PasoInicioMfa from './components/PasoInicioMfa';
import PasoQrMfa from './components/PasoQrMfa';
import PasoVerificacionMfa, { TotpConfirmForm } from './components/PasoVerificacionMfa';
import PasoExitoMfa from './components/PasoExitoMfa';
import './SetupMfa.css';

const { Content, Header } = Layout;
const { Title, Paragraph, Text } = Typography;

const SetupMfa: React.FC = () => {
  const { message } = useAntdApp();
  const [confirmForm] = Form.useForm<TotpConfirmForm>();
  const [setupData, setSetupData] = useState<MfaSetupResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [done, setDone] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();
  const { refreshAuth } = useAuth();
  // Se decide UNA vez al entrar: si cambiara al abrirse la sesión, el efecto de
  // abajo volvería a pedir un QR y reemplazaría el secreto recién activado.
  const [inicial] = useState(() => !authService.isAuthenticated() && authService.hasMfaSetupToken());

  // ──────────────────────────────────────────────────────────────────────────
  // SOLICITAR QR AL BACKEND
  // ──────────────────────────────────────────────────────────────────────────
  const requestSetup = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = inicial ? await authService.setupMfaInicial() : await authService.setupMfa();
      setSetupData(data);
      setCurrentStep(1);
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.message || 'Error al generar el QR. Inténtelo de nuevo.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [inicial]);

  // Cada pedido de QR genera un secreto NUEVO en el servidor. Si se pidiera dos
  // veces al entrar (React lo hace en desarrollo con StrictMode, o un remontaje),
  // la pantalla podía mostrar un secreto y el servidor guardar el otro: el código
  // de Google Authenticator salía «inválido» (visto en la E2E el 14/10/2026).
  const qrPedido = useRef(false);

  useEffect(() => {
    // Protección de ruta: sin sesión y sin venir del login, fuera.
    if (!authService.isAuthenticated() && !inicial) {
      navigate(FRONTEND_ROUTES.LOGIN, { replace: true });
      return;
    }
    if (qrPedido.current) return;
    qrPedido.current = true;
    requestSetup();
  }, [requestSetup, navigate, inicial]);

  // ──────────────────────────────────────────────────────────────────────────
  // CONFIRMAR CÓDIGO TOTP
  // ──────────────────────────────────────────────────────────────────────────
  const onConfirmCode = async (values: TotpConfirmForm) => {
    setConfirming(true);
    setError(null);
    try {
      const code = values.code.replace(/\s/g, '');
      const activado = inicial
        ? Boolean((await authService.confirmMfaInicial(code)).user)
        : (await authService.confirmMfa(code)).mfa_enabled;
      if (activado) {
        if (inicial) refreshAuth();
        setDone(true);
        setCurrentStep(3);
        message.success({ content: 'MFA activado correctamente. Su cuenta ahora está protegida.', duration: 3 });
        setTimeout(() => navigate(FRONTEND_ROUTES.DASHBOARD.HOME, { replace: true }), 2500);
      }
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 400) {
        setError('Código inválido o expirado. Asegúrese de que la hora del teléfono esté sincronizada.');
        confirmForm.resetFields();
      } else {
        setError(err?.response?.data?.error || err?.message || 'Error al verificar el código.');
      }
    } finally {
      setConfirming(false);
    }
  };

  const copySecret = () => {
    if (setupData?.secret) {
      navigator.clipboard.writeText(setupData.secret);
      message.success('Secreto copiado al portapapeles');
    }
  };

  // ──────────────────────────────────────────────────────────────────────────
  // RENDER
  // ──────────────────────────────────────────────────────────────────────────
  return (
    <Layout className="setup-mfa">
      <Header className="setup-mfa__cabecera">
        <span className="setup-mfa__logo"><HeartOutlined aria-hidden /></span>
        <span className="setup-mfa__marca">Fetal Medical Foundation</span>
        <span className="setup-mfa__espacio" />
        <Tag color="warning" icon={<SafetyOutlined />}>Configuración de Seguridad</Tag>
      </Header>

      <Content className="setup-mfa__contenido">
        <Card className="setup-mfa__tarjeta">
          {/* Título */}
          <div className="setup-mfa__titulo">
            <div className="mfa-icon">
              <SafetyOutlined />
            </div>
            <Title level={3}>Activar Autenticación de Dos Factores</Title>
            <Paragraph type="secondary">
              Su rol requiere MFA. Complete estos pasos para proteger su cuenta.
            </Paragraph>
          </div>

          {/* Steps */}
          <Steps
            current={currentStep}
            className="setup-mfa__pasos"
            size="small"
            items={[
              { title: 'Inicio', icon: <SafetyOutlined /> },
              { title: 'Escanear QR', icon: <QrcodeOutlined /> },
              { title: 'Verificar', icon: <KeyOutlined /> },
              { title: 'Listo', icon: <CheckCircleOutlined /> },
            ]}
          />

          {/* Errores globales */}
          {error && (
            <Alert
              message={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
              className="setup-mfa__bloque"
            />
          )}

          {currentStep === 0 && (
            <PasoInicioMfa loading={loading} onComenzar={requestSetup} />
          )}

          {currentStep === 1 && (
            <PasoQrMfa
              loading={loading}
              setupData={setupData}
              onRegenerar={requestSetup}
              onContinuar={() => setCurrentStep(2)}
              onCopySecret={copySecret}
            />
          )}

          {currentStep === 2 && (
            <PasoVerificacionMfa
              form={confirmForm}
              confirming={confirming}
              onConfirmCode={onConfirmCode}
              onVolver={() => setCurrentStep(1)}
            />
          )}

          {done && currentStep === 3 && (
            <PasoExitoMfa onIrDashboard={() => navigate(FRONTEND_ROUTES.DASHBOARD.HOME, { replace: true })} />
          )}

          <Divider />
          <Text type="secondary" className="setup-mfa__pie">
            <SafetyOutlined /> MFA protege sus datos y los de sus pacientes (Ley 3871)
          </Text>
        </Card>
      </Content>
    </Layout>
  );
};

export default SetupMfa;
