import React from 'react';
import { Form, Select, Button, Space, Row, Col, Divider } from 'antd';
import { UserOutlined, MedicineBoxOutlined, HomeOutlined } from '@ant-design/icons';
import { FormularioCitaAction } from '../formularioCitaUtils';

const { Option } = Select;

interface StepPacienteMedicoProps {
  pacientes: any[];
  medicos: any[];
  consultorios: any[];
  handleMedicoChange: (medicoId: number) => void;
  dispatch: React.Dispatch<FormularioCitaAction>;
}

const StepPacienteMedico: React.FC<StepPacienteMedicoProps> = ({
  pacientes, medicos, consultorios, handleMedicoChange, dispatch,
}) => (
  <>
    <Row gutter={16}>
      <Col xs={24} md={12}>
        <Form.Item
          label={
            <Space>
              <UserOutlined />
              <span>Paciente</span>
            </Space>
          }
          name="paciente"
          rules={[{ required: true, message: 'Seleccione el paciente' }]}
        >
          <Select
            placeholder="Buscar y seleccionar paciente"
            showSearch
            optionFilterProp="children"
            filterOption={(input, option) =>
              (option?.children as unknown as string).toLowerCase().includes(input.toLowerCase())
            }
          >
            {pacientes.map((p) => (
              <Option key={p.id} value={p.id}>
                {p.nombre} {p.apellido_paterno} {p.apellido_materno} - ID: {p.id_clinico || p.numero_documento}
              </Option>
            ))}
          </Select>
        </Form.Item>
      </Col>

      <Col xs={24} md={12}>
        <Form.Item
          label={
            <Space>
              <MedicineBoxOutlined />
              <span>Médico</span>
            </Space>
          }
          name="medico"
          rules={[{ required: true, message: 'Seleccione el médico' }]}
        >
          <Select
            placeholder="Seleccionar médico"
            onChange={handleMedicoChange}
          >
            {medicos.map((m) => (
              <Option key={m.id} value={m.id}>
                Dr(a). {m.nombre} {m.apellido_paterno}
                {m.especialidad && ` - ${m.especialidad}`}
              </Option>
            ))}
          </Select>
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col xs={24} md={12}>
        <Form.Item
          label="Tipo de Cita"
          name="tipo_cita"
          rules={[{ required: true, message: 'Seleccione el tipo de cita' }]}
        >
          <Select placeholder="Seleccionar tipo">
            <Option value="primera_vez">Primera Vez</Option>
            <Option value="control">Control</Option>
            <Option value="urgencia">Urgencia</Option>
            <Option value="seguimiento">Seguimiento</Option>
          </Select>
        </Form.Item>
      </Col>

      <Col xs={24} md={12}>
        <Form.Item
          label={
            <Space>
              <HomeOutlined />
              <span>Consultorio (Opcional)</span>
            </Space>
          }
          name="consultorio"
        >
          <Select placeholder="Seleccionar consultorio" allowClear>
            {consultorios.map((c) => (
              <Option key={c.id} value={c.id}>
                {c.nombre} - {c.ubicacion}
              </Option>
            ))}
          </Select>
        </Form.Item>
      </Col>
    </Row>

    <Divider />
    <Row justify="end">
      <Col>
        <Button type="primary" onClick={() => dispatch({ type: 'SET_CURRENT_STEP', payload: 1 })}>
          Siguiente
        </Button>
      </Col>
    </Row>
  </>
);

export default StepPacienteMedico;
