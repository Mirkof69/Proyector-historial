import React from 'react';
import { Row, Col, Statistic, Typography } from 'antd';
import { RiseOutlined, FallOutlined, MinusOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface EstadisticasLabProps {
  promedio: number;
  tendencia: number;
  ultimaVariacion: number;
  unidad: string;
}

const getTendenciaIcono = (tendencia: number) => {
  if (Math.abs(tendencia) < 5) {
    return <MinusOutlined style={{ color: 'var(--color-primario)' }} />;
  }
  return tendencia > 0
    ? <RiseOutlined style={{ color: 'var(--color-peligro)' }} />
    : <FallOutlined style={{ color: 'var(--color-exito)' }} />;
};

const getColorVariacion = (variacion: number) => {
  if (Math.abs(variacion) < 5) return 'var(--color-primario)';
  return variacion > 0 ? 'var(--color-peligro)' : 'var(--color-exito)';
};

const EstadisticasLab: React.FC<EstadisticasLabProps> = ({ promedio, tendencia, ultimaVariacion, unidad }) => (
  <Row gutter={16} style={{ marginTop: 24 }}>
    <Col xs={24} sm={8}>
      <Statistic
        title="Valor Promedio"
        value={promedio.toFixed(2)}
        suffix={unidad}
        precision={2}
        valueStyle={{ color: 'var(--color-primario)' }}
      />
    </Col>
    <Col xs={24} sm={8}>
      <Statistic
        title="Tendencia General"
        value={Math.abs(tendencia).toFixed(1)}
        suffix={<>% {getTendenciaIcono(tendencia)}</>}
        precision={1}
        valueStyle={{
          color:
            Math.abs(tendencia) < 5
              ? 'var(--color-primario)'
              : tendencia > 0
                ? 'var(--color-peligro)'
                : 'var(--color-exito)',
        }}
      />
      <Text type="secondary" style={{ fontSize: 12 }}>
        {Math.abs(tendencia) < 5
          ? 'Estable'
          : tendencia > 0
            ? 'Tendencia al alza'
            : 'Tendencia a la baja'}
      </Text>
    </Col>
    <Col xs={24} sm={8}>
      <Statistic
        title="Última Variación"
        value={Math.abs(ultimaVariacion).toFixed(1)}
        suffix="%"
        precision={1}
        valueStyle={{ color: getColorVariacion(ultimaVariacion) }}
      />
      <Text type="secondary" style={{ fontSize: 12 }}>
        {ultimaVariacion > 0 ? 'Aumento' : ultimaVariacion < 0 ? 'Disminución' : 'Sin cambio'} respecto al anterior
      </Text>
    </Col>
  </Row>
);

export default EstadisticasLab;
