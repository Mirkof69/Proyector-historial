import React from 'react';
import { Collapse, Row, Col, Form, Select, DatePicker, Radio, Space, Tooltip, Input } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import { TipoExamen } from '../../../services/laboratorioService';
import { PacienteSelect } from '../../../components/clinico/SelectoresClinicos';

const { TextArea } = Input;
const { Option } = Select;

interface DatosGeneralesLabProps {
  tiposExamen: TipoExamen[];
  onTipoExamenChange: (tipoExamenId: number) => void;
}

const DatosGeneralesLab: React.FC<DatosGeneralesLabProps> = ({ tiposExamen, onTipoExamenChange }) => (
  <Collapse defaultActiveKey={['1']} className="laboratorio-separado"
    items={[{
      key: '1',
      label: 'Datos Generales',
      children: (
        <>
          <Row gutter={[16, 0]}>
            <Col xs={24} md={12}>
              <Form.Item
                name="paciente"
                label="Paciente"
                rules={[{ required: true, message: 'Seleccione un paciente' }]}
              >
                {/* Busca en el servidor (todas las pacientes, sin distinguir acentos). */}
                <PacienteSelect placeholder="Buscar paciente por nombre o CI" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="tipo_examen"
                label="Tipo de Examen"
                rules={[{ required: true, message: 'Seleccione un tipo' }]}
              >
                <Select
                  placeholder="Seleccione un tipo de examen"
                  onChange={onTipoExamenChange}
                  options={tiposExamen.map((t) => ({
                    label: `${t.nombre} (${t.codigo})`,
                    value: t.id,
                  }))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={[16, 0]}>
            <Col xs={24} md={8}>
              <Form.Item
                name="fecha_solicitud"
                label="Fecha de Solicitud"
                rules={[{ required: true }]}
              >
                <DatePicker
                  className="laboratorio-ancho"
                  format={{ format: 'DD/MM/YYYY', type: 'mask' }}
                  showTime
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                name="prioridad"
                label={
                  <Space>
                    Prioridad
                    <Tooltip title="Seleccione la urgencia con la que se requiere el resultado">
                      <InfoCircleOutlined className="laboratorio-page__info" />
                    </Tooltip>
                  </Space>
                }
                rules={[{ required: true }]}
              >
                <Radio.Group>
                  <Radio value="normal">Normal</Radio>
                  <Radio value="urgente">Urgente</Radio>
                  <Radio value="stat">STAT</Radio>
                </Radio.Group>
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item name="estado" label="Estado">
                <Select>
                  <Option value="solicitado">Solicitado</Option>
                  <Option value="en_proceso">En Proceso</Option>
                  <Option value="completado">Completado</Option>
                  <Option value="cancelado">Cancelado</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={[16, 0]}>
            <Col xs={24} md={12}>
              <Form.Item name="fecha_muestra" label="Fecha de Toma de Muestra">
                <DatePicker className="laboratorio-ancho" format={{ format: 'DD/MM/YYYY', type: 'mask' }} showTime />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="fecha_resultado" label="Fecha de Resultado">
                <DatePicker className="laboratorio-ancho" format={{ format: 'DD/MM/YYYY', type: 'mask' }} showTime />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="indicaciones" label="Indicaciones Clínicas">
            <TextArea rows={2} placeholder="Motivo de la solicitud..." />
          </Form.Item>
        </>
      )
    }]}
  />
);

export default DatosGeneralesLab;
