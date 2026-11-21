import React from 'react';
import { Card, Tag, Typography, Timeline } from 'antd';
import { CalendarOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Embarazo } from '../../../services/embarazosService';
import { ControlPrenatal } from '../../../services/controlesService';

const { Text } = Typography;

interface DetalleEmbarazoTimelineProps {
  embarazo: Embarazo;
  eg: { semanas: number; dias: number; texto: string };
  trimestre: { numero: number; texto: string; color: string };
  diasRestantes: number;
  controles: ControlPrenatal[];
  ultimoControl: ControlPrenatal | null;
}

const DetalleEmbarazoTimeline: React.FC<DetalleEmbarazoTimelineProps> = ({
  embarazo, eg, trimestre, diasRestantes, controles, ultimoControl,
}) => (
  <Card title={<><CalendarOutlined /> Línea de Tiempo del Embarazo</>} className="u-mt-4">
    <Timeline
      mode="left"
      items={[
        {
          color: 'green',
          label: embarazo.fecha_registro ? dayjs(embarazo.fecha_registro).format('DD/MM/YYYY HH:mm') : 'Fecha desconocida',
          children: (
            <>
              <strong>Embarazo Registrado</strong>
              <br />
              <Text type="secondary">Inicio del seguimiento en el sistema</Text>
            </>
          )
        },
        {
          color: 'blue',
          label: dayjs(embarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY'),
          children: (
            <>
              <strong>Fecha Última Menstruación (FUM)</strong>
              <br />
              <Text type="secondary">Inicio del embarazo</Text>
            </>
          )
        },
        {
          color: 'blue',
          label: dayjs().format('DD/MM/YYYY'),
          dot: <ClockCircleOutlined className="u-t-md" />,
          children: (
            <>
              <strong>Edad Gestacional Actual</strong>
              <br />
              <Tag color={trimestre.color}>{eg.texto}</Tag>
              <Tag color={trimestre.color}>{trimestre.texto}</Tag>
            </>
          )
        },
        ...(controles.length > 0 ? [
          {
            color: 'blue',
            label: dayjs(ultimoControl!.fecha_control).format('DD/MM/YYYY'),
            children: (
              <>
                <strong>Último Control Prenatal</strong>
                <br />
                <Text type="secondary">Control #{ultimoControl!.numero_control}</Text>
              </>
            )
          }
        ] : []),
        {
          color: 'gray',
          label: dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY'),
          children: (
            <>
              <strong>Fecha Probable de Parto (FPP)</strong>
              <br />
              <Text type="secondary">{diasRestantes} días restantes</Text>
            </>
          )
        }
      ]}
    />
  </Card>
);

export default DetalleEmbarazoTimeline;
