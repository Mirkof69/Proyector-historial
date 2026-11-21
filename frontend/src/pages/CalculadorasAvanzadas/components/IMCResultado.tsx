import React from 'react';
import { Card, Row, Col, Statistic, Alert, Typography, Space, Tag } from 'antd';
import { HeartOutlined, LineChartOutlined, RiseOutlined } from '@ant-design/icons';
import { DatosPaciente, ResultadoIMC } from '../imcGananciaUtils';
import { tagEstado } from '../tonoEstado';

const { Text } = Typography;

interface IMCResultadoProps {
  resultado: ResultadoIMC;
  values: DatosPaciente;
}

const IMCResultado: React.FC<IMCResultadoProps> = ({ resultado, values }) => (
  <Space direction="vertical" size="large" className="calc-pila">
    {/* Estadísticas principales */}
    <Row gutter={[16, 16]}>
      <Col xs={12} sm={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="IMC Pregestacional"
            value={resultado.imc_pregestacional.toFixed(1)}
            suffix="kg/m²"
            valueStyle={{ color: resultado.color_imc }}
          />
          <Tag color={tagEstado(resultado.color_imc)} className="calc-nota-cifra">
            {resultado.clasificacion_imc}
          </Tag>
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="Ganancia Actual"
            value={resultado.ganancia_actual.toFixed(1)}
            suffix="kg"
            prefix={resultado.ganancia_actual >= 0 ? <RiseOutlined /> : ''}
            valueStyle={{ color: resultado.ganancia_actual >= 0 ? 'var(--color-exito)' : 'var(--color-peligro)' }}
          />
          <Text type="secondary" className="calc-nota-cifra">
            {values.semanas_gestacion} semanas
          </Text>
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="Rango Recomendado"
            value={`${resultado.ganancia_recomendada_min}-${resultado.ganancia_recomendada_max}`}
            suffix="kg"
          />
          <Text type="secondary" className="calc-nota-cifra">
            Total embarazo
          </Text>
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="Percentil Ganancia"
            value={`P${resultado.percentil_ganancia}`}
            prefix={<LineChartOutlined />}
          />
          <Text type="secondary" className="calc-nota-cifra">
            Curva Atalah
          </Text>
        </Card>
      </Col>
    </Row>

    {/* Estado nutricional */}
    <Card>
      <Alert
        message={resultado.estado_nutricional}
        description={
          <div>
            <Text strong>Ganancia ideal semanal: </Text>
            <Text>{resultado.ganancia_ideal_semana.toFixed(2)} kg/semana</Text>
            <br />
            <Text strong>Ganancia esperada a {values.semanas_gestacion} semanas: </Text>
            <Text>{resultado.ganancia_total_esperada.toFixed(1)} kg</Text>
          </div>
        }
        type={resultado.alertas.length > 0 ? 'warning' : 'success'}
        showIcon
        className="calc-bloque"
      />

      {resultado.alertas.length > 0 && (
        <Alert
          message="Alertas Clínicas"
          description={
            <ul className="calc-lista">
              {resultado.alertas.map((alerta) => (
                <li key={`alerta-${alerta}`}>{alerta}</li>
              ))}
            </ul>
          }
          type="error"
          showIcon
          className="calc-bloque"
        />
      )}

      <div>
        <Text strong className="calc-subtitulo">
          <HeartOutlined />
          Recomendaciones Clínicas:
        </Text>
        <ul className="calc-lista">
          {resultado.recomendaciones.map((rec) => (
            <li key={`rec-${rec}`}>
              {rec}
            </li>
          ))}
        </ul>
      </div>
    </Card>
  </Space>
);

export default IMCResultado;
