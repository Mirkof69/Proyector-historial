import React, { useState } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { Row, Col, Form } from "antd";
import { CalculatorOutlined } from '@ant-design/icons';
import {
  calcularBishop, getHistogramaData, getDistribucionPie, getTendenciaData,
  HISTORIAL_INICIAL, BishopScore, ResultadoBishop, HistorialBishop,
} from './scoreBishop/scoreBishopUtils';
import BishopStats from './scoreBishop/BishopStats';
import BishopForm from './scoreBishop/BishopForm';
import BishopResultado from './scoreBishop/BishopResultado';
import BishopHistorial from './scoreBishop/BishopHistorial';
import './ScoreBishop.css';

const ScoreBishop: React.FC = () => {
  const { message } = useAntdApp();
  const [form] = Form.useForm();
  const [resultado, setResultado] = useState<ResultadoBishop | null>(null);
  const [historial] = useState<HistorialBishop[]>(HISTORIAL_INICIAL);
  const [loading, setLoading] = useState(false);

  const onFinish = (values: BishopScore) => {
    setLoading(true);
    setTimeout(() => {
      const res = calcularBishop(values);
      setResultado(res);
      message.success(`Score Bishop: ${res.puntaje} - ${res.clasificacion}`);
      setLoading(false);
    }, 500);
  };

  const resetear = () => {
    form.resetFields();
    setResultado(null);
  };

  // Datos del radar (dependen del formulario y del resultado)
  const getRadarData = () => {
    if (!resultado) return [];
    const values = form.getFieldsValue();
    return [
      { parametro: 'Dilatación', valor: values.dilatacion || 0, maxValor: 3 },
      { parametro: 'Borramiento', valor: values.borramiento || 0, maxValor: 3 },
      { parametro: 'Estación', valor: values.estacion || 0, maxValor: 3 },
      { parametro: 'Consistencia', valor: values.consistencia || 0, maxValor: 2 },
      { parametro: 'Posición', valor: values.posicion || 0, maxValor: 2 }
    ];
  };

  // Estadísticas globales
  const promedioScore = historial.length > 0
    ? (historial.reduce((sum, h) => sum + h.puntaje, 0) / historial.length).toFixed(1)
    : 0;
  const tasaFavorable = historial.length > 0
    ? ((historial.filter(h => h.puntaje >= 8).length / historial.length) * 100).toFixed(0)
    : 0;

  return (
    <div className="score-bishop-page" style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1><CalculatorOutlined /> Score de Bishop - Maduración Cervical</h1>
        <p style={{ color: '#666' }}>
          Evaluación cuantitativa de favorabilidad del cérvix para inducción del parto (0-13 puntos)
        </p>
      </div>

      {/* Estadísticas globales */}
      <BishopStats
        total={historial.length}
        promedio={promedioScore}
        tasaFavorable={tasaFavorable}
        ultimoScore={historial[0]?.puntaje || 0}
      />

      <Row gutter={[16, 16]}>
        {/* Formulario */}
        <Col xs={24} lg={10}>
          <BishopForm
            form={form}
            loading={loading}
            resultado={resultado}
            radarData={getRadarData()}
            onFinish={onFinish}
            onReset={resetear}
          />
        </Col>

        {/* Resultado */}
        <Col xs={24} lg={14}>
          <BishopResultado
            resultado={resultado}
            distribucionPie={getDistribucionPie(historial)}
            histograma={getHistogramaData(historial)}
            tendencia={getTendenciaData(historial)}
          />
        </Col>
      </Row>

      {/* Historial */}
      <BishopHistorial historial={historial} />
    </div>
  );
};

export default ScoreBishop;
