import React from 'react';
import BotonSiguiente from './BotonSiguiente';
import { filtrarOpcion, ordenarPersonal } from '../../../utils/texto';
import { Form, Select, Space, Row, Col, Divider } from 'antd';
import { UserOutlined, MedicineBoxOutlined, HomeOutlined } from '@ant-design/icons';
import { FormularioCitaAction } from '../formularioCitaUtils';
import { PacienteSelect } from '../../../components/clinico/SelectoresClinicos';

const { Option } = Select;

interface StepPacienteMedicoProps {
  medicos: any[];
  consultorios: any[];
  handleMedicoChange: (medicoId: number) => void;
  dispatch: React.Dispatch<FormularioCitaAction>;
}

const StepPacienteMedico: React.FC<StepPacienteMedicoProps> = ({
  medicos, consultorios, handleMedicoChange, dispatch,
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
          {/* Busca en el servidor (todas las pacientes, sin distinguir acentos). */}
          <PacienteSelect placeholder="Buscar paciente por nombre o CI" />
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
            placeholder="Escriba o elija el médico"
            showSearch
            filterOption={filtrarOpcion}
            onChange={handleMedicoChange}
            options={ordenarPersonal(medicos).map((m) => ({
              value: m.id,
              label: `Dr(a). ${m.nombre} ${m.apellido_paterno ?? ''}${m.especialidad ? ` - ${m.especialidad}` : ''}`,
            }))}
          />
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
        <BotonSiguiente campos={['paciente', 'medico', 'tipo_cita']} alAvanzar={() => dispatch({ type: 'SET_CURRENT_STEP', payload: 1 })} />
      </Col>
    </Row>
  </>
);

export default StepPacienteMedico;
