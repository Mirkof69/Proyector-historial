import React, { useCallback, useEffect, useState } from 'react';
import { Alert, Button, Card, Col, Empty, Row, Segmented, Spin, Statistic, Table, Typography } from 'antd';
import { FileExcelOutlined, ReloadOutlined } from '@ant-design/icons';
import {
  Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import api from '../../services/api';
import { descargarArchivo } from '../../utils/descargarArchivo';
import { useRangoReportes } from './rangoReportes';

const { Text } = Typography;

/** Paleta categórica validada (colorblind-safe; ver skill dataviz). Orden fijo, nunca ciclado. */
// Series del tema (tokens.css --grafico-*): cambian solas con el tema.
export const SERIE = { azul: 'var(--grafico-2)', naranja: 'var(--grafico-5)', aqua: 'var(--grafico-4)', amarillo: 'var(--grafico-3)' };
const GRILLA = 'var(--color-borde-suave)';

interface Datos {
  desde: string; hasta: string;
  totales: { partos: number; recien_nacidos: number; cesareas: number; vaginales: number };
  tasas: Record<string, number | null>;
  nacimientos_por_mes: { mes: string; partos: number; cesareas: number }[];
  via_parto: { via: string; total: number }[];
  peso_al_nacer: { categoria: string; total: number }[];
  complicaciones: { tipo: string; total: number }[];
  estado_al_nacer: { estado: string; total: number }[];
}

const pct = (v: number | null | undefined) => (v === null || v === undefined ? '—' : `${v} %`);
const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
const mesCorto = (m: string) => `${MESES[Number(m.slice(5, 7)) - 1]} ${m.slice(2, 4)}`;

/** Barras horizontales de una sola serie, con la cifra escrita al final de cada barra. */
const BarrasHorizontales: React.FC<{ datos: { nombre: string; total: number }[]; color: string; titulo: string }> = ({
  datos, color, titulo,
}) => (
  datos.length === 0 ? <Empty description={`Sin ${titulo.toLowerCase()} en el período`} /> : (
    <div className="reportes-ancho" style={{ height: Math.max(160, datos.length * 44) }} role="img" aria-label={titulo}>
      <ResponsiveContainer>
        <BarChart data={datos} layout="vertical" margin={{ left: 8, right: 40 }} barCategoryGap={8}>
          <CartesianGrid horizontal={false} stroke={GRILLA} />
          <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
          <YAxis type="category" dataKey="nombre" width={170} tick={{ fontSize: 12 }} />
          <Tooltip cursor={{ fill: 'var(--color-hover)' }} />
          <Bar dataKey="total" name="Total" fill={color} radius={[0, 4, 4, 0]} maxBarSize={24}>
            <LabelList dataKey="total" position="right" className="reportes-etiqueta-grafica" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
);

/**
 * Natalidad y morbilidad del período elegido arriba: partos, vía de parto,
 * peso al nacer, prematuridad, Apgar y complicaciones. Todas las cifras salen
 * de los partos registrados (GET /api/reportes/natalidad/); si el período no
 * tiene partos, lo dice en vez de dibujar ceros como si fueran datos.
 */
const NatalidadMorbilidad: React.FC = () => {
  const rango = useRangoReportes();
  const [datos, setDatos] = useState<Datos | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [vista, setVista] = useState<'graficos' | 'tabla'>('graficos');

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      setDatos((await api.get('/reportes/natalidad/', { params: rango?.params })).data);
    } catch (e: any) {
      setError(e?.response?.data?.error || 'No se pudo cargar el reporte de natalidad.');
    } finally {
      setCargando(false);
    }
  }, [rango?.params.desde, rango?.params.hasta]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { cargar(); }, [cargar]);

  const exportar = () => descargarArchivo(
    `/reportes/natalidad/excel/?desde=${datos?.desde ?? ''}&hasta=${datos?.hasta ?? ''}`,
    `natalidad_${datos?.desde}_${datos?.hasta}.xlsx`,
  );

  const porMes = (datos?.nacimientos_por_mes ?? []).map((m) => ({
    mes: mesCorto(m.mes), Vaginales: m.partos - m.cesareas, 'Cesáreas': m.cesareas,
  }));

  return (
    <Spin spinning={cargando}>
      <Row justify="space-between" align="middle" gutter={[8, 8]} className="no-print reportes-separado">
        <Col><Segmented value={vista} onChange={(v) => setVista(v as 'graficos' | 'tabla')}
          options={[{ value: 'graficos', label: 'Gráficos' }, { value: 'tabla', label: 'Tabla' }]} /></Col>
        <Col>
          <Button icon={<ReloadOutlined />} onClick={cargar} className="reportes-boton-separado">Actualizar</Button>
          <Button icon={<FileExcelOutlined />} onClick={exportar} disabled={!datos?.totales.partos}>Excel</Button>
        </Col>
      </Row>
      {error && <Alert type="error" showIcon message={error} />}
      {datos && (datos.totales.partos === 0 ? (
        <Empty description="No hay partos registrados en el período elegido." />
      ) : (
        <>
          <Row gutter={[12, 12]} className="reportes-separado reportes-cifras">
            {[
              ['Partos', datos.totales.partos], ['Recién nacidos', datos.totales.recien_nacidos],
              ['Cesáreas', pct(datos.tasas.cesarea_pct)], ['Bajo peso al nacer', pct(datos.tasas.bajo_peso_pct)],
              ['Pretérmino (< 37 s)', pct(datos.tasas.pretermino_pct)], ['Apgar 5 min < 7', pct(datos.tasas.apgar5_menor_7_pct)],
              ['Hemorragia posparto', pct(datos.tasas.hemorragia_posparto_pct)],
              ['Partos con complicación', pct(datos.tasas.partos_con_complicacion_pct)],
            ].map(([titulo, valor]) => (
              <Col xs={12} md={6} key={String(titulo)}>
                <Card size="small"><Statistic title={titulo} value={valor as string | number} /></Card>
              </Col>
            ))}
          </Row>
          {vista === 'tabla' ? (
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Table size="small" pagination={false} rowKey="mes" title={() => <Text strong>Partos por mes</Text>}
                  dataSource={datos.nacimientos_por_mes}
                  columns={[{ title: 'Mes', dataIndex: 'mes' }, { title: 'Partos', dataIndex: 'partos' },
                    { title: 'Cesáreas', dataIndex: 'cesareas' }]} />
              </Col>
              <Col xs={24} lg={12}>
                <Table size="small" pagination={false} rowKey="via" title={() => <Text strong>Vía de parto</Text>}
                  dataSource={datos.via_parto} columns={[{ title: 'Vía', dataIndex: 'via' }, { title: 'Total', dataIndex: 'total' }]} />
                <Table size="small" pagination={false} rowKey="categoria" className="reportes-arriba"
                  title={() => <Text strong>Peso al nacer</Text>} dataSource={datos.peso_al_nacer}
                  columns={[{ title: 'Categoría', dataIndex: 'categoria' }, { title: 'Recién nacidos', dataIndex: 'total' }]} />
                <Table size="small" pagination={false} rowKey="tipo" className="reportes-arriba"
                  title={() => <Text strong>Complicaciones</Text>} dataSource={datos.complicaciones}
                  locale={{ emptyText: 'Sin complicaciones registradas' }}
                  columns={[{ title: 'Tipo', dataIndex: 'tipo' }, { title: 'Total', dataIndex: 'total' }]} />
              </Col>
            </Row>
          ) : (
            <Row gutter={[16, 16]}>
              <Col xs={24}>
                <Card size="small" title="Partos por mes, según la vía">
                  <div className="reportes-grafica-300" role="img" aria-label="Partos por mes, vaginales y cesáreas">
                    <ResponsiveContainer>
                      <BarChart data={porMes} margin={{ top: 16, right: 16, left: 0, bottom: 4 }} barCategoryGap="20%">
                        <CartesianGrid vertical={false} stroke={GRILLA} />
                        <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                        <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                        <Tooltip cursor={{ fill: 'var(--color-hover)' }} />
                        <Legend />
                        <Bar dataKey="Vaginales" stackId="via" fill={SERIE.azul} stroke="var(--color-superficie)" strokeWidth={2} maxBarSize={36} />
                        <Bar dataKey="Cesáreas" stackId="via" fill={SERIE.naranja} stroke="var(--color-superficie)" strokeWidth={2}
                          radius={[4, 4, 0, 0]} maxBarSize={36} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card size="small" title="Peso al nacer">
                  <BarrasHorizontales titulo="Peso al nacer" color={SERIE.azul}
                    datos={datos.peso_al_nacer.map((p) => ({ nombre: p.categoria, total: p.total }))} />
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card size="small" title="Complicaciones del parto">
                  <BarrasHorizontales titulo="Complicaciones" color={SERIE.azul}
                    datos={datos.complicaciones.map((c) => ({ nombre: c.tipo, total: c.total }))} />
                </Card>
              </Col>
            </Row>
          )}
        </>
      ))}
    </Spin>
  );
};

export default NatalidadMorbilidad;
