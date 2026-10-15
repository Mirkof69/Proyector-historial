import React from 'react';
import { Card, Row, Col, Statistic, Alert, Space } from 'antd';
import { HeartOutlined, WarningOutlined, MedicineBoxOutlined, AlertOutlined, OrderedListOutlined } from '@ant-design/icons';
import { ResultadoHemorragia } from '../hemorragiaObstetricaUtils';

interface HemorragiaResultadoProps {
  resultado: ResultadoHemorragia;
}

const HemorragiaResultado: React.FC<HemorragiaResultadoProps> = ({ resultado }) => (
  <>
    <Row gutter={[16, 16]} className="calc-bloque-arriba">
      <Col xs={24} sm={12} md={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="Shock Index"
            value={resultado.shock_index.toFixed(2)}
            valueStyle={{ color: resultado.color_shock }}
            prefix={<HeartOutlined />}
            suffix={resultado.clasificacion_shock}
          />
        </Card>
      </Col>

      <Col xs={24} sm={12} md={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="Gravedad"
            value={resultado.gravedad}
            valueStyle={{ color: resultado.color_gravedad }}
            prefix={<WarningOutlined />}
          />
        </Card>
      </Col>

      <Col xs={24} sm={12} md={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="Pérdida de Volemia"
            value={resultado.porcentaje_perdida.toFixed(1)}
            valueStyle={{ color: resultado.porcentaje_perdida > 30 ? 'var(--color-peligro)' : 'var(--color-aviso)' }}
            suffix="%"
          />
        </Card>
      </Col>

      <Col xs={24} sm={12} md={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="Volumen a Reponer"
            value={resultado.volumen_compensar.toFixed(0)}
            suffix="ml"
            prefix={<MedicineBoxOutlined />}
          />
        </Card>
      </Col>
    </Row>

    <Card title="Interpretación Clínica" className="calc-bloque-arriba">
      <Alert
        message={`Estado: ${resultado.estado_hemodinamico} | Riesgo de Shock: ${resultado.riesgo_shock}`}
        description={resultado.interpretacion}
        type={resultado.shock_index > 1.2 ? 'error' : resultado.shock_index > 0.9 ? 'warning' : 'success'}
        showIcon
      />
    </Card>

    {resultado.requiere_ptm && (
      <Card
        title={
          <span className="calc-titulo-peligro">
            <AlertOutlined /> PROTOCOLO DE TRANSFUSIÓN MASIVA (PTM) ACTIVADO
          </span>
        }
        className="calc-bloque-arriba"
      >
        <Alert
          message="CRITERIOS CUMPLIDOS PARA PTM"
          description="Transfusión agresiva necesaria. Ratio 1:1:1 (GR:PFC:Plaq). Contactar Banco de Sangre INMEDIATAMENTE."
          type="error"
          showIcon
          className="calc-bloque"
        />

        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Glóbulos Rojos"
              value={resultado.protocolo_ptm.globulos_rojos}
              suffix="unidades"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Plasma Fresco"
              value={resultado.protocolo_ptm.plasma}
              suffix="unidades"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Plaquetas"
              value={resultado.protocolo_ptm.plaquetas}
              suffix="unidades"
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Crioprecipitado"
              value={resultado.protocolo_ptm.crioprecipitado}
              suffix="unidades"
            />
          </Col>
        </Row>
      </Card>
    )}

    <Card title={<span className="calc-titulo-seccion"><AlertOutlined /> Medidas Inmediatas</span>} className="calc-bloque-arriba">
      <Space direction="vertical" className="calc-pila">
        {resultado.medidas_inmediatas.map((medida) => (
          <Alert
            key={`medida-${medida}`}
            message={medida}
            type={medida.includes('🚨') || medida.includes('🔴') ? 'error' : 'warning'}
            showIcon
          />
        ))}
      </Space>
    </Card>

    <Card title={<span className="calc-titulo-seccion"><OrderedListOutlined /> Intervenciones Escalonadas</span>} className="calc-bloque-arriba">
      <Space direction="vertical" className="calc-pila">
        {resultado.intervenciones_sugeridas.map((intervencion) => (
          <Alert
            key={`interv-${intervencion}`}
            message={intervencion}
            type="info"
            showIcon
          />
        ))}
      </Space>
    </Card>
  </>
);

export default HemorragiaResultado;
