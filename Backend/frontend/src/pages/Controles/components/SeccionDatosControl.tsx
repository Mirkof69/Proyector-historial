import React from 'react';
import { Form, InputNumber, DatePicker, Row, Col, Select, Divider, Space, Tag } from 'antd';
import { MedicineBoxOutlined } from '@ant-design/icons';
import { Embarazo } from '../../../services/embarazosService';
import { Paciente } from '../../../services/pacientesService';
import { getNombrePaciente } from '../formularioControlUtils';

const { Option } = Select;

interface SeccionDatosControlProps {
  embarazos: Embarazo[];
  pacientes: Paciente[];
  isEditing: boolean;
  calcularSemanasGestacion: (embarazoId: number) => void;
}

const SeccionDatosControl: React.FC<SeccionDatosControlProps> = ({
  embarazos, pacientes, isEditing, calcularSemanasGestacion,
}) => (
  <>
    {/* ========== DATOS DEL CONTROL ========== */}
    <Divider orientation="left">
      <Space>
        <MedicineBoxOutlined />
        Datos del Control
      </Space>
    </Divider>

    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="embarazo"
          label="Embarazo"
          rules={[{ required: true, message: 'Seleccione un embarazo' }]}
        >
          <Select
            placeholder="Seleccionar embarazo activo"
            showSearch
            filterOption={(input, option) => {
              const title = option?.title;
              if (typeof title === 'string') {
                return title.toLowerCase().includes(input.toLowerCase());
              }
              return false;
            }}
            onChange={calcularSemanasGestacion}
            disabled={isEditing}
            size="large"
          >
            {embarazos.map((e) => {
              const nombrePaciente = getNombrePaciente(e.id!, embarazos, pacientes);
              return (
                <Option key={e.id} value={e.id} title={nombrePaciente}>
                  <Space>
                    <Tag color="blue">G{e.numero_gesta}</Tag>
                    {nombrePaciente}
                  </Space>
                </Option>
              );
            })}
          </Select>
        </Form.Item>
      </Col>
      <Col span={6}>
        <Form.Item
          name="numero_control"
          label="N° Control"
          rules={[{ required: true, message: 'Requerido' }]}
        >
          <InputNumber style={{ width: '100%' }} min={1} max={20} size="large" />
        </Form.Item>
      </Col>
      <Col span={6}>
        <Form.Item
          name="fecha_control"
          label="Fecha del Control"
          rules={[{ required: true, message: 'Requerido' }]}
        >
          <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" size="large" />
        </Form.Item>
      </Col>
    </Row>
  </>
);

export default SeccionDatosControl;
