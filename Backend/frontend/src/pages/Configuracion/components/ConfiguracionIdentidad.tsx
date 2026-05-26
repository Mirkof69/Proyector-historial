import React from 'react';
import { Card, Form, Input, Button, Upload, Divider, Row, Col, Typography } from 'antd';
import { useAntdApp } from '../../../hooks/useMessage';
import { ShopOutlined, SaveOutlined, UploadOutlined } from '@ant-design/icons';

const { Paragraph } = Typography;
const { TextArea } = Input;

interface ConfiguracionIdentidadProps {
  form: any;
  saving: boolean;
  onSave: (values: any) => void;
  logoFileRef: any;
  configData: any;
}

const ConfiguracionIdentidad: React.FC<ConfiguracionIdentidadProps> = ({ form, saving, onSave, logoFileRef, configData }) => {
  const { message } = useAntdApp();
  const shopIcon = <ShopOutlined />;
  const uploadIcon = <UploadOutlined />;
  const saveIcon = <SaveOutlined />;

  return (
    <Card className="shadow-sm">
      <Form form={form} layout="vertical" onFinish={onSave}>
        <Row gutter={32}>
          <Col xs={24} lg={16}>
            <Divider orientation="left">Datos de la Institución</Divider>
            <Row gutter={16}>
              <Col span={24}>
                <Form.Item name="nombre_clinica" label="Nombre de la Clínica / Consultorio" rules={[{ required: true }]}>
                  <Input size="large" prefix={shopIcon} />
                </Form.Item>
              </Col>
              <Col span={24}>
                <Form.Item name="direccion" label="Dirección Física">
                  <TextArea rows={2} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="telefono_contacto" label="Teléfono Principal">
                  <Input />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="email_contacto" label="Email Público">
                  <Input />
                </Form.Item>
              </Col>
            </Row>
          </Col>

          <Col xs={24} lg={8} style={{ textAlign: 'center', borderLeft: '1px solid #f0f0f0' }}>
            <Divider orientation="center">Logo Oficial</Divider>
            <div style={{ marginBottom: 20 }}>
              <img
                src={configData?.logo_url || "https://via.placeholder.com/150?text=LOGO"}
                alt="Logo Actual"
                style={{ width: 150, height: 150, objectFit: 'contain', borderRadius: 8, border: '1px dashed #d9d9d9', padding: 10 }}
              />
            </div>
            <Upload maxCount={1} beforeUpload={() => false} onChange={(info) => { logoFileRef.current = info.file; }}>
              <Button icon={uploadIcon}>Subir Nuevo Logo</Button>
            </Upload>
            <Paragraph type="secondary" style={{ fontSize: 12, marginTop: 10 }}>
              Recomendado: PNG transparente, 300x300px. Se usará en recetas y reportes.
            </Paragraph>
          </Col>
        </Row>

        <Divider />

        <Row justify="end">
          <Button type="primary" htmlType="submit" icon={saveIcon} size="large" loading={saving}>
            Guardar Configuración General
          </Button>
        </Row>
      </Form>
    </Card>
  );
};

export default ConfiguracionIdentidad;
