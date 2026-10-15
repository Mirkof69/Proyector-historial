import React from 'react';
import { Form, Row, Col, Select, InputNumber, Divider, Button, Card } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';

const { Option } = Select;

interface SeccionRecienNacidoProps {
  tipoEvento: 'aborto' | 'parto' | null;
  /** Partos múltiples: solo al registrar (la edición toca el primer bebé). */
  permitirVarios?: boolean;
}

export const SeccionRecienNacido: React.FC<SeccionRecienNacidoProps> = ({ tipoEvento, permitirVarios = false }) => {
  if (tipoEvento !== 'parto') return null;

  return (
    <>
      <Divider orientation="left">Datos del Recién Nacido</Divider>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item
            name="sexo_bebe"
            label="Sexo"
            rules={[{ required: true, message: 'Seleccione sexo' }]}
          >
            <Select placeholder="Seleccione sexo">
              <Option value="masculino">Masculino</Option>
              <Option value="femenino">Femenino</Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item
            name="peso_bebe"
            label="Peso (g)"
            rules={[{ required: true, message: 'Ingrese peso' }]}
          >
            <InputNumber min={300} max={6000} className="partos-ancho" placeholder="3200" />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item
            name="talla_bebe"
            label="Talla (cm)"
            rules={[{ required: true, message: 'Ingrese talla' }]}
          >
            <InputNumber min={20} max={60} step={0.1} className="partos-ancho" placeholder="50.0" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="apgar_1min"
            label="Apgar 1 min"
            rules={[{ required: true, message: 'Ingrese Apgar 1 min' }]}
          >
            <InputNumber min={0} max={10} className="partos-ancho" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="apgar_5min"
            label="Apgar 5 min"
            rules={[{ required: true, message: 'Ingrese Apgar 5 min' }]}
          >
            <InputNumber min={0} max={10} className="partos-ancho" />
          </Form.Item>
        </Col>
      </Row>

      {/* Parto múltiple: antes solo se podía registrar un recién nacido. */}
      {permitirVarios && (
        <Form.List name="otros_recien_nacidos">
          {(campos, { add, remove }) => (
            <>
              {campos.map(({ key, name }, i) => (
                <Card
                  key={key}
                  size="small"
                  title={`Recién nacido ${i + 2} (parto múltiple)`}
                  className="partos-separado-sm"
                  extra={<Button type="text" danger icon={<DeleteOutlined />} onClick={() => remove(name)}
                    aria-label={`Quitar recién nacido ${i + 2}`} />}
                >
                  <Row gutter={16}>
                    <Col span={8}>
                      <Form.Item name={[name, 'sexo']} label="Sexo" rules={[{ required: true, message: 'Seleccione sexo' }]}>
                        <Select placeholder="Seleccione sexo">
                          <Option value="masculino">Masculino</Option>
                          <Option value="femenino">Femenino</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name={[name, 'peso_nacimiento']} label="Peso (g)" rules={[{ required: true, message: 'Ingrese peso' }]}>
                        <InputNumber min={300} max={6000} className="partos-ancho" placeholder="2400" />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item name={[name, 'talla_nacimiento']} label="Talla (cm)" rules={[{ required: true, message: 'Ingrese talla' }]}>
                        <InputNumber min={20} max={60} step={0.1} className="partos-ancho" placeholder="46.0" />
                      </Form.Item>
                    </Col>
                  </Row>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name={[name, 'apgar_1_minuto']} label="Apgar 1 min" rules={[{ required: true, message: 'Ingrese Apgar 1 min' }]}>
                        <InputNumber min={0} max={10} className="partos-ancho" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name={[name, 'apgar_5_minutos']} label="Apgar 5 min" rules={[{ required: true, message: 'Ingrese Apgar 5 min' }]}>
                        <InputNumber min={0} max={10} className="partos-ancho" />
                      </Form.Item>
                    </Col>
                  </Row>
                </Card>
              ))}
              <Button type="dashed" block icon={<PlusOutlined />} onClick={() => add()}>
                Agregar otro recién nacido (gemelar / múltiple)
              </Button>
            </>
          )}
        </Form.List>
      )}
    </>
  );
};
