/**
 * =============================================================================
 * PÁGINA DE LOGIN
 * =============================================================================
 * Autenticación de usuarios con diseño profesional
 * =============================================================================
 */

import React, { useState } from 'react';
import { Layout, Card, Form, Input, Button, Typography, Divider, Space, message } from 'antd';
import {
  UserOutlined,
  LockOutlined,
  LoginOutlined,
  ArrowLeftOutlined,
  HeartOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import './Login.css';

const { Title, Paragraph, Text } = Typography;
const { Header, Content } = Layout;

const Login: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      await authService.login({
        username: values.username,
        password: values.password,
      });

      message.success('¡Bienvenido al sistema!');

      // Redirigir al dashboard
      setTimeout(() => {
        navigate('/dashboard');
      }, 500);
    } catch (error: any) {
      message.error(
        error.message ||
        error.response?.data?.message ||
        'Error al iniciar sesión. Verifique sus credenciales.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout className="login-page">
      <Header className="login-header">
        <div className="header-content">
          <div className="logo-container">
            <HeartOutlined className="logo-icon" />
            <Title level={3} className="logo-text">
              Fetal Medical Foundation
            </Title>
          </div>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
          >
            Volver al Inicio
          </Button>
        </div>
      </Header>

      <Content className="login-content">
        <div className="login-container">
          <Card className="login-card">
            <div className="card-header">
              <div className="login-icon-wrapper">
                <LoginOutlined className="login-icon" />
              </div>
              <Title level={2}>Iniciar Sesión</Title>
              <Paragraph>
                Acceda al Sistema de Historial Médico Obstétrico
              </Paragraph>
            </div>

            <Form
              form={form}
              name="login"
              onFinish={onFinish}
              layout="vertical"
              size="large"
              className="login-form"
            >
              <Form.Item
                name="username"
                label="Usuario"
                rules={[
                  { required: true, message: 'Por favor ingrese su usuario' },
                  { min: 3, message: 'El usuario debe tener al menos 3 caracteres' },
                ]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="Ingrese su usuario"
                  autoComplete="username"
                />
              </Form.Item>

              <Form.Item
                name="password"
                label="Contraseña"
                rules={[
                  { required: true, message: 'Por favor ingrese su contraseña' },
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="Ingrese su contraseña"
                  autoComplete="current-password"
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  block
                  size="large"
                  className="btn-login"
                  icon={<LoginOutlined />}
                >
                  Iniciar Sesión
                </Button>
              </Form.Item>
            </Form>

            <Divider />

            <div className="register-section">
              <Text>¿Es paciente y no tiene cuenta?</Text>
              <Button
                type="link"
                onClick={() => navigate('/registro')}
                style={{ padding: 0, marginLeft: 8 }}
              >
                Regístrese aquí
              </Button>
            </div>

            <div className="forgot-password">
              <Button type="link" style={{ padding: 0 }}>
                ¿Olvidó su contraseña?
              </Button>
            </div>
          </Card>

          {/* INFO LATERAL */}
          <div className="login-info">
            <div className="info-box">
              <Title level={3}>Sistema Profesional</Title>
              <Paragraph>
                Plataforma integral para el seguimiento prenatal con tecnología
                de la Fetal Medicine Foundation
              </Paragraph>

              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div className="feature-item">
                  <HeartOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
                  <div>
                    <Text strong>Seguimiento Completo</Text>
                    <Paragraph>
                      Control de embarazos con alertas médicas en tiempo real
                    </Paragraph>
                  </div>
                </div>

                <div className="feature-item">
                  <LoginOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                  <div>
                    <Text strong>Acceso Seguro</Text>
                    <Paragraph>
                      Autenticación protegida con tokens JWT
                    </Paragraph>
                  </div>
                </div>

                <div className="feature-item">
                  <UserOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                  <div>
                    <Text strong>Gestión de Usuarios</Text>
                    <Paragraph>
                      Roles diferenciados para médicos, enfermeros y personal
                    </Paragraph>
                  </div>
                </div>
              </Space>
            </div>
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default Login;
