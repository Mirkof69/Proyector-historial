/**
 * =============================================================================
 * PÁGINA: CONFIGURACIÓN MFA — Google Authenticator
 * =============================================================================
 * Flujo:
 *   1. POST /api/usuarios/mfa/setup/  → recibe QR + secreto
 *   2. Usuario escanea QR con Google Authenticator
 *   3. POST /api/usuarios/mfa/confirm/ { code } → activa MFA
 *   4. Redirigir al dashboard
 *
 * Acceso: desde la pantalla de login cuando mfa_setup_required: true
 *         o desde Configuración de perfil para activar MFA voluntariamente
 * =============================================================================
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Layout,
  Card,
  Button,
  Typography,
  Steps,
  Alert,
  Input,
  Form,
  Spin,
  Space,
  Divider,
  message,
  Tag,
} from 'antd';
import {
  QrcodeOutlined,
  KeyOutlined,
  CheckCircleOutlined,
  MobileOutlined,
  SafetyOutlined,
  HeartOutlined,
  CopyOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../../services/authService';
import type { MfaSetupResponse } from '../../services/authService';
import { FRONTEND_ROUTES } from '../../config/routes';
import './SetupMfa.css';

const { Content, Header } = Layout;
const { Title, Paragraph, Text } = Typography;

interface TotpConfirmForm {
  code: string;
}

const SetupMfa: React.FC = () => {
  const [confirmForm] = Form.useForm<TotpConfirmForm>();
  const [setupData, setSetupData] = useState<MfaSetupResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [done, setDone] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();
  const location = useLocation();
  const locationState = location.state as { credentials?: { email: string; password: string } } | null;

  // ──────────────────────────────────────────────────────────────────────────
  // SOLICITAR QR AL BACKEND
  // ──────────────────────────────────────────────────────────────────────────
  const requestSetup = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await authService.setupMfa();
      setSetupData(data);
      setCurrentStep(1);
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.message || 'Error al generar el QR. Inténtelo de nuevo.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Protección de ruta: si no hay sesión y no venimos del login, fuera.
    if (!authService.isAuthenticated() && !locationState?.credentials) {
      navigate(FRONTEND_ROUTES.LOGIN, { replace: true });
      return;
    }

    // Si venimos desde el login con credenciales temporales o ya estamos autenticados, pedir el QR automáticamente
    if (authService.isAuthenticated()) {
      requestSetup();
    }
  }, [requestSetup, navigate, locationState]);

  // ──────────────────────────────────────────────────────────────────────────
  // CONFIRMAR CÓDIGO TOTP
  // ──────────────────────────────────────────────────────────────────────────
  const onConfirmCode = async (values: TotpConfirmForm) => {
    setConfirming(true);
    setError(null);
    try {
      const result = await authService.confirmMfa(values.code.replace(/\s/g, ''));
      if (result.mfa_enabled) {
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
          bodyStyle={{ padding: 36 }}
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

          {/* ── PASO 0: Inicio ── */}
          {currentStep === 0 && (
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
                  onClick={requestSetup}
                  style={{ borderRadius: 8 }}
                >
                  Comenzar configuración
                </Button>
              </Space>
            </div>
          )}

          {/* ── PASO 1: QR Code ── */}
          {currentStep === 1 && (
            <>
              {loading ? (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <Spin size="large" />
                  <Paragraph style={{ marginTop: 16 }}>Generando código QR seguro…</Paragraph>
                </div>
              ) : setupData && (
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
                      onClick={copySecret}
                      type="text"
                    />
                  </div>

                  <Space>
                    <Button icon={<ReloadOutlined />} onClick={requestSetup}>
                      Regenerar QR
                    </Button>
                    <Button
                      type="primary"
                      icon={<KeyOutlined />}
                      onClick={() => setCurrentStep(2)}
                      style={{ borderRadius: 8 }}
                    >
                      Ya escaneé el QR →
                    </Button>
                  </Space>
                </div>
              )}
            </>
          )}

          {/* ── PASO 2: Verificación ── */}
          {currentStep === 2 && (
            <>
              <Alert
                message="Paso 2: Ingrese el código de verificación"
                description="Abra Google Authenticator y escriba el código de 6 dígitos que aparece para 'Fetal Medical Bolivia'."
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Form
                form={confirmForm}
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
                        confirmForm.setFieldValue('code', val);
                        setTimeout(() => confirmForm.submit(), 100);
                      }
                    }}
                  />
                </Form.Item>

                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Button onClick={() => setCurrentStep(1)}>← Volver al QR</Button>
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
          )}

          {/* ── PASO 3: Éxito ── */}
          {done && currentStep === 3 && (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 16 }} />
              <Title level={3} style={{ color: '#52c41a' }}>¡MFA Activado!</Title>
              <Paragraph>
                Su cuenta ahora está protegida con autenticación de dos factores.
                Será redirigido al sistema en unos segundos…
              </Paragraph>
              <Button
                type="primary"
                size="large"
                onClick={() => navigate(FRONTEND_ROUTES.DASHBOARD.HOME, { replace: true })}
                style={{ marginTop: 16 }}
              >
                Ir al Dashboard
              </Button>
            </div>
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
