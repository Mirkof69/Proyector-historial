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
  Button,
  Card,
  Space,
  Alert,
  Spin,
  Steps,
  Modal,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  CalendarOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { pacientesService } from '../../services/pacientesService';
import { usuariosService } from '../../services/usuariosService';
import { consultoriosService } from '../../services/consultoriosService';
import { citasService, Cita, EstadoCita } from '../../services/citasService';
import { FichaCita } from './FichaCita';
import { reducer, initialState, steps } from './formularioCitaUtils';
import StepPacienteMedico from './components/StepPacienteMedico';
import StepFechaHora from './components/StepFechaHora';
import StepDetalles from './components/StepDetalles';

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
                <StepPacienteMedico
                  pacientes={state.pacientes}
                  medicos={state.medicos}
                  consultorios={state.consultorios}
                  handleMedicoChange={handleMedicoChange}
                  dispatch={dispatch}
                />
              )}

              {/* Step 1: Fecha y Hora */}
              {state.currentStep === 1 && (
                <StepFechaHora
                  medicoSeleccionado={state.medicoSeleccionado}
                  fechaSeleccionada={state.fechaSeleccionada}
                  loadingHorarios={state.loadingHorarios}
                  horariosDisponibles={state.horariosDisponibles}
                  handleFechaChange={handleFechaChange}
                  handleHoraChange={handleHoraChange}
                  handleHoraSelect={handleHoraSelect}
                  isHorarioDisponible={isHorarioDisponible}
                  dispatch={dispatch}
                />
              )}

              {/* Step 2: Detalles */}
              {state.currentStep === 2 && (
                <StepDetalles
                  horaSeleccionada={state.horaSeleccionada}
                  fechaSeleccionada={state.fechaSeleccionada}
                  loading={state.loading}
                  id={id}
                  handleCancel={handleCancel}
                  dispatch={dispatch}
                />
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
