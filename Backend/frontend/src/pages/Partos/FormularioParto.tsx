import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Form, Button, Card, Spin, Typography, Space, Badge
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  SaveOutlined, CloseOutlined, ArrowLeftOutlined, HeartOutlined, WarningOutlined
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { partosService, Recomendacion, AlertaParto } from '../../services/partosService';
import { embarazosService, Embarazo } from '../../services/embarazosService';
import { pacientesService, Paciente } from '../../services/pacientesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import dayjs from 'dayjs';

// Sub-componentes extraídos
import { SeccionEmbarazoEvento } from './sections/SeccionEmbarazoEvento';
import { SeccionAborto } from './sections/SeccionAborto';
import { SeccionParto } from './sections/SeccionParto';
import { SeccionRecienNacido } from './sections/SeccionRecienNacido';
import { AlertasYRecomendaciones } from './components/AlertasYRecomendaciones';

const { Title } = Typography;

const ARROW_LEFT_ICON_6 = <ArrowLeftOutlined />;
const CLOSE_ICON_3 = <CloseOutlined />;
const SAVE_ICON_5 = <SaveOutlined />;

const FormularioParto: React.FC = () => {
  const { message } = useAntdApp();
  const { embarazoId, id } = useParams<{ embarazoId?: string; id?: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const loadingDataRef = useRef(false);
  const embarazoRef = useRef<Embarazo | null>(null);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const pacientesRef = useRef<Paciente[]>([]);
  const [recomendaciones, setRecomendaciones] = useState<Recomendacion[]>([]);
  const [alertas, setAlertas] = useState<AlertaParto[]>([]);
  const [esAborto, setEsAborto] = useState(false);
  const [tipoEvento, setTipoEvento] = useState<'aborto' | 'parto' | null>(null);
  const [tipoEventoManual, setTipoEventoManual] = useState(false);
  const modoEdicion = !!id;

  // Memoizar calcularAlertasYRecomendaciones para evitar re-renders innecesarios
  const calcularAlertasYRecomendaciones = useCallback((edadGestacional: string) => {
    const regex = /^(\d+)\+(\d)$/;
    if (!regex.test(edadGestacional)) {
      setRecomendaciones([]);
      setAlertas([]);
      return;
    }

    const [, semanasStr, diasStr] = edadGestacional.match(regex)!;
    const semanas = parseInt(semanasStr);
    const dias = parseInt(diasStr);

    const esAbortoDetectado = semanas < 20;
    setEsAborto(esAbortoDetectado);

    if (!tipoEventoManual) {
      if (esAbortoDetectado && tipoEvento !== 'aborto') {
        setTipoEvento('aborto');
        message.info('Se ha seleccionado automáticamente: Protocolo de Aborto (< 20 semanas)');
      } else if (!esAbortoDetectado && tipoEvento !== 'parto') {
        setTipoEvento('parto');
        message.info('Se ha seleccionado automáticamente: Registro de Parto (≥ 20 semanas)');
      }
    }

    const alertasTemp: AlertaParto[] = [];
    if (semanas < 20) {
      alertasTemp.push({
        tipo: 'critica', nivel: 'error', categoria: 'edad_gestacional',
        mensaje: `⚠️ ABORTO: Edad gestacional muy temprana (${semanas}+${dias} semanas)`,
        recomendacion: 'Protocolo de aborto. Manejo de duelo. Apoyo psicológico.',
      });
    } else if (semanas < 28) {
      alertasTemp.push({
        tipo: 'critica', nivel: 'error', categoria: 'edad_gestacional',
        mensaje: `🚨 PREMATURO EXTREMO: ${semanas}+${dias} semanas`,
        recomendacion: 'Requiere UCIN nivel III. Surfactante. Soporte ventilatorio.',
      });
    } else if (semanas < 32) {
      alertasTemp.push({
        tipo: 'critica', nivel: 'error', categoria: 'edad_gestacional',
        mensaje: `⚠️ MUY PREMATURO: ${semanas}+${dias} semanas`,
        recomendacion: 'Requiere UCIN. Monitoreo intensivo neonatal.',
      });
    } else if (semanas < 37) {
      alertasTemp.push({
        tipo: 'moderada', nivel: 'warning', categoria: 'edad_gestacional',
        mensaje: `⚠️ PREMATURO: ${semanas}+${dias} semanas`,
        recomendacion: 'Vigilancia neonatal. Riesgo de SDR. Considerar corticoides.',
      });
    } else if (semanas >= 42) {
      alertasTemp.push({
        tipo: 'moderada', nivel: 'warning', categoria: 'edad_gestacional',
        mensaje: `⚠️ POST-TÉRMINO: ${semanas}+${dias} semanas`,
        recomendacion: 'Evaluación urgente. Considerar inducción. Monitoreo fetal continuo.',
      });
    }
    setAlertas(alertasTemp);

    const recs: Recomendacion[] = [];
    if (semanas < 14) {
      recs.push({
        tipo: 'informacion', periodo: 'Primer Trimestre', titulo: 'Cuidados del Primer Trimestre',
        recomendaciones: [
          'Iniciar ácido fólico (400-800 mcg/día)', 'Evitar alcohol, tabaco y drogas',
          'Ecografía del primer trimestre (11-13 semanas)', 'Exámenes de laboratorio',
          'Evitar medicamentos no prescritos', 'No levantar objetos pesados',
        ],
      });
    }
    if (semanas >= 14 && semanas < 28) {
      recs.push({
        tipo: 'informacion', periodo: 'Segundo Trimestre', titulo: 'Cuidados del Segundo Trimestre',
        recomendaciones: [
          'Ecografía morfológica (18-22 semanas)', 'Prueba de glucosa (24-28 semanas)',
          'Control de peso y presión arterial', 'Ejercicio moderado regular',
          'Suplemento de hierro si hay anemia', 'Vigilar signos de parto prematuro',
        ],
      });
    }
    if (semanas >= 28) {
      recs.push({
        tipo: 'importante', periodo: 'Tercer Trimestre', titulo: 'Cuidados del Tercer Trimestre',
        recomendaciones: [
          'Monitoreo fetal frecuente', 'Controles prenatales frecuentes',
          'Preparación para el parto', 'Vigilar movimientos fetales',
          'Acudir inmediatamente si hay signos de alarma',
        ],
      });
    }
    setRecomendaciones(recs);
  }, [tipoEvento, tipoEventoManual, message]);

  const cargarEmbarazo = useCallback(async (embarazoId: number) => {
    loadingDataRef.current = true;
    try {
      const data = await embarazosService.getById(embarazoId);
      embarazoRef.current = data;
      if (data) {
        let semanas = 0, dias = 0;
        if (data.fecha_ultima_menstruacion) {
          const hoy = dayjs(), fum = dayjs(data.fecha_ultima_menstruacion);
          const diff = hoy.diff(fum, 'day');
          semanas = Math.floor(diff / 7);
          dias = diff % 7;
        }
        form.setFieldsValue({
          embarazo: data.id,
          paciente: typeof data.paciente === 'object' ? (data.paciente as any).id : data.paciente,
          semanas_gestacion: semanas,
          dias_gestacion: dias,
        });
        calcularAlertasYRecomendaciones(`${semanas}+${dias}`);
      }
    } catch (error) {
      message.error('Error al cargar datos del embarazo');
    } finally {
      loadingDataRef.current = false;
    }
  }, [form, calcularAlertasYRecomendaciones, message]);

  const cargarParto = useCallback(async (partoId: number) => {
    loadingDataRef.current = true;
    try {
      const partoData = await partosService.getById(partoId);
      if (partoData.embarazo) {
        const embarazoData = await embarazosService.getById(partoData.embarazo);
        embarazoRef.current = embarazoData;
      }
      const edadGest = partoData.edad_gestacional_parto || '';
      let semanas = 0, dias = 0;
      if (edadGest) {
        const parts = edadGest.split('+');
        semanas = parseInt(parts[0]) || 0;
        dias = parseInt(parts[1]) || 0;
      }
      const isAborto = semanas < 20;
      setTipoEvento(isAborto ? 'aborto' : 'parto');
      setEsAborto(isAborto);
      calcularAlertasYRecomendaciones(edadGest);

      const formValues: any = {
        embarazo: partoData.embarazo,
        semanas_gestacion: semanas,
        dias_gestacion: dias,
        fecha_parto: partoData.fecha_parto ? dayjs(partoData.fecha_parto) : undefined,
        parto_finalizado: partoData.parto_finalizado,
        perdida_sanguinea_estimada: partoData.perdida_sanguinea_estimada,
        hemorragia_postparto: partoData.hemorragia_postparto,
        complicaciones_maternas: partoData.complicaciones_maternas,
      };

      if (isAborto) {
        formValues.tipo_aborto = partoData.tipo_aborto;
        formValues.metodo_evacuacion = partoData.metodo_evacuacion;
        formValues.apoyo_psicologico_realizado = partoData.apoyo_psicologico_realizado;
        formValues.protocolo_duelo_aplicado = partoData.protocolo_duelo_aplicado;
        formValues.observaciones_aborto = partoData.observaciones_aborto;
      } else {
        formValues.tipo_parto = partoData.tipo_parto;
        formValues.presentacion_fetal = partoData.presentacion_fetal;
        formValues.posicion_fetal = partoData.posicion_fetal;
        formValues.estado_membranas = partoData.estado_membranas;
        formValues.caracteristicas_liquido = partoData.caracteristicas_liquido;
        formValues.duracion_trabajo_parto_horas = partoData.duracion_trabajo_parto_horas;
        formValues.duracion_periodo_expulsivo_minutos = partoData.duracion_periodo_expulsivo_minutos;
        const rn = partoData.recien_nacidos?.[0];
        if (rn) {
          formValues.sexo_bebe = rn.sexo;
          formValues.peso_bebe = rn.peso_nacimiento;
          formValues.talla_bebe = rn.talla_nacimiento;
          formValues.apgar_1min = rn.apgar_1_minuto;
          formValues.apgar_5min = rn.apgar_5_minutos;
        }
      }
      form.setFieldsValue(formValues);
    } catch (error) {
      message.error('Error al cargar los datos del parto');
    } finally {
      loadingDataRef.current = false;
    }
  }, [form, calcularAlertasYRecomendaciones, message]);

  const fetchData = useCallback(async () => {
    try {
      const [pacientesData, embarazosData] = await Promise.all([
        pacientesService.getAll(),
        embarazosService.getAll()
      ]);
      pacientesRef.current = pacientesData;
      setEmbarazos(embarazosData.filter((e: Embarazo) => e.estado === 'activo'));
    } catch (error) {
      message.error('Error al cargar datos iniciales');
    }
  }, [message]);

  const initializeData = useCallback(async () => {
    await fetchData();
    if (id) {
      cargarParto(parseInt(id));
    } else if (embarazoId) {
      cargarEmbarazo(parseInt(embarazoId));
    }
  }, [id, embarazoId, cargarEmbarazo, cargarParto, fetchData]);

  useEffect(() => {
    initializeData();
  }, [initializeData]);

  const getNombrePaciente = (embId: number): string => {
    const emb = embarazos.find((e) => e.id === embId);
    if (!emb) return 'Paciente no encontrado';
    const pInfo = (emb as any).paciente_info;
    if (pInfo) return `${pInfo.id_clinico} - ${pInfo.nombre} ${pInfo.apellido_paterno}`;
    return 'Paciente no encontrado';
  };

  const handleEmbarazoChange = (embId: number) => {
    const selected = embarazos.find((e) => e.id === embId);
    embarazoRef.current = selected || null;
    setTipoEventoManual(false);
    if (selected) {
      let semanas = 0, dias = 0;
      if (selected.fecha_ultima_menstruacion) {
        const diff = dayjs().diff(dayjs(selected.fecha_ultima_menstruacion), 'day');
        semanas = Math.floor(diff / 7);
        dias = diff % 7;
      }
      form.setFieldsValue({
        embarazo: selected.id,
        paciente: typeof selected.paciente === 'object' ? (selected.paciente as any).id : selected.paciente,
        semanas_gestacion: semanas,
        dias_gestacion: dias,
      });
      calcularAlertasYRecomendaciones(`${semanas}+${dias}`);
    }
  };

  const handleSave = async (values: any) => {
    setLoading(true);
    try {
      const dataComun: any = {
        embarazo: embarazoRef.current?.id,
        paciente: typeof embarazoRef.current?.paciente === 'object' ? (embarazoRef.current.paciente as any).id : embarazoRef.current?.paciente,
        fecha_parto: values.fecha_parto ? dayjs(values.fecha_parto).format('YYYY-MM-DD HH:mm:ss') : undefined,
        edad_gestacional_parto: `${values.semanas_gestacion}+${values.dias_gestacion}`,
        parto_finalizado: values.parto_finalizado,
        perdida_sanguinea_estimada: values.perdida_sanguinea_estimada,
        hemorragia_postparto: values.hemorragia_postparto,
        complicaciones_maternas: values.complicaciones_maternas,
      };

      let dataToSend = { ...dataComun };
      if (tipoEvento === 'aborto') {
        Object.assign(dataToSend, {
          tipo_aborto: values.tipo_aborto,
          metodo_evacuacion: values.metodo_evacuacion,
          apoyo_psicologico_realizado: values.apoyo_psicologico_realizado || false,
          protocolo_duelo_aplicado: values.protocolo_duelo_aplicado || false,
          observaciones_aborto: values.observaciones_aborto,
        });
      } else if (tipoEvento === 'parto') {
        Object.assign(dataToSend, {
          tipo_parto: values.tipo_parto,
          presentacion_fetal: values.presentacion_fetal,
          posicion_fetal: values.posicion_fetal,
          estado_membranas: values.estado_membranas,
          caracteristicas_liquido: values.caracteristicas_liquido,
          duracion_trabajo_parto_horas: values.duracion_trabajo_parto_horas,
          duracion_periodo_expulsivo_minutos: values.duracion_periodo_expulsivo_minutos,
          sexo_bebe: values.sexo_bebe,
          peso_bebe: values.peso_bebe,
          talla_bebe: values.talla_bebe,
          apgar_1min: values.apgar_1min,
          apgar_5min: values.apgar_5min,
        });
      }

      if (modoEdicion && id) {
        await partosService.update(parseInt(id), dataToSend);
      } else {
        await partosService.create(dataToSend);
      }
      message.success('Guardado correctamente');
      navigate(FRONTEND_ROUTES.DASHBOARD.PARTOS);
    } catch (error) {
      message.error('Error al guardar');
    } finally {
      setLoading(false);
    }
  };

  if (loadingDataRef.current) return <div style={{ textAlign: 'center', padding: '100px' }}><Spin size="large" tip="Cargando…"><div /></Spin></div>;

  return (
    <div>
      <Button icon={ARROW_LEFT_ICON_6} onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>Volver</Button>
      <Card
        title={
          <Space>
            <Badge count={esAborto ? 'Aborto' : 'Parto'} style={{ backgroundColor: esAborto ? '#ff4d4f' : '#52c41a' }}>
              {tipoEvento === 'aborto' ? <WarningOutlined style={{ color: '#ff4d4f', fontSize: 24 }} /> : <HeartOutlined style={{ fontSize: 24 }} />}
            </Badge>
            <Title level={4} style={{ margin: 0 }}>{modoEdicion ? 'Editar' : 'Registro de'} {tipoEvento === 'aborto' ? 'Aborto' : 'Parto'}</Title>
          </Space>
        }
      >
        <Form form={form} layout="vertical" onFinish={handleSave} initialValues={{ tipo_parto: 'vaginal_espontaneo', parto_finalizado: true }}>
          <SeccionEmbarazoEvento
            embarazos={embarazos}
            embarazoId={embarazoId}
            tipoEvento={tipoEvento}
            setTipoEvento={setTipoEvento}
            setTipoEventoManual={setTipoEventoManual}
            getNombrePaciente={getNombrePaciente}
            handleEmbarazoChange={handleEmbarazoChange}
            form={form}
          />

          <AlertasYRecomendaciones alertas={alertas} recomendaciones={recomendaciones} />

          {tipoEvento === 'aborto' && <SeccionAborto form={form} calcularAlertasYRecomendaciones={calcularAlertasYRecomendaciones} />}
          {tipoEvento === 'parto' && (
            <>
              <SeccionParto form={form} calcularAlertasYRecomendaciones={calcularAlertasYRecomendaciones} tipoEvento={tipoEvento} />
              <SeccionRecienNacido tipoEvento={tipoEvento} />
            </>
          )}

          <div style={{ marginTop: 24, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => navigate(-1)} icon={CLOSE_ICON_3}>Cancelar</Button>
              <Button type="primary" htmlType="submit" icon={SAVE_ICON_5} loading={loading}>Guardar</Button>
            </Space>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default FormularioParto;
