import React, { useState, useEffect, useCallback } from 'react';
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
  Alert,
  Divider,
  Modal,
  Tag,
} from 'antd';
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

const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;

const ARROW_LEFT_ICON_4 = <ArrowLeftOutlined />;
const WARNING_ICON_5 = <WarningOutlined />;
const CLOSE_ICON_2 = <CloseOutlined />;
const SAVE_ICON_3 = <SaveOutlined />;

const FormularioEmbarazo: React.FC = () => {
  const {modal,  message } = useAntdApp();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  // const { validateEmbarazo } = useEmbarazoValidation(); // No usado actualmente
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
      <Button
        icon={ARROW_LEFT_ICON_4}
        onClick={handleCancel}
        style={{ marginBottom: 16 }}
      >
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
          <Divider orientation="left">Informacion General</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="paciente"
                label="Paciente"
                rules={[{ required: true, message: 'Seleccione un paciente' }]}
              >
                <Select
                  placeholder="Seleccione paciente"
                  optionLabelProp="label"
                  showSearch
                  filterOption={(input, option) =>
                    (option?.label as string ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {pacientes.map((p) => (
                    <Option key={p.id} value={p.id} label={`${p.nombre} ${p.apellido_paterno}`}>
                      {p.nombre} {p.apellido_paterno} - {p.id_clinico}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                name="numero_gesta"
                label="Numero de Gesta"
                rules={[
                  { required: true, message: 'Ingrese numero de gesta' },
                  { type: 'number', min: 1, message: 'Debe ser numero positivo' },
                  () => ({
                    validator(_, value) {
                      const numPara = form.getFieldValue('numero_para') || 0;
                      const numAbortos = form.getFieldValue('numero_abortos') || 0;

                      if (value && numPara > value) {
                        return Promise.reject(new Error(`El número de partos (${numPara}) no puede ser mayor que gestas (${value})`));
                      }

                      // G debe ser >= P + Abortos
                      const minGesta = numPara + numAbortos;
                      if (value && value < minGesta) {
                        return Promise.reject(new Error(`Gestas (${value}) debe ser al menos ${minGesta} (Partos ${numPara} + Abortos ${numAbortos})`));
                      }

                      return Promise.resolve();
                    },
                  }),
                ]}
              >
                <Input type="number" placeholder="1" min={1} />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Fechas y Calculos</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="fecha_ultima_menstruacion"
                label="Fecha Ultima Menstruacion"
                rules={[
                  { required: true, message: 'Seleccione la fecha' },
                  () => ({
                    validator(_, value) {
                      if (!value) {
                        return Promise.resolve();
                      }

                      const hoy = dayjs();
                      const fumDate = dayjs(value);

                      // No puede estar en el futuro
                      if (fumDate.isAfter(hoy)) {
                        return Promise.reject(new Error('La Fecha de Última Menstruación no puede estar en el futuro'));
                      }

                      // No puede ser más de 1 año atrás
                      const unAnioAtras = hoy.subtract(1, 'year');
                      if (fumDate.isBefore(unAnioAtras)) {
                        return Promise.reject(new Error('La Fecha de Última Menstruación no puede ser mayor a 1 año atrás'));
                      }

                      return Promise.resolve();
                    },
                  }),
                ]}
                tooltip="Se calcularan automaticamente FPP y edad gestacional"
              >
                <DatePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  placeholder="Seleccione fecha"
                />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                name="fecha_probable_parto"
                label="Fecha Probable de Parto"
                tooltip="Se calcula automaticamente (FUM + 280 dias)"
              >
                <DatePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  placeholder="Se completa automaticamente"
                  disabled
                />
              </Form.Item>
            </Col>
          </Row>

          {fppCalculada && (
            <Alert
              message={`FPP Calculada: ${fppCalculada}`}
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {edadGestacional && (
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Card>
                  <Text strong>Edad Gestacional:</Text>
                  <br />
                  <Text>{edadGestacional}</Text>
                </Card>
              </Col>
              <Col span={12}>
                <Card>
                  <Text strong>Trimestre Actual:</Text>
                  <br />
                  {trimestreActual ? (
                    <Tag color={trimestreActual === 1 ? 'blue' : trimestreActual === 2 ? 'green' : 'orange'} style={{ fontSize: 14, padding: '4px 12px', marginTop: 4 }}>
                      Trimestre {trimestreActual}
                    </Tag>
                  ) : (
                    <Text>-</Text>
                  )}
                </Card>
              </Col>
            </Row>
          )}

          <Divider orientation="left">Clasificacion del Embarazo</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="tipo_embarazo"
                label="Tipo de Embarazo"
                initialValue="simple"
              >
                <Select placeholder="Seleccione tipo">
                  <Option value="simple">Simple</Option>
                  <Option value="gemelar">Gemelar</Option>
                  <Option value="multiple">Multiple</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                name="riesgo_embarazo"
                label={
                  <Space>
                    Clasificacion de Riesgo
                    {form.getFieldValue('riesgo_embarazo') && (
                      <Tag color={
                        form.getFieldValue('riesgo_embarazo') === 'bajo' ? 'success' :
                          form.getFieldValue('riesgo_embarazo') === 'medio' ? 'warning' :
                            'error'
                      }>
                        {form.getFieldValue('riesgo_embarazo')?.toUpperCase()}
                      </Tag>
                    )}
                  </Space>
                }
                initialValue="bajo"
              >
                <Select placeholder="Seleccione riesgo" onChange={() => form.validateFields(['riesgo_embarazo'])}>
                  <Option value="bajo">Bajo Riesgo</Option>
                  <Option value="medio">Riesgo Medio</Option>
                  <Option value="alto">Alto Riesgo</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="estado"
                label={
                  <Space>
                    Estado
                    {form.getFieldValue('estado') && (
                      <Tag color={
                        form.getFieldValue('estado') === 'activo' ? 'processing' :
                          form.getFieldValue('estado') === 'finalizado' ? 'success' :
                            'error'
                      }>
                        {form.getFieldValue('estado')?.toUpperCase()}
                      </Tag>
                    )}
                  </Space>
                }
                initialValue="activo"
              >
                <Select placeholder="Seleccione estado" onChange={() => form.validateFields(['estado'])}>
                  <Option value="activo">Activo</Option>
                  <Option value="finalizado">Finalizado</Option>
                  <Option value="perdida">Perdida</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Historial Obstetrico</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="numero_abortos"
                label="Numero de Abortos"
                rules={[
                  { type: 'number', min: 0, message: 'Debe ser número positivo o cero' },
                ]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="0"
                  min={0}
                  onChange={() => form.validateFields(['numero_gesta'])}
                />
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item
                name="numero_cesareas"
                label="Numero de Cesareas"
                rules={[
                  { type: 'number', min: 0, message: 'Debe ser número positivo o cero' },
                ]}
              >
                <InputNumber style={{ width: '100%' }} placeholder="0" min={0} />
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item
                name="numero_para"
                label="Numero de Para"
                rules={[
                  { type: 'number', min: 0, message: 'Debe ser número positivo o cero' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      const gesta = getFieldValue('numero_gesta');
                      if (value !== undefined && gesta !== undefined && value > gesta) {
                        return Promise.reject('Los partos no pueden superar las gestas');
                      }
                      return Promise.resolve();
                    }
                  })
                ]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="0"
                  min={0}
                  onChange={() => form.validateFields(['numero_gesta'])}
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Datos Antropométricos Maternos</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="peso_pregestacional"
                label="Peso Pregestacional (kg)"
                rules={[
                  {
                    type: 'number',
                    min: 30,
                    max: 200,
                    message: 'El peso debe estar entre 30 y 200 kg',
                  },
                ]}
                tooltip="Peso de la madre antes del embarazo"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={30}
                  max={200}
                  step={0.1}
                  placeholder="Ej: 65.5"
                  onChange={calcularIMC}
                />
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item
                name="talla_materna"
                label="Talla Materna (cm)"
                rules={[
                  {
                    type: 'number',
                    min: 100,
                    max: 230,
                    message: 'La talla debe estar entre 100 y 230 cm',
                  },
                ]}
                tooltip="Estatura de la madre en centímetros"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={100}
                  max={230}
                  step={0.1}
                  placeholder="Ej: 165"
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

          <Divider orientation="left">Notas Medicas</Divider>

          <Form.Item
            name="notas"
            label="Notas y Observaciones"
          >
            <TextArea
              rows={4}
              placeholder="Ingrese cualquier informacion adicional relevante"
              maxLength={1000}
              showCount
            />
          </Form.Item>

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

