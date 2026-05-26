import React from 'react';
import { Form, InputNumber, Button, Row, Col, Divider, Alert, Radio, Select } from 'antd';
import { ThunderboltOutlined } from '@ant-design/icons';

const { Option } = Select;

interface FormularioBienestarFetalProps {
  loading: boolean;
}

export const FormularioBienestarFetal: React.FC<FormularioBienestarFetalProps> = ({ loading }) => {
  return (
    <>
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Divider orientation="left">Datos Generales</Divider>
        </Col>

        <Col xs={24} sm={12}>
          <Form.Item
            label="Edad Gestacional (semanas)"
            name="edad_gestacional"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={24} max={42} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12}>
          <Form.Item
            label="Peso Estimado Fetal (Percentil)"
            name="peso_estimado_percentil"
            rules={[{ required: true, message: 'Requerido' }]}
            tooltip="Percentil según curvas de crecimiento"
          >
            <InputNumber min={1} max={99} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24}>
          <Divider orientation="left">Cardiotocografía (CTG)</Divider>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Form.Item
            label="FCF Basal (lpm)"
            name="fcf_basal"
            rules={[{ required: true, message: 'Requerido' }]}
            tooltip="Frecuencia cardíaca fetal basal (normal 110-160)"
          >
            <InputNumber min={80} max={200} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Form.Item
            label="Variabilidad FCF (lpm)"
            name="variabilidad_fcf"
            rules={[{ required: true, message: 'Requerido' }]}
            tooltip="Amplitud de variabilidad (normal 6-25 lpm)"
          >
            <InputNumber min={0} max={50} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Form.Item
            label="Aceleraciones en 20 min"
            name="aceleraciones_20min"
            rules={[{ required: true, message: 'Requerido' }]}
            tooltip="Número de aceleraciones ≥15 lpm por ≥15 seg (reactivo: ≥2)"
          >
            <InputNumber min={0} max={20} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12}>
          <Form.Item
            label="Tipo de Desaceleraciones"
            name="desaceleraciones_tipo"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <Select>
              <Option value="ninguna">✅ Ninguna</Option>
              <Option value="tempranas">⚪ Tempranas (compresión cefálica)</Option>
              <Option value="variables">⚠️ Variables (compresión cordón)</Option>
              <Option value="tardias">🔴 Tardías (insuficiencia uteroplacentaria)</Option>
            </Select>
          </Form.Item>
        </Col>

        <Col xs={24} sm={12}>
          <Form.Item
            label="Contracciones en 10 min"
            name="contracciones_10min"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber min={0} max={10} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24}>
          <Divider orientation="left">Perfil Biofísico (Manning)</Divider>
          <Alert
            message="Cada componente: 2 puntos si normal, 0 si anormal. Total 0-10 puntos."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item label="NST Reactivo" name="nst_reactivo" valuePropName="checked">
            <Radio.Group>
              <Radio value={true}>Sí (2 pts)</Radio>
              <Radio value={false}>No (0 pts)</Radio>
            </Radio.Group>
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="Movimientos Respiratorios"
            name="movimientos_respiratorios"
            valuePropName="checked"
            tooltip="≥1 episodio ≥30 seg en 30 min"
          >
            <Radio.Group>
              <Radio value={true}>Sí (2 pts)</Radio>
              <Radio value={false}>No (0 pts)</Radio>
            </Radio.Group>
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="Movimientos Corporales"
            name="movimientos_corporales"
            valuePropName="checked"
            tooltip="≥3 movimientos discretos en 30 min"
          >
            <Radio.Group>
              <Radio value={true}>Sí (2 pts)</Radio>
              <Radio value={false}>No (0 pts)</Radio>
            </Radio.Group>
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="Tono Fetal"
            name="tono_fetal"
            valuePropName="checked"
            tooltip="≥1 extensión/flexión de extremidades"
          >
            <Radio.Group>
              <Radio value={true}>Sí (2 pts)</Radio>
              <Radio value={false}>No (0 pts)</Radio>
            </Radio.Group>
          </Form.Item>
        </Col>

        <Col xs={24} sm={12}>
          <Form.Item
            label="Volumen de Líquido Amniótico - AFI (cm)"
            name="volumen_liquido"
            rules={[{ required: true, message: 'Requerido' }]}
            tooltip="Índice de Líquido Amniótico. Normal ≥5 cm (2 pts), <5 cm (0 pts)"
          >
            <InputNumber min={0} max={30} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12}>
          <Form.Item name="oligohidramnios" valuePropName="checked">
            <Radio.Group>
              <Radio value={false}>Líquido Normal</Radio>
              <Radio value={true}>Oligohidramnios</Radio>
            </Radio.Group>
          </Form.Item>
        </Col>

        <Col xs={24}>
          <Divider orientation="left">Estudios Doppler</Divider>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="AU - PI"
            name="arteria_umbilical_pi"
            rules={[{ required: true, message: 'Requerido' }]}
            tooltip="Arteria Umbilical - Índice de Pulsatilidad (normal <1.4)"
          >
            <InputNumber min={0} max={3} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="AU - RI"
            name="arteria_umbilical_ri"
            rules={[{ required: true, message: 'Requerido' }]}
            tooltip="Arteria Umbilical - Índice de Resistencia (normal <0.7)"
          >
            <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item
            label="ACM - PI"
            name="arteria_cerebral_media_pi"
            rules={[{ required: true, message: 'Requerido' }]}
            tooltip="Arteria Cerebral Media - PI (normal >1.0, <1.0 = centralización)"
          >
            <InputNumber min={0} max={4} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Form.Item label="Ductus Venoso" name="ductus_venoso_normal" valuePropName="checked">
            <Radio.Group>
              <Radio value={true}>Normal</Radio>
              <Radio value={false}>Anormal</Radio>
            </Radio.Group>
          </Form.Item>
        </Col>

        <Col xs={24}>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              <ThunderboltOutlined /> Evaluar Bienestar Fetal
            </Button>
          </Form.Item>
        </Col>
      </Row>
    </>
  );
};
