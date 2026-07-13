import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  Form,
  Input,
  InputNumber,
  DatePicker,
  Button,
  Card,
  Row,
  Col,
  Select,
  Space,
  Spin,
  Typography,
  Divider,
  Alert,
  Modal,
  Checkbox,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  SaveOutlined,
  CloseOutlined,
  UserOutlined,
  PhoneOutlined,
  MailOutlined,
  IdcardOutlined,
  ArrowLeftOutlined,
  RiseOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { pacientesService } from '../../services/pacientesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import dayjs from 'dayjs';

const { Option } = Select;
const { Title, Text } = Typography;

const FormularioPaciente: React.FC = () => {
  const {modal,  message } = useAntdApp();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [edadCalculada, setEdadCalculada] = useState<string>('');
  const [imcCalculado, setImcCalculado] = useState<string>('');

  const isEditing = !!id;

  const handleCancel = useCallback(() => {
    navigate(FRONTEND_ROUTES.DASHBOARD.PACIENTES);
  }, [navigate]);

  const calcularEdad = React.useCallback((fecha: any) => {
    if (fecha) {
      const hoy = dayjs();
      const nacimiento = dayjs(fecha);
      const edad = hoy.diff(nacimiento, 'year');
      setEdadCalculada(`${edad} anos`);
    } else {
      setEdadCalculada('');
    }
  }, []);

  const calcularIMC = React.useCallback(() => {
    const peso = form.getFieldValue('peso_kg');
    const altura = form.getFieldValue('altura_cm');

    if (peso && altura && peso > 0 && altura > 0) {
      const alturaMetros = altura / 100;
      const imc = peso / (alturaMetros * alturaMetros);
      let clasificacion = '';

      if (imc < 18.5) {
        clasificacion = 'Bajo peso';
      } else if (imc < 25) {
        clasificacion = 'Normal';
      } else if (imc < 30) {
        clasificacion = 'Sobrepeso';
      } else {
        clasificacion = 'Obesidad';
      }

      setImcCalculado(`IMC: ${imc.toFixed(2)} - ${clasificacion}`);
    } else {
      setImcCalculado('');
    }
  }, [form]);

  const loadPaciente = React.useCallback(async (pacienteId: number) => {
    setLoadingData(true);
    try {
      const data = await pacientesService.getById(pacienteId) as any;
      form.setFieldsValue({
        nombre: data.nombre || '',
        apellido_paterno: data.apellido_paterno || '',
        apellido_materno: data.apellido_materno || '',
        genero: data.genero || '',
        estado_civil: data.estado_civil || '',
        fecha_nacimiento: data.fecha_nacimiento ? dayjs(data.fecha_nacimiento) : null,
        fecha_baja: data.fecha_baja ? dayjs(data.fecha_baja) : null,
        telefono: data.telefono || '',
        email: data.email || '',
        ci: data.ci || '',
        direccion: data.direccion || '',
        ciudad: data.ciudad || '',
        pais: data.pais || 'Bolivia',
        tipo_sangre: data.tipo_sangre || '',
        factor_rh: data.factor_rh || '',
        numero_seguro_social: data.numero_seguro_social || '',
        peso_kg: data.peso_kg || null,
        altura_cm: data.altura_cm || null,
        estado_paciente: data.estado_paciente || 'activo',
        contacto_emergencia_nombre: data.contacto_emergencia_nombre || '',
        contacto_emergencia_telefono: data.contacto_emergencia_telefono || '',
        contacto_emergencia_relacion: data.contacto_emergencia_relacion || '',
      });

      if (data.fecha_nacimiento) {
        calcularEdad(dayjs(data.fecha_nacimiento));
      }

      // Calcular IMC si existen peso y altura
      if (data.peso_kg && data.altura_cm) {
        setTimeout(() => calcularIMC(), 100);
      }
    } catch (error: any) {
      message.error('Error al cargar datos del paciente');
      handleCancel();
    } finally {
      setLoadingData(false);
    }
  }, [calcularEdad, calcularIMC, form, handleCancel, message]);

  useEffect(() => {
    if (isEditing && id) {
      loadPaciente(parseInt(id));
    }
  }, [id, isEditing, loadPaciente]);

  const handleSave = async (values: any, shouldExit: boolean = true) => {
    setLoading(true);

    try {
      const dataToSend: any = {
        nombre: values.nombre,
        apellido_paterno: values.apellido_paterno,
        apellido_materno: values.apellido_materno || '',
        genero: values.genero,
        estado_civil: values.estado_civil || '',
        fecha_nacimiento: values.fecha_nacimiento
          ? dayjs(values.fecha_nacimiento).format('YYYY-MM-DD')
          : undefined,
        telefono: values.telefono || '',
        email: values.email || '',
        ci: values.ci || '',
        direccion: values.direccion || '',
        ciudad: values.ciudad || '',
        pais: values.pais || 'Bolivia',
        activo: values.activo !== undefined ? values.activo : true,
        tipo_sangre: values.tipo_sangre || '',
        factor_rh: values.factor_rh || '',
        numero_seguro_social: values.numero_seguro_social || '',
        peso_kg: values.peso_kg || null,
        altura_cm: values.altura_cm || null,
        estado_paciente: values.estado_paciente || 'activo',
        fecha_baja: values.fecha_baja ? dayjs(values.fecha_baja).format('YYYY-MM-DD') : undefined,
        contacto_emergencia_nombre: values.contacto_emergencia_nombre || '',
        contacto_emergencia_telefono: values.contacto_emergencia_telefono || '',
        contacto_emergencia_relacion: values.contacto_emergencia_relacion || '',
      };

      // Consentimiento de tratamiento de datos (Ley 164 Bolivia) — solo
      // aplica a la creación; en edición no se reenvía (ya quedó registrado).
      if (!isEditing) {
        dataToSend.consentimiento_datos_aceptado = values.consentimiento_datos_aceptado || false;
      }

      if (isEditing) {
        await pacientesService.update(parseInt(id!), dataToSend);
        message.success('Paciente actualizado correctamente');
      } else {
        await pacientesService.create(dataToSend);
        message.success('Paciente creado correctamente');
      }

      if (shouldExit) {
        form.resetFields();
        setEdadCalculada('');
        navigate(FRONTEND_ROUTES.DASHBOARD.PACIENTES);
      } else {
        form.resetFields();
        setEdadCalculada('');
        message.info('Formulario listo para nuevo paciente');
      }
    } catch (error: any) {

      if (error.response?.data) {
        const errorData = error.response?.data;

        if (typeof errorData === 'object' && !errorData.message && !errorData.detail && !errorData.errores && !errorData.error) {
          const errorList = Object.entries(errorData).map(([field, msgs]: [string, any]) => {
            const msgArray = Array.isArray(msgs) ? msgs : [msgs];
            return `${field}: ${msgArray.join(', ')}`;
          });

          modal.error({
            title: 'Error al Guardar Paciente',
            content: (
              <div>
                <p><strong>Se encontraron los siguientes errores:</strong></p>
                <ul style={{ marginTop: 12 }}>
                  {errorList.map((err: string) => (
                    <li key={err} style={{ marginBottom: 8 }}>{err}</li>
                  ))}
                </ul>
              </div>
            ),
            width: 500,
          });
        } else if (errorData.errores) {
          const errores = errorData.errores;
          const fieldErrors = Object.keys(errores).map((field) => ({
            name: field,
            errors: Array.isArray(errores[field]) ? errores[field] : [errores[field]],
          }));
          form.setFields(fieldErrors);
          message.error('Por favor corrija los errores en el formulario');
        } else {
          const msg = errorData.detail || errorData.message || errorData.error || 'Error desconocido';
          modal.error({
            title: 'Error',
            content: msg,
          });
        }
      } else {
        message.error('Error al guardar el paciente');
      }
    } finally {
      setLoading(false);
    }
  };

  const onFinish = (values: any) => {
    handleSave(values, true);
  };

  const handleSaveAndNew = () => {
    form.validateFields().then((values) => {
      handleSave(values, false);
    }).catch(() => {
      message.error('Por favor complete todos los campos requeridos');
    });
  };

  if (loadingData) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" tip="Cargando datos del paciente…"><div /></Spin>
      </div>
    );
  }

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={handleCancel}
        style={{ marginBottom: 16 }}
      >
        Volver a la lista
      </Button>

      <Card
        title={
          <Space>
            <UserOutlined />
            <Title level={4} style={{ margin: 0 }}>
              {isEditing ? 'Editar Paciente' : 'Nuevo Paciente'}
            </Title>
          </Space>
        }
      >
        <Alert
          message="Informacion Importante"
          description="Los campos marcados con asterisco (*) son obligatorios. El ID Clinico se genera automaticamente."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          onValuesChange={(changedValues) => {
            if (changedValues.fecha_nacimiento !== undefined) {
              calcularEdad(changedValues.fecha_nacimiento);
            }
          }}
        >
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

          <Divider orientation="left">Informacion Medica</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="tipo_sangre"
                label="Tipo de Sangre"
              >
                <Select placeholder="Seleccione tipo de sangre">
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

            <Col span={8}>
              <Form.Item
                name="factor_rh"
                label="Factor RH"
              >
                <Select placeholder="Seleccione factor RH">
                  <Option value="positivo">Positivo</Option>
                  <Option value="negativo">Negativo</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item
                name="numero_seguro_social"
                label="Numero de Seguro Social"
                rules={[
                  {
                    pattern: /^[0-9-]*$/,
                    message: 'Solo numeros y guiones',
                  },
                ]}
                tooltip="Numero del seguro o afiliacion medica"
              >
                <Input placeholder="Ej: 123456789-0" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="peso_kg"
                label="Peso (kg)"
                rules={[
                  {
                    type: 'number',
                    min: 20,
                    max: 200,
                    message: 'El peso debe estar entre 20 y 200 kg',
                  },
                ]}
                tooltip="Peso actual del paciente en kilogramos"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={20}
                  max={200}
                  step={0.1}
                  placeholder="Ej: 65.5"
                  prefix={<RiseOutlined />}
                  onChange={calcularIMC}
                />
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item
                name="altura_cm"
                label="Altura (cm)"
                rules={[
                  {
                    type: 'number',
                    min: 100,
                    max: 220,
                    message: 'La altura debe estar entre 100 y 220 cm',
                  },
                ]}
                tooltip="Altura del paciente en centimetros"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={100}
                  max={220}
                  step={0.1}
                  placeholder="Ej: 165"
                  prefix={<RiseOutlined />}
                  onChange={calcularIMC}
                />
              </Form.Item>
            </Col>

            <Col span={8}>
              {imcCalculado && (
                <Alert
                  message={imcCalculado}
                  type="info"
                  showIcon
                  style={{ marginTop: 30 }}
                />
              )}
            </Col>
          </Row>

          <Divider orientation="left">Estado Administrativo</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="estado_paciente"
                label="Estado"
              >
                <Select placeholder="Seleccione estado">
                  <Option value="activo">Activo</Option>
                  <Option value="inactivo">Inactivo</Option>
                  <Option value="trasladado">Trasladado</Option>
                  <Option value="fallecido">Fallecido</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                name="fecha_baja"
                label="Fecha de Baja (si aplica)"
                tooltip="Solo si el paciente esta inactivo"
              >
                <DatePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  placeholder="Seleccione fecha"
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Contacto de Emergencia</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="contacto_emergencia_nombre"
                label="Nombre"
                rules={[
                  {
                    pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$/,
                    message: 'Solo letras y espacios',
                  },
                ]}
              >
                <Input prefix={<UserOutlined />} placeholder="Nombre del contacto" />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                name="contacto_emergencia_telefono"
                label="Telefono"
                rules={[
                  {
                    pattern: /^[0-9+\-\s()]*$/,
                    message: 'Solo numeros y simbolos telefonicos',
                  },
                  {
                    validator: (_, value) => {
                      if (!value) return Promise.resolve();
                      const clean = value.replace(/[\s\-()]/g, '');
                      if (clean.length >= 7 && clean.length <= 8) return Promise.resolve();
                      return Promise.reject(new Error('Telefono debe tener 7-8 digitos'));
                    },
                  },
                ]}
              >
                <Input prefix={<PhoneOutlined />} placeholder="Ej: 70123456" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="contacto_emergencia_relacion"
                label="Relacion con el Paciente"
                rules={[
                  {
                    pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$/,
                    message: 'Solo letras y espacios',
                  },
                ]}
              >
                <Input placeholder="Ej: Madre, Esposo, Hermano, etc." />
              </Form.Item>
            </Col>
          </Row>

          {!isEditing && (
            <>
              <Divider orientation="left">Consentimiento de Tratamiento de Datos</Divider>
              <Form.Item
                name="consentimiento_datos_aceptado"
                valuePropName="checked"
                rules={[
                  {
                    validator: (_, value) =>
                      value
                        ? Promise.resolve()
                        : Promise.reject(new Error('Se requiere el consentimiento del paciente para registrar sus datos (Ley 164)')),
                  },
                ]}
              >
                <Checkbox>
                  El paciente (o su representante) ha sido informado y otorga su consentimiento
                  expreso para la recolección y tratamiento de sus datos personales con fines
                  de atención médica, conforme a la Ley 164 de Bolivia.
                </Checkbox>
              </Form.Item>
            </>
          )}

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button icon={<CloseOutlined />} onClick={handleCancel} size="large">
                Cancelar
              </Button>

              {!isEditing && (
                <Button
                  onClick={handleSaveAndNew}
                  loading={loading}
                  icon={<SaveOutlined />}
                  size="large"
                  style={{ backgroundColor: '#52c41a', borderColor: '#52c41a', color: 'white' }}
                >
                  Guardar y Nuevo
                </Button>
              )}

              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<SaveOutlined />}
                size="large"
              >
                {isEditing ? 'Guardar y Salir' : 'Guardar y Salir'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default FormularioPaciente;
