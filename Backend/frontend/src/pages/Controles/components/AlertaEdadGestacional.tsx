import React from 'react';
import { Alert, Space, Typography } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface AlertaEdadGestacionalProps {
  semanasGestacion: number;
}

const AlertaEdadGestacional: React.FC<AlertaEdadGestacionalProps> = ({ semanasGestacion }) => {
  if (semanasGestacion <= 0) return null;

  return (
    <Alert
      message={
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text strong>
            📋 Campos Obligatorios según Edad Gestacional: {semanasGestacion} semanas
          </Text>
          {semanasGestacion < 12 && (
            <Text type="secondary">
              • Antes de 12 semanas: Altura Uterina NO es medible todavía. Los demás campos obstétricos son opcionales.
            </Text>
          )}
          {semanasGestacion >= 12 && semanasGestacion < 20 && (
            <Text type="warning">
              • 12-19 semanas: <strong>Altura Uterina</strong> comienza a ser medible. FCF y movimientos fetales aún NO detectables.
            </Text>
          )}
          {semanasGestacion >= 20 && (
            <Text type="success">
              • 20+ semanas: <strong>TODOS los campos obstétricos son obligatorios</strong> (Altura Uterina, FCF, Presentación, Movimientos Fetales, Edema, Proteinuria).
            </Text>
          )}
        </Space>
      }
      type={semanasGestacion < 12 ? 'info' : semanasGestacion < 20 ? 'warning' : 'success'}
      showIcon
      icon={<InfoCircleOutlined />}
      style={{ marginBottom: 16, marginTop: 16 }}
    />
  );
};

export default AlertaEdadGestacional;
