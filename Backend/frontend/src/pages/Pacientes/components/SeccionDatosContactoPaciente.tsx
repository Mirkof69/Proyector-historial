import React from 'react';
import { Form, Input, DatePicker, Row, Col, Select, Typography, Divider } from 'antd';
import { UserOutlined, PhoneOutlined, MailOutlined, IdcardOutlined } from '@ant-design/icons';

const { Option } = Select;
const { Text } = Typography;

interface SeccionDatosContactoPacienteProps {
  edadCalculada: string;
}

const SeccionDatosContactoPaciente: React.FC<SeccionDatosContactoPacienteProps> = ({ edadCalculada }) => (
  <>
    <Divider orientation="left">Datos Personales</Divider>

    <Row gutter={16}>
      <Col span={8}>
        <Form.Item
          name="nombre"
          label="Nombre"
          rules={[
            { required: true, message: 'Ingrese el nombre' },
            {
              pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/,
              message: 'Solo letras y espacios',
            },
          ]}
        >
          <Input prefix={<UserOutlined />} placeholder="Nombre" />
        </Form.Item>
      </Col>

      <Col span={8}>
        <Form.Item
          name="apellido_paterno"
          label="Apellido Paterno"
          rules={[
            { required: true, message: 'Ingrese el apellido paterno' },
            {
              pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/,
              message: 'Solo letras y espacios',
            },
          ]}
        >
          <Input prefix={<UserOutlined />} placeholder="Apellido Paterno" />
        </Form.Item>
      </Col>

      <Col span={8}>
        <Form.Item
          name="apellido_materno"
          label="Apellido Materno"
          rules={[
            {
              pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$/,
              message: 'Solo letras y espacios',
            },
          ]}
        >
          <Input prefix={<UserOutlined />} placeholder="Apellido Materno (Opcional)" />
        </Form.Item>
      </Col>
    </Row>

    <Divider orientation="left">Informacion Demografica</Divider>

    <Row gutter={16}>
      <Col span={6}>
        <Form.Item
          name="genero"
          label="Genero"
          rules={[{ required: true, message: 'Seleccione el genero' }]}
        >
          <Select placeholder="Seleccione genero">
            <Option value="femenino">Femenino</Option>
            <Option value="masculino">Masculino</Option>
            <Option value="otro">Otro</Option>
          </Select>
        </Form.Item>
      </Col>

      <Col span={6}>
        <Form.Item
          name="estado_civil"
          label="Estado Civil"
        >
          <Select placeholder="Seleccione estado civil">
            <Option value="soltero">Soltero/a</Option>
            <Option value="casado">Casado/a</Option>
            <Option value="union_libre">Unión Libre</Option>
            <Option value="divorciado">Divorciado/a</Option>
            <Option value="viudo">Viudo/a</Option>
          </Select>
        </Form.Item>
      </Col>

      <Col span={6}>
        <Form.Item
          name="fecha_nacimiento"
          label="Fecha de Nacimiento"
          rules={[{ required: true, message: 'Seleccione la fecha' }]}
          tooltip="La edad se calculara automaticamente"
        >
          <DatePicker
            style={{ width: '100%' }}
            format="DD/MM/YYYY"
            placeholder="Seleccione fecha"
          />
        </Form.Item>
        {edadCalculada && (
          <Text type="success" style={{ fontSize: 12 }}>
            Edad: {edadCalculada}
          </Text>
        )}
      </Col>

      <Col span={6}>
        <Form.Item
          name="ci"
          label="Cedula de Identidad"
          rules={[
            {
              pattern: /^[0-9-]*$/,
              message: 'Solo numeros y guiones',
            },
          ]}
          tooltip="Documento de identidad del paciente"
        >
          <Input prefix={<IdcardOutlined />} placeholder="Ej: 12345678" />
        </Form.Item>
      </Col>
    </Row>

    <Divider orientation="left">Informacion de Contacto</Divider>

    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="telefono"
          label="Telefono"
          rules={[
            {
              pattern: /^[0-9+\-\s()]*$/,
              message: 'Solo numeros y simbolos telefonicos',
            },
          ]}
        >
          <Input prefix={<PhoneOutlined />} placeholder="Ej: 70123456 o +591 70123456" />
        </Form.Item>
      </Col>

      <Col span={12}>
        <Form.Item
          name="email"
          label="Correo Electronico"
          rules={[{ type: 'email', message: 'Email invalido' }]}
        >
          <Input prefix={<MailOutlined />} placeholder="correo@ejemplo.com" />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="ciudad"
          label="Ciudad"
        >
          <Input placeholder="Ciudad de residencia" />
        </Form.Item>
      </Col>

      <Col span={12}>
        <Form.Item
          name="pais"
          label="Pais"
          initialValue="Bolivia"
        >
          <Input placeholder="Pais" />
        </Form.Item>
      </Col>
    </Row>

    <Divider orientation="left">Domicilio</Divider>

    <Form.Item
      name="direccion"
      label="Direccion Completa"
      tooltip="Direccion de residencia del paciente"
    >
      <Input.TextArea
        rows={3}
        placeholder="Calle, numero, zona, ciudad. Ej: Av. 6 de Agosto #123, Zona Centro, La Paz"
        maxLength={500}
        showCount
      />
    </Form.Item>
  </>
);

export default SeccionDatosContactoPaciente;
