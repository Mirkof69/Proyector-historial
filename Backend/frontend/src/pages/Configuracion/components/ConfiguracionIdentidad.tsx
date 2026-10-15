import React from 'react';
import { Card, Form, Input, Button, Upload, Divider, Row, Col, Typography } from 'antd';
import { useAntdApp } from '../../../hooks/useMessage';
import { ShopOutlined, SaveOutlined, UploadOutlined, PictureOutlined } from '@ant-design/icons';

const { Paragraph } = Typography;
const { TextArea } = Input;

interface ConfiguracionIdentidadProps {
  form: any;
  saving: boolean;
  onSave: (values: any) => void;
  logoFileRef: any;
  configData: any;
}

const SHOP_ICON = <ShopOutlined />;
const UPLOAD_ICON = <UploadOutlined />;
const SAVE_ICON = <SaveOutlined />;

const ConfiguracionIdentidad: React.FC<ConfiguracionIdentidadProps> = ({ form, saving, onSave, logoFileRef, configData }) => {
  const { message } = useAntdApp();

  return (
    <Card>
      <Form form={form} layout="vertical" onFinish={onSave}>
        <Row gutter={32}>
          <Col xs={24} lg={16}>
            <Divider orientation="left">Datos de la Institución</Divider>
            <Row gutter={16}>
              <Col span={24}>
                <Form.Item name="nombre_clinica" label="Nombre de la Clínica / Consultorio" rules={[{ required: true }]}>
                  <Input size="large" prefix={SHOP_ICON} />
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

          <Col xs={24} lg={8} className="configuracion-page__logo">
            <Divider orientation="center">Logo Oficial</Divider>
            {/* Sin logo cargado: marcador local (antes se pedía una imagen a
                via.placeholder.com, que no carga en la red del hospital). */}
            {configData?.logo_url
              ? <img src={configData.logo_url} alt="Logo Actual" className="configuracion-page__logo-imagen" />
              : <div className="configuracion-page__logo-imagen" role="img" aria-label="Logo Actual"><PictureOutlined /> LOGO</div>}
            <Upload maxCount={1} beforeUpload={() => false} onChange={(info) => { logoFileRef.current = info.file; }}>
              <Button icon={UPLOAD_ICON}>Subir Nuevo Logo</Button>
            </Upload>
            <Paragraph type="secondary" className="configuracion-page__ayuda">
              Recomendado: PNG transparente, 300x300px. Se usará en recetas y reportes.
            </Paragraph>
          </Col>
        </Row>

        <Divider />

        <Row justify="end">
          <Button type="primary" htmlType="submit" icon={SAVE_ICON} loading={saving}>
            Guardar Configuración General
          </Button>
        </Row>
      </Form>
    </Card>
  );
};

export default ConfiguracionIdentidad;
