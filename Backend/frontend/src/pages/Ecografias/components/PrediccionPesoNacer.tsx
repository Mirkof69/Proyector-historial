import React, { useState } from 'react';
import { Alert, Button, Card, Col, InputNumber, Row, Statistic, Tag } from 'antd';
import { ExperimentOutlined } from '@ant-design/icons';
import { iaMedicaService, PrediccionPeso } from '../../../services/iaMedicaService';

/**
 * Peso al nacer previsto por el modelo supervisado, con Hadlock al lado.
 * Si el sistema no puede predecir (sin modelo, gemelar, ecografía temprana),
 * muestra el motivo que devuelve el servidor y ningún número.
 */

const COLOR_CLASE: Record<string, string> = { bajo_peso: 'orange', normal: 'green', macrosomia: 'red' };
const NOMBRE_CLASE: Record<string, string> = {
  bajo_peso: 'Bajo peso (< 2.500 g)', normal: 'Peso normal', macrosomia: 'Macrosomía (> 4.000 g)',
};
const gramos = (g: number | null) => (g == null ? '—' : `${g.toLocaleString('es-BO')} g`);

const PrediccionPesoNacer: React.FC<{ ecografiaId: number }> = ({ ecografiaId }) => {
  const [semanas, setSemanas] = useState<number | null>(39);
  const [resultado, setResultado] = useState<PrediccionPeso | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  const predecir = async () => {
    setCargando(true);
    setError(null);
    setResultado(null);
    try {
      setResultado(await iaMedicaService.predecirPesoNacer(ecografiaId, semanas ?? 39));
    } catch (e: any) {
      setError(e?.response?.data?.error || e?.message || 'No se pudo calcular la predicción.');
    } finally {
      setCargando(false);
    }
  };

  return (
    <Card size="small" style={{ marginTop: 16 }}
      title={<span><ExperimentOutlined /> Peso al nacer previsto</span>}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'end' }}>
        <div>
          <label htmlFor="semanas-parto" style={{ display: 'block', marginBottom: 4 }}>
            Si nace a las (semanas)
          </label>
          <InputNumber id="semanas-parto" min={24} max={42} step={1} value={semanas}
            onChange={(v) => setSemanas(v)} />
        </div>
        <Button type="primary" loading={cargando} onClick={predecir}>Calcular</Button>
      </div>

      {error && <Alert style={{ marginTop: 12 }} type="info" showIcon message={error} />}

      {resultado && (
        <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Statistic title="Modelo" value={gramos(resultado.peso_previsto_g)}
                suffix={resultado.margen_g ? `± ${resultado.margen_g} g` : undefined} />
            </Col>
            <Col xs={24} md={8}>
              <Statistic title="Hadlock (fórmula clínica)" value={gramos(resultado.peso_hadlock_proyectado_g)} />
            </Col>
            <Col xs={24} md={8}>
              <div style={{ marginBottom: 4, opacity: 0.75 }}>Clase</div>
              <Tag color={COLOR_CLASE[resultado.clase]}>{NOMBRE_CLASE[resultado.clase] ?? resultado.clase}</Tag>
            </Col>
          </Row>
          {resultado.advertencias.map((a) => <Alert key={a} type="warning" showIcon message={a} />)}
          <p style={{ margin: 0, fontSize: 12, opacity: 0.75 }}>
            Modelo {resultado.modelo.version} · {resultado.modelo.algoritmo} · R² de validación{' '}
            {resultado.modelo.r2_validacion ?? '—'}. Ecografía de {resultado.semanas_ecografia} semanas.
            Es apoyo a la decisión, no un diagnóstico.
          </p>
        </div>
      )}
    </Card>
  );
};

export default PrediccionPesoNacer;
