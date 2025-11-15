// ===========================================
// FORMULARIO DE PACIENTE - CREAR/EDITAR
// ===========================================
// Componente completo para creación y edición de pacientes
// Incluye validación, manejo de errores y cálculo automático de edad

import React, { useEffect, useState } from 'react';
import {
  Form,
  Input,
  Select,
  DatePicker,
  Button,
  Card,
  Row,
  Col,
  message,
  Spin,
  Divider
} from 'antd';
import { SaveOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { PacientesService } from '../../services/api';
import { Paciente } from '../../types';
import dayjs from 'dayjs';

const { Option } = Select;
const { TextArea } = Input;

// Componente principal del formulario
const PacienteForm: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const isEditing = !!id;

  // Efecto para cargar datos al editar
  useEffect(() => {
    if (isEditing) {
      fetchPaciente();
    }
  }, [id]);

  // Función para obtener datos del paciente al editar
  const fetchPaciente = async () => {
    setLoading(true);
    try {
      const response = await PacientesService.getById(Number(id));
      const paciente: Paciente = response.data;

      // Transformar los datos para el formulario
      form.setFieldsValue({
        ...paciente,
        fecha_nacimiento: paciente.fecha_nacimiento ? dayjs(paciente.fecha_nacimiento) : null,
      });
    } catch (error) {
      message.error('Error al cargar datos del paciente');
      navigate('/pacientes');
    } finally {
      setLoading(false);
    }
  };

  // Función para guardar (crear o actualizar)
  const handleSubmit = async (values: any) => {
    setSaving(true);
    try {
      // Preparar datos para enviar
      const data = {
        ...values,
        fecha_nacimiento: values.fecha_nacimiento ? values.fecha_nacimiento.format('YYYY-MM-DD') : null,
      };

      if (isEditing) {
        await PacientesService.update(Number(id), data);
        message.success('Paciente actualizado exitosamente');
      } else {
        await PacientesService.create(data);
        message.success('Paciente creado exitosamente');
      }

      navigate('/pacientes');
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
        message.error('Error al guardar paciente');
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
              onClick={() => navigate('/pacientes')}
              style={{ marginRight: 16 }}
            />
            {isEditing ? 'Editar Paciente' : 'Nuevo Paciente'}
          </div>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            genero: 'femenino',
            estado_civil: 'soltera',
            activo: true,
          }}
        >
          <Divider orientation="left">Datos de Identificación</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="ID Clínico"
                name="id_clinico"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Input placeholder="Ej: PAC-2024-001" />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Cédula de Identidad"
                name="cedula_identidad"
              >
                <Input placeholder="Ej: 1234567" />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Pasaporte"
                name="pasaporte"
              >
                <Input placeholder="Número de pasaporte" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Datos Personales</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Nombre"
                name="nombre"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Input placeholder="Nombre" />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Apellido Paterno"
                name="apellido_paterno"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Input placeholder="Apellido paterno" />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Apellido Materno"
                name="apellido_materno"
              >
                <Input placeholder="Apellido materno" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Fecha de Nacimiento"
                name="fecha_nacimiento"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <DatePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  placeholder="Seleccione fecha"
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Género"
                name="genero"
                rules={[{ required: true, message: 'Campo requerido' }]}
              >
                <Select placeholder="Seleccione género">
                  <Option value="femenino">Femenino</Option>
                  <Option value="masculino">Masculino</Option>
                  <Option value="otro">Otro</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Estado Civil"
                name="estado_civil"
              >
                <Select placeholder="Seleccione estado civil">
                  <Option value="soltera">Soltera</Option>
                  <Option value="casada">Casada</Option>
                  <Option value="divorciada">Divorciada</Option>
                  <Option value="viuda">Viuda</Option>
                  <Option value="union_libre">Unión Libre</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Datos Médicos</Divider>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Grupo Sanguíneo"
                name="grupo_sanguineo"
              >
                <Select placeholder="Seleccione grupo sanguíneo">
                  <Option value="O+">O+</Option>
                  <Option value="O-">O-</Option>
                  <Option value="A+">A+</Option>
                  <Option value="A-">A-</Option>
                  <Option value="B+">B+</Option>
                  <Option value="B-">B-</Option>
                  <Option value="AB+">AB+</Option>
                  <Option value="AB-">AB-</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Factor RH"
                name="factor_rh"
              >
                <Select placeholder="Seleccione factor RH">
                  <Option value="positivo">Positivo</Option>
                  <Option value="negativo">Negativo</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item
                label="Estado"
                name="activo"
              >
                <Select>
                  <Option value={true}>Activo</Option>
                  <Option value={false}>Inactivo</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Contacto</Divider>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="Teléfono Principal"
                name="telefono_principal"
              >
                <Input placeholder="Ej: +591 12345678" />
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Form.Item
                label="Teléfono Secundario"
                name="telefono_secundario"
              >
                <Input placeholder="Teléfono alternativo" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="Email"
                name="email"
                rules={[{ type: 'email', message: 'Email inválido' }]}
              >
                <Input type="email" placeholder="correo@ejemplo.com" />
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Form.Item
                label="Dirección"
                name="direccion"
              >
                <Input placeholder="Dirección completa" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Información Adicional</Divider>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="Ocupación"
                name="ocupacion"
              >
                <Input placeholder="Profesión u ocupación" />
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Form.Item
                label="Nivel de Educación"
                name="nivel_educacion"
              >
                <Select placeholder="Seleccione nivel">
                  <Option value="ninguno">Ninguno</Option>
                  <Option value="primaria">Primaria</Option>
                  <Option value="secundaria">Secundaria</Option>
                  <Option value="tecnico">Técnico</Option>
                  <Option value="universitario">Universitario</Option>
                  <Option value="posgrado">Posgrado</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="Observaciones"
            name="observaciones"
          >
            <TextArea
              rows={4}
              placeholder="Observaciones adicionales sobre el paciente"
            />
          </Form.Item>

          {/* Botones de acción */}
          <Form.Item>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <Button onClick={() => navigate('/pacientes')}>
                Cancelar
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={saving}
              >
                {isEditing ? 'Actualizar' : 'Crear'} Paciente
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default PacienteForm;
