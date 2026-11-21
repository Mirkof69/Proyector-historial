import React from 'react';
import { Card, Tag, Row, Col, Statistic } from 'antd';
import { CalendarOutlined, HeartOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { ControlPrenatal } from '../../../services/controlesService';

interface DetalleControlStatsProps {
  edadGestacionalTexto: string;
  trimestre: number;
  presionArterialTexto: string;
  isHipertension: boolean;
  control: ControlPrenatal;
  isFCFAnormal: boolean | 0 | null | undefined;
  porcentajeCalidad: number;
}

const DetalleControlStats: React.FC<DetalleControlStatsProps> = ({
  edadGestacionalTexto, trimestre, presionArterialTexto, isHipertension, control, isFCFAnormal, porcentajeCalidad,
}) => (
  <Row gutter={[16, 16]} className="pc-cifras">
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="Edad Gestacional"
          value={edadGestacionalTexto}
          prefix={<CalendarOutlined />}
          suffix={
            <Tag color="processing">
              {trimestre}° Trimestre
            </Tag>
          }
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="Presión Arterial"
          value={presionArterialTexto}
          prefix={<HeartOutlined />}
          suffix="mmHg"
          valueStyle={{ color: isHipertension ? 'var(--color-peligro)' : 'var(--color-exito)' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="FCF"
          value={control.frecuencia_cardiaca_fetal || '-'}
          prefix={<HeartOutlined />}
          suffix="lpm"
          valueStyle={{ color: isFCFAnormal ? 'var(--color-peligro)' : 'var(--color-exito)' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="Calidad del Control"
          value={porcentajeCalidad.toFixed(0)}
          prefix={<CheckCircleOutlined />}
          suffix="%"
          valueStyle={{
            color: porcentajeCalidad >= 80 ? 'var(--color-exito)' : porcentajeCalidad >= 60 ? 'var(--color-aviso)' : 'var(--color-peligro)',
          }}
        />
      </Card>
    </Col>
  </Row>
);

export default DetalleControlStats;
