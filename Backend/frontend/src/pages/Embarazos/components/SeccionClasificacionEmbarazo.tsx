import React from 'react';
import { Divider, Row, Col, Form, Select, InputNumber, Space, Tag } from 'antd';
import type { FormInstance } from 'antd';

const { Option } = Select;

const SeccionClasificacionEmbarazo: React.FC<{ form: FormInstance }> = ({ form }) => (
  <>
    <Divider orientation="left">Clasificacion del Embarazo</Divider>

    <Row gutter={16}>
      <Col span={12}>
        <Form.Item name="tipo_embarazo" label="Tipo de Embarazo" initialValue="simple">
          <Select placeholder="Seleccione tipo">
            <Option value="simple">Simple</Option>
            <Option value="gemelar">Gemelar</Option>
            <Option value="multiple">Multiple</Option>
          </Select>
        </Form.Item>
      </Col>

      <Col span={12}>
        <Form.Item
          name="riesgo_embarazo"
          label={
            <Space>
              Clasificacion de Riesgo
              {form.getFieldValue('riesgo_embarazo') && (
                <Tag color={
                  form.getFieldValue('riesgo_embarazo') === 'bajo' ? 'success' :
                    form.getFieldValue('riesgo_embarazo') === 'medio' ? 'warning' :
                      'error'
                }>
                  {form.getFieldValue('riesgo_embarazo')?.toUpperCase()}
                </Tag>
              )}
            </Space>
          }
          initialValue="bajo"
        >
          <Select placeholder="Seleccione riesgo" onChange={() => form.validateFields(['riesgo_embarazo'])}>
            <Option value="bajo">Bajo Riesgo</Option>
            <Option value="medio">Riesgo Medio</Option>
            <Option value="alto">Alto Riesgo</Option>
          </Select>
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col span={24}>
        <Form.Item
          name="estado"
          label={
            <Space>
              Estado
              {form.getFieldValue('estado') && (
                <Tag color={
                  form.getFieldValue('estado') === 'activo' ? 'processing' :
                    form.getFieldValue('estado') === 'finalizado' ? 'success' :
                      'error'
                }>
                  {form.getFieldValue('estado')?.toUpperCase()}
                </Tag>
              )}
            </Space>
          }
          initialValue="activo"
        >
          <Select placeholder="Seleccione estado" onChange={() => form.validateFields(['estado'])}>
            <Option value="activo">Activo</Option>
            <Option value="finalizado">Finalizado</Option>
            <Option value="perdida">Perdida</Option>
          </Select>
        </Form.Item>
      </Col>
    </Row>

    <Divider orientation="left">Historial Obstetrico</Divider>

    <Row gutter={16}>
      <Col span={8}>
        <Form.Item
          name="numero_abortos"
          label="Numero de Abortos"
          rules={[{ type: 'number', min: 0, message: 'Debe ser número positivo o cero' }]}
        >
          <InputNumber style={{ width: '100%' }} placeholder="0" min={0} onChange={() => form.validateFields(['numero_gesta'])} />
        </Form.Item>
      </Col>

      <Col span={8}>
        <Form.Item
          name="numero_cesareas"
          label="Numero de Cesareas"
          rules={[{ type: 'number', min: 0, message: 'Debe ser número positivo o cero' }]}
        >
          <InputNumber style={{ width: '100%' }} placeholder="0" min={0} />
        </Form.Item>
      </Col>

      <Col span={8}>
        <Form.Item
          name="numero_para"
          label="Numero de Para"
          rules={[
            { type: 'number', min: 0, message: 'Debe ser número positivo o cero' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                const gesta = getFieldValue('numero_gesta');
                if (value !== undefined && gesta !== undefined && value > gesta) {
                  return Promise.reject('Los partos no pueden superar las gestas');
                }
                return Promise.resolve();
              }
            })
          ]}
        >
          <InputNumber style={{ width: '100%' }} placeholder="0" min={0} onChange={() => form.validateFields(['numero_gesta'])} />
        </Form.Item>
      </Col>
    </Row>
  </>
);

export default SeccionClasificacionEmbarazo;
