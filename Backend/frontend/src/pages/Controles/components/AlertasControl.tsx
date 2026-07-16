import React from 'react';
import { Alert, Tag, Space, Typography } from 'antd';
import { WarningOutlined } from '@ant-design/icons';
import { ControlPrenatal } from '../../../services/controlesService';

const { Text } = Typography;

interface AlertasControlProps {
  control: ControlPrenatal;
}

const AlertasControl: React.FC<AlertasControlProps> = ({ control }) => (
  <>
    {/* @ts-ignore */}
    {control.tiene_alertas && control.alertas && control.alertas.length > 0 && (
      <Alert
        message={
          <Space>
            <WarningOutlined />
            {/* @ts-ignore */}
            <Text strong>{control.alertas.length} Alerta(s) Médica(s) Detectada(s)</Text>
          </Space>
        }
        description={
          <ul style={{ marginBottom: 0, paddingLeft: 20, marginTop: 8 }}>
            {/* @ts-ignore */}
            {control.alertas.map((alerta: any) => (
              <li key={`${alerta.tipo}-${alerta.mensaje}`} style={{ marginBottom: 8, fontSize: 13, lineHeight: 1.5 }}>
                <Space direction="vertical" size={0}>
                  {/* Mensaje principal */}
                  <Text strong>
                    {alerta.mensaje || alerta.tipo || 'Alerta sin descripción'}
                  </Text>
                  {/* Detalles adicionales */}
                  {alerta.valor && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Valor: {alerta.valor}
                    </Text>
                  )}
                  {alerta.nivel && (
                    <Tag
                      color={
                        alerta.nivel === 'alto' || alerta.nivel === 'critico'
                          ? 'red'
                          : alerta.nivel === 'medio'
                            ? 'orange'
                            : 'blue'
                      }
                      style={{ marginTop: 4 }}
                    >
                      {alerta.nivel.toUpperCase()}
                    </Tag>
                  )}
                </Space>
              </li>
            ))}
          </ul>
        }
        type="error"
        showIcon
        closable
        style={{ marginBottom: 16 }}
      />
    )}
  </>
);

export default AlertasControl;
