// ===========================================
// FORMULARIO DE USUARIO - CREAR/EDITAR
// ===========================================
// Componente completo para gestión de usuarios del sistema
// Incluye roles, permisos y validación de contraseñas

import React, { useEffect, useState } from 'react';
import {
  Form,
  Input,
  Select,
  Button,
  Card,
  Row,
  Col,
  message,
  Spin,
  Divider,
  Switch
} from 'antd';
import { SaveOutlined, ArrowLeftOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { UsuariosService } from '../../services/api';
import { Usuario } from '../../types';

const { Option } = Select;
const { TextArea } = Input;

// Componente principal del formulario
const UsuarioForm: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const isEditing = !!id;

  // Efecto para cargar datos al editar
  useEffect(() => {
    if (isEditing) {
      fetchUsuario();
    }
  }, [id]);

  // Obtener datos del usuario al editar
  const fetchUsuario = async () => {
    setLoading(true);
    try {
      const response = await UsuariosService.getById(Number(id));
      const usuario: Usuario = response.data;

      // Transformar los datos para el formulario
      form.setFieldsValue({
        username: usuario.username,
        nombre_completo: usuario.nombre_completo,
        email: usuario.email,
        rol: usuario.rol,
        estado: usuario.estado,
        telefono: usuario.telefono,
        cedula_identidad: usuario.cedula_identidad,
        especialidad: usuario.especialidad,
        numero_registro_profesional: usuario.numero_registro_profesional,
        observaciones: usuario.observaciones,
      });
    } catch (error) {
      message.error('Error al cargar datos del usuario');
      navigate('/usuarios');
    } finally {
      setLoading(false);
    }
  };

  // Función para guardar (crear o actualizar)
  const handleSubmit = async (values: any) => {
    // Validar contraseñas si se está creando
    if (!isEditing) {
      if (!values.password) {
        message.error('La contraseña es requerida');
        return;
      }
      if (values.password !== values.password_confirm) {
        message.error('Las contraseñas no coinciden');
        return;
      }
    }

    // Validar contraseñas si se está cambiando
    if (isEditing && values.password) {
      if (values.password !== values.password_confirm) {
        message.error('Las contraseñas no coinciden');
        return;
      }
    }

    setSaving(true);
    try {
      // Preparar datos para enviar (omitir password_confirm)
      const { password_confirm, ...data } = values;

      // Si está editando y no cambió la contraseña, omitirla
      if (isEditing && !data.password) {
        delete data.password;
      }

      if (isEditing) {
        await UsuariosService.update(Number(id), data);
        message.success('Usuario actualizado exitosamente');
      } else {
        await UsuariosService.create(data);
        message.success('Usuario creado exitosamente');
      }

      navigate('/usuarios');
    } catch (error: any) {
      console.error('Error al guardar:', error);

      // Manejo de errores específicos
      if (error.response?.data) {
        const errors = error.response.data;
        Object.keys(errors).forEach(key => {
          const errorMessage = Array.isArray(errors[key]) ? errors[key][0] : errors[key];
          message.error(`${key}: ${errorMessage}`);
        });
      } else {
        message.error('Error al guardar usuario');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <div>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/usuarios')}
              style={{ marginRight: 16 }}
            />
            {isEditing ? 'Editar Usuario' : 'Nuevo Usuario'}
          </div>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            rol: 'medico',
            estado: 'activo',
          }}
        >
          <Divider orientation="left">Información de Cuenta</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Nombre de Usuario"
                name="username"
                rules={[
                  { required: true, message: 'Campo requerido' },
                  { min: 3, message: 'Mínimo 3 caracteres' },
                ]}
              >
                <Input placeholder="usuario123" disabled={isEditing} />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Email"
                name="email"
                rules={[
                  { required: true, message: 'Campo requerido' },
                  { type: 'email', message: 'Email inválido' },
                ]}
              >
                <Input type="email" placeholder="correo@ejemplo.com" />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Nombre Completo"
                name="nombre_completo"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Input placeholder="Dr. Juan Pérez" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">
            <LockOutlined /> Contraseña {isEditing && '(dejar en blanco para no cambiar)'}
          </Divider>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="Contraseña"
                name="password"
                rules={
                  !isEditing
                    ? [
                        { required: true, message: 'Campo requerido' },
                        { min: 8, message: 'Mínimo 8 caracteres' },
                      ]
                    : []
                }
              >
                <Input.Password placeholder="Ingrese contraseña" />
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Form.Item
                label="Confirmar Contraseña"
                name="password_confirm"
                dependencies={['password']}
                rules={
                  !isEditing
                    ? [{ required: true, message: 'Confirme la contraseña' }]
                    : []
                }
              >
                <Input.Password placeholder="Confirme contraseña" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Rol y Permisos</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Rol"
                name="rol"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Select>
                  <Option value="administrador">Administrador</Option>
                  <Option value="medico">Médico</Option>
                  <Option value="enfermera">Enfermera</Option>
                  <Option value="recepcionista">Recepcionista</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Estado"
                name="estado"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Select>
                  <Option value="activo">Activo</Option>
                  <Option value="inactivo">Inactivo</Option>
                  <Option value="bloqueado">Bloqueado</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Datos Personales</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Cédula de Identidad"
                name="cedula_identidad"
              >
                <Input placeholder="CI del usuario" />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Teléfono"
                name="telefono"
              >
                <Input placeholder="+591 12345678" />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Especialidad"
                name="especialidad"
              >
                <Input placeholder="Ej: Ginecología, Pediatría" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="Número de Registro Profesional"
                name="numero_registro_profesional"
              >
                <Input placeholder="Número de matrícula profesional" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Observaciones</Divider>

          <Form.Item
            label="Observaciones"
            name="observaciones"
          >
            <TextArea
              rows={4}
              placeholder="Observaciones sobre el usuario, horarios, etc."
            />
          </Form.Item>

          {/* Botones de acción */}
          <Form.Item>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <Button onClick={() => navigate('/usuarios')}>
                Cancelar
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={saving}
              >
                {isEditing ? 'Actualizar' : 'Crear'} Usuario
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default UsuarioForm;
