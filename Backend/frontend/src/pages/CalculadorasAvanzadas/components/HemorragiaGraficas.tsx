import React from 'react';
import { Card, Row, Col, Divider, Table } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ComposedChart, Area
} from 'recharts';
import {
  ResultadoHemorragia, RegistroHemorragia,
  renderVolemiaLabel, HISTORIAL_TICK, SHOCK_INDEX_LABEL, PERDIDA_LABEL,
  getDataCausas4T, getDataDistribucion, getDataSignosVitales, getDataPTM,
} from '../hemorragiaObstetricaUtils';
import { columnasHistorialHemorragia } from './columnsHemorragia';

interface HemorragiaGraficasProps {
  resultado: ResultadoHemorragia;
  form: FormInstance;
  historial: RegistroHemorragia[];
}

const HemorragiaGraficas: React.FC<HemorragiaGraficasProps> = ({ resultado, form, historial }) => (
  <>
    <Divider>
      <LineChartOutlined /> Análisis Gráfico
    </Divider>
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card title="Distribución de Causas HPP (4 T's)">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getDataCausas4T()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="causa" />
              <YAxis label={{ value: 'Frecuencia (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="porcentaje" name="Frecuencia (%)">
                {getDataCausas4T().map((entry: any) => (
                  <Cell key={`cell-${entry.causa}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Pérdida de Volemia">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={getDataDistribucion(resultado)}
                label={renderVolemiaLabel}
                outerRadius={100}
                dataKey="value"
              >
                {getDataDistribucion(resultado).map((entry: any) => (
                  <Cell key={`cell-${entry.name}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="Signos Vitales vs Valores Normales">
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={getDataSignosVitales(form.getFieldsValue())}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="parametro" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="valor" fill="#ff4d4f" name="Valor Actual" />
              <Line type="monotone" dataKey="referencia" stroke="#52c41a" name="Referencia" strokeWidth={2} />
              <Area type="monotone" dataKey="normal_max" fill="#95de64" stroke="#95de64" fillOpacity={0.3} name="Rango Normal" />
            </ComposedChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      {resultado && resultado.requiere_ptm && (
        <Col xs={24} lg={12}>
          <Card title="Protocolo PTM - Componentes">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getDataPTM(resultado)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="componente" />
                <YAxis label={{ value: 'Unidades', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="unidades" name="Unidades">
                  {getDataPTM(resultado).map((entry: any) => (
                    <Cell key={`cell-${entry.componente}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      )}
    </Row>

    {historial.length > 0 && (
      <Card title="Historial de Evaluaciones" style={{ marginTop: 16 }}>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={[...historial].reverse()}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="fecha" tick={HISTORIAL_TICK} />
            <YAxis yAxisId="left" label={SHOCK_INDEX_LABEL} />
            <YAxis yAxisId="right" orientation="right" label={PERDIDA_LABEL} />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="shock_index" stroke="#ff4d4f" name="Shock Index" strokeWidth={2} />
            <Line yAxisId="right" type="monotone" dataKey="perdida_ml" stroke="#1890ff" name="Pérdida (ml)" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>

        <Table
          columns={columnasHistorialHemorragia}
          dataSource={historial}
          rowKey={(record) => record.fecha}
          pagination={{ pageSize: 5 }}
          size="small"
          style={{ marginTop: 16 }}
        />
      </Card>
    )}
  </>
);

export default HemorragiaGraficas;
