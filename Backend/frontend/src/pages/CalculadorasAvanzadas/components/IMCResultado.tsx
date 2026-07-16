import React from 'react';
import { Card, Row, Col, Statistic, Alert, Typography, Space, Tag } from 'antd';
import { HeartOutlined, LineChartOutlined, RiseOutlined } from '@ant-design/icons';
import { DatosPaciente, ResultadoIMC } from '../imcGananciaUtils';

const { Text } = Typography;

interface IMCResultadoProps {
  resultado: ResultadoIMC;
  values: DatosPaciente;
}

const IMCResultado: React.FC<IMCResultadoProps> = ({ resultado, values }) => (
  <Space direction="vertical" size="large" style={{ width: '100%' }}>
    {/* Estadísticas principales */}
    <Row gutter={16}>
      <Col xs={12} sm={6}>
        <Card variant="borderless">
          <Statistic
            title="IMC Pregestacional"
            value={resultado.imc_pregestacional.toFixed(1)}
            suffix="kg/m²"
            valueStyle={{ color: resultado.color_imc }}
          />
          <Tag color={resultado.color_imc} style={{ marginTop: 8 }}>
            {resultado.clasificacion_imc}
          </Tag>
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card variant="borderless">
          <Statistic
            title="Ganancia Actual"
            value={resultado.ganancia_actual.toFixed(1)}
            suffix="kg"
            prefix={resultado.ganancia_actual >= 0 ? <RiseOutlined /> : ''}
            valueStyle={{ color: resultado.ganancia_actual >= 0 ? '#52c41a' : '#f5222d' }}
          />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {values.semanas_gestacion} semanas
          </Text>
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card variant="borderless">
          <Statistic
            title="Rango Recomendado"
            value={`${resultado.ganancia_recomendada_min}-${resultado.ganancia_recomendada_max}`}
            suffix="kg"
            valueStyle={{ color: '#1890ff' }}
          />
          <Text type="secondary" style={{ fontSize: 12 }}>
            Total embarazo
          </Text>
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card variant="borderless">
          <Statistic
            title="Percentil Ganancia"
            value={`P${resultado.percentil_ganancia}`}
            prefix={<LineChartOutlined />}
            valueStyle={{ color: '#722ed1' }}
          />
          <Text type="secondary" style={{ fontSize: 12 }}>
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
        style={{ marginBottom: 16 }}
      />

      {resultado.alertas.length > 0 && (
        <Alert
          message="Alertas Clínicas"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              {resultado.alertas.map((alerta) => (
                <li key={`alerta-${alerta}`}>{alerta}</li>
              ))}
            </ul>
          }
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <div>
        <Text strong style={{ display: 'block', marginBottom: 8 }}>
          <HeartOutlined style={{ marginRight: 8, color: '#eb2f96' }} />
          Recomendaciones Clínicas:
        </Text>
        <ul style={{ marginBottom: 0 }}>
          {resultado.recomendaciones.map((rec) => (
            <li key={`rec-${rec}`} style={{ marginBottom: 4 }}>
              {rec}
            </li>
          ))}
        </ul>
      </div>
    </Card>
  </Space>
);

export default IMCResultado;
