/**
 * =============================================================================
 * FORMULARIO DE USUARIO
 * =============================================================================
 * Formulario completo para crear/editar usuarios del sistema
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import {Form,
  Input,
  Select,
  Button,
  Space,
  Card,
  Divider,
  Switch,
  Upload,
  Avatar,
  Spin} from "antd";
import {
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  SafetyOutlined,
  UploadOutlined,
  LockOutlined,
} from '@ant-design/icons';
import { usuariosService, Usuario, UsuarioCreate, UsuarioUpdate } from '../../services/usuariosService';

const { Option } = Select;
const { TextArea } = Input;

interface FormularioUsuarioProps {
  usuario?: Usuario | null;
  onClose: (reload?: boolean) => void;
}

const ROLES = [
  { value: 'medico', label: 'Médico' },
  { value: 'enfermero', label: 'Enfermero' },
  { value: 'enfermera', label: 'Enfermera' },
  { value: 'administrador', label: 'Administrador' },
  { value: 'recepcion', label: 'Recepción' },
  { value: 'laboratorista', label: 'Laboratorista' },
];

const ESPECIALIDADES = [
  'Medicina General',
  'Ginecología y Obstetricia',
  'Pediatría',
  'Medicina Interna',
  'Cardiología',
  'Traumatología',
  'Neurología',
  'Dermatología',
  'Oftalmología',
  'Otorrinolaringología',
  'Urología',
  'Cirugía General',
  'Anestesiología',
  'Radiología',
  'Laboratorio Clínico',
];

const FormularioUsuario: React.FC<FormularioUsuarioProps> = ({ usuario, onClose }) => {
  const { message } = useAntdApp();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedFotoPreview, setSelectedFotoPreview] = useState<string | null>(null);
  const fotoPreview = selectedFotoPreview || usuario?.foto_url || null;

  // Patrón oficial de React para ajustar estado al cambiar una prop (sin ref
  // mutado en render): guardar el id previo en estado y comparar.
  const [prevUsuarioId, setPrevUsuarioId] = useState<number | undefined>(usuario?.id);
  if (usuario?.id !== prevUsuarioId) {
    setPrevUsuarioId(usuario?.id);
    setSelectedFotoPreview(null);
  }

  const isEditing = !!usuario;

  // eslint-disable-next-line react-doctor/no-adjust-state-on-prop-change
  useEffect(() => {
    if (usuario) {
      form.setFieldsValue({
        nombre: usuario.nombre,
        apellido_paterno: usuario.apellido_paterno,
        apellido_materno: usuario.apellido_materno,
        email: usuario.email,
        rol: usuario.rol,
        especialidad: usuario.especialidad,
        telefono: usuario.telefono,
        descripcion: usuario.descripcion,
        activo: usuario.activo,
        is_staff: usuario.is_staff,
      });
    } else {
      form.resetFields();
      form.setFieldsValue({ activo: true, is_staff: false });
    }
  }, [usuario, form]);

  const handleSubmit = async (values: any) => {
    setSaving(true);
    try {
      if (isEditing && usuario?.id) {
        const updateData: UsuarioUpdate = {
          nombre: values.nombre,
          apellido_paterno: values.apellido_paterno,
          apellido_materno: values.apellido_materno,
          email: values.email,
          rol: values.rol,
          especialidad: values.especialidad,
          telefono: values.telefono,
          descripcion: values.descripcion,
          activo: values.activo,
          is_staff: values.is_staff,
        };
        await usuariosService.update(usuario.id, updateData);
        message.success('Usuario actualizado correctamente');
      } else {
        const createData: UsuarioCreate = {
          nombre: values.nombre,
          apellido_paterno: values.apellido_paterno,
          apellido_materno: values.apellido_materno,
          email: values.email,
          password: values.password,
          password_confirm: values.password_confirm,
          rol: values.rol,
          especialidad: values.especialidad,
          telefono: values.telefono,
          descripcion: values.descripcion,
          activo: values.activo,
          is_staff: values.is_staff,
        };
        await usuariosService.create(createData);
        message.success('Usuario creado correctamente');
      }
      onClose(true);
    } catch (error: any) {
      const errorMsg = error?.response?.data?.message || error?.response?.data?.error || 'Error al guardar el usuario';
      message.error(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit}>
      <Divider orientation="left">Información Personal</Divider>

      <Form.Item
        label="Foto de Perfil"
        extra="Formatos aceptados: JPG, PNG. Tamaño máximo: 2MB"
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Avatar size={64} icon={<UserOutlined />} src={fotoPreview} />
          <Upload
            accept="image/*"
            showUploadList={false}
            beforeUpload={(file) => {
              if (file.size > 2 * 1024 * 1024) {
                message.error('La imagen no debe superar los 2MB');
                return false;
              }
              const reader = new FileReader();
              reader.onload = (e) => setSelectedFotoPreview(e.target?.result as string);
              reader.readAsDataURL(file);
              return false;
            }}
          >
            <Button icon={<UploadOutlined />}>Seleccionar Imagen</Button>
          </Upload>
        </div>
      </Form.Item>

      <Form.Item
        label="Nombre"
        name="nombre"
        rules={[{ required: true, message: 'Ingrese el nombre' }]}
      >
        <Input prefix={<UserOutlined />} placeholder="Nombre" />
      </Form.Item>

      <Form.Item
        label="Apellido Paterno"
        name="apellido_paterno"
        rules={[{ required: true, message: 'Ingrese el apellido paterno' }]}
      >
        <Input placeholder="Apellido Paterno" />
      </Form.Item>

      <Form.Item
        label="Apellido Materno"
        name="apellido_materno"
      >
        <Input placeholder="Apellido Materno (opcional)" />
      </Form.Item>

      <Form.Item
        label="Email"
        name="email"
        rules={[
          { required: true, message: 'Ingrese el email' },
          { type: 'email', message: 'Ingrese un email válido' },
        ]}
      >
        <Input prefix={<MailOutlined />} placeholder="correo@ejemplo.com" />
      </Form.Item>

      {!isEditing && (
        <>
          <Divider orientation="left">Contraseña</Divider>
          <Form.Item
            label="Contraseña"
            name="password"
            rules={[
              { required: true, message: 'Ingrese la contraseña' },
              { min: 8, message: 'La contraseña debe tener al menos 8 caracteres' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Contraseña" />
          </Form.Item>

          <Form.Item
            label="Confirmar Contraseña"
            name="password_confirm"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Confirme la contraseña' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Las contraseñas no coinciden'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Confirmar contraseña" />
          </Form.Item>
        </>
      )}

      <Divider orientation="left">Información Profesional</Divider>

      <Form.Item
        label="Rol"
        name="rol"
        rules={[{ required: true, message: 'Seleccione el rol' }]}
      >
        <Select prefix={<SafetyOutlined />} placeholder="Seleccione un rol">
          {ROLES.map((rol) => (
            <Option key={rol.value} value={rol.value}>
              {rol.label}
            </Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item
        label="Especialidad"
        name="especialidad"
      >
        <Select placeholder="Seleccione una especialidad" allowClear showSearch>
          {ESPECIALIDADES.map((esp) => (
            <Option key={esp} value={esp}>
              {esp}
            </Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item
        label="Teléfono"
        name="telefono"
      >
        <Input prefix={<PhoneOutlined />} placeholder="Número de teléfono" />
      </Form.Item>

      <Form.Item
        label="Descripción"
        name="descripcion"
      >
        <TextArea rows={3} placeholder="Descripción opcional del usuario" />
      </Form.Item>

      <Divider orientation="left">Configuración</Divider>

      <Form.Item label="Usuario Activo" name="activo" valuePropName="checked">
        <Switch checkedChildren="Activo" unCheckedChildren="Inactivo" />
      </Form.Item>

      <Form.Item label="Es Staff" name="is_staff" valuePropName="checked">
        <Switch checkedChildren="Staff" unCheckedChildren="No Staff" />
      </Form.Item>

      <Divider />

      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" loading={saving}>
            {isEditing ? 'Actualizar' : 'Crear'} Usuario
          </Button>
          <Button onClick={() => onClose()}>Cancelar</Button>
        </Space>
      </Form.Item>
    </Form>
  );
};

export default FormularioUsuario;
