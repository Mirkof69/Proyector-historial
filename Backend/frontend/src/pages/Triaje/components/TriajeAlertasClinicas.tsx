import React from 'react';
import { Alert, Typography } from 'antd';
import { WarningOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface TriajeAlertasClinicasProps {
  alertas: string[];
}

const TriajeAlertasClinicas: React.FC<TriajeAlertasClinicasProps> = ({ alertas }) => {
  if (alertas.length === 0) return null;

  return (
    <Alert
      message={<Text strong>Intervención Requerida / Alertas Clínicas</Text>}
      description={
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          {alertas.map((alerta) => (
            <li key={alerta}>{alerta}</li>
          ))}
        </ul>
      }
      type="error"
      showIcon
      icon={<WarningOutlined className="status-pulse" />}
      style={{ marginBottom: 24, borderRadius: '8px' }}
    />
  );
};

export default TriajeAlertasClinicas;
