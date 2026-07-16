import React from 'react';
import { Card, Row, Col, Divider, Table } from 'antd';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ComposedChart, Area
} from 'recharts';
import {
  ResultadoRiesgo, RegistroRiesgo,
  formatMoMTooltip, renderRiesgoLabel, formatRiesgoTooltip, formatRatioTooltip,
  getDataBiomarcadores, getDataDistribucionRiesgo, getDataEvolucionTemporal, getDataRatioSfltPlgf,
} from '../riesgoPreeclampsiaUtils';
import { columnsRiesgoPE } from './columnsRiesgoPE';

interface RiesgoPEGraficasProps {
  resultado: ResultadoRiesgo;
  historial: RegistroRiesgo[];
}

const RiesgoPEGraficas: React.FC<RiesgoPEGraficasProps> = ({ resultado, historial }) => (
  <>
    <Divider>📊 Análisis de Biomarcadores (MoM)</Divider>
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card title="Biomarcadores MoM vs Referencia">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getDataBiomarcadores(resultado)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={formatMoMTooltip} />
              <Legend />
              <Bar dataKey="referencia" fill="#8884d8" name="Referencia (MoM=1.0)" />
              <Bar dataKey="mom" fill="#82ca9d" name="MoM Actual">
                {getDataBiomarcadores(resultado).map((entry) => (
                  <Cell key={`cell-${entry.name}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ marginTop: 16, fontSize: 12, color: '#666' }}>
            <p><strong>MoM (Multiple of Median):</strong> Ratio del valor observado respecto a la mediana poblacional para esa edad gestacional.</p>
            <p>• PlGF {'<'}0.7 MoM: Factor de riesgo significativo</p>
            <p>• UtA-PI {'>'}1.5 MoM: Resistencia placentaria elevada</p>
          </div>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Distribución del Riesgo">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={getDataDistribucionRiesgo(resultado)}
                label={renderRiesgoLabel}
                outerRadius={100}
                dataKey="value"
              >
                {getDataDistribucionRiesgo(resultado).map((entry) => (
                  <Cell key={`cell-${entry.name}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={formatRiesgoTooltip} />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ marginTop: 16, fontSize: 12, color: '#666' }}>
            <p><strong>PE Precoz:</strong> Preeclampsia antes de las 34 semanas (más severa)</p>
            <p><strong>PE Tardía:</strong> Preeclampsia después de las 34 semanas</p>
          </div>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Ratio sFlt-1/PlGF (Verlohren Rule)">
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={getDataRatioSfltPlgf(resultado)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="semana" />
              <YAxis />
              <Tooltip formatter={formatRatioTooltip} />
              <Legend />
              <Area type="monotone" dataKey="limite_pe" fill="#f5222d20" stroke="#f5222d" name="Umbral PE (>85)" />
              <Area type="monotone" dataKey="limite_normal" fill="#52c41a20" stroke="#52c41a" name="Límite Normal (38)" />
              <Line type="monotone" dataKey="ratio" stroke="#1890ff" strokeWidth={3} name="Ratio Actual" dot={{ r: 5 }} />
            </ComposedChart>
          </ResponsiveContainer>
          <div style={{ marginTop: 16, fontSize: 12, color: '#666' }}>
            <p><strong>Verlohren Rule:</strong></p>
            <p>• Ratio {'<'}38: Riesgo muy bajo de PE en próxima semana</p>
            <p>• Ratio 38-85: Zona intermedia, vigilancia</p>
            <p>• Ratio {'>'}85: Alto riesgo de PE, considerar finalización</p>
          </div>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        {historial.length > 1 && (
          <Card title="Evolución Temporal del Riesgo">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={getDataEvolucionTemporal(historial)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="evaluacion" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="riesgo_precoz" stroke="#f5222d" strokeWidth={2} name="Riesgo Precoz (%)" dot={{ r: 4 }} />
                <Line yAxisId="left" type="monotone" dataKey="riesgo_tardia" stroke="#fa8c16" strokeWidth={2} name="Riesgo Tardía (%)" dot={{ r: 4 }} />
                <Line yAxisId="right" type="monotone" dataKey="plgf_mom" stroke="#1890ff" strokeWidth={2} name="PlGF MoM" dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        )}
      </Col>
    </Row>

    <Divider>📋 Historial de Evaluaciones</Divider>

    <Card>
      <Table
        dataSource={historial}
        columns={columnsRiesgoPE}
        pagination={{ pageSize: 5 }}
        rowKey={(record) => record.fecha}
        size="small"
      />
    </Card>

    <Divider>📚 Información Clínica</Divider>

    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card title="Modelo FMF Bayesiano" size="small">
          <p><strong>Fundamento:</strong> El modelo de la Fetal Medicine Foundation combina factores maternos, biomarcadores séricos y ecográficos mediante likelihood ratios para estimar el riesgo individualizado.</p>
          <p><strong>Biomarcadores clave:</strong></p>
          <ul style={{ fontSize: 12 }}>
            <li><strong>PlGF:</strong> Factor de crecimiento placentario. Bajo en PE por disfunción placentaria.</li>
            <li><strong>sFlt-1:</strong> Receptor soluble antiangiogénico. Elevado en PE.</li>
            <li><strong>PAPP-A:</strong> Proteína plasmática A asociada al embarazo. Baja en PE precoz.</li>
            <li><strong>MAP:</strong> Presión arterial media. Elevada indica riesgo cardiovascular.</li>
            <li><strong>UtA-PI:</strong> Índice de pulsatilidad de arterias uterinas. Alto indica resistencia placentaria.</li>
          </ul>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Profilaxis y Manejo" size="small">
          <p><strong>Aspirina (AAS):</strong></p>
          <ul style={{ fontSize: 12 }}>
            <li>Dosis: 150mg/día VO nocturna</li>
            <li>Inicio: 11-14 semanas (idealmente antes de 16 sem)</li>
            <li>Duración: Hasta 36 semanas</li>
            <li>Eficacia: Reduce PE precoz en 62% (ASPRE trial)</li>
          </ul>
          <p><strong>Calcio:</strong></p>
          <ul style={{ fontSize: 12 }}>
            <li>Dosis: 1.5-2g/día si ingesta dietética {'<'}600mg/día</li>
            <li>Eficacia: Reduce PE en 55% en mujeres con baja ingesta</li>
          </ul>
          <p><strong>Seguimiento:</strong></p>
          <ul style={{ fontSize: 12 }}>
            <li>Alto riesgo: Control cada 2-3 semanas</li>
            <li>Riesgo intermedio: Control cada 3-4 semanas</li>
            <li>Bajo riesgo: Seguimiento prenatal estándar</li>
          </ul>
        </Card>
      </Col>
    </Row>
  </>
);

export default RiesgoPEGraficas;
