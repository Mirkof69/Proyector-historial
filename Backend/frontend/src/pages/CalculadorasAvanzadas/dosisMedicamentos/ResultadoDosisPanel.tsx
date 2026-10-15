import React from 'react';
import { Card, Row, Col, Statistic, Divider, Typography, Tag, Alert } from 'antd';
import { SafetyOutlined, WarningOutlined } from '@ant-design/icons';
import { ResultadoDosis } from './dosisMedicamentosUtils';

const { Text } = Typography;

const ResultadoDosisPanel: React.FC<{ resultado: ResultadoDosis }> = ({ resultado }) => (
  <>
    <Card title={<><SafetyOutlined /> Dosis Calculada</>} className="calc-bloque">
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Statistic
            title="Dosis"
            value={resultado.dosis_calculada}
            suffix={resultado.unidad}
            className="calc-cifra-grande"
            valueStyle={{ color: resultado.color }}
          />
        </Col>
        <Col xs={24} sm={8}>
          <Statistic
            title="CLCr"
            value={resultado.clcr}
            precision={1}
            suffix="mL/min"
            valueStyle={{ color: resultado.clcr < 60 ? 'var(--color-aviso)' : 'var(--color-exito)' }}
          />
        </Col>
        <Col xs={24} sm={8}>
          <Statistic
            title="Categoría FDA"
            value={resultado.categoria_fda}
            valueStyle={{ color: resultado.categoria_fda === 'X' || resultado.categoria_fda === 'D' ? 'var(--color-peligro)' : 'var(--color-exito)' }}
          />
        </Col>
      </Row>
      <Divider className="calc-separador" />
      <div className="calc-datos-via">
        <Text strong>Vía:</Text> <Tag color="processing">{resultado.via}</Tag>
        <br />
        <Text strong>Frecuencia:</Text> <Text>{resultado.frecuencia}</Text>
      </div>
    </Card>

    <Alert
      message="Información del Medicamento"
      description={resultado.interpretacion}
      type={resultado.color === 'var(--color-peligro)' ? 'error' : resultado.color === 'var(--color-aviso)' ? 'warning' : 'info'}
      showIcon
      className="calc-bloque"
    />

    {resultado.ajuste_renal !== 'No requiere ajuste' && (
      <Alert
        message="Ajuste por Función Renal"
        description={resultado.ajuste_renal}
        type={resultado.clcr < 30 ? 'error' : 'warning'}
        showIcon
        icon={<WarningOutlined />}
        className="calc-bloque"
      />
    )}

    {resultado.contraindicaciones.length > 0 && (
      <Alert
        message="Contraindicaciones"
        description={
          <ul className="calc-lista">
            {resultado.contraindicaciones.map((item) => (
              <li key={`ci-${item}`}>{item}</li>
            ))}
          </ul>
        }
        type="error"
        showIcon
        className="calc-bloque"
      />
    )}

    {resultado.precauciones.length > 0 && (
      <Alert
        message="Precauciones"
        description={
          <ul className="calc-lista">
            {resultado.precauciones.map((item) => (
              <li key={`prec-${item}`}>{item}</li>
            ))}
          </ul>
        }
        type="warning"
        showIcon
        className="calc-bloque"
      />
    )}
  </>
);

export default ResultadoDosisPanel;
