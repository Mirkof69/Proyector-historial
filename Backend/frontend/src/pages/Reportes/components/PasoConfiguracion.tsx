import React from 'react';
import { Form, Input, Select, DatePicker, Space, Row, Col, Divider, Radio, Typography, Checkbox } from 'antd';
import {
  FileTextOutlined, FilePdfOutlined, FileExcelOutlined, InfoCircleOutlined,
} from '@ant-design/icons';
import { TipoReporteConfig } from '../../../services/reportesService';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { TextArea } = Input;
const { Title, Paragraph } = Typography;

interface PasoConfiguracionProps {
  tipoDetalle: TipoReporteConfig | null;
}

const PasoConfiguracion: React.FC<PasoConfiguracionProps> = ({ tipoDetalle }) => {
  const formatosDisponibles = tipoDetalle
    ? [
        tipoDetalle.formato_pdf !== false && 'pdf',
        tipoDetalle.formato_excel !== false && 'excel',
      ].filter(Boolean)
    : ['pdf', 'excel'];
  const requiereFechas = tipoDetalle?.incluir_fecha_inicio || tipoDetalle?.incluir_fecha_fin;

  return (
    <div>
      <Title level={4}>Configure los parámetros del reporte</Title>
      <Paragraph type="secondary">
        Complete la información necesaria para generar el reporte
      </Paragraph>

      <Row gutter={[16, 0]}>
        <Col xs={24}>
          <Form.Item
            name="nombre"
            label="Nombre del Reporte"
            rules={[{ required: true, message: 'Ingrese el nombre' }]}
            tooltip="Nombre descriptivo para identificar el reporte"
          >
            <Input
              placeholder="Ej: Partos Enero 2025"
              size="large"
              prefix={<FileTextOutlined />}
            />
          </Form.Item>
        </Col>

        <Col xs={24}>
          <Form.Item
            name="descripcion"
            label={
              <Space>
                Descripción (Opcional)
                <InfoCircleOutlined style={{ color: '#1890ff' }} />
              </Space>
            }
            tooltip="Descripción adicional del reporte"
          >
            <TextArea
              rows={3}
              placeholder="Descripción detallada del reporte..."
              showCount
              maxLength={200}
            />
          </Form.Item>
        </Col>

        <Col xs={24} md={12}>
          <Form.Item
            name="formato"
            label="Formato de Salida"
            rules={[{ required: true, message: 'Seleccione el formato' }]}
          >
            <Radio.Group size="large">
              {formatosDisponibles.includes('pdf') && (
                <Radio value="pdf">
                  <Space>
                    <FilePdfOutlined style={{ color: '#ff4d4f' }} />
                    PDF
                  </Space>
                </Radio>
              )}
              {formatosDisponibles.includes('excel') && (
                <Radio value="excel">
                  <Space>
                    <FileExcelOutlined style={{ color: '#52c41a' }} />
                    Excel
                  </Space>
                </Radio>
              )}
            </Radio.Group>
          </Form.Item>
        </Col>

        {requiereFechas && (
          <Col xs={24} md={12}>
            <Form.Item
              name="rango_fechas"
              label="Rango de Fechas"
              rules={[{ required: true, message: 'Seleccione el rango' }]}
              tooltip="Período de tiempo para el reporte"
            >
              <RangePicker
                style={{ width: '100%' }}
                format="DD/MM/YYYY"
                size="large"
              />
            </Form.Item>
          </Col>
        )}

        <Col xs={24}>
          <Divider>Opciones Adicionales</Divider>
          <Form.Item name="incluir_graficos" valuePropName="checked">
            <Checkbox>Incluir gráficos estadísticos</Checkbox>
          </Form.Item>
          <Form.Item name="incluir_estadisticas" valuePropName="checked">
            <Checkbox>Incluir resumen estadístico</Checkbox>
          </Form.Item>
          <Form.Item
            name="agrupar_por"
            label="Agrupar por"
            tooltip="Criterio de agrupación de datos"
          >
            <Select placeholder="Seleccione criterio" allowClear>
              <Option value="semana">Semana</Option>
              <Option value="mes">Mes</Option>
              <Option value="medico">Médico</Option>
              <Option value="tipo">Tipo</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>
    </div>
  );
};

export default PasoConfiguracion;
