import React from 'react';
import { Space, Divider, Alert, Collapse } from 'antd';
import { WarningOutlined, ExclamationCircleOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { AlertaParto, Recomendacion } from '../../../services/partosService';

interface AlertasYRecomendacionesProps {
  alertas: AlertaParto[];
  recomendaciones: Recomendacion[];
}

export const AlertasYRecomendaciones: React.FC<AlertasYRecomendacionesProps> = ({ alertas, recomendaciones }) => {
  return (
    <>
      {alertas.length > 0 && (
        <>
          <Divider orientation="left">
            <Space><WarningOutlined style={{ color: '#ff4d4f' }} />Alertas Médicas</Space>
          </Divider>
          <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }} size="middle">
            {alertas.map((alerta) => (
              <Alert
                key={`${alerta.tipo}-${alerta.mensaje}`}
                message={alerta.mensaje}
                description={<div><strong>Recomendación:</strong> {alerta.recomendacion}</div>}
                type={alerta.nivel === 'error' ? 'error' : 'warning'}
                showIcon
                icon={alerta.tipo === 'critica' ? <ExclamationCircleOutlined /> : <WarningOutlined />}
              />
            ))}
          </Space>
        </>
      )}

      {recomendaciones.length > 0 && (
        <>
          <Divider orientation="left">Recomendaciones Médicas</Divider>
          <Collapse
            accordion
            style={{ marginBottom: 16 }}
            defaultActiveKey={['0']}
            items={recomendaciones.map((rec) => {
              const getAlertType = () => {
                if (rec.tipo === 'urgente') return 'error';
                if (rec.tipo === 'atencion' || rec.tipo === 'importante') return 'warning';
                return 'info';
              };

              return {
                key: rec.titulo || rec.periodo,
                label: (
                  <Space>
                    {rec.tipo === 'urgente' ? <WarningOutlined /> : <InfoCircleOutlined />}
                    <strong>{rec.periodo}:</strong> {rec.titulo}
                  </Space>
                ),
                children: (
                  <Alert
                    type={getAlertType()}
                    message={rec.titulo}
                    description={
                      <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                        {rec.recomendaciones.map((r) => <li key={`rec-${r}`}>{r}</li>)}
                      </ul>
                    }
                    showIcon
                  />
                )
              };
            })}
          />
        </>
      )}
    </>
  );
};
