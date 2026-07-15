import React from 'react';
import { Card, Form, Space, Row, Col, Alert, Radio, Spin, Typography, Tag } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import { TipoReporteConfig } from '../../../services/reportesService';
import { iconoPorCategoria } from '../generarReporteUtils';

const { Title, Paragraph } = Typography;

interface PasoTipoReporteProps {
  cargandoTipos: boolean;
  tiposReporte: TipoReporteConfig[];
  tipoSeleccionado: number | null;
  handleTipoReporteChange: (tipoId: number) => void;
}

const PasoTipoReporte: React.FC<PasoTipoReporteProps> = ({
  cargandoTipos, tiposReporte, tipoSeleccionado, handleTipoReporteChange,
}) => (
  <div>
    <Title level={4}>Seleccione el tipo de reporte</Title>
    <Paragraph type="secondary">
      Elija el tipo de reporte que desea generar
    </Paragraph>

    {cargandoTipos ? (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <Spin />
      </div>
    ) : tiposReporte.length === 0 ? (
      <Alert
        type="warning"
        showIcon
        message="No hay tipos de reporte configurados"
        description="Un administrador debe crear al menos un Tipo de Reporte activo antes de poder generar reportes."
      />
    ) : (
      <Form.Item
        name="tipo_reporte"
        rules={[{ required: true, message: 'Seleccione un tipo de reporte' }]}
      >
        <Radio.Group
          style={{ width: '100%' }}
          onChange={(e) => handleTipoReporteChange(e.target.value)}
        >
          <Row gutter={[16, 16]}>
            {tiposReporte.map((tipo) => (
              <Col xs={24} sm={12} md={8} key={tipo.id}>
                <Card
                  hoverable
                  className={
                    tipoSeleccionado === tipo.id ? 'reporte-card-selected' : ''
                  }
                >
                  <Radio value={tipo.id} style={{ width: '100%' }}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div style={{ textAlign: 'center' }}>
                        {iconoPorCategoria[tipo.categoria] || <FileTextOutlined style={{ fontSize: 48 }} />}
                      </div>
                      <Title level={5} style={{ marginBottom: 8 }}>
                        {tipo.nombre}
                      </Title>
                      <Paragraph
                        type="secondary"
                        style={{ marginBottom: 8, fontSize: 12 }}
                      >
                        {tipo.descripcion}
                      </Paragraph>
                      <Tag color={tipo.categoria === 'estadistico' ? 'blue' : 'green'}>
                        {tipo.categoria_display || tipo.categoria}
                      </Tag>
                    </Space>
                  </Radio>
                </Card>
              </Col>
            ))}
          </Row>
        </Radio.Group>
      </Form.Item>
    )}
  </div>
);

export default PasoTipoReporte;
