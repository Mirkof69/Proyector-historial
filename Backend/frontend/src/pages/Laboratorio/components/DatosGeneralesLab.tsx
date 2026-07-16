import React from 'react';
import { Collapse, Row, Col, Form, Select, DatePicker, Radio, Space, Tooltip, Input } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import { TipoExamen } from '../../../services/laboratorioService';
import { Paciente } from '../../../services/pacientesService';

const { TextArea } = Input;
const { Option } = Select;

interface DatosGeneralesLabProps {
  pacientes: Paciente[];
  tiposExamen: TipoExamen[];
  onTipoExamenChange: (tipoExamenId: number) => void;
}

const DatosGeneralesLab: React.FC<DatosGeneralesLabProps> = ({ pacientes, tiposExamen, onTipoExamenChange }) => (
  <Collapse defaultActiveKey={['1']} style={{ marginBottom: 16 }}
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
                <Select
                  placeholder="Seleccione un paciente"
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    (option?.label as string ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  options={pacientes.map((p) => ({
                    label: `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''} - ${p.id_clinico}`,
                    value: p.id,
                  }))}
                />
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
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
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
                      <InfoCircleOutlined style={{ color: '#1890ff' }} />
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
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" showTime />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="fecha_resultado" label="Fecha de Resultado">
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" showTime />
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
