import React, { useState, useCallback, useEffect } from 'react';
import {
  Form,
  Button,
  Card,
  Space,
  Spin,
  Typography,
  Alert,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  SaveOutlined,
  CloseOutlined,
  UserOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { pacientesService } from '../../services/pacientesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import dayjs from 'dayjs';
import SeccionDatosContactoPaciente from './components/SeccionDatosContactoPaciente';
import SeccionInfoMedicaPaciente from './components/SeccionInfoMedicaPaciente';
import SeccionAdminEmergenciaPaciente from './components/SeccionAdminEmergenciaPaciente';
import SeccionConsentimientoPaciente from './components/SeccionConsentimientoPaciente';

const { Title } = Typography;

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
          <SeccionDatosContactoPaciente edadCalculada={edadCalculada} />

          <SeccionInfoMedicaPaciente calcularIMC={calcularIMC} imcCalculado={imcCalculado} />

          <SeccionAdminEmergenciaPaciente />

          {!isEditing && <SeccionConsentimientoPaciente />}

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
