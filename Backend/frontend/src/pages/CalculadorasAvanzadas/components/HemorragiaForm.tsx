import React from 'react';
import { Card, Form, InputNumber, Button, Row, Col, Alert, Select, Divider, Checkbox } from 'antd';
import { HeartOutlined, ThunderboltOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';

const { Option } = Select;

interface HemorragiaFormProps {
  form: FormInstance;
  onFinish: (valores: any) => void;
  loading: boolean;
}

const HemorragiaForm: React.FC<HemorragiaFormProps> = ({ form, onFinish, loading }) => (
  <Card
    title={
      <span>
        <HeartOutlined style={{ marginRight: 8, color: '#ff4d4f' }} />
        Evaluación de Hemorragia Obstétrica
      </span>
    }
  >
    <Alert
      message="Protocolo 4 T's para Hemorragia Postparto"
      description="Evaluación sistemática: TONO (atonía), TRAUMA (laceraciones), TEJIDO (retención), TROMBINA (coagulopatía). Incluye Shock Index y Protocolo de Transfusión Masiva."
      type="info"
      showIcon
      style={{ marginBottom: 16 }}
    />

    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      initialValues={{
        frecuencia_cardiaca: 80,
        presion_sistolica: 120,
        presion_diastolica: 80,
        frecuencia_respiratoria: 16,
        temperatura: 36.5,
        saturacion_o2: 98,
        perdida_estimada_ml: 500,
        tiempo_minutos: 30,
        causa_principal: 'tono',
        tono_uterino: 'firme',
        placenta_completa: true,
        laceraciones: false,
        coagulopatia: false,
        hemoglobina_inicial: 12,
        hemoglobina_actual: 11,
        plaquetas: 200000,
        fibrinogeno: 350
      }}
    >
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Divider orientation="left">Signos Vitales</Divider>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Form.Item
            label="Frecuencia Cardíaca (lpm)"
            name="frecuencia_cardiaca"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={40} max={200} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Form.Item
            label="Presión Sistólica (mmHg)"
            name="presion_sistolica"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={50} max={200} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Form.Item
            label="Presión Diastólica (mmHg)"
            name="presion_diastolica"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={30} max={120} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Form.Item
            label="Frecuencia Respiratoria (rpm)"
            name="frecuencia_respiratoria"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={8} max={40} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Form.Item
            label="Temperatura (°C)"
            name="temperatura"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={34} max={42} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Form.Item
            label="Saturación O₂ (%)"
            name="saturacion_o2"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={70} max={100} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24}>
          <Divider orientation="left">Pérdida Sanguínea</Divider>
        </Col>

        <Col xs={24} sm={12}>
          <Form.Item
            label="Pérdida Estimada (ml)"
            name="perdida_estimada_ml"
            rules={[{ required: true, message: 'Requerido' }]}
            tooltip="Volumen total estimado de sangre perdida"
          >
            <InputNumber min={0} max={5000} step={50} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12}>
          <Form.Item
            label="Tiempo desde inicio (minutos)"
            name="tiempo_minutos"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={0} max={360} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24}>
          <Divider orientation="left">Evaluación Obstétrica (4 T's)</Divider>
        </Col>

        <Col xs={24} sm={12}>
          <Form.Item
            label="Causa Principal Sospechada"
            name="causa_principal"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <Select>
              <Option value="tono">🔴 TONO - Atonía Uterina (70%)</Option>
              <Option value="trauma">🟠 TRAUMA - Laceraciones/Desgarros (20%)</Option>
              <Option value="tejido">🟡 TEJIDO - Retención Placentaria (8%)</Option>
              <Option value="trombina">🟣 TROMBINA - Coagulopatía (2%)</Option>
            </Select>
          </Form.Item>
        </Col>

        <Col xs={24} sm={12}>
          <Form.Item
            label="Tono Uterino"
            name="tono_uterino"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <Select>
              <Option value="firme">✅ Firme (bien contraído)</Option>
              <Option value="blando">⚠️ Blando</Option>
              <Option value="muy_blando">🔴 Muy Blando (atónico)</Option>
            </Select>
          </Form.Item>
        </Col>

        <Col xs={24} sm={8}>
          <Form.Item name="placenta_completa" valuePropName="checked">
            <Checkbox>Placenta Completa</Checkbox>
          </Form.Item>
        </Col>

        <Col xs={24} sm={8}>
          <Form.Item name="laceraciones" valuePropName="checked">
            <Checkbox>Laceraciones Identificadas</Checkbox>
          </Form.Item>
        </Col>

        <Col xs={24} sm={8}>
          <Form.Item name="coagulopatia" valuePropName="checked">
            <Checkbox>Coagulopatía Presente</Checkbox>
          </Form.Item>
        </Col>

        <Col xs={24}>
          <Divider orientation="left">Laboratorios</Divider>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="Hb Inicial (g/dL)"
            name="hemoglobina_inicial"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={5} max={18} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="Hb Actual (g/dL)"
            name="hemoglobina_actual"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={3} max={18} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="Plaquetas (/μL)"
            name="plaquetas"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={10000} max={500000} step={1000} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="Fibrinógeno (mg/dL)"
            name="fibrinogeno"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={50} max={600} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24}>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              <ThunderboltOutlined /> Evaluar Hemorragia
            </Button>
          </Form.Item>
        </Col>
      </Row>
    </Form>
  </Card>
);

export default HemorragiaForm;
