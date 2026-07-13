/**
 * =================================================================================
 * MODAL CAMBIAR CONTRASEÑA - ADMIN PUEDE CAMBIAR SIN CONTRASEÑA ACTUAL
 * =================================================================================
 */

import React, { useState } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import {Modal,
  Form,
  Input,
  Button,
  Space,
  Alert,
  Divider,
  Typography} from "antd";
import { LockOutlined, KeyOutlined } from '@ant-design/icons';
import { usuariosService, Usuario } from '../../services/usuariosService';

const { Text } = Typography;

interface ModalCambiarPasswordProps {
  open: boolean;
  usuario: Usuario;
  onClose: (reload?: boolean) => void;
}

const ModalCambiarPassword: React.FC<ModalCambiarPasswordProps> = ({
  open,
  usuario,
  onClose,
}) => {
  const { message } = useAntdApp();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: any) => {
    try {
      setLoading(true);

      // Validar que las contraseñas coincidan
      if (values.password_nueva !== values.password_nueva_confirm) {
        message.error('Las contraseñas no coinciden');
        return;
      }

      // Llamar al servicio para cambiar la contraseña (admin no requiere contraseña actual)
      await usuariosService.adminCambiarPassword(usuario.id!, {
        password_nueva: values.password_nueva,
        password_nueva_confirm: values.password_nueva_confirm,
      });

      message.success(`Contraseña de ${usuario.nombre_completo} actualizada correctamente`);
      form.resetFields();
      onClose(true);
    } catch (error: any) {
      if (error.response?.data) {
        const errors = error.response?.data;
        Object.keys(errors).forEach(key => {
          if (Array.isArray(errors[key])) {
            message.error(`${key}: ${errors[key].join(', ')}`);
          } else {
            message.error(`${key}: ${errors[key]}`);
          }
        });
      } else {
        message.error('Error al cambiar la contraseña');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onClose();
  };

  return (
    <Modal
      title={
        <Space>
          <KeyOutlined style={{ color: '#1890ff' }} />
          <span>Cambiar Contraseña</span>
        </Space>
      }
      open={open}
      onCancel={handleCancel}
      footer={null}
      width={500}
      destroyOnHidden
    >
      <Alert
        message="Cambio de Contraseña Administrativo"
        description={
          <>
            Está cambiando la contraseña de <strong>{usuario.nombre_completo}</strong>.
            <br />
            Como administrador, no necesita ingresar la contraseña actual del usuario.
          </>
        }
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Text type="secondary" style={{ display: 'block', marginBottom: 24, fontSize: 13 }}>
        Usuario: <strong>{usuario.nombre_completo}</strong> • Email: <strong>{usuario.email}</strong>
      </Text>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        <Form.Item
          name="password_nueva"
          label="Nueva Contraseña"
          rules={[
            { required: true, message: 'Ingrese la nueva contraseña' },
            { min: 8, message: 'La contraseña debe tener al menos 8 caracteres' },
          ]}
          hasFeedback
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="Ingrese la nueva contraseña"
            size="large"
          />
        </Form.Item>

        <Form.Item
          name="password_nueva_confirm"
          label="Confirmar Nueva Contraseña"
          dependencies={['password_nueva']}
          rules={[
            { required: true, message: 'Confirme la nueva contraseña' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password_nueva') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('Las contraseñas no coinciden'));
              },
            }),
          ]}
          hasFeedback
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="Confirme la nueva contraseña"
            size="large"
          />
        </Form.Item>

        <Divider />

        <Alert
          message="Requisitos de Seguridad"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              <li>Mínimo 8 caracteres</li>
              <li>Se recomienda usar mayúsculas, minúsculas, números y símbolos</li>
              <li>Evite contraseñas obvias o comunes</li>
            </ul>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
          <Space>
            <Button onClick={handleCancel} size="large">
              Cancelar
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              danger
              size="large"
              icon={<KeyOutlined />}
            >
              Cambiar Contraseña
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ModalCambiarPassword;
