import React from 'react';
import { Card, Row, Col, Statistic, Alert, Space } from 'antd';
import { HeartOutlined, WarningOutlined, MedicineBoxOutlined } from '@ant-design/icons';
import { ResultadoHemorragia } from '../hemorragiaObstetricaUtils';

interface HemorragiaResultadoProps {
  resultado: ResultadoHemorragia;
}

const HemorragiaResultado: React.FC<HemorragiaResultadoProps> = ({ resultado }) => (
  <>
    <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
      <Col xs={24} sm={12} md={6}>
        <Card>
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
        <Card>
          <Statistic
            title="Gravedad"
            value={resultado.gravedad}
            valueStyle={{ color: resultado.color_gravedad }}
            prefix={<WarningOutlined />}
          />
        </Card>
      </Col>

      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic
            title="Pérdida de Volemia"
            value={resultado.porcentaje_perdida.toFixed(1)}
            valueStyle={{ color: resultado.porcentaje_perdida > 30 ? '#ff4d4f' : '#faad14' }}
            suffix="%"
          />
        </Card>
      </Col>

      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic
            title="Volumen a Reponer"
            value={resultado.volumen_compensar.toFixed(0)}
            valueStyle={{ color: '#1890ff' }}
            suffix="ml"
            prefix={<MedicineBoxOutlined />}
          />
        </Card>
      </Col>
    </Row>

    <Card title="Interpretación Clínica" style={{ marginTop: 16 }}>
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
          <span style={{ color: '#ff4d4f' }}>
            🚨 PROTOCOLO DE TRANSFUSIÓN MASIVA (PTM) ACTIVADO
          </span>
        }
        style={{ marginTop: 16 }}
      >
        <Alert
          message="CRITERIOS CUMPLIDOS PARA PTM"
          description="Transfusión agresiva necesaria. Ratio 1:1:1 (GR:PFC:Plaq). Contactar Banco de Sangre INMEDIATAMENTE."
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Glóbulos Rojos"
              value={resultado.protocolo_ptm.globulos_rojos}
              suffix="unidades"
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Plasma Fresco"
              value={resultado.protocolo_ptm.plasma}
              suffix="unidades"
              valueStyle={{ color: '#faad14' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Plaquetas"
              value={resultado.protocolo_ptm.plaquetas}
              suffix="unidades"
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Crioprecipitado"
              value={resultado.protocolo_ptm.crioprecipitado}
              suffix="unidades"
              valueStyle={{ color: '#722ed1' }}
            />
          </Col>
        </Row>
      </Card>
    )}

    <Card title="🚨 Medidas Inmediatas" style={{ marginTop: 16 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
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

    <Card title="📋 Intervenciones Escalonadas" style={{ marginTop: 16 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
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
