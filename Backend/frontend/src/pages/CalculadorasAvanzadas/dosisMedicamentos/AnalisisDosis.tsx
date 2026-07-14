import React from 'react';
import { Card, Row, Col, Divider, Table, Tag, Typography } from 'antd';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line
} from 'recharts';
import {
  ResultadoDosis, RegistroDosis, renderAlertasLabel,
  getDataDosisRango, getDataAlertas, getDataFuncionRenal, getDataHistorico,
} from './dosisMedicamentosUtils';

const { Text } = Typography;

const columnas = [
  { title: 'Fecha', dataIndex: 'fecha', key: 'fecha', width: 150 },
  { title: 'Medicamento', dataIndex: 'medicamento', key: 'medicamento' },
  {
    title: 'Dosis',
    key: 'dosis',
    render: (record: RegistroDosis) => `${record.dosis_calculada} ${record.unidad}`
  },
  { title: 'Vía', dataIndex: 'via', key: 'via' },
  { title: 'CLCr', dataIndex: 'clcr', key: 'clcr', render: (val: number) => `${val.toFixed(1)} mL/min` },
  {
    title: 'FDA',
    dataIndex: 'categoria_fda',
    key: 'categoria_fda',
    render: (val: string) => {
      let color = 'green';
      if (val === 'X' || val === 'D') color = 'red';
      else if (val === 'C') color = 'orange';
      return <Tag color={color}>{val}</Tag>;
    }
  }
];

interface AnalisisDosisProps {
  resultado: ResultadoDosis;
  historial: RegistroDosis[];
  tooltipFormatter: (value: any) => string;
}

