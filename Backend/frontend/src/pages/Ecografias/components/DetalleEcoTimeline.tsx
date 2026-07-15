import React from 'react';
import { Card, Space, Timeline, Typography, Checkbox } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Ecografia } from '../../../services/ecografiasService';

const { Text } = Typography;

interface DetalleEcoTimelineProps {
  ecografia: Ecografia;
}

const DetalleEcoTimeline: React.FC<DetalleEcoTimelineProps> = ({ ecografia }) => (
  <Card
    title={
      <Space>
        <InfoCircleOutlined />
        Línea de Tiempo del Estudio
      </Space>
    }
    style={{ marginBottom: 16 }}
  >
    <Timeline
      items={[
        {
          color: 'green',
          children: (
            <>
              <Text strong>Estudio Solicitado</Text>
              <br />
              <Text type="secondary">{dayjs(ecografia.fecha_ecografia).subtract(1, 'day').format('DD/MM/YYYY')}</Text>
            </>
          ),
        },
        {
          color: 'blue',
          children: (
            <>
              <Text strong>Ecografía Realizada</Text>
              <br />
              <Text type="secondary">{dayjs(ecografia.fecha_ecografia).format('DD/MM/YYYY HH:mm')}</Text>
              <br />
              <Space style={{ marginTop: 4 }}>
                <Checkbox checked disabled>Biometría completa</Checkbox>
                <Checkbox checked={!!ecografia.anatomia} disabled>Evaluación anatómica</Checkbox>
                <Checkbox checked={!!ecografia.anexos} disabled>Anexos evaluados</Checkbox>
              </Space>
            </>
          ),
        },
        {
          color: ecografia.diagnostico ? 'green' : 'gray',
          children: (
            <>
              <Text strong>Diagnóstico Emitido</Text>
              <br />
              <Text type="secondary">
                {ecografia.diagnostico ? dayjs(ecografia.fecha_ecografia).format('DD/MM/YYYY') : 'Pendiente'}
              </Text>
            </>
          ),
        },
        {
          color: ecografia.requiere_seguimiento ? 'orange' : 'green',
          children: (
            <>
              <Text strong>{ecografia.requiere_seguimiento ? 'Requiere Seguimiento' : 'Estudio Completo'}</Text>
              <br />
              <Text type="secondary">
                {ecografia.requiere_seguimiento ? 'Se programará control adicional' : 'No requiere seguimiento especial'}
              </Text>
            </>
          ),
        },
      ]}
    />
  </Card>
);

export default DetalleEcoTimeline;
