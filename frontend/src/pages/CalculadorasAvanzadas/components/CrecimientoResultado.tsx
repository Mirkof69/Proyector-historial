import React from 'react';
import { Card, Row, Col, Statistic, Alert } from 'antd';
import { AlertOutlined, SafetyOutlined } from '@ant-design/icons';
import { ResultadoCrecimiento } from '../crecimientoFetalUtils';

interface CrecimientoResultadoProps {
  resultado: ResultadoCrecimiento;
}

const CrecimientoResultado: React.FC<CrecimientoResultadoProps> = ({ resultado }) => (
  <>
    <Card title={<><SafetyOutlined /> Estadísticas del Crecimiento</>} className="calc-bloque">
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Statistic
            title="Peso Fetal Estimado"
            value={resultado.efw}
            precision={0}
            suffix="g"
            valueStyle={{ color: resultado.color }}
          />
        </Col>
        <Col xs={24} sm={8}>
          <Statistic
            title="Percentil"
            value={resultado.percentil}
            precision={1}
            prefix="p"
            valueStyle={{ color: resultado.color }}
          />
        </Col>
        <Col xs={24} sm={8}>
          <Statistic
            title="Z-Score"
            value={resultado.zscore}
            precision={2}
            valueStyle={{ color: Math.abs(resultado.zscore) > 2 ? 'var(--color-peligro)' : 'var(--color-exito)' }}
          />
        </Col>
      </Row>
    </Card>

    <Alert
      message={resultado.clasificacion}
      description={
        <div className="calc-parrafos">
          <p><strong>Interpretación:</strong> {resultado.interpretacion}</p>
          <p><strong>Recomendación:</strong> {resultado.recomendacion}</p>
        </div>
      }
      type={resultado.categoria === 'NORMAL' ? 'success' : resultado.categoria === 'PEG' || resultado.categoria === 'GEG' ? 'warning' : 'error'}
      showIcon
      icon={resultado.categoria === 'NORMAL' ? <SafetyOutlined /> : <AlertOutlined />}
      className="calc-bloque"
    />

    <Card title="Percentiles de Parámetros Biométricos" size="small">
      <Row gutter={[8, 8]}>
        <Col xs={12} sm={6}>
          <Statistic title="BPD" value={resultado.bpd_percentil} precision={1} prefix="p" className="calc-cifra-pequena" />
        </Col>
        <Col xs={12} sm={6}>
          <Statistic title="HC" value={resultado.hc_percentil} precision={1} prefix="p" className="calc-cifra-pequena" />
        </Col>
        <Col xs={12} sm={6}>
          <Statistic title="AC" value={resultado.ac_percentil} precision={1} prefix="p" className="calc-cifra-pequena" />
        </Col>
        <Col xs={12} sm={6}>
          <Statistic title="FL" value={resultado.fl_percentil} precision={1} prefix="p" className="calc-cifra-pequena" />
        </Col>
      </Row>
    </Card>
  </>
);

export default CrecimientoResultado;
