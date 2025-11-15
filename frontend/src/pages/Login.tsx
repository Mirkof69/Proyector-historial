// ===========================================
// PÁGINA DE LOGIN
// ===========================================

import React, { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Login.css';

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      message.success('Inicio de sesión exitoso');
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Error de login:', error);
      message.error(
        error.response?.data?.error || 'Error al iniciar sesión. Verifique sus credenciales.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <Card className="login-card" title="Sistema de Historial Médico">
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          layout="vertical"
        >
          <Form.Item
            label="Usuario"
            name="username"
            rules={[{ required: true, message: 'Por favor ingrese su usuario' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="Usuario" 
              size="large"
            />
          </Form.Item>

          <Form.Item
            label="Contraseña"
            name="password"
            rules={[{ required: true, message: 'Por favor ingrese su contraseña' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Contraseña"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading} 
              block 
              size="large"
            >
              Iniciar Sesión
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default Login;
