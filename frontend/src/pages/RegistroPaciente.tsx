/**
 * =============================================================================
 * PÁGINA DE REGISTRO DE PACIENTES
 * =============================================================================
 * Formulario público para que pacientes puedan registrarse
 * =============================================================================
 */

import React, { useState } from 'react';
import { Layout, Card, Form, Input, Button, Typography, message, Space } from 'antd';
import {
  UserOutlined,
  MailOutlined,
  LockOutlined,
  PhoneOutlined,
  HeartOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import './RegistroPaciente.css';

const { Title, Paragraph, Text } = Typography;
const { Header, Content } = Layout;

const RegistroPaciente: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      await authService.register({
        username: values.username,
        email: values.email,
        password: values.password,
        nombre: values.nombre,
        apellido: values.apellido,
        telefono: values.telefono,
      });

      message.success('¡Registro exitoso! Ahora puede iniciar sesión.');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (error: any) {
      message.error(error.message || 'Error al registrarse. Intente nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout className="registro-page">
      <Header className="registro-header">
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

      <Content className="registro-content">
        <Card className="registro-card">
          <div className="card-header">
            <UserOutlined className="card-icon" />
            <Title level={2}>Registro de Pacientes</Title>
            <Paragraph>
              Complete el formulario para crear su cuenta en el sistema
            </Paragraph>
          </div>

          <Form
            form={form}
            name="registro"
            onFinish={onFinish}
            layout="vertical"
            size="large"
            className="registro-form"
          >
            <Form.Item
              name="nombre"
              label="Nombre"
              rules={[
                { required: true, message: 'Por favor ingrese su nombre' },
                { min: 2, message: 'El nombre debe tener al menos 2 caracteres' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="Ingrese su nombre"
              />
            </Form.Item>

            <Form.Item
              name="apellido"
              label="Apellido"
              rules={[
                { required: true, message: 'Por favor ingrese su apellido' },
                { min: 2, message: 'El apellido debe tener al menos 2 caracteres' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="Ingrese su apellido"
              />
            </Form.Item>

            <Form.Item
              name="username"
              label="Nombre de Usuario"
              rules={[
                { required: true, message: 'Por favor ingrese un nombre de usuario' },
                { min: 4, message: 'El nombre de usuario debe tener al menos 4 caracteres' },
                { pattern: /^[a-zA-Z0-9_]+$/, message: 'Solo letras, números y guión bajo' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="Elija un nombre de usuario"
              />
            </Form.Item>

            <Form.Item
              name="email"
              label="Correo Electrónico"
              rules={[
                { required: true, message: 'Por favor ingrese su correo electrónico' },
                { type: 'email', message: 'Ingrese un correo electrónico válido' },
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="ejemplo@correo.com"
              />
            </Form.Item>

            <Form.Item
              name="telefono"
              label="Teléfono"
              rules={[
                { required: true, message: 'Por favor ingrese su teléfono' },
                { pattern: /^[0-9+\-\s()]+$/, message: 'Ingrese un teléfono válido' },
              ]}
            >
              <Input
                prefix={<PhoneOutlined />}
                placeholder="+54 11 1234-5678"
              />
            </Form.Item>

            <Form.Item
              name="password"
              label="Contraseña"
              rules={[
                { required: true, message: 'Por favor ingrese una contraseña' },
                { min: 8, message: 'La contraseña debe tener al menos 8 caracteres' },
              ]}
              hasFeedback
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Ingrese su contraseña"
              />
            </Form.Item>

            <Form.Item
              name="confirm_password"
              label="Confirmar Contraseña"
              dependencies={['password']}
              hasFeedback
              rules={[
                { required: true, message: 'Por favor confirme su contraseña' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('Las contraseñas no coinciden'));
                  },
                }),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Confirme su contraseña"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                size="large"
                className="btn-registro"
              >
                Registrarse
              </Button>
            </Form.Item>

            <div className="login-link">
              <Text>¿Ya tiene una cuenta? </Text>
              <Button
                type="link"
                onClick={() => navigate('/login')}
              >
                Iniciar Sesión
              </Button>
            </div>
          </Form>
        </Card>

        <div className="info-section">
          <Space direction="vertical" size="middle">
            <Card size="small" className="info-card">
              <Text strong>📋 Registro Simple</Text>
              <Paragraph>
                Complete el formulario y tendrá acceso inmediato a su cuenta
              </Paragraph>
            </Card>
            <Card size="small" className="info-card">
              <Text strong>🔒 Datos Seguros</Text>
              <Paragraph>
                Su información está protegida y es completamente confidencial
              </Paragraph>
            </Card>
            <Card size="small" className="info-card">
              <Text strong>📱 Acceso 24/7</Text>
              <Paragraph>
                Consulte su historial médico en cualquier momento
              </Paragraph>
            </Card>
          </Space>
        </div>
      </Content>
    </Layout>
  );
};

export default RegistroPaciente;
