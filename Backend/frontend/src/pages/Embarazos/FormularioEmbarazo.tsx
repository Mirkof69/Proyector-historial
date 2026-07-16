import React, { useState, useEffect, useCallback } from 'react';
import { Form, Button, Card, Space, Spin, Typography, Alert } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  SaveOutlined,
  CloseOutlined,
  ArrowLeftOutlined,
  HeartOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { embarazosService } from '../../services/embarazosService';
import { pacientesService, Paciente } from '../../services/pacientesService';
import { FRONTEND_ROUTES } from '../../config/routes';
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { useEmbarazoValidation } from '../../hooks/useFormValidation';
import dayjs from 'dayjs';
import SeccionDatosGeneralesEmbarazo from './components/SeccionDatosGeneralesEmbarazo';
import SeccionClasificacionEmbarazo from './components/SeccionClasificacionEmbarazo';
import SeccionAntropometriaEmbarazo from './components/SeccionAntropometriaEmbarazo';

const { Title } = Typography;

const ARROW_LEFT_ICON_4 = <ArrowLeftOutlined />;
const WARNING_ICON_5 = <WarningOutlined />;
const CLOSE_ICON_2 = <CloseOutlined />;
const SAVE_ICON_3 = <SaveOutlined />;

const FormularioEmbarazo: React.FC = () => {
  const { modal, message } = useAntdApp();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [fppCalculada, setFppCalculada] = useState<string>('');
  const [edadGestacional, setEdadGestacional] = useState<string>('');
  const [trimestreActual, setTrimestreActual] = useState<number>(0);
  const [alertasRiesgo, setAlertasRiesgo] = useState<string[]>([]);
  const [imcCalculado, setImcCalculado] = useState<string>('');

  const isEditing = !!id;

  const calcularTrimestre = useCallback((semanas: number) => {
    if (semanas < 13) setTrimestreActual(1);
    else if (semanas < 27) setTrimestreActual(2);
    else setTrimestreActual(3);
  }, []);

  const evaluarAlertas = useCallback((semanas: number) => {
    const alertas: string[] = [];
    if (semanas < 8) alertas.push('Embarazo muy precoz - Confirmacion recomendada');
    if (semanas > 42) alertas.push('Embarazo prolongado - Evaluacion medica urgente');
    setAlertasRiesgo(alertas);
  }, []);

  const calcularEdadGestacional = useCallback((fecha: any) => {
    if (fecha && fecha.isValid()) {
      const hoy = dayjs();
      const semanas = hoy.diff(fecha, 'weeks');
      const dias = hoy.diff(fecha, 'days') % 7;
      setEdadGestacional(`${semanas} semanas ${dias} dias`);
      calcularTrimestre(semanas);
      evaluarAlertas(semanas);
    } else {
      setEdadGestacional('');
      setTrimestreActual(0);
      setAlertasRiesgo([]);
    }
  }, [calcularTrimestre, evaluarAlertas]);

  const calcularFPP = useCallback((fecha: any) => {
    if (fecha && fecha.isValid()) {
      const fpp = fecha.add(280, 'days');
      setFppCalculada(fpp.format('DD/MM/YYYY'));
      calcularEdadGestacional(fecha);
    }
  }, [calcularEdadGestacional]);

  const calcularIMC = useCallback(() => {
    const peso = form.getFieldValue('peso_pregestacional');
    const talla = form.getFieldValue('talla_materna');

    if (peso && talla && peso > 0 && talla > 0) {
      const tallaMetros = talla / 100;
      const imc = peso / (tallaMetros * tallaMetros);
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

      setImcCalculado(`IMC Pregestacional: ${imc.toFixed(2)} - ${clasificacion}`);
    } else {
      setImcCalculado('');
    }
  }, [form]);

  const cargarPacientes = useCallback(async () => {
    try {
      const data = await pacientesService.getAll();
      const pacientesFemeninos = data.filter((p) => p.genero === 'femenino');
      setPacientes(pacientesFemeninos);
    } catch (error: any) {
      message.error('Error al cargar lista de pacientes');
    }
  }, [message]);

  const handleCancel = useCallback(() => {
    navigate(FRONTEND_ROUTES.DASHBOARD.EMBARAZOS);
  }, [navigate]);

  const cargarEmbarazo = useCallback(async (embarazoId: number) => {
    setLoadingData(true);
    try {
      const data = await embarazosService.getById(embarazoId);
      form.setFieldsValue({
        ...data,
        fecha_ultima_menstruacion: data.fecha_ultima_menstruacion ? dayjs(data.fecha_ultima_menstruacion) : null,
        fecha_probable_parto: data.fecha_probable_parto ? dayjs(data.fecha_probable_parto) : null,
        paciente: typeof data.paciente === 'object' ? (data.paciente as any).id : data.paciente,
      });
      if (data.fecha_ultima_menstruacion) {
        calcularFPP(dayjs(data.fecha_ultima_menstruacion));
      }
      if (data.peso_pregestacional && data.talla_materna) {
        calcularIMC();
      }
    } catch (error: any) {
      message.error('Error al cargar datos del embarazo');
      handleCancel();
    } finally {
      setLoadingData(false);
    }
  }, [calcularFPP, calcularIMC, form, handleCancel, message]);

  useEffect(() => {
    cargarPacientes();
    if (isEditing) {
      cargarEmbarazo(parseInt(id!));
    } else {
      setLoadingData(false);
    }
  }, [id, isEditing, cargarPacientes, cargarEmbarazo]);

  const handleSave = async (values: any) => {
    setLoading(true);
    try {
      const dataToSend: any = {
        paciente: values.paciente,
        numero_gesta: values.numero_gesta || 1,
        fecha_ultima_menstruacion: values.fecha_ultima_menstruacion
          ? dayjs(values.fecha_ultima_menstruacion).format('YYYY-MM-DD')
          : undefined,
        fecha_probable_parto: values.fecha_probable_parto
          ? dayjs(values.fecha_probable_parto).format('YYYY-MM-DD')
          : undefined,
        tipo_embarazo: values.tipo_embarazo || 'simple',
        riesgo_embarazo: values.riesgo_embarazo || 'bajo',
        estado: values.estado || 'activo',
        numero_abortos: values.numero_abortos || 0,
        numero_cesareas: values.numero_cesareas || 0,
        numero_para: values.numero_para || 0,
        peso_pregestacional: values.peso_pregestacional || null,
        talla_materna: values.talla_materna || null,
        notas: values.notas || '',
      };

      if (isEditing) {
        await embarazosService.update(parseInt(id!), dataToSend);
        message.success('Embarazo actualizado correctamente');
      } else {
        await embarazosService.create(dataToSend);
        message.success('Embarazo creado correctamente');
      }

      navigate(FRONTEND_ROUTES.DASHBOARD.EMBARAZOS);
    } catch (error: any) {
      if (error.response?.data) {
        const errorData = error.response?.data;
        if (errorData.errores) {
          const fieldErrors = Object.keys(errorData.errores).map((field) => ({
            name: field,
            errors: Array.isArray(errorData.errores[field])
              ? errorData.errores[field]
              : [errorData.errores[field]],
          }));
          form.setFields(fieldErrors);
        } else if (errorData.detail) {
          modal.error({ title: 'Error', content: errorData.detail });
        }
      }
      message.error('Error al guardar el embarazo');
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" tip="Cargando datos del embarazo…"><div /></Spin>
      </div>
    );
  }

  return (
    <div>
      <Button icon={ARROW_LEFT_ICON_4} onClick={handleCancel} style={{ marginBottom: 16 }}>
        Volver a la lista
      </Button>

      <Card
        title={
          <Space>
            <HeartOutlined />
            <Title level={4} style={{ margin: 0 }}>
              {isEditing ? 'Editar Embarazo' : 'Nuevo Embarazo'}
            </Title>
          </Space>
        }
      >
        {alertasRiesgo.length > 0 && (
          <Alert
            message="Alertas detectadas"
            description={
              <ul>
                {alertasRiesgo.map((alerta) => (
                  <li key={alerta}>{alerta}</li>
                ))}
              </ul>
            }
            type="warning"
            showIcon
            icon={WARNING_ICON_5}
            style={{ marginBottom: 16 }}
          />
        )}

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          onValuesChange={(changedValues) => {
            if (changedValues.fecha_ultima_menstruacion !== undefined) {
              calcularFPP(changedValues.fecha_ultima_menstruacion);
            }
          }}
        >
          <SeccionDatosGeneralesEmbarazo
            form={form}
            pacientes={pacientes}
            fppCalculada={fppCalculada}
            edadGestacional={edadGestacional}
            trimestreActual={trimestreActual}
          />

          <SeccionClasificacionEmbarazo form={form} />

          <SeccionAntropometriaEmbarazo imcCalculado={imcCalculado} onCalcularIMC={calcularIMC} />

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button icon={CLOSE_ICON_2} onClick={handleCancel} size="large">
                Cancelar
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={SAVE_ICON_3}
                size="large"
              >
                {isEditing ? 'Guardar Cambios' : 'Crear Embarazo'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default FormularioEmbarazo;
