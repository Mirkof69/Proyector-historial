/**
 * ==================================================================================
 * FORMULARIO DE CITA - CREACIÓN/EDICIÓN COMPLETA
 * ==================================================================================
 * Formulario completo para gestión de citas médicas
 * Incluye: paciente, médico, consultorio, tipo, fecha/hora, motivo
 * Con validaciones, horarios disponibles  y lógica de conflicts
 * ==================================================================================
 */

import React, { useReducer, useEffect, useCallback } from 'react';
import {
  Form,
  Input,
  Select,
  DatePicker,
  TimePicker,
  Button,
  Card,
  Space,
  Row,
  Col,
  Alert,
  Spin,
  Steps,
  Divider,
  Tag,
  Tooltip,
  Modal,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  SaveOutlined,
  CloseOutlined,
  CalendarOutlined,
  UserOutlined,
  MedicineBoxOutlined,
  HomeOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { pacientesService } from '../../services/pacientesService';
import { usuariosService } from '../../services/usuariosService';
import { consultoriosService } from '../../services/consultoriosService';
import { citasService, Cita, HorarioDisponible, EstadoCita } from '../../services/citasService';
import { FichaCita } from './FichaCita';

const { Option } = Select;
const { TextArea } = Input;
// Step component disponible para API legacy, actualmente usando items API moderna
const { Step } = Steps; // eslint-disable-line @typescript-eslint/no-unused-vars

interface FormularioCitaState {
  loading: boolean;
  loadingHorarios: boolean;
  pacientes: any[];
  medicos: any[];
  consultorios: any[];
  horariosDisponibles: HorarioDisponible[];
  medicoSeleccionado: number | null;
  fechaSeleccionada: dayjs.Dayjs | null;
  horaSeleccionada: dayjs.Dayjs | null;
  modalFichaVisible: boolean;
  citaCreada: Cita | null;
  currentStep: number;
}

type FormularioCitaAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_LOADING_HORARIOS'; payload: boolean }
  | { type: 'SET_PACIENTES'; payload: any[] }
  | { type: 'SET_MEDICOS'; payload: any[] }
  | { type: 'SET_CONSULTORIOS'; payload: any[] }
  | { type: 'SET_HORARIOS_DISPONIBLES'; payload: HorarioDisponible[] }
  | { type: 'SET_MEDICO_SELECCIONADO'; payload: number | null }
  | { type: 'SET_FECHA_SELECCIONADA'; payload: dayjs.Dayjs | null }
  | { type: 'SET_HORA_SELECCIONADA'; payload: dayjs.Dayjs | null }
  | { type: 'SET_MODAL_FICHA_VISIBLE'; payload: boolean }
  | { type: 'SET_CITA_CREADA'; payload: Cita | null }
  | { type: 'SET_CURRENT_STEP'; payload: number }
  | { type: 'SET_INITIAL_DATA'; payload: { pacientes: any[]; medicos: any[]; consultorios: any[] } };

const initialState: FormularioCitaState = {
  loading: false,
  loadingHorarios: false,
  pacientes: [],
  medicos: [],
  consultorios: [],
  horariosDisponibles: [],
  medicoSeleccionado: null,
  fechaSeleccionada: null,
  horaSeleccionada: null,
  modalFichaVisible: false,
  citaCreada: null,
  currentStep: 0,
};

function reducer(state: FormularioCitaState, action: FormularioCitaAction): FormularioCitaState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_LOADING_HORARIOS':
      return { ...state, loadingHorarios: action.payload };
    case 'SET_PACIENTES':
      return { ...state, pacientes: action.payload };
    case 'SET_MEDICOS':
      return { ...state, medicos: action.payload };
    case 'SET_CONSULTORIOS':
      return { ...state, consultorios: action.payload };
    case 'SET_HORARIOS_DISPONIBLES':
      return { ...state, horariosDisponibles: action.payload };
    case 'SET_MEDICO_SELECCIONADO':
      return { ...state, medicoSeleccionado: action.payload };
    case 'SET_FECHA_SELECCIONADA':
      return { ...state, fechaSeleccionada: action.payload };
    case 'SET_HORA_SELECCIONADA':
      return { ...state, horaSeleccionada: action.payload };
    case 'SET_MODAL_FICHA_VISIBLE':
      return { ...state, modalFichaVisible: action.payload };
    case 'SET_CITA_CREADA':
      return { ...state, citaCreada: action.payload };
    case 'SET_CURRENT_STEP':
      return { ...state, currentStep: action.payload };
    case 'SET_INITIAL_DATA':
      return {
        ...state,
        pacientes: action.payload.pacientes,
        medicos: action.payload.medicos,
        consultorios: action.payload.consultorios,
      };
    default:
      return state;
  }
}

