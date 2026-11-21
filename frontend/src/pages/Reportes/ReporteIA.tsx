import React, { useCallback, useEffect, useState } from 'react';
import { Alert, Button, Card, Col, Empty, Row, Spin, Statistic, Typography } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import {
  Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import api from '../../services/api';
import { ModeloCatalogo } from '../../services/iaMedicaService';
import CatalogoModelos from '../IaMedica/components/CatalogoModelos';
import { useRangoReportes } from './rangoReportes';
import { SERIE } from './NatalidadMorbilidad';

const { Text } = Typography;

interface Datos {
  analisis_imagen: {
    total: number; validados_por_medico: number; tiempo_medio_ms: number | null;
    por_resultado: { resultado: string; total: number }[];
    por_plano: { plano: string; total: number }[];
  };
  cardiotocografia: { clase: string; total: number }[];
  prediccion_peso: {
    predicciones: number; cerradas_con_nacimiento: number;
    error_medio_modelo_g: number | null; error_medio_hadlock_g: number | null;
  };
  modelos: ModeloCatalogo[];
}

const Barras: React.FC<{ titulo: string; datos: { nombre: string; total: number }[] }> = ({ titulo, datos }) => (
  <Card size="small" title={titulo}>
    {datos.length === 0 ? <Empty description="Sin datos en el período" /> : (
      <div className="reportes-ancho" style={{ height: Math.max(150, datos.length * 42) }} role="img" aria-label={titulo}>
        <ResponsiveContainer>
          <BarChart data={datos} layout="vertical" margin={{ left: 8, right: 40 }}>
            <CartesianGrid horizontal={false} />
            <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="nombre" width={150} tick={{ fontSize: 12 }} />
            <Tooltip cursor={{ fill: 'var(--color-hover)' }} />
            <Bar dataKey="total" name="Total" fill={SERIE.azul} radius={[0, 4, 4, 0]} maxBarSize={22}>
              <LabelList dataKey="total" position="right" className="reportes-etiqueta-grafica" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    )}
  </Card>
);

/**
 * Uso y resultados de la IA en el período, y la fiabilidad MEDIDA de cada
 * modelo (GET /api/reportes/ia/). El error del modelo de peso se mide contra
 * los bebés que ya nacieron, no contra los datos de entrenamiento.
 */
const ReporteIA: React.FC = () => {
  const rango = useRangoReportes();
  const [datos, setDatos] = useState<Datos | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      setDatos((await api.get('/reportes/ia/', { params: rango?.params })).data);
    } catch (e: any) {
      setError(e?.response?.data?.error || 'No se pudo cargar el reporte de IA.');
    } finally {
      setCargando(false);
    }
  }, [rango?.params.desde, rango?.params.hasta]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { cargar(); }, [cargar]);

  const p = datos?.prediccion_peso;
  return (
    <Spin spinning={cargando}>
      <div className="no-print reportes-acciones-derecha">
        <Button icon={<ReloadOutlined />} onClick={cargar}>Actualizar</Button>
      </div>
      {error && <Alert type="error" showIcon message={error} />}
      {datos && (
        <>
          <Row gutter={[12, 12]} className="reportes-separado reportes-cifras">
            <Col xs={12} md={6}><Card size="small"><Statistic title="Ecografías analizadas" value={datos.analisis_imagen.total} /></Card></Col>
            <Col xs={12} md={6}><Card size="small"><Statistic title="Validadas por un médico" value={datos.analisis_imagen.validados_por_medico} /></Card></Col>
            <Col xs={12} md={6}><Card size="small"><Statistic title="Tiempo medio por análisis"
              value={datos.analisis_imagen.tiempo_medio_ms ?? '—'} suffix={datos.analisis_imagen.tiempo_medio_ms ? 'ms' : ''} /></Card></Col>
            <Col xs={12} md={6}><Card size="small"><Statistic title="Cardiotocografías clasificadas"
              value={datos.cardiotocografia.reduce((a, c) => a + c.total, 0)} /></Card></Col>
          </Row>
          <Row gutter={[16, 16]} className="reportes-separado">
            <Col xs={24} lg={8}><Barras titulo="Resultado del análisis de ecografías"
              datos={datos.analisis_imagen.por_resultado.map((r) => ({ nombre: r.resultado, total: r.total }))} /></Col>
            <Col xs={24} lg={8}><Barras titulo="Plano anatómico reconocido"
              datos={datos.analisis_imagen.por_plano.map((r) => ({ nombre: r.plano, total: r.total }))} /></Col>
            <Col xs={24} lg={8}><Barras titulo="Cardiotocografías por clase"
              datos={datos.cardiotocografia.map((r) => ({ nombre: r.clase, total: r.total }))} /></Col>
          </Row>
          <Card size="small" title="Peso al nacer: predicho frente al real" className="reportes-separado">
            {p && p.cerradas_con_nacimiento > 0 ? (
              <Row gutter={16}>
                <Col xs={12} md={6}><Statistic title="Predicciones" value={p.predicciones} /></Col>
                <Col xs={12} md={6}><Statistic title="Con el bebé ya nacido" value={p.cerradas_con_nacimiento} /></Col>
                <Col xs={12} md={6}><Statistic title="Error medio del modelo" value={p.error_medio_modelo_g ?? '—'} suffix="g" /></Col>
                <Col xs={12} md={6}><Statistic title="Error medio de Hadlock" value={p.error_medio_hadlock_g ?? '—'} suffix="g" /></Col>
              </Row>
            ) : (
              <Text type="secondary">
                {p?.predicciones ? `${p.predicciones} predicciones en el período; ninguna tiene todavía el peso real del recién nacido.`
                  : 'No hubo predicciones de peso en el período.'}
                {' '}El error real se mide solo cuando nace el bebé.
              </Text>
            )}
          </Card>
          <CatalogoModelos modelos={datos.modelos} />
        </>
      )}
    </Spin>
  );
};

export default ReporteIA;
