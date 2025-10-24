import React, { useState } from 'react';
import { Form, Input, DatePicker, Button, Card, message, Row, Col, Select } from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../services/authService';
import dayjs from 'dayjs';
import 'dayjs/locale/es';

dayjs.locale('es');

interface FormularioPacienteProps {
  onCancel: () => void;
  onSuccess: () => void;
}

const FormularioPaciente: React.FC<FormularioPacienteProps> = ({ onCancel, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  // Validación para solo letras
  const validateLettersOnly = (_: any, value: string) => {
    if (!value) return Promise.resolve();
    const regex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
    if (!regex.test(value)) {
      return Promise.reject('Solo se permiten letras y espacios');
    }
    return Promise.resolve();
  };

  // Validación para teléfono
  const validatePhone = (_: any, value: string) => {
    if (!value) return Promise.resolve();
    const regex = /^[0-9\+\-\s\(\)]+$/;
    if (!regex.test(value)) {
      return Promise.reject('Solo se permiten números');
    }
    return Promise.resolve();
  };

  // Validación para CI
  const validateCI = (_: any, value: string) => {
    if (!value) return Promise.resolve();
    const regex = /^[0-9\-]+$/;
    if (!regex.test(value)) {
      return Promise.reject('Solo se permiten números y guiones');
    }
    return Promise.resolve();
  };

  // Función para traducir mensajes del inglés al español
  const translateError = (msg: string): string => {
    const translations: any = {
      'paciente with this id clinico already exists.': 'ID Clínico duplicado',
      'paciente with this cedula identidad already exists.': 'Cédula de Identidad duplicada',
      'This field is required.': 'Este campo es obligatorio',
      'Enter a valid email address.': 'Ingrese un correo electrónico válido',
      'This field may not be blank.': 'Este campo no puede estar en blanco'
    };
    
    return translations[msg] || msg;
  };

  const onFinish = async (values: any) => {
    setLoading(true);
    
    try {
      const token = authService.getToken();
      const response = await axios.post('http://127.0.0.1:8000/api/pacientes/', {
        nombre: values.nombre,
        apellido_paterno: values.apellido_paterno,
        apellido_materno: values.apellido_materno,
        genero: values.genero,
        id_clinico: values.id_clinico || '',
        fecha_nacimiento: dayjs(values.fecha_nacimiento).format('YYYY-MM-DD'),
        telefono_principal: values.telefono,
        email: values.email,
        cedula_identidad: values.cedula_identidad,
        direccion: values.direccion,
        activo: true
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      message.success('Paciente registrado exitosamente');
      form.resetFields();
      onSuccess();
    } catch (error: any) {
      console.error('Error al crear paciente:', error.response?.data);
      
      const errorData = error.response?.data;
      
      // Mapear errores del backend a campos del formulario
      if (errorData?.errores) {
        const fieldErrors: any = {};
        
        Object.keys(errorData.errores).forEach(key => {
          const errorArray = errorData.errores[key];
          let errorMessage = Array.isArray(errorArray) ? errorArray[0] : errorArray;
          
          // Traducir el mensaje
          errorMessage = translateError(errorMessage);
          
          // Mapear nombres de campos del backend al frontend
          const fieldMap: any = {
            'nombre': 'nombre',
            'apellido_paterno': 'apellido_paterno',
            'apellido_materno': 'apellido_materno',
            'id_clinico': 'id_clinico',
            'cedula_identidad': 'cedula_identidad',
            'telefono_principal': 'telefono',
            'email': 'email',
            'genero': 'genero',
            'fecha_nacimiento': 'fecha_nacimiento'
          };
          
          const frontendField = fieldMap[key] || key;
          fieldErrors[frontendField] = errorMessage;
        });
        
        // Establecer errores en los campos del formulario
        form.setFields(
          Object.keys(fieldErrors).map(field => ({
            name: field,
            errors: [fieldErrors[field]]
          }))
        );
        
        message.error('Por favor corrija los errores en el formulario');
      } else if (errorData?.error) {
        message.error(translateError(errorData.error));
      } else {
        message.error('Error al crear paciente');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Nuevo Paciente">
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="nombre"
              label="Nombre"
              rules={[
                { required: true, message: 'Este campo es obligatorio' },
                { validator: validateLettersOnly }
              ]}
            >
              <Input placeholder="Nombre" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="apellido_paterno"
              label="Apellido Paterno"
              rules={[
                { required: true, message: 'Este campo es obligatorio' },
                { validator: validateLettersOnly }
              ]}
            >
              <Input placeholder="Apellido Paterno" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="apellido_materno"
              label="Apellido Materno"
              rules={[{ validator: validateLettersOnly }]}
            >
              <Input placeholder="Apellido Materno (opcional)" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="genero"
              label="Género"
              rules={[{ required: true, message: 'Este campo es obligatorio' }]}
            >
              <Select placeholder="Seleccionar género">
                <Select.Option value="femenino">Femenino</Select.Option>
                <Select.Option value="masculino">Masculino</Select.Option>
                <Select.Option value="otro">Otro</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="id_clinico"
              label="ID Clínico (dejar vacío para auto-generar)"
              rules={[
                { pattern: /^HC-\d{3,}$/, message: 'Formato válido: HC-001, HC-002, etc.' }
              ]}
            >
              <Input placeholder="Ejemplo: HC-001 o dejar vacío" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="fecha_nacimiento"
              label="Fecha de Nacimiento"
              rules={[{ required: true, message: 'Este campo es obligatorio' }]}
            >
              <DatePicker 
                style={{ width: '100%' }} 
                format="DD/MM/YYYY"
                placeholder="Seleccionar fecha"
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="telefono"
              label="Teléfono"
              rules={[{ validator: validatePhone }]}
            >
              <Input placeholder="Ejemplo: 70123456" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="email"
              label="Correo Electrónico"
              rules={[{ type: 'email', message: 'Ingrese un correo electrónico válido' }]}
            >
              <Input placeholder="ejemplo@correo.com" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="cedula_identidad"
              label="Cédula de Identidad"
              rules={[{ validator: validateCI }]}
            >
              <Input placeholder="Ejemplo: 12345678" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="direccion"
              label="Dirección"
            >
              <Input placeholder="Calle, número, zona" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
            Guardar
          </Button>
          <Button style={{ marginLeft: 8 }} onClick={onCancel} icon={<CloseOutlined />}>
            Cancelar
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default FormularioPaciente;