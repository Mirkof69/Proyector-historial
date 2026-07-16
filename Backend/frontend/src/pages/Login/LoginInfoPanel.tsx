import React from 'react';
import { Card, Typography, Divider, Space, Alert } from 'antd';
import {
  SafetyOutlined, CheckCircleOutlined, MedicineBoxOutlined, TeamOutlined, LockOutlined, KeyOutlined,
} from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

const LoginInfoPanel: React.FC<{ showTotpHelp: boolean }> = ({ showTotpHelp }) => (
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

    {showTotpHelp && (
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
);

export default LoginInfoPanel;