const AnalisisDosis: React.FC<AnalisisDosisProps> = ({ resultado, historial, tooltipFormatter }) => (
  <>
    <Divider>📊 Análisis de Dosis y Seguridad</Divider>
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card title="Rango de Dosis Terapéutica">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getDataDosisRango(resultado)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="categoria" type="category" width={120} />
              <Tooltip formatter={tooltipFormatter} />
              <Legend />
              <Bar dataKey="valor" name={`Dosis (${resultado.unidad})`}>
                {getDataDosisRango(resultado).map((entry) => (
                  <Cell key={`cell-${entry.categoria}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Alertas de Seguridad">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={getDataAlertas(resultado)} label={renderAlertasLabel} outerRadius={100} dataKey="cantidad">
                {getDataAlertas(resultado).map((entry) => (
                  <Cell key={`cell-${entry.tipo}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Función Renal (Cockcroft-Gault)">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getDataFuncionRenal(resultado)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="etapa" />
              <YAxis label={{ value: 'CLCr (mL/min)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="min" fill="#e0e0e0" name="Rango mínimo" />
              <Bar dataKey="max" fill="#bdbdbd" name="Rango máximo" />
              <Bar dataKey="actual" fill="#1890ff" name="CLCr Actual" />
            </BarChart>
          </ResponsiveContainer>
          <div style={{ marginTop: 12, fontSize: 12, color: '#666' }}>
            <p><strong>CLCr actual:</strong> {resultado.clcr.toFixed(1)} mL/min</p>
            <p>Normal: ≥90 | Leve: 60-89 | Moderada: 30-59 | Severa: 15-29 | Terminal: {'<'}15</p>
          </div>
        </Card>
      </Col>

      {historial.length > 1 && (
        <Col xs={24} lg={12}>
          <Card title="Tendencia de Dosis Calculadas">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={getDataHistorico(historial)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="numero" label={{ value: 'Cálculo #', position: 'insideBottom', offset: -5 }} />
                <YAxis yAxisId="left" label={{ value: 'Dosis', angle: -90, position: 'insideLeft' }} />
                <YAxis yAxisId="right" orientation="right" label={{ value: 'CLCr', angle: 90, position: 'insideRight' }} />
                <Tooltip />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="dosis" stroke="#1890ff" strokeWidth={2} name="Dosis" dot={{ r: 5 }} />
                <Line yAxisId="right" type="monotone" dataKey="clcr" stroke="#52c41a" strokeWidth={2} name="CLCr" dot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      )}
    </Row>

    {resultado.interacciones.length > 0 && (
      <>
        <Divider>⚠️ Interacciones Medicamentosas</Divider>
        <Card>
          <ul>
            {resultado.interacciones.map((item) => (
              <li key={`interaccion-${item}`} style={{ marginBottom: 8 }}>
                <Text strong style={{ color: '#fa8c16' }}>{item}</Text>
              </li>
            ))}
          </ul>
        </Card>
      </>
    )}

    <Divider>📋 Historial de Cálculos</Divider>

    <Card>
      <Table
        dataSource={historial}
        columns={columnas}
        pagination={{ pageSize: 5 }}
        rowKey={(record) => record.fecha}
        size="small"
        scroll={{ x: true }}
      />
    </Card>

    <Divider>📚 Información Clínica</Divider>

    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card title="Categorías FDA en Embarazo" size="small">
          <p style={{ fontSize: 12 }}><strong>A:</strong> Estudios controlados sin riesgo</p>
          <p style={{ fontSize: 12 }}><strong>B:</strong> Sin evidencia de riesgo en humanos (ej: Penicilinas, Insulina)</p>
          <p style={{ fontSize: 12 }}><strong>C:</strong> Riesgo no descartado (mayoría de medicamentos)</p>
          <p style={{ fontSize: 12 }}><strong>D:</strong> Evidencia positiva de riesgo, usar solo si beneficio supera riesgo</p>
          <p style={{ fontSize: 12 }}><strong>X:</strong> Contraindicado en embarazo</p>
          <p style={{ fontSize: '12px', marginTop: 8, color: '#666' }}>Nota: FDA eliminó este sistema en 2015, pero sigue siendo referencia clínica</p>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Ajuste por Función Renal" size="small">
          <p style={{ fontSize: 12 }}><strong>CLCr (Cockcroft-Gault):</strong></p>
          <p style={{ fontSize: '12px' }}>CLCr = [(140 - edad) × peso × 0.85] / (72 × Cr)</p>
          <p style={{ fontSize: 12, marginTop: 8 }}><strong>Guía de ajuste:</strong></p>
          <ul style={{ fontSize: '12px' }}>
            <li>CLCr {'>'}90: Sin ajuste</li>
            <li>CLCr 60-89: Monitoreo</li>
            <li>CLCr 30-59: Reducir dosis o aumentar intervalo</li>
            <li>CLCr 15-29: Reducción significativa</li>
            <li>CLCr {'<'}15: Considerar hemodiálisis o medicamento alternativo</li>
          </ul>
        </Card>
      </Col>

      <Col xs={24}>
        <Card title="Precauciones Generales en Obstetricia" size="small">
          <Row gutter={16}>
            <Col span={8}>
              <p style={{ fontSize: 12 }}><strong>Antes de prescribir:</strong></p>
              <ul style={{ fontSize: '12px' }}>
                <li>Confirmar edad gestacional</li>
                <li>Verificar función renal</li>
                <li>Revisar alergias</li>
                <li>Considerar interacciones</li>
              </ul>
            </Col>
            <Col span={8}>
              <p style={{ fontSize: 12 }}><strong>Monitoreo:</strong></p>
              <ul style={{ fontSize: '12px' }}>
                <li>Signos vitales maternos</li>
                <li>Frecuencia cardíaca fetal</li>
                <li>Contractilidad uterina</li>
                <li>Efectos adversos</li>
              </ul>
            </Col>
            <Col span={8}>
              <p style={{ fontSize: 12 }}><strong>Documentación:</strong></p>
              <ul style={{ fontSize: '12px' }}>
                <li>Indicación precisa</li>
                <li>Dosis, vía y hora</li>
                <li>Respuesta clínica</li>
                <li>Efectos adversos</li>
              </ul>
            </Col>
          </Row>
        </Card>
      </Col>
    </Row>
  </>
);

export default AnalisisDosis;
