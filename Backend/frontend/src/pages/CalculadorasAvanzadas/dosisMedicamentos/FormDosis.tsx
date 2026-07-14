import React from 'react';
import { Card, Form, Row, Col, InputNumber, Switch, Divider, Select, Button } from 'antd';
import type { FormInstance } from 'antd';
import { MedicineBoxOutlined, ExperimentOutlined } from '@ant-design/icons';
import { medicamentos, DatosPaciente } from './dosisMedicamentosUtils';

const { Option } = Select;

interface FormDosisProps {
  form: FormInstance;
  onFinish: (valores: DatosPaciente) => void;
}

const FormDosis: React.FC<FormDosisProps> = ({ form, onFinish }) => (
  <Card title={<><ExperimentOutlined /> Datos del Paciente y Medicamento</>}>
    <Form form={form} layout="vertical" onFinish={onFinish}>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item label="Peso (kg)" name="peso" rules={[{ required: true }]} initialValue={70}>
            <InputNumber min={40} max={150} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="Edad (años)" name="edad" rules={[{ required: true }]} initialValue={30}>
            <InputNumber min={15} max={50} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="Creatinina (mg/dL)" name="creatinina" rules={[{ required: true }]} initialValue={0.9}>
            <InputNumber min={0.3} max={10} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="Semanas Gestación" name="semanas" initialValue={28}>
            <InputNumber min={0} max={42} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item label="Embarazada" name="es_embarazada" valuePropName="checked" initialValue={true}>
        <Switch checkedChildren="Sí" unCheckedChildren="No" />
      </Form.Item>

      <Divider>Selección de Medicamento</Divider>

      <Form.Item label="Medicamento" name="medicamento" rules={[{ required: true }]} initialValue="oxitocina">
        <Select showSearch optionFilterProp="children">
          {medicamentos.map(med => (
            <Option key={med.value} value={med.value}>{med.label}</Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item label="Vía de Administración" name="via" rules={[{ required: true }]} initialValue="IV">
        <Select>
          <Option value="IV">Intravenosa (IV)</Option>
          <Option value="IM">Intramuscular (IM)</Option>
          <Option value="SC">Subcutánea (SC)</Option>
          <Option value="VO">Vía Oral (VO)</Option>
          <Option value="sublingual">Sublingual</Option>
          <Option value="vaginal">Vaginal</Option>
          <Option value="rectal">Rectal</Option>
        </Select>
      </Form.Item>

      <Form.Item style={{ marginTop: 24 }}>
        <Button type="primary" htmlType="submit" block size="large" icon={<MedicineBoxOutlined />}>
          Calcular Dosis
        </Button>
      </Form.Item>
    </Form>
  </Card>
);

export default FormDosis;
