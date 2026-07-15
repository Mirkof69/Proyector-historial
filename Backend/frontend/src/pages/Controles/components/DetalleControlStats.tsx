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
  <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Edad Gestacional"
          value={edadGestacionalTexto}
          prefix={<CalendarOutlined />}
          suffix={
            <Tag color={trimestre === 1 ? 'cyan' : trimestre === 2 ? 'blue' : 'purple'}>
              {trimestre}° Trimestre
            </Tag>
          }
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Presión Arterial"
          value={presionArterialTexto}
          prefix={<HeartOutlined />}
          suffix="mmHg"
          valueStyle={{ color: isHipertension ? '#cf1322' : '#3f8600' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="FCF"
          value={control.frecuencia_cardiaca_fetal || '-'}
          prefix={<HeartOutlined />}
          suffix="lpm"
          valueStyle={{ color: isFCFAnormal ? '#cf1322' : '#3f8600' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Calidad del Control"
          value={porcentajeCalidad.toFixed(0)}
          prefix={<CheckCircleOutlined />}
          suffix="%"
          valueStyle={{
            color: porcentajeCalidad >= 80 ? '#3f8600' : porcentajeCalidad >= 60 ? '#faad14' : '#cf1322',
          }}
        />
      </Card>
    </Col>
  </Row>
);

export default DetalleControlStats;
