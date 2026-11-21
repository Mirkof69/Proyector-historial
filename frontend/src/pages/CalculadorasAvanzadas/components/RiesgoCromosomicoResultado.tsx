import React from 'react';
import { Card, Row, Col, Statistic, Alert, Divider } from 'antd';
import { WarningOutlined, SafetyOutlined } from '@ant-design/icons';
import { ResultadoRiesgo, formatRiesgo } from '../riesgoCromosomicoUtils';

interface RiesgoCromosomicoResultadoProps {
  resultado: ResultadoRiesgo;
}

const RiesgoCromosomicoResultado: React.FC<RiesgoCromosomicoResultadoProps> = ({ resultado }) => (
  <>
    <Card title={<><SafetyOutlined /> Estadísticas del Riesgo</>} className="calc-bloque">
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Statistic
            title="Riesgo T21 (Down)"
            value={formatRiesgo(resultado.riesgo_t21)}
            valueStyle={{ color: resultado.riesgo_t21 >= 1 / 250 ? 'var(--color-peligro)' : resultado.riesgo_t21 >= 1 / 1000 ? 'var(--color-aviso)' : 'var(--color-exito)' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Riesgo T18 (Edwards)"
            value={formatRiesgo(resultado.riesgo_t18)}
            valueStyle={{ color: resultado.riesgo_t18 >= 1 / 250 ? 'var(--color-peligro)' : resultado.riesgo_t18 >= 1 / 1000 ? 'var(--color-aviso)' : 'var(--color-exito)' }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Riesgo T13 (Patau)"
            value={formatRiesgo(resultado.riesgo_t13)}
            valueStyle={{ color: resultado.riesgo_t13 >= 1 / 250 ? 'var(--color-peligro)' : resultado.riesgo_t13 >= 1 / 1000 ? 'var(--color-aviso)' : 'var(--color-exito)' }}
          />
        </Col>
      </Row>
      <Divider className="calc-separador" />
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Statistic title="NT MoM" value={resultado.nt_mom} precision={2} className="calc-cifra-pequena" />
        </Col>
        <Col span={8}>
          <Statistic title="PAPP-A MoM" value={resultado.pappa_mom} precision={2} className="calc-cifra-pequena" />
        </Col>
        <Col span={8}>
          <Statistic title="βhCG MoM" value={resultado.bhcg_mom} precision={2} className="calc-cifra-pequena" />
        </Col>
      </Row>
    </Card>

    <Alert
      message={resultado.screening_positivo ? 'SCREENING POSITIVO' : 'SCREENING NEGATIVO'}
      description={
        <div className="calc-parrafos">
          <p><strong>T21:</strong> {resultado.clasificacion_t21}</p>
          <p><strong>T18:</strong> {resultado.clasificacion_t18}</p>
          <p><strong>T13:</strong> {resultado.clasificacion_t13}</p>
          <p><strong>Interpretación:</strong> {resultado.interpretacion}</p>
          <p><strong>Recomendación:</strong> {resultado.recomendacion}</p>
        </div>
      }
      type={resultado.screening_positivo ? 'error' : 'success'}
      showIcon
      icon={resultado.screening_positivo ? <WarningOutlined /> : <SafetyOutlined />}
      className="calc-bloque"
    />
  </>
);

export default RiesgoCromosomicoResultado;
