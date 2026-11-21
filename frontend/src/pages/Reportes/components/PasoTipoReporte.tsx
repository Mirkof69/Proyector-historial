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
      <div className="reportes-cargando">
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
          className="reportes-ancho"
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
                  <Radio value={tipo.id} className="reportes-ancho">
                    <Space direction="vertical" className="reportes-ancho">
                      <div className="reportes-centro">
                        {iconoPorCategoria[tipo.categoria] || <FileTextOutlined className="reportes-icono-tipo" />}
                      </div>
                      <Title level={5}>
                        {tipo.nombre}
                      </Title>
                      <Paragraph
                        type="secondary"
                        className="reportes-texto-ayuda"
                      >
                        {tipo.descripcion}
                      </Paragraph>
                      <Tag color={tipo.categoria === 'estadistico' ? 'default' : 'success'}>
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
