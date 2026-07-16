import React from 'react';
import { Form, Input, Select, Row, Col, Alert, Divider, Radio, Space, DatePicker } from 'antd';
import { HeartOutlined, UserOutlined, MedicineBoxOutlined } from '@ant-design/icons';

const { Option } = Select;
const { TextArea } = Input;

interface SeccionInfoConsultaNotaProps {
  pacientes: any[];
  handlePacienteChange: (pacienteId: number) => void;
  loading: boolean;
  tiposConsulta: { value: string; label: string }[];
  notaAnterior: { mensaje: string; tipo: 'success' | 'info' | 'warning' } | null;
  setNotaAnterior: (value: null) => void;
}

const SeccionInfoConsultaNota: React.FC<SeccionInfoConsultaNotaProps> = ({
  pacientes, handlePacienteChange, loading, tiposConsulta, notaAnterior, setNotaAnterior,
}) => (
  <>
    {/* INFORMACIÓN BÁSICA */}
    <Divider orientation="left">Información de la Consulta</Divider>

    <Row gutter={16}>
      <Col xs={24} md={12}>
        <Form.Item
          label="Paciente"
          name="paciente"
          rules={[{ required: true, message: 'Seleccione la paciente' }]}
        >
          <Select
            placeholder="Seleccionar paciente"
            showSearch
            optionFilterProp="children"
            suffixIcon={<UserOutlined />}
            onChange={handlePacienteChange}
            loading={loading}
            filterOption={(input, option) =>
              (option?.children as unknown as string)
                .toLowerCase()
                .includes(input.toLowerCase())
            }
          >
            {pacientes.map((p) => (
              <Option key={p.id} value={p.id}>
                {p.nombre} {p.apellido_paterno} {p.apellido_materno} - {p.ci}
              </Option>
            ))}
          </Select>
        </Form.Item>
      </Col>

      <Col xs={24} md={6}>
        <Form.Item
          label="Fecha y Hora de Consulta"
          name="fecha_consulta"
          rules={[{ required: true, message: 'Seleccione la fecha' }]}
        >
          <DatePicker
            showTime
            format="DD/MM/YYYY HH:mm"
            style={{ width: '100%' }}
            placeholder="Seleccionar fecha"
          />
        </Form.Item>
      </Col>

      <Col xs={24} md={12}>
        <Form.Item
          label={
            <Space>
              <HeartOutlined style={{ color: '#eb2f96' }} />
              Tipo de Consulta
            </Space>
          }
          name="tipo_consulta"
          rules={[{ required: true, message: 'Seleccione el tipo' }]}
        >
          <Radio.Group size="large">
            {tiposConsulta.map((tipo) => (
              <Radio.Button key={tipo.value} value={tipo.value}>
                {tipo.value === 'control_prenatal' && <HeartOutlined style={{ marginRight: 4 }} />}
                {tipo.value !== 'control_prenatal' && <MedicineBoxOutlined style={{ marginRight: 4 }} />}
                {tipo.label}
              </Radio.Button>
            ))}
          </Radio.Group>
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col xs={24}>
        <Form.Item
          label="Motivo de Consulta"
          name="motivo_consulta"
          rules={[{ required: true, message: 'Ingrese el motivo de consulta' }]}
        >
          <TextArea
            rows={3}
            placeholder="Describa el motivo de la consulta según lo referido por la paciente"
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Col>
    </Row>

    {notaAnterior && (
      <Alert
        message={notaAnterior.mensaje}
        type={notaAnterior.tipo}
        showIcon
        closable
        onClose={() => setNotaAnterior(null)}
        style={{ marginBottom: 16 }}
      />
    )}
  </>
);

export default SeccionInfoConsultaNota;
