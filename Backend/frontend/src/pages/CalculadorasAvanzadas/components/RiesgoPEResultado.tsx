import React from 'react';
import { Card, Row, Col, Statistic, Alert } from 'antd';
import { SafetyOutlined, MedicineBoxOutlined, WarningOutlined } from '@ant-design/icons';
import { ResultadoRiesgo } from '../riesgoPreeclampsiaUtils';

const MEDICINE_BOX_ICON_5 = <MedicineBoxOutlined />;

interface RiesgoPEResultadoProps {
  resultado: ResultadoRiesgo;
}

const RiesgoPEResultado: React.FC<RiesgoPEResultadoProps> = ({ resultado }) => (
  <>
    <Card title={<><SafetyOutlined /> Estadísticas del Riesgo</>} className="calc-bloque">
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Statistic
            title="Riesgo PE Precoz (<34 sem)"
            value={resultado.riesgo_pe_precoz}
            precision={2}
            suffix="%"
            valueStyle={{ color: resultado.riesgo_pe_precoz >= 10 ? 'var(--color-peligro)' : resultado.riesgo_pe_precoz >= 5 ? 'var(--color-aviso)' : 'var(--color-exito)' }}
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="Riesgo PE Tardía (≥34 sem)"
            value={resultado.riesgo_pe_tardia}
            precision={2}
            suffix="%"
            valueStyle={{ color: resultado.riesgo_pe_tardia >= 15 ? 'var(--color-peligro)' : resultado.riesgo_pe_tardia >= 5 ? 'var(--color-aviso)' : 'var(--color-exito)' }}
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="PlGF MoM"
            value={resultado.plgf_mom}
            precision={2}
            valueStyle={{ color: resultado.plgf_mom < 0.7 ? 'var(--color-peligro)' : 'var(--color-exito)' }}
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="Ratio sFlt-1/PlGF"
            value={resultado.ratio_sflt_plgf}
            precision={1}
            valueStyle={{ color: resultado.ratio_sflt_plgf > 85 ? 'var(--color-peligro)' : resultado.ratio_sflt_plgf > 38 ? 'var(--color-aviso)' : 'var(--color-exito)' }}
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
          <p><strong>Seguimiento:</strong> {resultado.seguimiento}</p>
        </div>
      }
      type={resultado.riesgo_pe_precoz >= 10 ? 'error' : resultado.riesgo_pe_precoz >= 5 ? 'warning' : 'success'}
      showIcon
      icon={resultado.riesgo_pe_precoz >= 10 ? <WarningOutlined /> : resultado.aspirina_indicada ? <MedicineBoxOutlined /> : <SafetyOutlined />}
      className="calc-bloque"
    />

    {resultado.aspirina_indicada && (
      <Alert
        message="Profilaxis con Aspirina Indicada"
        description="Iniciar Aspirina 150mg/día vía oral, por la noche, desde las 12 hasta las 36 semanas de gestación. Demostrado reducir el riesgo de PE precoz hasta en 62% (metaanálisis ASPRE trial)."
        type="info"
        showIcon
        icon={MEDICINE_BOX_ICON_5}
        className="calc-bloque"
      />
    )}
  </>
);

export default RiesgoPEResultado;
