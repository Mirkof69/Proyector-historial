import React, { Suspense } from 'react';
import { Card, Row, Col, Divider, Table, Spin } from 'antd';
import { BarChartOutlined, HistoryOutlined, ReadOutlined } from '@ant-design/icons';
import {
  DatosBiometria, ResultadoCrecimiento, RegistroCrecimiento,
  PROPORCIONES_DOMAIN, formatPesoTooltip, formatRatioTooltip, renderPercentilLabel, formatPercentilTooltip,
  getDataBiometria, getDataCurvasCrecimiento, getDataDistribucionPercentiles, getDataProporcionesFetales, getDataEvolucion,
} from '../crecimientoFetalUtils';
import { columnsCrecimiento } from './columnsCrecimiento';
// Recharts se importa directo: envuelto en lazy() pieza por pieza, el gráfico no
// reconocía a sus hijos (Pie, Bar, Line…) y se dibujaba vacío.
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Area, ReferenceLine } from 'recharts';

interface CrecimientoGraficasProps {
  resultado: ResultadoCrecimiento;
  datosBiometria: DatosBiometria;
  historial: RegistroCrecimiento[];
}

const CrecimientoGraficas: React.FC<CrecimientoGraficasProps> = ({ resultado, datosBiometria, historial }) => (
  <>
    <Divider><span className="calc-titulo-seccion"><BarChartOutlined /> Curvas de Crecimiento Fetal</span></Divider>

    <Row gutter={[16, 16]}>
      <Col xs={24} lg={16}>
        <Card title="Curva de Peso Fetal Estimado (EFW) - Percentiles Intergrowth-21st">
          <Suspense fallback={<div className="calc-cargando"><Spin /></div>}>
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart data={getDataCurvasCrecimiento(datosBiometria, resultado)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="semana" label={{ value: 'Semanas de Gestación', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Peso (g)', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={formatPesoTooltip} />
                <Legend />
                <Area type="monotone" dataKey="p3" fill="var(--color-peligro)" fillOpacity={0.08} stroke="var(--color-peligro)" strokeWidth={1} name="p3" />
                <Area type="monotone" dataKey="p10" fill="var(--color-aviso)" fillOpacity={0.08} stroke="var(--color-aviso)" strokeWidth={1} name="p10" />
                <Line type="monotone" dataKey="p50" stroke="var(--grafico-2)" strokeWidth={3} name="p50 (Mediana)" dot={false} />
                <Line type="monotone" dataKey="p90" stroke="var(--color-aviso)" strokeWidth={1} name="p90" dot={false} />
                <Line type="monotone" dataKey="p97" stroke="var(--color-peligro)" strokeWidth={1} name="p97" dot={false} />
                <Line type="monotone" dataKey="actual" stroke="var(--grafico-1)" strokeWidth={4} name="EFW Actual" dot={{ r: 8, fill: 'var(--grafico-1)' }} />
              </ComposedChart>
            </ResponsiveContainer>
          </Suspense>
          <div className="calc-nota">
            <p><strong>Interpretación de percentiles:</strong></p>
            <p>• {'<'}p3: RCIU severo | p3-p10: PEG | p10-p90: Normal | p90-p97: GEG | {'>'}p97: Macrosomía</p>
          </div>
        </Card>
      </Col>

      <Col xs={24} lg={8}>
        <Card title="Valores Biométricos vs Percentiles">
          <Suspense fallback={<div className="calc-cargando"><Spin /></div>}>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={getDataBiometria(datosBiometria, resultado)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="parametro" />
                <YAxis yAxisId="left" orientation="left" label={{ value: 'Valor (mm)', angle: -90, position: 'insideLeft' }} />
                <YAxis yAxisId="right" orientation="right" label={{ value: 'Percentil', angle: 90, position: 'insideRight' }} />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="valor" fill="var(--grafico-1)" name="Valor Medido (mm)" />
                <Bar yAxisId="right" dataKey="percentil" fill="var(--grafico-2)" name="Percentil" />
                <ReferenceLine yAxisId="right" y={50} stroke="var(--color-texto-2)" strokeDasharray="3 3" label="p50" />
              </BarChart>
            </ResponsiveContainer>
          </Suspense>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Ratios de Proporciones Fetales">
          <Suspense fallback={<div className="calc-cargando"><Spin /></div>}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getDataProporcionesFetales(datosBiometria)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={PROPORCIONES_DOMAIN} />
                <YAxis dataKey="ratio" type="category" />
                <Tooltip formatter={formatRatioTooltip} />
                <Legend />
                <Bar dataKey="valor" name="Valor Calculado">
                  {getDataProporcionesFetales(datosBiometria).map((entry) => (
                    <Cell key={`cell-${entry.ratio}`} fill={entry.color} />
                  ))}
                </Bar>
                <ReferenceLine x={1.0} stroke="var(--color-texto-2)" strokeDasharray="3 3" />
              </BarChart>
            </ResponsiveContainer>
          </Suspense>
          <div className="calc-nota">
            <p><strong>HC/AC:</strong> {'>'} 1 sugiere asimetría cefálica (RCIU tipo II)</p>
            <p><strong>FL/AC:</strong> Útil para detectar anomalías esqueléticas</p>
            <p><strong>FL/HC:</strong> Alterado en displasias y cromosomopatías</p>
          </div>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Distribución de Percentiles Biométricos">
          <Suspense fallback={<div className="calc-cargando"><Spin /></div>}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={getDataDistribucionPercentiles(resultado)}
                  label={renderPercentilLabel}
                  outerRadius={100}
                  dataKey="value"
                  nameKey="name"
                >
                  {getDataDistribucionPercentiles(resultado).map((entry, index) => {
                    const colors = ['var(--grafico-1)', 'var(--grafico-2)', 'var(--grafico-3)', 'var(--grafico-6)'];
                    return <Cell key={`cell-${entry.name}`} fill={colors[index % colors.length]} />;
                  })}
                </Pie>
                <Tooltip formatter={formatPercentilTooltip} />
              </PieChart>
            </ResponsiveContainer>
          </Suspense>
        </Card>
      </Col>

      {historial.length > 1 && (
        <Col xs={24}>
          <Card title="Evolución del Crecimiento Fetal">
            <Suspense fallback={<div className="calc-cargando"><Spin /></div>}>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={getDataEvolucion(historial)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="evaluacion" />
                  <YAxis yAxisId="left" label={{ value: 'EFW (g)', angle: -90, position: 'insideLeft' }} />
                  <YAxis yAxisId="right" orientation="right" label={{ value: 'Percentil', angle: 90, position: 'insideRight' }} />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="efw" stroke="var(--grafico-1)" strokeWidth={3} name="EFW (g)" dot={{ r: 5 }} />
                  <Line yAxisId="left" type="monotone" dataKey="p50" stroke="var(--grafico-2)" strokeWidth={2} strokeDasharray="5 5" name="p50 Esperado" dot={{ r: 4 }} />
                  <Line yAxisId="right" type="monotone" dataKey="percentil" stroke="var(--grafico-3)" strokeWidth={2} name="Percentil Actual" dot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </Suspense>
          </Card>
        </Col>
      )}
    </Row>

    <Divider><span className="calc-titulo-seccion"><HistoryOutlined /> Historial de Mediciones</span></Divider>

    <Card>
      <Table
        dataSource={historial}
        columns={columnsCrecimiento}
        pagination={{ pageSize: 5 }}
        rowKey={(record) => record.fecha}
        size="small"
        scroll={{ x: true }}
      />
    </Card>

    <Divider><span className="calc-titulo-seccion"><ReadOutlined /> Información Clínica</span></Divider>

    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card title="Fórmulas de Hadlock" size="small">
          <p><strong>Fórmulas de Estimación de Peso Fetal:</strong></p>
          <ul>
            <li><strong>Hadlock 1:</strong> Utiliza BPD, HC, AC, FL (4 parámetros) - Más completa pero requiere todas las mediciones</li>
            <li><strong>Hadlock 2:</strong> Utiliza AC, FL (2 parámetros) - Más simple, útil cuando faltan medidas cefálicas</li>
            <li><strong>Hadlock 3:</strong> Utiliza BPD, AC, FL (3 parámetros)</li>
            <li><strong>Hadlock 4:</strong> Utiliza HC, AC, FL (3 parámetros) - Recomendada por ISUOG, mejor precisión</li>
          </ul>
          <p><strong>Precisión:</strong> ±15% del peso real en el 95% de los casos. Tiende a sobreestimar en fetos pequeños y subestimar en macrosómicos.</p>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Clasificaciones Clínicas" size="small">
          <p><strong>Categorías según Percentil:</strong></p>
          <ul>
            <li><strong>RCIU ({'<'}p3):</strong> Restricción del crecimiento intrauterino. Requiere Doppler y evaluación urgente.</li>
            <li><strong>PEG (p3-p10):</strong> Pequeño para edad gestacional. Puede ser constitucional o patológico.</li>
            <li><strong>NORMAL (p10-p90):</strong> Rango adecuado para edad gestacional.</li>
            <li><strong>GEG (p90-p97):</strong> Grande para edad gestacional. Descartar diabetes gestacional.</li>
            <li><strong>MACROSOMÍA ({'>'}p97):</strong> Riesgo aumentado de distocia de hombros y trauma obstétrico.</li>
          </ul>
          <p><strong>RCIU Tipo I:</strong> Simétrico (proporcionado) - afectación temprana</p>
          <p><strong>RCIU Tipo II:</strong> Asimétrico (desproporcionado) - afectación tardía, HC/AC {'>'}1</p>
        </Card>
      </Col>

      <Col xs={24}>
        <Card title="Estándares Intergrowth-21st" size="small">
          <p><strong>Proyecto Intergrowth-21st:</strong> Estudio multicéntrico de la OMS que generó estándares internacionales de crecimiento fetal basados en poblaciones sanas de 8 países.</p>
          <p><strong>Ventajas:</strong> Aplicables universalmente, metodología rigurosa, incluyen múltiples parámetros biométricos y peso estimado.</p>
          <p><strong>Uso clínico:</strong> Identificación temprana de RCIU y macrosomía, seguimiento de embarazos de alto riesgo, toma de decisiones sobre momento y vía de parto.</p>
        </Card>
      </Col>
    </Row>
  </>
);

export default CrecimientoGraficas;
