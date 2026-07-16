import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Form, Card, Row, Col, Skeleton } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { vacunasService, RegistroVacunaCreate, TipoVacuna } from '../../services/vacunasService';
import { pacientesService } from '../../services/pacientesService';
import { datosClinicosService } from '../../services/datosClinicosService';
import { authService } from '../../services/authService';
import { useAntdApp } from '../../hooks/useMessage';
import FormularioVacunaHeader from './components/FormularioVacunaHeader';
import CamposFormularioVacuna from './components/CamposFormularioVacuna';
import GuiaEsquemaVacuna from './components/GuiaEsquemaVacuna';
import './Vacunas.css';

const FormularioVacuna: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const { id } = useParams<{ id: string }>();

  // Estados
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [pacientes, setPacientes] = useState<any[]>([]);
  const [tiposVacunas, setTiposVacunas] = useState<TipoVacuna[]>([]);
  const [vacunaSeleccionada, setVacunaSeleccionada] = useState<TipoVacuna | null>(null);
  const [proximaDosisCalculada, setProximaDosisCalculada] = useState<string>('');
  const [progresoDosis, setProgresoDosis] = useState<number>(0);
  const [alertas, setAlertas] = useState<string[]>([]);
  const [historialVacunacion, setHistorialVacunacion] = useState<{
    mensaje: string;
    tipo: 'success' | 'info' | 'warning';
    totalVacunas?: number;
  } | null>(null);

  const cargarRegistroRef = useRef<(registroId: number, tipos?: TipoVacuna[]) => Promise<void>>(async () => {});

  const cargarDatos = useCallback(async (registroId?: number) => {
    try {
      setLoading(true);
      const [pacientesData, vacunasData] = await Promise.all([
        pacientesService.getAll(),
        vacunasService.getTiposVacunas({ page_size: 1000 })
      ]);

      const pacientesArr = Array.isArray(pacientesData) ? pacientesData : [];
      const vacunas = vacunasData.results || vacunasData;
      const tiposArr = Array.isArray(vacunas) ? vacunas : [];

      setPacientes(pacientesArr);
      setTiposVacunas(tiposArr);

      if (registroId && tiposArr.length > 0) {
        await cargarRegistroRef.current(registroId, tiposArr);
      }
    } catch (error) {
      message.error('Error al cargar datos del sistema');
    } finally {
      setLoading(false);
    }
  }, [message]);

  const cargarRegistro = useCallback(async (registroId: number, tipos?: TipoVacuna[]) => {
    try {
      setLoading(true);
      const registro = await vacunasService.getRegistroById(registroId);

      const formValues = {
        ...registro,
        fecha_aplicacion: registro.fecha_aplicacion ? dayjs(registro.fecha_aplicacion) : null,
        proxima_dosis_fecha: registro.proxima_dosis_fecha ? dayjs(registro.proxima_dosis_fecha) : null,
      };

      form.setFieldsValue(formValues);

      const tiposToUse = tipos || tiposVacunas;
      if (registro.tipo_vacuna && tiposToUse.length > 0) {
        const vacuna = tiposToUse.find(v => v.id === registro.tipo_vacuna);
        if (vacuna) {
          setVacunaSeleccionada(vacuna);
          setProgresoDosis(Math.min((registro.numero_dosis / vacuna.dosis_requeridas) * 100, 100));
        }
      }
    } catch (error) {
      message.error('No se pudo cargar la información del registro');
    } finally {
      setLoading(false);
    }
  }, [form, message, tiposVacunas]);

  useEffect(() => {
    cargarRegistroRef.current = cargarRegistro;
  }, [cargarRegistro]);

  useEffect(() => {
    if (id) {
      cargarDatos(parseInt(id));
    } else {
      cargarDatos();
    }
  }, [id, cargarDatos]);

  const calcularProgresoDosis = useCallback((dosisActual: number, dosisRequeridas: number) => {
    const progreso = (dosisActual / dosisRequeridas) * 100;
    setProgresoDosis(Math.min(progreso, 100));
  }, []);

  const handlePacienteChange = useCallback(async (pacienteId: number) => {
    if (id) return;

    setLoading(true);
    setHistorialVacunacion(null);

    try {
      const [historial, datosCompletos] = await Promise.all([
        vacunasService.getRegistrosPorPaciente(pacienteId, { page_size: 1000 }),
        datosClinicosService.obtenerDatosCompletos(pacienteId)
      ]);

      const registros = historial.results || [];
      const { antecedentes, embarazoActual } = datosCompletos;
      const mensajes: string[] = [];

      let tieneAlertas = false;

      if (registros.length > 0) {
        const vacunasUnicas = new Set(registros.map((r: any) => r.tipo_vacuna));
        mensajes.push(`${registros.length} dosis registradas (${vacunasUnicas.size} tipos)`);
      }

      if (embarazoActual?.embarazo) {
        mensajes.push('Embarazo activo');
        form.setFieldValue('embarazo', embarazoActual.embarazo.id);
      }

      if (antecedentes.alergias) {
        mensajes.push(`Alergias: ${antecedentes.alergias}`);
        tieneAlertas = true;
      }

      setHistorialVacunacion({
        mensaje: mensajes.length > 0 ? mensajes.join(' | ') : 'Sin antecedentes de inmunización registrados.',
        tipo: tieneAlertas ? 'warning' : 'info',
        totalVacunas: registros.length
      });
    } catch (error) {
    } finally {
      setLoading(false);
    }
  }, [id, form]);

  const handleVacunaChange = useCallback((tipoVacunaId: number) => {
    const vacuna = tiposVacunas.find(v => v.id === tipoVacunaId);
    setVacunaSeleccionada(vacuna || null);

    const fechaAplicacion = form.getFieldValue('fecha_aplicacion');
    if (vacuna && vacuna.intervalo_dosis_dias && fechaAplicacion) {
      const proximaFecha = dayjs(fechaAplicacion).add(vacuna.intervalo_dosis_dias, 'day');
      setProximaDosisCalculada(proximaFecha.toISOString());
      form.setFieldValue('proxima_dosis_fecha', proximaFecha);
    }

    const numeroDosis = form.getFieldValue('numero_dosis') || 1;
    if (vacuna) {
      calcularProgresoDosis(numeroDosis, vacuna.dosis_requeridas);
      setAlertas([
        ...(vacuna.contraindicaciones ? [`Contraindicaciones: ${vacuna.contraindicaciones}`] : []),
        ...(vacuna.efectos_secundarios ? [`Efectos secundarios: ${vacuna.efectos_secundarios}`] : [])
      ]);
    }
  }, [tiposVacunas, form, calcularProgresoDosis]);

  const handleDosisChange = useCallback((dosis: number | null) => {
    if (vacunaSeleccionada && dosis !== null) {
      calcularProgresoDosis(dosis, vacunaSeleccionada.dosis_requeridas);
      if (dosis > vacunaSeleccionada.dosis_requeridas) {
        message.warning(`El esquema de esta vacuna contempla ${vacunaSeleccionada.dosis_requeridas} dosis.`);
      }
    }
  }, [vacunaSeleccionada, calcularProgresoDosis, message]);

  const handleFechaAplicacionChange = useCallback((fecha: dayjs.Dayjs | null) => {
    if (fecha && vacunaSeleccionada?.intervalo_dosis_dias) {
      const proximaFecha = dayjs(fecha).add(vacunaSeleccionada.intervalo_dosis_dias, 'day');
      setProximaDosisCalculada(proximaFecha.toISOString());
      form.setFieldValue('proxima_dosis_fecha', proximaFecha);
    }
  }, [vacunaSeleccionada, form]);

  const handleSubmit = async (values: any) => {
    setSubmitting(true);
    try {
      const registroData: RegistroVacunaCreate = {
        ...values,
        fecha_aplicacion: values.fecha_aplicacion ? values.fecha_aplicacion.toISOString() : new Date().toISOString(),
        proxima_dosis_fecha: values.proxima_dosis_fecha ? values.proxima_dosis_fecha.toISOString() : undefined,
        aplicado_por: authService.getCurrentUser()?.id || 1,
      };

      if (id) {
        await vacunasService.actualizarRegistro(parseInt(id), registroData);
        message.success('Registro de inmunización actualizado');
      } else {
        await vacunasService.crearRegistro(registroData);
        message.success('Registro de inmunización exitoso');
      }
      navigate('/dashboard/vacunas');
    } catch (error: any) {
      message.error('Error al guardar el registro');
    } finally {
      setSubmitting(false);
    }
  };

  const viasAdministracion = vacunasService.getViasAdministracion();

  return (
    <div className="animate-fade-in" style={{ padding: '24px' }}>
      <Card className="shadow-card overflow-hidden">
        <FormularioVacunaHeader
          esEdicion={!!id}
          submitting={submitting}
          onCancelar={() => navigate('/dashboard/vacunas')}
          onGuardar={() => form.submit()}
        />

        {loading ? (
          <Skeleton active paragraph={{ rows: 12 }} style={{ padding: '24px' }} />
        ) : (
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{
              fecha_aplicacion: dayjs(),
              numero_dosis: 1,
              via_administracion: 'intramuscular',
            }}
            className="premium-form"
          >
            <Row gutter={24}>
              <Col xs={24} lg={16}>
                <CamposFormularioVacuna
                  pacientes={pacientes}
                  tiposVacunas={tiposVacunas}
                  historialVacunacion={historialVacunacion}
                  viasAdministracion={viasAdministracion}
                  proximaDosisCalculada={proximaDosisCalculada}
                  onPacienteChange={handlePacienteChange}
                  onVacunaChange={handleVacunaChange}
                  onFechaAplicacionChange={handleFechaAplicacionChange}
                  onDosisChange={handleDosisChange}
                />
              </Col>

              <Col xs={24} lg={8}>
                <GuiaEsquemaVacuna
                  vacunaSeleccionada={vacunaSeleccionada}
                  progresoDosis={progresoDosis}
                  numeroDosis={form.getFieldValue('numero_dosis') || 0}
                  alertas={alertas}
                />
              </Col>
            </Row>
          </Form>
        )}
      </Card>
    </div>
  );
};

export default FormularioVacuna;
