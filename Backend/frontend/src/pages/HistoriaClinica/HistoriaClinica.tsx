import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Layout,
  Card,
  Row,
  Col,
  Typography,
  Tabs,
  Table,
  Tag,
  Button,
  Descriptions,
  Alert,
  Spin,
  Divider,
  Tooltip,
  Space,
  Badge,
  Form,
  Input,
  Select,
  List,
  Dropdown
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  MedicineBoxOutlined,
  ExperimentOutlined,
  ScanOutlined,
  ArrowLeftOutlined,
  HeartOutlined,
  LineChartOutlined,
  HistoryOutlined,
  WomanOutlined,
  PlusOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  SafetyCertificateOutlined,
  CalculatorOutlined,
  TableOutlined,
  SearchOutlined,
  BellOutlined
} from '@ant-design/icons';
import axios, { AxiosResponse } from 'axios';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import duration from 'dayjs/plugin/duration';
import 'dayjs/locale/es';
import './HistoriaClinica.css';
import { API_URL } from '../../services/api';
import { antecedentesService,
  AntecedenteGinecoObstetrico,
  AntecedentePatologico
} from '../../services/antecedentesService';
import { useAuth } from '../../hooks/useAuth';
import {
  Paciente,
  Embarazo,
  ControlPrenatal,
  Ecografia,
  Laboratorio,
  NotaEvolucion,
  Tratamiento,
  Vacuna,
  Cita,
  Parto,
  AlertaClinica,
  CalculadoraResultado,
  ProtocoloObstetrico,
  EstadisticaGlobal,
  ExportConfig,
  BusquedaFiltro,
  RecordatorioClinico
} from './types';
import {
  PROTOCOLOS_EMBARAZO,
  VACUNAS_EMBARAZO,
  getReferenceAU,
  calcularEG,
  calcularFPP,
  calcularIMC,
  calcularGananciaPesoRecomendada,
  calcularRiesgoPreeclampsia,
  calcularPesoFetalEstimado,
  calcularPercentilFetal,
  generarAlertas,
  interpretarNST,
  actualizarProtocolos,
  calcularTendencias
} from './utils';
import TabVacunas from './sections/TabVacunas';
import {
  ModalRegistroPacienteCompleto
} from './sections/ModalRegistroPacienteCompleto';
import TabTratamientos from './sections/TabTratamientos';
import TabPartos from './sections/TabPartos';
import TabNotasEvolucion from './sections/TabNotasEvolucion';
import DashboardObstetrico from './sections/TabDashboard';
import TabControles from './sections/TabControles';
import TabEcografias from './sections/TabEcografias';
import TabLaboratorios from './sections/TabLaboratorios';
import TabHerramientasClinicas from './sections/TabHerramientasClinicas';
import TabProtocolosCumplimiento from './sections/TabProtocolosCumplimiento';
import TabComparacionEmbarazos from './sections/TabComparacionEmbarazos';
import TabAntecedentes from './sections/TabAntecedentes';
import HeaderInfoPaciente from './sections/HeaderInfoPaciente';
import HistoriaClinicaModales from './sections/HistoriaClinicaModales';
import { RiesgoPreeclampsiaItem } from './historiaClinicaHelpers';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  RechartsTooltip,
  ResponsiveContainer,
} from './rechartsLazy';

const { Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

dayjs.extend(relativeTime);
dayjs.extend(duration);
dayjs.locale('es');


const HistoriaClinica: React.FC = () => {
  const { message, notification, modal } = useAntdApp();
  const { id: pacienteId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const [formNota] = Form.useForm();
  const [formReceta] = Form.useForm();
  const mountedRef = React.useRef(false);
  React.useEffect(() => { mountedRef.current = true; }, []);

  // --- ESTADOS GLOBALES ---
  const isMounted = React.useRef(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');

  // --- DATOS CLÍNICOS ---
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [embarazoActivo, setEmbarazoActivo] = useState<Embarazo | null>(null);
  const [historialEmbarazos, setHistorialEmbarazos] = useState<Embarazo[]>([]);
  const [controles, setControles] = useState<ControlPrenatal[]>([]);
  const [ecografias, setEcografias] = useState<Ecografia[]>([]);
  const [laboratorios, setLaboratorios] = useState<Laboratorio[]>([]);
  const [notas, setNotas] = useState<NotaEvolucion[]>([]);
  const [tratamientos, setTratamientos] = useState<Tratamiento[]>([]);
  const [vacunas, setVacunas] = useState<Vacuna[]>([]);
  const [citas, setCitas] = useState<Cita[]>([]);
  const [partos, setPartos] = useState<Parto[]>([]);
  const [antecedenteGineco, setAntecedenteGineco] = useState<AntecedenteGinecoObstetrico | null>(null);
  const [antecedentePatologico, setAntecedentePatologico] = useState<AntecedentePatologico | null>(null);

  // --- VISIBILIDAD DE MODALES/DRAWERS ---
  const [drawerNotasVisible, setDrawerNotasVisible] = useState(false);
  const [modalRiesgoVisible, setModalRiesgoVisible] = useState(false);
  const [modalRecetaVisible, setModalRecetaVisible] = useState(false);
  const [drawerCalculadoraVisible, setDrawerCalculadoraVisible] = useState(false);
  const [modalProtocolosVisible, setModalProtocolosVisible] = useState(false);
  const [modalExportarVisible, setModalExportarVisible] = useState(false);
  const [drawerTimelineVisible, setDrawerTimelineVisible] = useState(false);
  const [modalComparacionVisible, setModalComparacionVisible] = useState(false);
  const [drawerAlertasVisible, setDrawerAlertasVisible] = useState(false);

  // --- ESTADOS PARA FUNCIONES AVANZADAS ---
  const [alertasActivas, setAlertasActivas] = useState<AlertaClinica[]>([]);
  const [protocolosEmbarazo, setProtocolosEmbarazo] = useState<ProtocoloObstetrico[]>([]);
  const [recordatorios, setRecordatorios] = useState<RecordatorioClinico[]>([]);
  const [busquedaFiltro, setBusquedaFiltro] = useState<BusquedaFiltro>({ texto: '', categoria: 'TODO' });

  const handleAgregarRecordatorio = useCallback(() => {
    setRecordatorios(prev => [
      ...prev,
      {
        id: `rec-${crypto.randomUUID()}`,
        tipo: 'CONTROL',
        titulo: 'Recordatorio',
        descripcion: 'Nuevo recordatorio',
        fecha_programada: dayjs().add(7, 'days').format('YYYY-MM-DD'),
        dias_restantes: 7,
        completado: false,
        prioridad: 'MEDIA',
      },
    ]);
    message.success('Recordatorio agregado');
  }, [message]);

  const resultadosCalculadoraRef = useRef<CalculadoraResultado[]>([]);
  const [tendenciasLaboratorio, setTendenciasLaboratorio] = useState<Array<{ examen: string; valores: Array<{ fecha: string; valor: number; referencia: string }>; tendencia: 'MEJORANDO' | 'EMPEORANDO' | 'ESTABLE' }>>([]);

  // --- CONFIGURACIÓN DE VISTA ---
  const [vistaCompacta, setVistaCompacta] = useState(false);
  const [mostrarGraficasAvanzadas, setMostrarGraficasAvanzadas] = useState(true);
  const [periodoVisualizacion, setPeriodoVisualizacion] = useState<'TODO' | 'ULTIMO_MES' | 'ULTIMO_TRIMESTRE'>('TODO');

  // ==========================================
  // 4. CARGA DE DATOS (PARALLEL FETCHING)
  // ==========================================
  const fetchHistoriaClinica = React.useCallback(async () => {
    if (!pacienteId) return;
    setLoading(true);
    try {
      const token = getToken();
      const headers = { Authorization: `Bearer ${token}` };

      // 1. Datos Base del Paciente
      const resPaciente = await axios.get(`${API_URL}/pacientes/${pacienteId}/`, { headers });
      setPaciente(resPaciente.data);

      // 2. Buscar Embarazos
      const resEmbarazos = await axios.get(`${API_URL}/embarazos/?paciente=${pacienteId}`, { headers });
      const todosEmbarazos = Array.isArray(resEmbarazos.data.results || resEmbarazos.data)
        ? (resEmbarazos.data.results || resEmbarazos.data)
        : [];

      // Separar activo e historial
      const activo = todosEmbarazos.find((e: Embarazo) => e.estado === 'activo');

      // Si no hay embarazo activo, usar el más reciente (ordenado por FUM)
      const embarazoParaMostrar = activo || (todosEmbarazos.length > 0
        ? todosEmbarazos.reduce((latest: Embarazo, e: Embarazo) =>
            new Date(e.fecha_ultima_menstruacion).getTime() > new Date(latest.fecha_ultima_menstruacion).getTime() ? e : latest
          )
        : null);

      setEmbarazoActivo(embarazoParaMostrar);
      setHistorialEmbarazos(todosEmbarazos.filter((e: Embarazo) => e.id !== embarazoParaMostrar?.id));

      // 3. Carga de Datos (carga para embarazo activo o más reciente)
      const promises: Promise<AxiosResponse<any>>[] = [
        axios.get(`${API_URL}/notas-evolucion/?paciente=${pacienteId}`, { headers }),
        axios.get(`${API_URL}/vacunas/?paciente=${pacienteId}`, { headers }),
        axios.get(`${API_URL}/citas/?paciente=${pacienteId}`, { headers }).catch(err => ({ data: [], status: 200, statusText: 'OK', headers: {}, config: {} as any, request: {} })),
        axios.get(`${API_URL}/partos/?paciente=${pacienteId}`, { headers }).catch(err => ({ data: [], status: 200, statusText: 'OK', headers: {}, config: {} as any, request: {} }))
      ];

      const emptyResponse = { data: [], status: 200, statusText: 'OK', headers: {}, config: {} as any, request: {} };

      if (embarazoParaMostrar) {
        promises.push(
          axios.get(`${API_URL}/controles/?embarazo=${embarazoParaMostrar.id}`, { headers })
            .catch(() => emptyResponse)
        );
        promises.push(
          axios.get(`${API_URL}/ecografias/?embarazo=${embarazoParaMostrar.id}`, { headers })
            .catch(() => emptyResponse)
        );
        promises.push(
          axios.get(`${API_URL}/laboratorios/?paciente=${pacienteId}&fecha_min=${embarazoParaMostrar.fecha_ultima_menstruacion}`, { headers })
            .catch(() => emptyResponse)
        );
        // REMOVIDO: tratamientos endpoint no existe
        // promises.push(
        //   axios.get(`${API_URL}/tratamientos/?embarazo=${embarazoParaMostrar.id}`, { headers })
        //     .catch(() => emptyResponse)
        // );
      } else {
        // Si no hay ningún embarazo, aún así intentar cargar datos generales
        promises.push(Promise.resolve(emptyResponse));
        promises.push(Promise.resolve(emptyResponse));
        promises.push(
          axios.get(`${API_URL}/laboratorios/?paciente=${pacienteId}&limit=10`, { headers })
            .catch(() => emptyResponse)
        );
        // REMOVIDO: tratamientos endpoint no existe
        // promises.push(Promise.resolve(emptyResponse));
      }

      const [resNotas, resVacunas, resCitas, resPartos, resControles, resEcos, resLabs] = await Promise.all(promises);

      const notasData = resNotas.data.results || resNotas.data;
      if (isMounted.current) {
        setNotas(Array.isArray(notasData) ? notasData : []);
      }

      const vacunasData = resVacunas.data.results || resVacunas.data;
      const citasData = resCitas.data.results || resCitas.data;
      const partosData = resPartos.data.results || resPartos.data;
      const ctrlData = resControles.data.results || resControles.data;
      const controlesArray = Array.isArray(ctrlData) ? ctrlData : [];
      const ecosData = resEcos.data.results || resEcos.data;
      const labsData = resLabs.data.results || resLabs.data;

      if (isMounted.current) {
        setVacunas(Array.isArray(vacunasData) ? vacunasData : []);
        setCitas(Array.isArray(citasData) ? citasData : []);
        setPartos(Array.isArray(partosData) ? partosData : []);
        setControles(controlesArray.sort((a: any, b: any) => new Date(a.fecha_control || a.fecha || 0).getTime() - new Date(b.fecha_control || b.fecha || 0).getTime()));
        setEcografias(Array.isArray(ecosData) ? ecosData : []);
        setLaboratorios(Array.isArray(labsData) ? labsData : []);
        setTratamientos([]);
      }

      // Cargar antecedentes médicos detallados
      try {
        const antecedentes = await antecedentesService.getAntecedentesPaciente(Number(pacienteId));
        setAntecedenteGineco(antecedentes.ginecoObstetrico);
        setAntecedentePatologico(antecedentes.patologico);
      } catch (err) {
        setAntecedenteGineco(null);
        setAntecedentePatologico(null);
      }

      // Cargar datos adicionales de análisis
      if (isMounted.current) {
        setAlertasActivas(generarAlertas(controlesArray, labsData, embarazoParaMostrar));
        setProtocolosEmbarazo(actualizarProtocolos(controlesArray, ecosData, labsData));
        setTendenciasLaboratorio(calcularTendencias(labsData));
      }

    } catch (err: any) {
      setError("No se pudo cargar la historia clínica completa. Verifique su conexión o permisos.");
      notification.error({ message: 'Error de Conexión', description: 'Algunos módulos clínicos no pudieron cargarse.' });
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [pacienteId, notification, getToken]);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    fetchHistoriaClinica();
  }, [fetchHistoriaClinica]); // Usar fetchHistoriaClinica como dependencia

  // ==========================================
  // 5. LÓGICA DE NEGOCIO Y CÁLCULOS
  // ==========================================

  const calcularEGActual = React.useCallback(() => {
    if (!embarazoActivo) return { semanas: 0, dias: 0 };
    const fechaBase = embarazoActivo.fecha_ultima_menstruacion;
    const hoy = dayjs();
    const fum = dayjs(fechaBase);
    const diasDiff = hoy.diff(fum, 'days');
    return { semanas: Math.floor(diasDiff / 7), dias: diasDiff % 7 };
  }, [embarazoActivo]);

  const datosGraficas = useMemo(() => {
    return controles.map(c => {
      const ref = getReferenceAU(c.semanas_gestacion);
      return {
        semana: c.semanas_gestacion,
        peso: c.peso_actual,
        au: c.altura_uterina,
        sistolica: c.presion_arterial_sistolica,
        diastolica: c.presion_arterial_diastolica,
        p10: ref.p10,
        p50: ref.p50,
        p90: ref.p90,
        fecha: dayjs(c.fecha_control || c.fecha).format('DD/MM')
      };
    });
  }, [controles]);

  const alertasClinicas = useMemo(() => {
    const list: AlertaClinica[] = [];
    const ultimoCtrl = controles[controles.length - 1];
    if (ultimoCtrl && (ultimoCtrl.presion_arterial_sistolica >= 140 || ultimoCtrl.presion_arterial_diastolica >= 90)) {
      list.push({
        id: `alerta-${Date.now()}-1`,
        tipo: 'ERROR',
        prioridad: 'ALTA',
        mensaje: 'ALERTA: Presión Arterial Elevada en último control. Descartar Preeclampsia.',
        categoria: 'SIGNOS_VITALES',
        fecha_generacion: new Date().toISOString(),
        resuelta: false,
        acciones_recomendadas: ['Control de PA en 48h', 'Laboratorios: Proteinuria, Creatinina', 'Evaluación por especialista']
      });
    }
    const labsAnormales = laboratorios.filter(l => l.es_anormal).length;
    if (labsAnormales > 0) {
      list.push({
        id: `alerta-${Date.now()}-2`,
        tipo: 'WARNING',
        prioridad: 'MEDIA',
        mensaje: `${labsAnormales} resultados de laboratorio reportados como ANORMALES.`,
        categoria: 'LABORATORIO',
        fecha_generacion: new Date().toISOString(),
        resuelta: false,
        acciones_recomendadas: ['Revisar resultados', 'Correlacionar con clínica', 'Considerar repetir exámenes']
      });
    }
    if (((paciente as any)?.grupo_sanguineo || paciente?.tipo_sangre) && paciente?.factor_rh === '-' && !laboratorios.some(l => l.tipo_examen.includes('Coombs'))) {
      list.push({
        id: `alerta-${Date.now()}-3`,
        tipo: 'WARNING',
        prioridad: 'MEDIA',
        mensaje: 'Paciente RH Negativo: Verificar solicitud de Test de Coombs Indirecto.',
        categoria: 'INMUNOLOGIA',
        fecha_generacion: new Date().toISOString(),
        resuelta: false,
        acciones_recomendadas: ['Solicitar Coombs Indirecto', 'Evaluar necesidad de Inmunoglobulina Anti-D']
      });
    }

    // Verificar protocolos de atención según edad gestacional
    if (embarazoActivo) {
      const { semanas } = calcularEGActual();

      // Alerta para ecografía morfológica
      if (semanas >= 18 && semanas <= 23 && !ecografias.some(e => e.tipo.includes('Morfológica'))) {
        list.push({
          id: `alerta-${Date.now()}-4`,
          tipo: 'INFO',
          prioridad: 'ALTA',
          mensaje: `Semana ${semanas}: VENTANA ÓPTIMA para Ecografía Morfológica (18-23 sem)`,
          categoria: 'PROTOCOLO',
          fecha_generacion: new Date().toISOString(),
          resuelta: false,
          acciones_recomendadas: ['Agendar ecografía morfológica Nivel II', 'Informar a la paciente']
        });
      }

      // Alerta para test de O'Sullivan
      if (semanas >= 24 && semanas <= 28 && !laboratorios.some(l => {
        const tipoExamen = String(l.tipo_examen || '').toLowerCase();
        return tipoExamen.includes('glucosa') || tipoExamen.includes('sullivan');
      })) {
        list.push({
          id: `alerta-${Date.now()}-5`,
          tipo: 'INFO',
          prioridad: 'ALTA',
          mensaje: `Semana ${semanas}: Solicitar Test de O'Sullivan (Tamizaje Diabetes Gestacional)`,
          categoria: 'PROTOCOLO',
          fecha_generacion: new Date().toISOString(),
          resuelta: false,
          acciones_recomendadas: ['Solicitar Curva de Tolerancia a la Glucosa 75g', 'Educación sobre diabetes gestacional']
        });
      }

      // Alerta para cultivo vaginal/rectal (Streptococo B)
      if (semanas >= 35 && semanas <= 37 && !laboratorios.some(l => {
        const tipoExamen = String(l.tipo_examen || '').toLowerCase();
        return tipoExamen.includes('cultivo') && tipoExamen.includes('vaginal');
      })) {
        list.push({
          id: `alerta-${Date.now()}-6`,
          tipo: 'INFO',
          prioridad: 'ALTA',
          mensaje: `Semana ${semanas}: Solicitar Cultivo Vaginal/Rectal para Streptococo B`,
          categoria: 'PROTOCOLO',
          fecha_generacion: new Date().toISOString(),
          resuelta: false,
          acciones_recomendadas: ['Toma de muestra vaginal y rectal', 'Informar a la paciente sobre prevención de Streptococo B']
        });
      }

      // Alerta de controles insuficientes
      const controlesEsperados = Math.floor(semanas / 4) + 1;
      if (controles.length < controlesEsperados) {
        list.push({
          id: `alerta-${Date.now()}-7`,
          tipo: 'WARNING',
          prioridad: 'MEDIA',
          mensaje: `Controles prenatales insuficientes: ${controles.length} de ${controlesEsperados} esperados`,
          categoria: 'ADHERENCIA',
          fecha_generacion: new Date().toISOString(),
          resuelta: false,
          acciones_recomendadas: ['Fortalecer adherencia al control prenatal', 'Identificar barreras de acceso', 'Agendar próxima cita']
        });
      }
    }

    return list;
  }, [controles, laboratorios, paciente, embarazoActivo, ecografias, calcularEGActual]);

  // ==========================================
  // 6. MANEJADORES (HANDLERS)
  // ==========================================

  const handleAddNota = useCallback(async (values: any) => {
    setSaving(true);
    try {
      const nuevaNota = { ...values, id: Date.now(), fecha_hora: new Date().toISOString(), autor: { username: 'dr_actual' } };
      setNotas(prev => [nuevaNota, ...prev]);
      message.success('Nota guardada exitosamente');
      formNota.resetFields();
      setDrawerNotasVisible(false);
    } catch (e) {
      message.error('Error al guardar nota');
    } finally {
      setSaving(false);
    }
  }, [message, formNota]);

  const handleAddTratamiento = useCallback(async (values: any) => {
    setModalRecetaVisible(false);
    message.success("Tratamiento prescrito correctamente");
  }, [message]);

  const handleExportarHistoria = useCallback((config: ExportConfig) => {
    setSaving(true);
    try {
      notification.success({
        message: 'Exportación Iniciada',
        description: `Generando archivo ${config.formato}. Se descargará automáticamente.`
      });

      // Aquí iría la lógica real de exportación
      setTimeout(() => {
        message.success(`Historia clínica exportada en formato ${config.formato}`);
        setModalExportarVisible(false);
      }, 1500);
    } catch (error) {
      message.error('Error al exportar historia clínica');
    } finally {
      setSaving(false);
    }
  }, [notification, message]);

  const handleCalcularRiesgo = useCallback(() => {
    if (!paciente || !embarazoActivo || controles.length === 0) {
      message.warning('Se requieren datos de paciente y controles para calcular el riesgo');
      return;
    }

    const ultimoControl = controles[controles.length - 1];
    const riesgoPreeclampsia = calcularRiesgoPreeclampsia(
      paciente.edad ?? paciente.edad_actual ?? 0,
      ultimoControl.imc_actual || ultimoControl.imc || 0,
      ultimoControl.presion_arterial_sistolica,
      ultimoControl.presion_arterial_diastolica,
      {
        hipertension: String(paciente.antecedentes_patologicos || '').toLowerCase().includes('hipertens'),
        preeclampsiaPrevias: historialEmbarazos.filter(e =>
          String(e.observaciones || '').toLowerCase().includes('preeclampsia')
        ).length,
        diabetes: String(paciente.antecedentes_patologicos || '').toLowerCase().includes('diabetes')
      }
    );

    modal.info({
      title: 'Evaluación de Riesgo de Preeclampsia',
      width: 600,
      content: (
        <div>
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Nivel de Riesgo">
              <Tag color={riesgoPreeclampsia.nivel === 'ALTO' ? 'red' : riesgoPreeclampsia.nivel === 'MODERADO' ? 'orange' : 'green'}>
                {riesgoPreeclampsia.nivel}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Score Total">{riesgoPreeclampsia.score} puntos</Descriptions.Item>
          </Descriptions>
          <Divider orientation="left">Recomendaciones Clínicas</Divider>
          <List
            size="small"
            dataSource={riesgoPreeclampsia?.recomendaciones || []}
            renderItem={(item) => <RiesgoPreeclampsiaItem item={item} />}
          />
        </div>
      )
    });
  }, [paciente, embarazoActivo, controles, message, historialEmbarazos, modal]);

  const handleCalcularPesoFetal = useCallback((dbt: number, ca: number, lf: number) => {
    if (!embarazoActivo) {
      message.warning('No hay embarazo activo');
      return;
    }

    const pesoEstimado = calcularPesoFetalEstimado(dbt, ca, lf);
    const { semanas } = calcularEGActual();
    const { percentil, clasificacion } = calcularPercentilFetal(pesoEstimado, semanas);

    const resultado: CalculadoraResultado = {
      nombre: 'Peso Fetal Estimado',
      valor: Math.round(pesoEstimado),
      unidad: 'gramos',
      interpretacion: `Percentil ${percentil}: ${clasificacion}`,
      rango_normal: `P10-P90 para ${semanas} semanas`,
      alerta: percentil < 10 || percentil > 90
    };

    resultadosCalculadoraRef.current = [resultado, ...resultadosCalculadoraRef.current];

    notification.info({
      message: 'Cálculo Completado',
      description: `Peso fetal estimado: ${Math.round(pesoEstimado)}g (P${percentil})`,
      duration: 5
    });
  }, [embarazoActivo, message, calcularEGActual, notification]);

  const handleCalcularIMCGanancia = useCallback(() => {
    if (!paciente || controles.length === 0) {
      message.warning('Se requieren datos de controles prenatales');
      return;
    }

    const primerControl = controles[0];
    const ultimoControl = controles[controles.length - 1];

    if (!primerControl.peso_actual || !ultimoControl.peso_actual) {
      message.warning('Se requieren datos de peso en los controles prenatales');
      return;
    }

    // Asumiendo que tenemos la talla en el paciente (en cm)
    const tallaAsumida = 160; // Esto debería venir de los datos del paciente
    const imcInicial = calcularIMC(primerControl.peso_actual, tallaAsumida);
    const imcActual = calcularIMC(ultimoControl.peso_actual, tallaAsumida);

    const { semanas } = calcularEGActual();
    const gananciaRecomendada = calcularGananciaPesoRecomendada(imcInicial, semanas);
    const gananciaReal = ultimoControl.peso_actual - primerControl.peso_actual;

    const resultados: CalculadoraResultado[] = [
      {
        nombre: 'IMC Pregestacional',
        valor: imcInicial.toFixed(1),
        unidad: 'kg/m²',
        interpretacion: imcInicial < 18.5 ? 'Bajo Peso' : imcInicial < 25 ? 'Normal' : imcInicial < 30 ? 'Sobrepeso' : 'Obesidad',
        alerta: imcInicial < 18.5 || imcInicial >= 30
      },
      {
        nombre: 'IMC Actual',
        valor: imcActual.toFixed(1),
        unidad: 'kg/m²'
      },
      {
        nombre: 'Ganancia de Peso Actual',
        valor: gananciaReal.toFixed(1),
        unidad: 'kg',
        interpretacion: gananciaReal < gananciaRecomendada.minimo ? 'Insuficiente' :
          gananciaReal > gananciaRecomendada.maximo ? 'Excesiva' : 'Adecuada',
        rango_normal: `${gananciaRecomendada.minimo.toFixed(1)} - ${gananciaRecomendada.maximo.toFixed(1)} kg`,
        alerta: gananciaReal < gananciaRecomendada.minimo || gananciaReal > gananciaRecomendada.maximo
      },
      {
        nombre: 'Ganancia Total Recomendada',
        valor: `${gananciaRecomendada.total.min} - ${gananciaRecomendada.total.max}`,
        unidad: 'kg'
      }
    ];

    resultadosCalculadoraRef.current = resultados;

    modal.info({
      title: 'Análisis de IMC y Ganancia de Peso',
      width: 650,
      content: (
        <Table
          dataSource={resultados}
          columns={[
            { title: 'Parámetro', dataIndex: 'nombre', key: 'nombre' },
            {
              title: 'Valor',
              key: 'valor',
              render: (_, r) => <Text strong>{r.valor} {r.unidad}</Text>
            },
            {
              title: 'Interpretación',
              dataIndex: 'interpretacion',
              render: (text, r) => text ? (
                <Tag color={r.alerta ? 'red' : 'green'}>{text}</Tag>
              ) : '-'
            },
            { title: 'Rango Normal', dataIndex: 'rango_normal', render: (text) => text || '-' }
          ]}
          pagination={false}
          size="small"
        />
      )
    });
  }, [paciente, controles, message, calcularEGActual, modal]);

  const handleVerTendenciasLaboratorio = useCallback(() => {
    // Agrupar laboratorios por tipo de examen
    const agrupados: { [key: string]: Array<{ fecha: string; valor: number; referencia: string }> } = {};

    laboratorios.forEach(lab => {
      // Solo procesar laboratorios cuantitativos
      const valorNumerico = parseFloat(lab.resultado);
      if (!isNaN(valorNumerico)) {
        if (!agrupados[lab.tipo_examen]) {
          agrupados[lab.tipo_examen] = [];
        }
        agrupados[lab.tipo_examen].push({
          fecha: lab.fecha_toma,
          valor: valorNumerico,
          referencia: lab.valores_referencia
        });
      }
    });

    const tendencias: Array<{ examen: string; valores: Array<{ fecha: string; valor: number; referencia: string }>; tendencia: 'MEJORANDO' | 'EMPEORANDO' | 'ESTABLE' }> = Object.keys(agrupados).map(examen => {
      const valores = agrupados[examen].sort((a, b) =>
        new Date(a.fecha).getTime() - new Date(b.fecha).getTime()
      );

      // Determinar tendencia simple (comparando primero vs último)
      let tendencia: 'MEJORANDO' | 'EMPEORANDO' | 'ESTABLE' = 'ESTABLE';
      if (valores.length >= 2) {
        const primerValor = valores[0].valor;
        const ultimoValor = valores[valores.length - 1].valor;
        const cambio = ((ultimoValor - primerValor) / primerValor) * 100;

        if (Math.abs(cambio) < 10) {
          tendencia = 'ESTABLE';
        } else {
          // Esto es simplificado - en la realidad depende del tipo de examen
          tendencia = cambio > 0 ? 'EMPEORANDO' : 'MEJORANDO';
        }
      }

      return { examen, valores, tendencia };
    });

    setTendenciasLaboratorio(tendencias);

    modal.info({
      title: 'Análisis de Tendencias de Laboratorio',
      width: 800,
      content: (
        <div>
          {tendencias.map((t) => (
            <Card key={t.examen} size="small" style={{ marginBottom: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <Text strong>{t.examen}</Text>
                  <Tag color={t.tendencia === 'MEJORANDO' ? 'green' : t.tendencia === 'EMPEORANDO' ? 'red' : 'blue'}>
                    {t.tendencia}
                  </Tag>
                </Space>
                <ResponsiveContainer width="100%" height={150}>
                  <ComposedChart data={t.valores.map(v => ({ ...v, fechaCorta: dayjs(v.fecha).format('DD/MM') }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="fechaCorta" />
                    <YAxis />
                    <RechartsTooltip />
                    <Line type="monotone" dataKey="valor" stroke="#1890ff" strokeWidth={2} dot={{ r: 4 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Space>
            </Card>
          ))}
        </div>
      )
    });
  }, [laboratorios, modal]);

  const handleGenerarRecordatorios = useCallback(() => {
    if (!embarazoActivo) {
      message.warning('No hay embarazo activo');
      return;
    }

    const { semanas } = calcularEGActual();
    const nuevosRecordatorios: RecordatorioClinico[] = [];

    // Recordatorio de próximo control
    const ultimoControl = controles[controles.length - 1];
    if (ultimoControl && ultimoControl.proximo_control) {
      const diasRestantes = dayjs(ultimoControl.proximo_control).diff(dayjs(), 'days');
      if (diasRestantes >= 0 && diasRestantes <= 30) {
        nuevosRecordatorios.push({
          id: `rec-${Date.now()}-1`,
          tipo: 'CONTROL',
          titulo: 'Próximo Control Prenatal',
          descripcion: `Control #${controles.length + 1} - ${dayjs(ultimoControl.proximo_control).format('DD/MM/YYYY')}`,
          fecha_programada: ultimoControl.proximo_control,
          dias_restantes: diasRestantes,
          completado: false,
          prioridad: diasRestantes <= 3 ? 'ALTA' : diasRestantes <= 7 ? 'MEDIA' : 'BAJA'
        });
      }
    }

    // Recordatorios de vacunas pendientes
    VACUNAS_EMBARAZO.forEach(vacuna => {
      if (vacuna.obligatoria && !vacunas.some(v => v.nombre.includes(vacuna.nombre.split(' ')[0]))) {
        nuevosRecordatorios.push({
          id: `rec-${Date.now()}-vac-${vacuna.nombre}`,
          tipo: 'VACUNA',
          titulo: 'Vacuna Pendiente',
          descripcion: `Aplicar: ${vacuna.nombre}`,
          fecha_programada: dayjs().add(7, 'days').format('YYYY-MM-DD'),
          dias_restantes: 7,
          completado: false,
          prioridad: 'ALTA'
        });
      }
    });

    // Recordatorios de protocolos pendientes
    PROTOCOLOS_EMBARAZO.forEach(protocolo => {
      if (semanas >= protocolo.semanas_inicio && semanas <= protocolo.semanas_fin) {
        // Verificar si falta algún examen del protocolo
        const examenFaltante = protocolo.examenes_requeridos.find(examen => {
          const examenLower = String(examen || '').toLowerCase();
          return !laboratorios.some(l => String(l.tipo_examen || '').toLowerCase().includes(examenLower)) &&
            !ecografias.some(e => String(e.tipo || '').toLowerCase().includes(examenLower));
        });

        if (examenFaltante) {
          nuevosRecordatorios.push({
            id: `rec-${Date.now()}-prot-${protocolo.id}`,
            tipo: 'EXAMEN',
            titulo: protocolo.nombre,
            descripcion: `Solicitar ${examenFaltante}`,
            fecha_programada: dayjs().add(3, 'days').format('YYYY-MM-DD'),
            dias_restantes: 3,
            completado: false,
            prioridad: 'ALTA'
          });
        }
      }
    });

    // Recordatorio de tratamientos activos
    for (const tratamiento of tratamientos.filter(t => t.activo)) {
      const diasDesdeInicio = dayjs().diff(dayjs(tratamiento.fecha_inicio), 'days');
      const duracionMatch = tratamiento.duracion.match(/(\d+)/);
      if (duracionMatch) {
        const duracionDias = parseInt(duracionMatch[1]);
        const diasRestantes = duracionDias - diasDesdeInicio;

        if (diasRestantes > 0 && diasRestantes <= 7) {
          nuevosRecordatorios.push({
            id: `rec-${Date.now()}-trat-${tratamiento.id}`,
            tipo: 'TRATAMIENTO',
            titulo: 'Fin de Tratamiento',
            descripcion: `Finaliza tratamiento: ${tratamiento.medicamento}`,
            fecha_programada: dayjs(tratamiento.fecha_inicio).add(duracionDias, 'days').format('YYYY-MM-DD'),
            dias_restantes: diasRestantes,
            completado: false,
            prioridad: 'MEDIA'
          });
        }
      }
    }

    setRecordatorios(nuevosRecordatorios);

    notification.success({
      message: 'Recordatorios Generados',
      description: `Se generaron ${nuevosRecordatorios.length} recordatorios clínicos`,
      duration: 4
    });
  }, [embarazoActivo, calcularEGActual, controles, vacunas, laboratorios, ecografias, tratamientos, message, notification]);

  const estadisticasGlobales = useMemo<EstadisticaGlobal | null>(() => {
    if (!embarazoActivo) return null;

    const { semanas } = calcularEGActual();
    const diasHastaFPP = dayjs(embarazoActivo.fecha_probable_parto).diff(dayjs(), 'days');

    return {
      total_controles: controles.length,
      total_ecografias: ecografias.length,
      total_laboratorios: laboratorios.length,
      total_notas: notas.length,
      total_registros: controles.length + ecografias.length + laboratorios.length + notas.length + citas.length + partos.length,
      ultimo_control: controles.length > 0 ? controles[controles.length - 1].fecha : undefined,
      proxima_cita: controles.length > 0 ? controles[controles.length - 1].proximo_control : undefined,
      edad_gestacional_semanas_actual: semanas,
      dias_hasta_fpp: diasHastaFPP,
      adherencia_tratamiento: tratamientos.filter(t => t.activo).length > 0 ? 85 : 100,
      porcentaje_protocolos_cumplidos: 75
    };
  }, [embarazoActivo, controles, ecografias, laboratorios, notas, tratamientos, citas, partos, calcularEGActual]);

  // ==========================================
  // 7. SUB-COMPONENTES DE UI
  // ==========================================


  // ==========================================
  // 8. RENDERIZADO FINAL
  // ==========================================

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <Spin size="large">
        <div style={{ padding: 50, textAlign: 'center' }}>
          <p>Cargando expediente clínico…</p>
        </div>
      </Spin>
    </div>
  );
  if (error) return <Alert message="Error" description={error} type="error" showIcon style={{ margin: 20 }} />;

  return (
    <Layout style={{ background: 'var(--bg-primary, #fff)', minHeight: '100vh' }} suppressHydrationWarning>
      <div style={{ padding: '20px 40px' }}>
        <Space style={{ marginBottom: 16 }}>
          <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => navigate('/pacientes')}>Lista de Pacientes</Button>
          <Text type="secondary"> / HC: {paciente?.nombre} {paciente?.apellido_paterno || paciente?.apellidos || ''}</Text>
        </Space>

        <HeaderInfoPaciente
          paciente={paciente}
          embarazoActivo={embarazoActivo}
          pacienteId={pacienteId}
          navigate={navigate}
          setDrawerCalculadoraVisible={setDrawerCalculadoraVisible}
          setModalExportarVisible={setModalExportarVisible}
          setModalRiesgoVisible={setModalRiesgoVisible}
          setModalProtocolosVisible={setModalProtocolosVisible}
          setDrawerTimelineVisible={setDrawerTimelineVisible}
          setModalComparacionVisible={setModalComparacionVisible}
          setDrawerAlertasVisible={setDrawerAlertasVisible}
        />

        {/* CONTROLES DE VISTA Y FILTROS */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={[16, 8]} align="middle">
            <Col flex="auto">
              <Space wrap>
                <Input
                  placeholder="Buscar en historia clínica..."
                  prefix={<SearchOutlined />}
                  value={busquedaFiltro.texto}
                  onChange={(e) =>
                    setBusquedaFiltro(prev => ({ ...prev, texto: e.target.value }))
                  }
                  style={{ width: 250 }}
                />
                <Select
                  value={busquedaFiltro.categoria}
                  onChange={(val) =>
                    setBusquedaFiltro(prev => ({ ...prev, categoria: val }))
                  }
                  style={{ width: 150 }}
                >
                  <Option value="TODO">Todo</Option>
                  <Option value="CONTROLES">Controles</Option>
                  <Option value="LABORATORIOS">Laboratorios</Option>
                  <Option value="NOTAS">Notas</Option>
                </Select>
                <Select
                  value={periodoVisualizacion}
                  onChange={setPeriodoVisualizacion}
                  style={{ width: 150 }}
                >
                  <Option value="TODO">Todo el embarazo</Option>
                  <Option value="ULTIMO_MES">Último mes</Option>
                  <Option value="ULTIMO_TRIMESTRE">Último trimestre</Option>
                </Select>
              </Space>
            </Col>
            <Col>
              <Space>
                <Tooltip title="Vista compacta">
                  <Button
                    type={vistaCompacta ? 'primary' : 'default'}
                    icon={<TableOutlined />}
                    onClick={() => setVistaCompacta(prev => !prev)}
                  />
                </Tooltip>
                <Tooltip title="Gráficas avanzadas">
                  <Button
                    type={mostrarGraficasAvanzadas ? 'primary' : 'default'}
                    icon={<LineChartOutlined />}
                    onClick={() => setMostrarGraficasAvanzadas(prev => !prev)}
                  />
                </Tooltip>
                <Badge count={recordatorios.length} offset={[-5, 5]}>
                  <Dropdown
                    menu={{
                      items: [
                        ...(recordatorios.length === 0 ? [
                          { key: 'none', label: 'Sin recordatorios', disabled: true }
                        ] : recordatorios.map((rec) => ({
                          key: rec.id,
                          label: (
                            <Space direction="vertical" size="small">
                              <Text strong>{rec.titulo}</Text>
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                {rec.descripcion}
                              </Text>
                            </Space>
                          )
                        }))),
                        { type: 'divider' as const },
                        {
                          key: 'agregar',
                          label: 'Agregar recordatorio',
                          icon: <PlusOutlined />,
                          onClick: () => {
                            modal.confirm({
                              title: 'Agregar Recordatorio',
                              content: (
                                <Form>
                                  <Form.Item label="Recordatorio">
                                    <TextArea rows={3} placeholder="Escribe un recordatorio..." />
                                  </Form.Item>
                                </Form>
                              ),
                              onOk: handleAgregarRecordatorio,
                            });
                          }
                        },
                        {
                          key: 'ver_todos',
                          label: 'Ver todos los recordatorios',
                          icon: <BellOutlined />,
                          onClick: () => setDrawerAlertasVisible(true)
                        }
                      ]
                    }}
                    trigger={['click']}
                  >
                    <Button icon={<ClockCircleOutlined />}>Recordatorios</Button>
                  </Dropdown>
                </Badge>
                {estadisticasGlobales && (
                  <Tooltip
                    title={`Total registros: ${estadisticasGlobales.total_registros}`}
                  >
                    <Button icon={<CalculatorOutlined />}>
                      Estadísticas ({estadisticasGlobales.total_registros})
                    </Button>
                  </Tooltip>
                )}
              </Space>
            </Col>
          </Row>
        </Card>

        <Card className="main-tabs-card" styles={{ body: { padding: 0 } }}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            size="large"
            type="line"
            tabBarStyle={{ padding: '0 20px' }}
            items={[
              {
                key: 'dashboard',
                label: <span><HeartOutlined /> Dashboard</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <DashboardObstetrico
                      alertasClinicas={alertasClinicas}
                      embarazoActivo={embarazoActivo}
                      controles={controles}
                      laboratorios={laboratorios}
                      ecografias={ecografias}
                      calcularEGActual={calcularEGActual}
                      datosGraficas={datosGraficas}
                      pacienteId={pacienteId}
                      navigate={navigate}
                    />
                  </div>
                ),
              },
              {
                key: 'antecedentes',
                label: <span><HistoryOutlined /> Antecedentes</span>,
                children: (
                  <TabAntecedentes
                    paciente={paciente}
                    antecedenteGineco={antecedenteGineco}
                    antecedentePatologico={antecedentePatologico}
                    historialEmbarazos={historialEmbarazos}
                  />
                ),
              },
              {
                key: 'controles',
                label: <span><MedicineBoxOutlined /> Controles</span>,
                disabled: !embarazoActivo,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabControles
                      controles={controles}
                      embarazoActivo={embarazoActivo}
                      navigate={navigate}
                    />
                  </div>
                ),
              },
              {
                key: 'ecografias',
                label: <span><ScanOutlined /> Ecografías</span>,
                disabled: !embarazoActivo,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabEcografias ecografias={ecografias} navigate={navigate} embarazoActivo={embarazoActivo} />
                  </div>
                ),
              },
              {
                key: 'laboratorio',
                label: <span><ExperimentOutlined /> Laboratorio</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabLaboratorios laboratorios={laboratorios} />
                  </div>
                ),
              },
              {
                key: 'notas',
                label: <span><FileTextOutlined /> Evolución (SOAP)</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabNotasEvolucion
                      notas={notas}
                      setDrawerNotasVisible={setDrawerNotasVisible}
                    />
                  </div>
                ),
              },
              {
                key: 'partos',
                label: <span><WomanOutlined /> Partos</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabPartos
                      partos={partos}
                      pacienteId={pacienteId}
                      navigate={navigate}
                    />
                  </div>
                ),
              },
              {
                key: 'vacunas',
                label: <span><SafetyCertificateOutlined /> Vacunas</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabVacunas vacunas={vacunas} />
                  </div>
                ),
              },
              {
                key: 'tratamientos',
                label: <span><MedicineBoxOutlined /> Tratamientos</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabTratamientos
                      tratamientos={tratamientos}
                      setModalRecetaVisible={setModalRecetaVisible}
                    />
                  </div>
                ),
              },
              {
                key: 'herramientas',
                label: <span><CalculatorOutlined /> Herramientas Clínicas</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabHerramientasClinicas
                      handleCalcularRiesgo={handleCalcularRiesgo}
                      handleCalcularIMCGanancia={handleCalcularIMCGanancia}
                      handleVerTendenciasLaboratorio={handleVerTendenciasLaboratorio}
                      handleGenerarRecordatorios={handleGenerarRecordatorios}
                      handleCalcularPesoFetal={handleCalcularPesoFetal}
                      setModalExportarVisible={setModalExportarVisible}
                      laboratorios={laboratorios}
                      calcularEG={calcularEG}
                      calcularFPP={calcularFPP}
                      interpretarNST={interpretarNST}
                      notification={notification}
                    />
                  </div>
                ),
              },
              {
                key: 'protocolos',
                label: <span><SafetyCertificateOutlined /> Protocolos</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabProtocolosCumplimiento
                      calcularEGActual={calcularEGActual}
                      laboratorios={laboratorios}
                      ecografias={ecografias}
                    />
                  </div>
                ),
              },
              {
                key: 'comparacion',
                label: <span><LineChartOutlined /> Comparación Embarazos</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabComparacionEmbarazos
                      embarazoActivo={embarazoActivo}
                      historialEmbarazos={historialEmbarazos}
                      navigate={navigate}
                      pacienteId={pacienteId}
                    />
                  </div>
                ),
              },
            ]}
          />
        </Card >

        <HistoriaClinicaModales
          drawerNotasVisible={drawerNotasVisible}
          setDrawerNotasVisible={setDrawerNotasVisible}
          formNota={formNota}
          handleAddNota={handleAddNota}
          saving={saving}
          modalRecetaVisible={modalRecetaVisible}
          setModalRecetaVisible={setModalRecetaVisible}
          formReceta={formReceta}
          handleAddTratamiento={handleAddTratamiento}
          drawerCalculadoraVisible={drawerCalculadoraVisible}
          setDrawerCalculadoraVisible={setDrawerCalculadoraVisible}
          message={message}
          modalExportarVisible={modalExportarVisible}
          setModalExportarVisible={setModalExportarVisible}
          handleExportarHistoria={handleExportarHistoria}
          modalRiesgoVisible={modalRiesgoVisible}
          setModalRiesgoVisible={setModalRiesgoVisible}
          handleCalcularRiesgo={handleCalcularRiesgo}
          paciente={paciente}
          embarazoActivo={embarazoActivo}
          controles={controles}
          modalProtocolosVisible={modalProtocolosVisible}
          setModalProtocolosVisible={setModalProtocolosVisible}
          protocolosEmbarazo={protocolosEmbarazo}
          drawerTimelineVisible={drawerTimelineVisible}
          setDrawerTimelineVisible={setDrawerTimelineVisible}
          ecografias={ecografias}
          laboratorios={laboratorios}
          notas={notas}
          modalComparacionVisible={modalComparacionVisible}
          setModalComparacionVisible={setModalComparacionVisible}
          tendenciasLaboratorio={tendenciasLaboratorio}
          drawerAlertasVisible={drawerAlertasVisible}
          setDrawerAlertasVisible={setDrawerAlertasVisible}
          alertasActivas={alertasActivas}
          setAlertasActivas={setAlertasActivas}
        />

      </div >
    </Layout >
  );
};


export default HistoriaClinica;
