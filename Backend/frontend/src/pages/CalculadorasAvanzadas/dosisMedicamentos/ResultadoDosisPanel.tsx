import React from 'react';
import { Card, Row, Col, Statistic, Divider, Typography, Tag, Alert } from 'antd';
import { SafetyOutlined, WarningOutlined } from '@ant-design/icons';
import { ResultadoDosis } from './dosisMedicamentosUtils';

const { Text } = Typography;

const ResultadoDosisPanel: React.FC<{ resultado: ResultadoDosis }> = ({ resultado }) => (
  <>
    <Card title={<><SafetyOutlined /> Dosis Calculada</>} style={{ marginBottom: 16 }}>
      <Row gutter={16}>
        <Col span={8}>
          <Statistic
            title="Dosis"
            value={resultado.dosis_calculada}
            suffix={resultado.unidad}
            valueStyle={{ color: resultado.color, fontWeight: 'bold', fontSize: 28 }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="CLCr"
            value={resultado.clcr}
            precision={1}
            suffix="mL/min"
            valueStyle={{ color: resultado.clcr < 60 ? '#fa8c16' : '#52c41a', fontSize: 20 }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Categoría FDA"
            value={resultado.categoria_fda}
            valueStyle={{ color: resultado.categoria_fda === 'X' || resultado.categoria_fda === 'D' ? '#f5222d' : '#52c41a', fontSize: 20 }}
          />
        </Col>
      </Row>
      <Divider style={{ margin: '12px 0' }} />
      <div style={{ padding: '8px 0' }}>
        <Text strong>Vía:</Text> <Tag color="blue">{resultado.via}</Tag>
        <br />
        <Text strong>Frecuencia:</Text> <Text>{resultado.frecuencia}</Text>
      </div>
    </Card>

    <Alert
      message="Información del Medicamento"
      description={resultado.interpretacion}
      type={resultado.color === '#f5222d' ? 'error' : resultado.color === '#fa8c16' ? 'warning' : 'info'}
      showIcon
      style={{ marginBottom: 16 }}
    />

    {resultado.ajuste_renal !== 'No requiere ajuste' && (
      <Alert
        message="Ajuste por Función Renal"
        description={resultado.ajuste_renal}
        type={resultado.clcr < 30 ? 'error' : 'warning'}
        showIcon
        icon={<WarningOutlined />}
        style={{ marginBottom: 16 }}
      />
    )}

    {resultado.contraindicaciones.length > 0 && (
      <Alert
        message="Contraindicaciones"
        description={
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {resultado.contraindicaciones.map((item) => (
              <li key={`ci-${item}`}>{item}</li>
            ))}
          </ul>
        }
        type="error"
        showIcon
        style={{ marginBottom: 16 }}
      />
    )}

    {resultado.precauciones.length > 0 && (
      <Alert
        message="Precauciones"
        description={
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {resultado.precauciones.map((item) => (
              <li key={`prec-${item}`}>{item}</li>
            ))}
          </ul>
        }
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
      />
    )}
  </>
);

export default ResultadoDosisPanel;
