import React from 'react';
import { Tag, Space, Typography, Badge, Timeline, Collapse } from 'antd';
import { CheckCircleOutlined, HeartOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { ControlPrenatal } from '../../../services/controlesService';

const { Text } = Typography;

interface DetalleControlHistorialProps {
  controlesEmbarazo: ControlPrenatal[];
  control: ControlPrenatal;
}

const DetalleControlHistorial: React.FC<DetalleControlHistorialProps> = ({ controlesEmbarazo, control }) => (
  <Collapse
    style={{ marginTop: 16 }}
    items={[
      {
        key: '1',
        label: (
          <Space>
            <ClockCircleOutlined />
            <Text strong>Historial Completo de Controles</Text>
            <Badge count={controlesEmbarazo.length} style={{ backgroundColor: '#1890ff' }} />
          </Space>
        ),
        children: (
          <Timeline
            mode="left"
            items={controlesEmbarazo.map((ctrl) => ({
              color: ctrl.id === control.id ? 'green' : 'blue',
              dot:
                ctrl.id === control.id ? (
                  <CheckCircleOutlined style={{ fontSize: 16 }} />
                ) : (
                  <HeartOutlined style={{ fontSize: 16 }} />
                ),
              label: dayjs(ctrl.fecha_control).format('DD/MM/YYYY'),
              children: (
                <Space direction="vertical" size="small">
                  <Text strong={ctrl.id === control.id}>
                    Control #{ctrl.numero_control}
                    {ctrl.id === control.id && (
                      <Tag color="green" style={{ marginLeft: 8 }}>
                        ACTUAL
                      </Tag>
                    )}
                  </Text>
                  <Text type="secondary">
                    Edad gestacional:{' '}
                    {ctrl.edad_gestacional_semanas
                      ? `${ctrl.edad_gestacional_semanas} sem + ${ctrl.edad_gestacional_dias || 0} días`
                      : 'N/A'}
                  </Text>
                  {ctrl.peso_actual && (
                    <Text type="secondary">Peso: {ctrl.peso_actual} kg</Text>
                  )}
                  {ctrl.presion_arterial_sistolica && ctrl.presion_arterial_diastolica && (
                    <Text type="secondary">
                      PA: {ctrl.presion_arterial_sistolica}/{ctrl.presion_arterial_diastolica} mmHg
                    </Text>
                  )}
                </Space>
              ),
            }))}
          />
        ),
      },
    ]}
  />
);

export default DetalleControlHistorial;
