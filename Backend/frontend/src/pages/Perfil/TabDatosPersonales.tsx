import React from 'react';
import { Form, Row, Col, Input, Upload, Progress, Space, Button, Typography } from 'antd';
import type { FormInstance } from 'antd';
import type { UploadProps } from 'antd/es/upload/interface';
import {
  UserOutlined, PhoneOutlined, MailOutlined, UploadOutlined,
  SaveOutlined, EditOutlined, LogoutOutlined,
} from '@ant-design/icons';
import { Usuario } from './perfilTypes';

const { Text } = Typography;

interface TabDatosPersonalesProps {
  form: FormInstance;
  user: Usuario;
  updating: boolean;
  uploadProps: UploadProps;
  uploadProgress: number;
  onFinish: (values: any) => void;
  onDescartar: () => void;
  onLogout: () => void;
}

const TabDatosPersonales: React.FC<TabDatosPersonalesProps> = ({
  form, user, updating, uploadProps, uploadProgress, onFinish, onDescartar, onLogout,
}) => (
  <Form
    form={form}
    layout="vertical"
    onFinish={onFinish}
    initialValues={user}
  >
    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="nombre"
          label="Nombres"
          rules={[{ required: true, message: 'Los nombres son obligatorios' }]}
        >
          <Input prefix={<UserOutlined />} />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item
          name="apellido_paterno"
          label="Apellido Paterno"
          rules={[{ required: true, message: 'El apellido paterno es obligatorio' }]}
        >
          <Input />
        </Form.Item>
      </Col>
    </Row>
    <Row gutter={16}>
      <Col span={12}>
        <Form.Item name="apellido_materno" label="Apellido Materno">
          <Input />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item name="telefono" label="Teléfono">
          <Input prefix={<PhoneOutlined />} />
        </Form.Item>
      </Col>
    </Row>

    <Form.Item
      name="email"
      label="Correo Electrónico"
      rules={[{ required: true, type: 'email', message: 'Ingrese un email válido' }]}
    >
      <Input
        prefix={<MailOutlined />}
        disabled
        title="El email no puede ser modificado"
      />
    </Form.Item>

    <Form.Item label="Foto de Perfil">
      {uploadProgress > 0 && uploadProgress < 100 && (
        <Progress percent={uploadProgress} style={{ marginBottom: 12 }} />
      )}
      <Upload {...uploadProps} listType="picture-card" maxCount={1}>
        <div>
          <UploadOutlined style={{ fontSize: 24 }} />
          <div style={{ marginTop: 8 }}>Subir Foto</div>
        </div>
      </Upload>
      <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
        JPG o PNG, máximo 2MB. Se guarda al hacer clic en "Guardar Cambios".
      </Text>
    </Form.Item>

    <Form.Item>
      <Space>
        <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={updating}>
          Guardar Cambios
        </Button>
        <Button onClick={onDescartar} icon={<EditOutlined />}>
          Descartar
        </Button>
        <Button danger icon={<LogoutOutlined />} onClick={onLogout}>
          Cerrar Sesión
        </Button>
      </Space>
    </Form.Item>
  </Form>
);

export default TabDatosPersonales;