interface HorariosDisponiblesProps {
  medicoSeleccionado: number | null;
  fechaSeleccionada: dayjs.Dayjs | null;
  loadingHorarios: boolean;
  horariosDisponibles: HorarioDisponible[];
  onHoraSelect: (hora: string) => void;
}

const HorariosDisponibles: React.FC<HorariosDisponiblesProps> = ({
  medicoSeleccionado,
  fechaSeleccionada,
  loadingHorarios,
  horariosDisponibles,
  onHoraSelect,
}) => {
  if (!medicoSeleccionado || !fechaSeleccionada) {
    return null;
  }

  if (loadingHorarios) {
    return (
      <Card size="small" title="Horarios Disponibles" style={{ marginTop: 16 }}>
        <Spin />
      </Card>
    );
  }

  if (horariosDisponibles.length === 0) {
    return null;
  }

  const disponibles = horariosDisponibles.filter(h => h.disponible);
  const ocupados = horariosDisponibles.filter(h => !h.disponible);

  return (
    <Card size="small" title="Horarios Disponibles" style={{ marginTop: 16 }}>
      {disponibles.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <strong>Disponibles:</strong>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
            {disponibles.map((h) => (
              <Tag
                key={h.hora}
                color="green"
                style={{ cursor: 'pointer' }}
                onClick={() => onHoraSelect(h.hora)}
              >
                {h.hora}
              </Tag>
            ))}
          </div>
        </div>
      )}
      {ocupados.length > 0 && (
        <div>
          <strong>Ocupados:</strong>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
            {ocupados.map((h) => (
              <Tooltip key={h.hora} title={h.motivo || 'No disponible'}>
                <Tag color="red">{h.hora}</Tag>
              </Tooltip>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};

const FormularioCita: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const { id } = useParams<{ id: string }>();

  const [state, dispatch] = useReducer(reducer, initialState);

  const cargarDatos = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const [pacientesData, usuariosData, consultoriosData] = await Promise.all([
        pacientesService.getAll(),
        usuariosService.getAll(),
        consultoriosService.getAll()
      ]);

      dispatch({
        type: 'SET_INITIAL_DATA',
        payload: {
          pacientes: pacientesData,
          medicos: usuariosData.filter((u: any) => u.rol === 'medico' || u.rol === 'administrador'),
          consultorios: consultoriosData.filter((c: any) => c.activo && !c.en_mantenimiento),
        },
      });
    } catch (error) {
      message.error('Error al cargar los datos del formulario');
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [message]);

  const cargarCita = useCallback(async (citaId: number) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const cita = await citasService.getById(citaId);

      const fechaCita = dayjs(cita.fecha_cita);
      const horaCita = dayjs(cita.hora_cita, 'HH:mm:ss');

      form.setFieldsValue({
        paciente: cita.paciente,
        medico: cita.medico,
        consultorio: cita.consultorio,
        tipo_cita: cita.tipo_cita,
        fecha_cita: fechaCita,
        hora_cita: horaCita,
        duracion: cita.duracion,
        motivo: cita.motivo,
        observaciones: cita.observaciones,
      });

      dispatch({ type: 'SET_MEDICO_SELECCIONADO', payload: cita.medico || null });
      dispatch({ type: 'SET_FECHA_SELECCIONADA', payload: fechaCita });
      dispatch({ type: 'SET_HORA_SELECCIONADA', payload: horaCita });

      if (cita.medico && fechaCita) {
        dispatch({ type: 'SET_LOADING_HORARIOS', payload: true });
        try {
          const horarios = await citasService.getHorariosDisponibles(
            cita.medico,
            fechaCita.format('YYYY-MM-DD')
          );
          dispatch({ type: 'SET_HORARIOS_DISPONIBLES', payload: horarios });
        } catch (error) {
          dispatch({ type: 'SET_HORARIOS_DISPONIBLES', payload: [] });
        } finally {
          dispatch({ type: 'SET_LOADING_HORARIOS', payload: false });
        }
      }
    } catch (error) {
      message.error('Error al cargar la cita');
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [form, message]);

  useEffect(() => {
    cargarDatos();
    if (id) {
      cargarCita(parseInt(id));
    }
  }, [id, cargarDatos, cargarCita]);

  const handleSubmit = async (values: any) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const citaData: Partial<Cita> = {
        paciente: values.paciente,
        medico: values.medico,
        consultorio: values.consultorio || null,
        tipo_cita: values.tipo_cita,
        fecha_cita: values.fecha_cita.format('YYYY-MM-DD'),
        hora_cita: values.hora_cita.format('HH:mm:ss'),
        duracion: values.duracion || 30,
        motivo: values.motivo,
        observaciones: values.observaciones || '',
        estado: 'agendada' as EstadoCita,
      };

      let cita: Cita;
      if (id) {
        cita = await citasService.update(parseInt(id), citaData);
        message.success('Cita actualizada correctamente');
      } else {
        cita = await citasService.create(citaData);
        message.success('Cita creada correctamente');
      }

      dispatch({ type: 'SET_CITA_CREADA', payload: cita });
      dispatch({ type: 'SET_MODAL_FICHA_VISIBLE', payload: true });
    } catch (error: any) {
      const errorMsg = error?.response?.data?.message || error?.response?.data?.error || 'Error al guardar la cita';
      message.error(errorMsg);
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const handleCerrarFicha = () => {
    dispatch({ type: 'SET_MODAL_FICHA_VISIBLE', payload: false });
    navigate('/dashboard/citas');
  };

  const handleCancel = () => {
    navigate('/dashboard/citas');
  };

  const cargarHorariosPara = useCallback(async (medicoId: number, fecha: dayjs.Dayjs) => {
    dispatch({ type: 'SET_LOADING_HORARIOS', payload: true });
    try {
      const horarios = await citasService.getHorariosDisponibles(
        medicoId,
        fecha.format('YYYY-MM-DD')
      );
      dispatch({ type: 'SET_HORARIOS_DISPONIBLES', payload: horarios });
    } catch (error) {
      dispatch({ type: 'SET_HORARIOS_DISPONIBLES', payload: [] });
    } finally {
      dispatch({ type: 'SET_LOADING_HORARIOS', payload: false });
    }
  }, []);

  const handleMedicoChange = useCallback((medicoId: number) => {
    dispatch({ type: 'SET_MEDICO_SELECCIONADO', payload: medicoId });
    form.setFieldsValue({ hora_cita: null });
    dispatch({ type: 'SET_HORA_SELECCIONADA', payload: null });
    dispatch({ type: 'SET_HORARIOS_DISPONIBLES', payload: [] });
    if (medicoId && state.fechaSeleccionada) {
      cargarHorariosPara(medicoId, state.fechaSeleccionada);
    }
  }, [state.fechaSeleccionada, form, cargarHorariosPara]);

  const handleFechaChange = useCallback((date: dayjs.Dayjs | null) => {
    dispatch({ type: 'SET_FECHA_SELECCIONADA', payload: date });
    form.setFieldsValue({ hora_cita: null });
    dispatch({ type: 'SET_HORA_SELECCIONADA', payload: null });
    dispatch({ type: 'SET_HORARIOS_DISPONIBLES', payload: [] });
    if (state.medicoSeleccionado && date) {
      cargarHorariosPara(state.medicoSeleccionado, date);
    }
  }, [state.medicoSeleccionado, form, cargarHorariosPara]);

  const handleHoraChange = (time: dayjs.Dayjs | null) => {
    dispatch({ type: 'SET_HORA_SELECCIONADA', payload: time });
  };

  const handleHoraSelect = (hora: string) => {
    const [hours, minutes] = hora.split(':');
    const time = dayjs().hour(parseInt(hours)).minute(parseInt(minutes));
    form.setFieldsValue({ hora_cita: time });
    dispatch({ type: 'SET_HORA_SELECCIONADA', payload: time });
  };

  const isHorarioDisponible = (hora: dayjs.Dayjs): boolean => {
    if (state.horariosDisponibles.length === 0) return true;
    const horaStr = hora.format('HH:mm');
    const horario = state.horariosDisponibles.find(h => h.hora === horaStr);
    return horario?.disponible !== false;
  };

  const steps = [
    {
      title: 'Paciente y Médico',
      description: 'Seleccione el paciente y el médico',
    },
    {
      title: 'Fecha y Hora',
      description: 'Programe la cita',
    },
    {
      title: 'Detalles',
      description: 'Complete la información',
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <CalendarOutlined style={{ fontSize: 24, color: '#1890ff' }} />
            <span style={{ fontSize: 20, fontWeight: 600 }}>
              {id ? 'Editar Cita' : 'Nueva Cita Médica'}
            </span>
          </Space>
        }
        extra={
          <Alert
            message={id ? 'Modo Edición' : 'Modo Creación'}
            type={id ? 'warning' : 'info'}
            showIcon
          />
        }
      >
        {state.loading && !id ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>Cargando…</div>
          </div>
        ) : (
          <>
            <Steps current={state.currentStep} items={steps} style={{ marginBottom: 24 }} />

            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              autoComplete="off"
              initialValues={{
                duracion: 30,
                tipo_cita: 'control',
              }}
            >
              {/* Step 0: Paciente y Médico */}
              {state.currentStep === 0 && (
                <>
                  <Row gutter={16}>
                    <Col xs={24} md={12}>
                      <Form.Item
                        label={
                          <Space>
                            <UserOutlined />
                            <span>Paciente</span>
                          </Space>
                        }
                        name="paciente"
                        rules={[{ required: true, message: 'Seleccione el paciente' }]}
                      >
                        <Select
                          placeholder="Buscar y seleccionar paciente"
                          showSearch
                          optionFilterProp="children"
                          filterOption={(input, option) =>
                            (option?.children as unknown as string).toLowerCase().includes(input.toLowerCase())
                          }
                        >
                          {state.pacientes.map((p) => (
                            <Option key={p.id} value={p.id}>
                              {p.nombre} {p.apellido_paterno} {p.apellido_materno} - ID: {p.id_clinico || p.numero_documento}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>

                    <Col xs={24} md={12}>
                      <Form.Item
                        label={
                          <Space>
                            <MedicineBoxOutlined />
                            <span>Médico</span>
                          </Space>
                        }
                        name="medico"
                        rules={[{ required: true, message: 'Seleccione el médico' }]}
                      >
                        <Select
                          placeholder="Seleccionar médico"
                          onChange={handleMedicoChange}
                        >
                          {state.medicos.map((m) => (
                            <Option key={m.id} value={m.id}>
                              Dr(a). {m.nombre} {m.apellido_paterno}
                              {m.especialidad && ` - ${m.especialidad}`}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col xs={24} md={12}>
                      <Form.Item
                        label="Tipo de Cita"
                        name="tipo_cita"
                        rules={[{ required: true, message: 'Seleccione el tipo de cita' }]}
                      >
                        <Select placeholder="Seleccionar tipo">
                          <Option value="primera_vez">Primera Vez</Option>
                          <Option value="control">Control</Option>
                          <Option value="urgencia">Urgencia</Option>
                          <Option value="seguimiento">Seguimiento</Option>
                        </Select>
                      </Form.Item>
                    </Col>

                    <Col xs={24} md={12}>
                      <Form.Item
                        label={
                          <Space>
                            <HomeOutlined />
                            <span>Consultorio (Opcional)</span>
                          </Space>
                        }
                        name="consultorio"
                      >
                        <Select placeholder="Seleccionar consultorio" allowClear>
                          {state.consultorios.map((c) => (
                            <Option key={c.id} value={c.id}>
                              {c.nombre} - {c.ubicacion}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>

                  <Divider />
                  <Row justify="end">
                    <Col>
                      <Button type="primary" onClick={() => dispatch({ type: 'SET_CURRENT_STEP', payload: 1 })}>
                        Siguiente
                      </Button>
                    </Col>
                  </Row>
                </>
              )}

              {/* Step 1: Fecha y Hora */}
              {state.currentStep === 1 && (
                <>
                  <Alert
                    message="Programación de Cita"
                    description="Seleccione la fecha y hora de la cita. Los horarios disponibles se mostrarán automáticamente."
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />

                  <Row gutter={16}>
                    <Col xs={24} md={8}>
                      <Form.Item
                        label={
                          <Space>
                            <CalendarOutlined />
                            <span>Fecha de la Cita</span>
                          </Space>
                        }
                        name="fecha_cita"
                        rules={[{ required: true, message: 'Seleccione la fecha' }]}
                      >
                        <DatePicker
                          style={{ width: '100%' }}
                          format="DD/MM/YYYY"
                          disabledDate={(current) => current && current < dayjs().startOf('day')}
                          onChange={handleFechaChange}
                        />
                      </Form.Item>
                    </Col>

                    <Col xs={24} md={8}>
                      <Form.Item
                        label={
                          <Space>
                            <ClockCircleOutlined />
                            <span>Hora de la Cita</span>
                          </Space>
                        }
                        name="hora_cita"
                        rules={[
                          { required: true, message: 'Seleccione la hora' },
                          {
                            validator: (_, value) => {
                              if (!value) return Promise.resolve();
                              if (isHorarioDisponible(value)) {
                                return Promise.resolve();
                              }
                              return Promise.reject(new Error('Este horario no está disponible'));
                            },
                          },
                        ]}
                      >
                        <TimePicker
                          style={{ width: '100%' }}
                          format="HH:mm"
                          minuteStep={15}
                          disabled={!state.medicoSeleccionado || !state.fechaSeleccionada}
                          onChange={handleHoraChange}
                        />
                      </Form.Item>
                    </Col>

                    <Col xs={24} md={8}>
                      <Form.Item
                        label="Duración (minutos)"
                        name="duracion"
                        tooltip="Duración estimada de la consulta"
                      >
                        <Select>
                          <Option value={15}>15 minutos</Option>
                          <Option value={30}>30 minutos</Option>
                          <Option value={45}>45 minutos</Option>
                          <Option value={60}>1 hora</Option>
                          <Option value={90}>1.5 horas</Option>
                          <Option value={120}>2 horas</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>

                  <HorariosDisponibles
                    medicoSeleccionado={state.medicoSeleccionado}
                    fechaSeleccionada={state.fechaSeleccionada}
                    loadingHorarios={state.loadingHorarios}
                    horariosDisponibles={state.horariosDisponibles}
                    onHoraSelect={handleHoraSelect}
                  />

                  <Divider />
                  <Row justify="space-between">
                    <Col>
                      <Button onClick={() => dispatch({ type: 'SET_CURRENT_STEP', payload: 0 })}>
                        Anterior
                      </Button>
                    </Col>
                    <Col>
                      <Button type="primary" onClick={() => dispatch({ type: 'SET_CURRENT_STEP', payload: 2 })}>
                        Siguiente
                      </Button>
                    </Col>
                  </Row>
                </>
              )}

              {/* Step 2: Detalles */}
              {state.currentStep === 2 && (
                <>
                  {/* Resumen de Selección */}
                  {state.horaSeleccionada && state.fechaSeleccionada && (
                    <Alert
                      message="Resumen de Cita"
                      description={
                        <>
                          <strong>Fecha:</strong> {state.fechaSeleccionada.format('DD/MM/YYYY')} |
                          <strong> Hora:</strong> {state.horaSeleccionada.format('HH:mm')}
                        </>
                      }
                      type="info"
                      showIcon
                      style={{ marginBottom: 16 }}
                    />
                  )}
                  <Row gutter={16}>
                    <Col xs={24}>
                      <Form.Item
                        label={
                          <Space>
                            <InfoCircleOutlined />
                            <span>Motivo de la Cita</span>
                          </Space>
                        }
                        name="motivo"
                        rules={[
                          { required: true, message: 'Ingrese el motivo de la cita' },
                          { min: 10, message: 'El motivo debe tener al menos 10 caracteres' },
                        ]}
                      >
                        <TextArea
                          rows={4}
                          placeholder="Describa el motivo de la cita según lo referido por el paciente"
                          maxLength={500}
                          showCount
                        />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col xs={24}>
                      <Form.Item
                        label="Observaciones Adicionales (Opcional)"
                        name="observaciones"
                      >
                        <TextArea
                          rows={3}
                          placeholder="Observaciones adicionales sobre la cita"
                          maxLength={500}
                          showCount
                        />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Divider />
                  <Row justify="space-between">
                    <Col>
                      <Button onClick={() => dispatch({ type: 'SET_CURRENT_STEP', payload: 1 })}>
                        Anterior
                      </Button>
                    </Col>
                    <Col>
                      <Space>
                        <Button icon={<CloseOutlined />} onClick={handleCancel}>
                          Cancelar
                        </Button>
                        <Button
                          type="primary"
                          htmlType="submit"
                          loading={state.loading}
                          icon={<SaveOutlined />}
                        >
                          {id ? 'Actualizar' : 'Crear'} Cita
                        </Button>
                      </Space>
                    </Col>
                  </Row>
                </>
              )}
            </Form>
          </>
        )}
      </Card>

      <Modal
        open={state.modalFichaVisible}
        onCancel={handleCerrarFicha}
        footer={[
          <Button key="cerrar" onClick={handleCerrarFicha}>
            Cerrar y Volver
          </Button>
        ]}
        width={800}
        styles={{ body: { padding: 0 } }}
        centered
        destroyOnHidden
      >
        {state.citaCreada && <FichaCita cita={state.citaCreada} />}
      </Modal>
    </div>
  );
};

export default FormularioCita;

