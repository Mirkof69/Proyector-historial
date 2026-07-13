import React from 'react';
import { Card, Space, Progress, Descriptions, Tag, Divider, Typography, Empty } from 'antd';
import { InfoCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { TipoVacuna } from '../../../services/vacunasService';

const { Text } = Typography;

interface GuiaEsquemaVacunaProps {
  vacunaSeleccionada: TipoVacuna | null;
  progresoDosis: number;
  numeroDosis: number;
  alertas: string[];
}

const GuiaEsquemaVacuna: React.FC<GuiaEsquemaVacunaProps> = ({ vacunaSeleccionada, progresoDosis, numeroDosis, alertas }) => (
  <Card title={<Space><InfoCircleOutlined /> Guía del Esquema</Space>} className="sidebar-card">
    {vacunaSeleccionada ? (
      <div className="vacuna-guide-content">
        <div className="progreso-container" style={{ textAlign: 'center', marginBottom: 24 }}>
          <Progress
            type="dashboard"
            percent={progresoDosis}
            strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
          />
          <div style={{ marginTop: 8 }}>
            <Text strong>Cobertura: {progresoDosis.toFixed(0)}%</Text>
            <br />
            <Text type="secondary">
              Dosis {numeroDosis} de {vacunaSeleccionada.dosis_requeridas}
            </Text>
          </div>
        </div>

        <Descriptions column={1} size="small" bordered>
          <Descriptions.Item label="Intervalo Min.">{vacunaSeleccionada.intervalo_dosis_dias || 0} días</Descriptions.Item>
          <Descriptions.Item label="Embarazo">
            {vacunaSeleccionada.obligatoria_embarazo ? <Tag color="error">Recomendada</Tag> : <Tag>Opcional</Tag>}
          </Descriptions.Item>
        </Descriptions>

        {alertas.length > 0 && (
          <div style={{ marginTop: 20 }}>
            <Divider style={{ margin: '12px 0' }} />
            {alertas.map((a) => (
              <div key={`alerta-${a}`} style={{ marginBottom: 10, display: 'flex', gap: 8 }}>
                <WarningOutlined style={{ color: '#faad14' }} />
                <Text style={{ fontSize: '0.85em' }}>{a}</Text>
              </div>
            ))}
          </div>
        )}
      </div>
    ) : (
      <Empty description="Seleccione una vacuna" />
    )}
  </Card>
);

export default GuiaEsquemaVacuna;
