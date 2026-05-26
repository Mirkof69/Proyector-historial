import React from 'react';
import { Form, InputNumber, Select, Row, Col } from 'antd';

const { Option } = Select;

interface AntecedentesFormFieldsProps {
  pacientes: any[];
}

const AntecedentesFormFields: React.FC<AntecedentesFormFieldsProps> = ({ pacientes }) => (
  <>
    <Form.Item
      label="Paciente"
      name="paciente"
      rules={[{ required: true, message: 'Seleccione un paciente' }]}
    >
      <Select
        placeholder="Seleccionar paciente"
        showSearch
        filterOption={(input, option) =>
          (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
        }
        options={pacientes.map(p => ({
          label: `${p.nombre} ${p.apellido_paterno || p.apellido || ''}`.trim(),
          value: p.id,
        }))}
      />
    </Form.Item>

    <Row gutter={16}>
      <Col span={8}>
        <Form.Item label="Gestas (G)" name="gestas">
          <InputNumber min={0} style={{ width: '100%' }} placeholder="0" />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="Partos (P)" name="partos">
          <InputNumber min={0} style={{ width: '100%' }} placeholder="0" />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="Abortos (A)" name="abortos">
          <InputNumber min={0} style={{ width: '100%' }} placeholder="0" />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col span={8}>
        <Form.Item label="Cesáreas (C)" name="cesareas">
          <InputNumber min={0} style={{ width: '100%' }} placeholder="0" />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="Hijos Vivos" name="hijos_vivos">
          <InputNumber min={0} style={{ width: '100%' }} placeholder="0" />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item label="Menarquia (años)" name="menarquia_edad">
          <InputNumber min={8} max={20} style={{ width: '100%' }} placeholder="Ej: 13" />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col span={12}>
        <Form.Item label="Ciclos Menstruales" name="ciclos_menstruales">
          <Select placeholder="Seleccionar" allowClear>
            <Option value="regular">Regular</Option>
            <Option value="irregular">Irregular</Option>
            <Option value="amenorrea">Amenorrea</Option>
          </Select>
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item label="Duración ciclo (días)" name="duracion_ciclo_dias">
          <InputNumber min={15} max={60} style={{ width: '100%' }} placeholder="28" />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col span={12}>
        <Form.Item label="Inicio vida sexual (años)" name="inicio_vida_sexual_edad">
          <InputNumber min={10} max={50} style={{ width: '100%' }} />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item label="Método anticonceptivo actual" name="metodo_anticonceptivo_actual">
          <Select placeholder="Seleccionar" allowClear>
            <Option value="ninguno">Ninguno</Option>
            <Option value="hormonal_oral">Hormonal oral (píldora)</Option>
            <Option value="diu">DIU</Option>
            <Option value="preservativo">Preservativo</Option>
            <Option value="implante">Implante</Option>
            <Option value="inyectable">Inyectable</Option>
            <Option value="otro">Otro</Option>
          </Select>
        </Form.Item>
      </Col>
    </Row>
  </>
);

export default AntecedentesFormFields;
