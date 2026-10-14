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

import React, { useState, useEffect, useCallback } from 'react';
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

  useEffect(() => {
    // Protección de ruta: sin sesión y sin venir del login, fuera.
    if (!authService.isAuthenticated() && !inicial) {
      navigate(FRONTEND_ROUTES.LOGIN, { replace: true });
      return;
    }
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
        message.success({ content: '✅ MFA activado correctamente. Su cuenta ahora está protegida.', duration: 3 });
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
    <Layout style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)' }}>
      <Header style={{ background: 'transparent', display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <HeartOutlined style={{ color: '#ff6b8a', fontSize: 22, marginRight: 10 }} />
        <span style={{ color: '#fff', fontWeight: 700, fontSize: 16 }}>Fetal Medical Foundation</span>
        <span style={{ flex: 1 }} />
        <Tag color="gold" icon={<SafetyOutlined />}>Configuración de Seguridad</Tag>
      </Header>

      <Content style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '24px' }}>
        <Card
          style={{
            width: '100%',
            maxWidth: 620,
            borderRadius: 16,
            boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
          }}
          styles={{ body: { padding: 36 } }}
        >
          {/* Título */}
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <div className="mfa-icon">
              <SafetyOutlined style={{ color: '#fff' }} />
            </div>
            <Title level={3} style={{ margin: 0 }}>Activar Autenticación de Dos Factores</Title>
            <Paragraph type="secondary" style={{ marginTop: 8 }}>
              Su rol requiere MFA. Complete estos pasos para proteger su cuenta.
            </Paragraph>
          </div>

          {/* Steps */}
          <Steps
            current={currentStep}
            style={{ marginBottom: 28 }}
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
              style={{ marginBottom: 20 }}
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
          <Text type="secondary" style={{ fontSize: 12, display: 'block', textAlign: 'center' }}>
            <SafetyOutlined /> MFA protege sus datos y los de sus pacientes (Ley 3871)
          </Text>
        </Card>
      </Content>
    </Layout>
  );
};

export default SetupMfa;
