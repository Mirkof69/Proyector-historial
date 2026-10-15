import React from 'react';
import { Card, Space, Progress, Tag, Button, Typography } from 'antd';
import { TriajeEnfermeria } from '../../../services/triajeService';

const { Text } = Typography;

interface PanelRiesgoClinicoProps {
  triaje: TriajeEnfermeria;
  onVerHistorial: () => void;
}

const PanelRiesgoClinico: React.FC<PanelRiesgoClinicoProps> = ({ triaje, onVerHistorial }) => (
  <Card title="Panel de Riesgo Clínico" className="triaje-panel-riesgo">
    <Space direction="vertical" className="triaje-ancho" size="large">
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
          strokeWidth={12}
        />
      </div>

      <div className="stat-indicator">
        <Text type="secondary">Oxigenación Periférica</Text>
        <Progress
          type="dashboard"
          percent={triaje.saturacion_oxigeno || 0}
          width={100}
          strokeColor={triaje.saturacion_oxigeno && triaje.saturacion_oxigeno < 95 ? 'var(--color-peligro)' : 'var(--color-exito)'}
        />
      </div>

      <Card size="small" className="triaje-prioridad">
        <div>
          <Text type="secondary">Estado de Priorización</Text>
          <div className="triaje-prioridad__valor">
            <Tag color={
              triaje.prioridad === 'urgente' ? 'error' :
                triaje.prioridad === 'alto' ? 'warning' :
                  triaje.prioridad === 'normal' ? 'processing' : 'success'
            } className="triaje-prioridad__tag">
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
