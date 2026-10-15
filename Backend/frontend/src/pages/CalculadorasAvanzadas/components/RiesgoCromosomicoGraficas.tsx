import React from 'react';
import { Card, Row, Col, Divider, Table } from 'antd';
import { BarChartOutlined, HistoryOutlined, ReadOutlined } from '@ant-design/icons';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Area, AreaChart
} from 'recharts';
import {
  ResultadoRiesgo, RegistroScreening,
  formatMoMTooltip, renderRiesgoLabel, formatRiesgoTooltip,
  getDataEdadVsRiesgo, getDataBiomarcadores, getDataDistribucionRiesgo, getDataEvolucion,
} from '../riesgoCromosomicoUtils';
import { columnsRiesgoCromosomico } from './columnsRiesgoCromosomico';

interface RiesgoCromosomicoGraficasProps {
  resultado: ResultadoRiesgo;
  historial: RegistroScreening[];
}

const RiesgoCromosomicoGraficas: React.FC<RiesgoCromosomicoGraficasProps> = ({ resultado, historial }) => (
  <>
    <Divider><span className="calc-titulo-seccion"><BarChartOutlined /> Análisis de Biomarcadores y Riesgo</span></Divider>
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card title="Biomarcadores MoM (Múltiplos de la Mediana)">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getDataBiomarcadores(resultado)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={formatMoMTooltip} />
              <Legend />
              <Bar dataKey="referencia" fill="var(--color-borde-fuerte)" name="Referencia (MoM=1.0)" />
              <Bar dataKey="mom" fill="var(--grafico-1)" name="MoM Actual">
                {getDataBiomarcadores(resultado).map((entry: any) => (
                  <Cell key={`cell-${entry.name}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="calc-nota">
            <p><strong>NT elevado (MoM {'>'}2.0):</strong> Aumenta riesgo de aneuploidías</p>
            <p><strong>PAPP-A bajo (MoM {'<'}0.5):</strong> Marcador de riesgo para T21</p>
            <p><strong>βhCG alto (MoM {'>'}2.0):</strong> Asociado a T21</p>
          </div>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Distribución del Riesgo de Aneuploidías">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={getDataDistribucionRiesgo(resultado)}
                label={renderRiesgoLabel}
                outerRadius={100}
                dataKey="value"
              >
                {getDataDistribucionRiesgo(resultado).map((entry: any) => (
                  <Cell key={`cell-${entry.name}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={formatRiesgoTooltip} />
            </PieChart>
          </ResponsiveContainer>
          <div className="calc-nota">
            <p><strong>Riesgo Alto ({'>'}1:250):</strong> Se sugiere asesoramiento genético o prueba diagnóstica invasiva (amniocentesis/CVS)</p>
            <p><strong>Riesgo Intermedio (1:250 a 1:1000):</strong> Considerar ADN fetal libre en sangre materna (NIPT)</p>
            <p><strong>Riesgo Bajo ({'<'}1:1000):</strong> Control de rutina</p>
          </div>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Riesgo de T21 Según Edad Materna">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={getDataEdadVsRiesgo()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="edad" />
              <YAxis label={{ value: 'Riesgo (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="riesgo_basal" stroke="var(--color-peligro)" fill="var(--color-peligro)" fillOpacity={0.15} name="Riesgo Basal T21" />
              <Line type="monotone" dataKey="punto_corte" stroke="var(--color-texto-2)" strokeDasharray="5 5" name="Límite de Alto Riesgo (1:250)" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      {historial.length > 0 && (
        <Col xs={24} lg={12}>
          <Card title="Tendencia de Riesgo (Evaluaciones Previas)">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={getDataEvolucion(historial)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="evaluacion" />
                <YAxis label={{ value: 'Riesgo (%)', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="riesgo_t21_pct" stroke="var(--grafico-5)" name="T21 (Down)" strokeWidth={2} />
                <Line type="monotone" dataKey="riesgo_t18_pct" stroke="var(--grafico-3)" name="T18 (Edwards)" strokeWidth={2} />
                <Line type="monotone" dataKey="riesgo_t13_pct" stroke="var(--grafico-6)" name="T13 (Patau)" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      )}
    </Row>

    <Divider><span className="calc-titulo-seccion"><HistoryOutlined /> Historial de Screenings</span></Divider>

    <Card>
      <Table
        dataSource={historial}
        columns={columnsRiesgoCromosomico}
        pagination={{ pageSize: 5 }}
        rowKey={(record) => record.fecha}
        size="small"
        scroll={{ x: true }}
      />
    </Card>

    <Divider><span className="calc-titulo-seccion"><ReadOutlined /> Información Clínica</span></Divider>

    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card title="Screening Combinado Primer Trimestre" size="small">
          <p><strong>Fundamento:</strong> Combina edad materna, NT ecográfico y biomarcadores séricos (PAPP-A y βhCG libre) mediante modelo Bayesiano (Fetal Medicine Foundation).</p>
          <p><strong>Ventana temporal:</strong> 11+0 a 13+6 semanas de gestación</p>
          <p><strong>Sensibilidad:</strong></p>
          <ul>
            <li>T21: 90-95% (tasa de falsos positivos 5%)</li>
            <li>T18/T13: 85-90%</li>
          </ul>
          <p><strong>Punto de corte:</strong> 1:250 al término (screening positivo)</p>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Aneuploidías Principales" size="small">
          <p><strong>Trisomía 21 (Síndrome de Down):</strong></p>
          <ul>
            <li>NT elevado, PAPP-A bajo, βhCG alto</li>
            <li>Incidencia: 1:700 nacimientos (varía con edad materna)</li>
            <li>Compatible con vida, discapacidad intelectual variable</li>
          </ul>
          <p><strong>Trisomía 18 (Síndrome de Edwards):</strong></p>
          <ul>
            <li>NT elevado, PAPP-A bajo, βhCG bajo</li>
            <li>Incidencia: 1:6000</li>
            <li>Pronóstico grave, alta mortalidad perinatal</li>
          </ul>
          <p><strong>Trisomía 13 (Síndrome de Patau):</strong></p>
          <ul>
            <li>NT elevado, biomarcadores variables</li>
            <li>Incidencia: 1:10000</li>
            <li>Pronóstico grave, alta mortalidad perinatal</li>
          </ul>
        </Card>
      </Col>

      <Col xs={24}>
        <Card title="Manejo según Resultado" size="small">
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <p><strong>Screening POSITIVO (≥1:250):</strong></p>
              <ul>
                <li>Consejo genético</li>
                <li>Oferta de estudio invasivo (amniocentesis/biopsia corial)</li>
                <li>Alternativa: NIPT como segunda línea</li>
                <li>Ecografía detallada 18-22 semanas</li>
              </ul>
            </Col>
            <Col xs={24} md={8}>
              <p><strong>Riesgo INTERMEDIO (1:250-1:1000):</strong></p>
              <ul>
                <li>Considerar NIPT</li>
                <li>Ecografía detallada</li>
                <li>Consejo genético optativo</li>
                <li>Seguimiento estrecho</li>
              </ul>
            </Col>
            <Col xs={24} md={8}>
              <p><strong>Screening NEGATIVO ({'<'}1:1000):</strong></p>
              <ul>
                <li>Seguimiento habitual</li>
                <li>Ecografía morfológica 18-22 semanas</li>
                <li>Recordar: No excluye 100% aneuploidía</li>
              </ul>
            </Col>
          </Row>
        </Card>
      </Col>
    </Row>
  </>
);

export default RiesgoCromosomicoGraficas;
