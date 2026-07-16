import React from 'react';
import { Alert, Form, Input, Divider, Space, Button } from 'antd';
import type { FormInstance } from 'antd';
import { LockOutlined, KeyOutlined, CheckOutlined, EditOutlined } from '@ant-design/icons';

interface TabSeguridadProps {
  form: FormInstance;
  updating: boolean;
  onFinish: (values: any) => void;
}

const TabSeguridad: React.FC<TabSeguridadProps> = ({ form, updating, onFinish }) => (
  <>
    <Alert
      message="Zona de Seguridad"
      description="Asegúrese de usar una contraseña robusta con al menos 8 caracteres, letras, números y caracteres especiales."
      type="warning"
      showIcon
      style={{ marginBottom: 20 }}
    />

    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      style={{ maxWidth: 500 }}
    >
      <Form.Item
        name="currentPassword"
        label="Contraseña Actual"
        rules={[{ required: true, message: 'Requerida para confirmar su identidad' }]}
      >
        <Input.Password prefix={<LockOutlined />} />
      </Form.Item>

      <Divider />

      <Form.Item
        name="newPassword"
        label="Nueva Contraseña"
        rules={[{ required: true, min: 8, message: 'Mínimo 8 caracteres' }]}
      >
        <Input.Password prefix={<KeyOutlined />} />
      </Form.Item>

      <Form.Item
        name="confirmPassword"
        label="Confirmar Nueva Contraseña"
        dependencies={['newPassword']}
        rules={[
          { required: true, message: 'Confirme la contraseña' },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('newPassword') === value) {
                return Promise.resolve();
              }
              return Promise.reject(new Error('Las contraseñas no coinciden'));
            },
          }),
        ]}
      >
        <Input.Password prefix={<KeyOutlined />} />
      </Form.Item>

      <Form.Item>
        <Space>
          <Button type="primary" danger htmlType="submit" icon={<CheckOutlined />} loading={updating}>
            Actualizar Contraseña
          </Button>
          <Button onClick={() => form.resetFields()} icon={<EditOutlined />}>
            Limpiar
          </Button>
        </Space>
      </Form.Item>
    </Form>
  </>
);

export default TabSeguridad;
