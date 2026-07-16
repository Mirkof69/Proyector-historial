import React from 'react';
import { Card, Row, Col, Statistic, Alert } from 'antd';
import { AlertOutlined, SafetyOutlined } from '@ant-design/icons';
import { ResultadoCrecimiento } from '../crecimientoFetalUtils';

interface CrecimientoResultadoProps {
  resultado: ResultadoCrecimiento;
}

const CrecimientoResultado: React.FC<CrecimientoResultadoProps> = ({ resultado }) => (
  <>
    <Card title={<><SafetyOutlined /> Estadísticas del Crecimiento</>} style={{ marginBottom: 16 }}>
      <Row gutter={16}>
        <Col span={8}>
          <Statistic
            title="Peso Fetal Estimado"
            value={resultado.efw}
            precision={0}
            suffix="g"
            valueStyle={{ color: resultado.color, fontWeight: 'bold' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Percentil"
            value={resultado.percentil}
            precision={1}
            prefix="p"
            valueStyle={{ color: resultado.color, fontWeight: 'bold' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Z-Score"
            value={resultado.zscore}
            precision={2}
            valueStyle={{ color: Math.abs(resultado.zscore) > 2 ? '#f5222d' : '#52c41a' }}
          />
        </Col>
      </Row>
    </Card>

    <Alert
      message={resultado.clasificacion}
      description={
        <div>
          <p style={{ marginBottom: 8 }}><strong>Interpretación:</strong> {resultado.interpretacion}</p>
          <p style={{ marginBottom: 0 }}><strong>Recomendación:</strong> {resultado.recomendacion}</p>
        </div>
      }
      type={resultado.categoria === 'NORMAL' ? 'success' : resultado.categoria === 'PEG' || resultado.categoria === 'GEG' ? 'warning' : 'error'}
      showIcon
      icon={resultado.categoria === 'NORMAL' ? <SafetyOutlined /> : <AlertOutlined />}
      style={{ marginBottom: 16 }}
    />

    <Card title="Percentiles de Parámetros Biométricos" size="small">
      <Row gutter={8}>
        <Col span={6}>
          <Statistic title="BPD" value={resultado.bpd_percentil} precision={1} prefix="p" valueStyle={{ fontSize: 16 }} />
        </Col>
        <Col span={6}>
          <Statistic title="HC" value={resultado.hc_percentil} precision={1} prefix="p" valueStyle={{ fontSize: 16 }} />
        </Col>
        <Col span={6}>
          <Statistic title="AC" value={resultado.ac_percentil} precision={1} prefix="p" valueStyle={{ fontSize: 16 }} />
        </Col>
        <Col span={6}>
          <Statistic title="FL" value={resultado.fl_percentil} precision={1} prefix="p" valueStyle={{ fontSize: 16 }} />
        </Col>
      </Row>
    </Card>
  </>
);

export default CrecimientoResultado;
