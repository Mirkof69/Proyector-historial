import React from 'react';
import { Form, Row, Col, DatePicker, InputNumber, Select, Divider, Checkbox, Space, Input } from 'antd';
import { ExclamationCircleOutlined, WarningOutlined } from '@ant-design/icons';

const { Option } = Select;

interface SeccionAbortoProps {
  form: any;
  calcularAlertasYRecomendaciones: (eg: string) => void;
}

export const SeccionAborto: React.FC<SeccionAbortoProps> = ({ form, calcularAlertasYRecomendaciones }) => {
  return (
    <>
      <Divider orientation="left">
        <Space>
          <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
          <strong style={{ color: '#ff4d4f' }}>PROTOCOLO DE ABORTO</strong>
        </Space>
      </Divider>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item
            name="fecha_parto"
            label="Fecha del Evento"
            rules={[{ required: true, message: 'Ingrese fecha del evento' }]}
          >
            <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY HH:mm" showTime />
          </Form.Item>
        </Col>

        <Col span={8}>
          <Form.Item
            name="semanas_gestacion"
            label="Semanas"
            rules={[{ required: true, message: 'Ingrese semanas' }]}
          >
            <InputNumber
              placeholder="Ej: 12"
              min={1}
              max={19}
              style={{ width: '100%' }}
              onChange={(value) => {
                const dias = form.getFieldValue('dias_gestacion') || 0;
                if (value !== null) {
                  calcularAlertasYRecomendaciones(`${value}+${dias}`);
                }
              }}
            />
          </Form.Item>
        </Col>

        <Col span={8}>
          <Form.Item
            name="dias_gestacion"
            label="Días"
            rules={[{ required: true, message: 'Ingrese días' }]}
          >
            <InputNumber
              placeholder="Ej: 3"
              min={0}
              max={6}
              style={{ width: '100%' }}
              onChange={(value) => {
                const semanas = form.getFieldValue('semanas_gestacion') || 0;
                if (value !== null) {
                  calcularAlertasYRecomendaciones(`${semanas}+${value}`);
                }
              }}
            />
          </Form.Item>
        </Col>
      </Row>

      <Divider orientation="left" style={{ marginTop: 24 }}>Datos del Aborto</Divider>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="tipo_aborto"
            label="Tipo de Aborto"
            rules={[{ required: true, message: 'Seleccione tipo de aborto' }]}
            tooltip="Clasificación del tipo de aborto según hallazgos clínicos"
          >
            <Select placeholder="Seleccione tipo de aborto" size="large">
              <Option value="espontaneo">
                <Space><WarningOutlined style={{ color: '#faad14' }} />Espontáneo</Space>
              </Option>
              <Option value="inducido">
                <Space><ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />Inducido Terapéutico</Space>
              </Option>
              <Option value="incompleto">Incompleto</Option>
              <Option value="completo">Completo</Option>
              <Option value="diferido">Diferido/Retenido</Option>
              <Option value="inevitable">Inevitable</Option>
            </Select>
          </Form.Item>
        </Col>

        <Col span={12}>
          <Form.Item
            name="metodo_evacuacion"
            label="Método de Evacuación"
            rules={[{ required: true, message: 'Seleccione método de evacuación' }]}
            tooltip="Método utilizado para evacuación uterina"
          >
            <Select placeholder="Seleccione método" size="large">
              <Option value="aspiracion">Aspiración por Vacío (AMEU)</Option>
              <Option value="legrado">Legrado Uterino</Option>
              <Option value="medico">Método Médico (Misoprostol)</Option>
              <Option value="expectante">Manejo Expectante</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Divider orientation="left">Apoyo Psicológico y Duelo</Divider>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="apoyo_psicologico_realizado" valuePropName="checked">
            <Checkbox>✅ Se proporcionó apoyo psicológico</Checkbox>
          </Form.Item>
        </Col>

        <Col span={12}>
          <Form.Item name="protocolo_duelo_aplicado" valuePropName="checked">
            <Checkbox>✅ Se aplicó protocolo de duelo</Checkbox>
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="hemorragia_postparto" valuePropName="checked">
            <Checkbox>⚠️ Hemorragia post-evacuación</Checkbox>
          </Form.Item>
          <Form.Item name="perdida_sanguinea_estimada" label="Pérdida Sanguínea (mL)">
            <InputNumber min={0} step={50} placeholder="0" style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col span={12}>
          <Form.Item name="complicaciones_maternas" label="Complicaciones">
            <Input.TextArea rows={3} placeholder="Describa complicaciones si las hay" maxLength={500} showCount />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item name="observaciones_aborto" label="Observaciones del Aborto">
        <Input.TextArea rows={4} placeholder="Describa el manejo del aborto..." maxLength={1000} showCount />
      </Form.Item>

      <Divider orientation="left">Estado</Divider>
      <Form.Item name="parto_finalizado" valuePropName="checked" initialValue={true}>
        <Checkbox>Procedimiento finalizado</Checkbox>
      </Form.Item>
    </>
  );
};
