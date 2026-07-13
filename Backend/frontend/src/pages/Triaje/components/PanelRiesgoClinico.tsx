import React from 'react';
import { Card, Space, Progress, Tag, Button, Typography } from 'antd';
import { TriajeEnfermeria } from '../../../services/triajeService';

const { Text } = Typography;

interface PanelRiesgoClinicoProps {
  triaje: TriajeEnfermeria;
  onVerHistorial: () => void;
}

const PanelRiesgoClinico: React.FC<PanelRiesgoClinicoProps> = ({ triaje, onVerHistorial }) => (
  <Card title="Panel de Riesgo Clínico" className="gradient-card" style={{ height: '100%' }}>
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <div className="stat-indicator">
        <Text type="secondary">Estabilidad Hemodinámica</Text>
        <Progress
          percent={triaje.presion_sistolica >= 140 ? 40 : 100}
          status={triaje.presion_sistolica >= 140 ? 'exception' : 'success'}
          strokeWidth={12}
        />
      </div>

      <div className="stat-indicator">
        <Text type="secondary">Nivel Térmico</Text>
        <Progress
          percent={triaje.temperatura >= 38 ? 100 : (triaje.temperatura / 40) * 100}
          status={triaje.temperatura >= 38 ? 'exception' : 'active'}
          strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
          strokeWidth={12}
        />
      </div>

      <div className="stat-indicator">
        <Text type="secondary">Oxigenación Periférica</Text>
        <Progress
          type="dashboard"
          percent={triaje.saturacion_oxigeno || 0}
          width={100}
          strokeColor={triaje.saturacion_oxigeno && triaje.saturacion_oxigeno < 95 ? '#ff4d4f' : '#52c41a'}
        />
      </div>

      <Card size="small" style={{ background: 'rgba(255,255,255,0.5)', border: 'none' }}>
        <div style={{ textAlign: 'center' }}>
          <Text type="secondary">Estado de Priorización</Text>
          <div style={{ marginTop: 8 }}>
            <Tag color={
              triaje.prioridad === 'urgente' ? 'red' :
                triaje.prioridad === 'alto' ? 'volcano' :
                  triaje.prioridad === 'normal' ? 'blue' : 'green'
            } style={{ fontSize: '1.2em', padding: '8px 20px', width: '100%', textAlign: 'center' }}>
              {(triaje.prioridad || 'NORMAL').toUpperCase()}
            </Tag>
          </div>
        </div>
      </Card>

      <Button
        block
        size="large"
        type="dashed"
        onClick={onVerHistorial}
      >
        Ver Historial del Paciente
      </Button>
    </Space>
  </Card>
);

export default PanelRiesgoClinico;
