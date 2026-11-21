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
          <ul className="pc-lista u-mt-2">
            {/* @ts-ignore */}
            {control.alertas.map((alerta: any) => (
              <li key={`${alerta.tipo}-${alerta.mensaje}`} className="u-t-sm">
                <Space direction="vertical" size={0}>
                  {/* Mensaje principal */}
                  <Text strong>
                    {alerta.mensaje || alerta.tipo || 'Alerta sin descripción'}
                  </Text>
                  {/* Detalles adicionales */}
                  {alerta.valor && (
                    <Text type="secondary" className="u-t-xs">
                      Valor: {alerta.valor}
                    </Text>
                  )}
                  {alerta.nivel && (
                    <Tag
                      color={
                        alerta.nivel === 'alto' || alerta.nivel === 'critico'
                          ? 'error'
                          : alerta.nivel === 'medio'
                            ? 'warning'
                            : 'processing'
                      }
                      className="u-mt-1"
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
        className="u-mb-4"
      />
    )}
  </>
);

export default AlertasControl;
