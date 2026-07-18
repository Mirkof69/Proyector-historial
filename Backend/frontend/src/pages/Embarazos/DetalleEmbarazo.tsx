/**
 * =============================================================================
 * MÓDULO: EMBARAZOS - DETALLE COMPLETO
 * =============================================================================
 * Muestra todos los detalles de un embarazo individual
 * Incluye progreso gestacional, controles y análisis médico
 * Con cálculos automáticos y visualizaciones mejoradas
 * =============================================================================
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Button,
  Spin,
  Space,
  Typography,
  Alert,
  Empty,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  WarningOutlined,
  PlusOutlined,
  SafetyOutlined,
  HistoryOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { embarazosService, Embarazo } from '../../services/embarazosService';
import { pacientesService, Paciente } from '../../services/pacientesService';
import { controlesService, ControlPrenatal } from '../../services/controlesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import { useAntdApp } from '../../hooks/useMessage';
import { descargarArchivo } from '../../utils/descargarArchivo';
import {
  calcularSemanasGestacion, calcularDiasRestantes, calcularProgreso,
  getTrimestre, calcularIMCClasificacion, getEstadoConfig, getRiesgoConfig,
} from './detalleEmbarazoUtils';
import DetalleEmbarazoStats from './components/DetalleEmbarazoStats';
import DetalleEmbarazoInfo from './components/DetalleEmbarazoInfo';
import DetalleEmbarazoTabs from './components/DetalleEmbarazoTabs';
import DetalleEmbarazoTimeline from './components/DetalleEmbarazoTimeline';
import RiesgoDetalladoModal from './components/RiesgoDetalladoModal';
import TimelineCompletoModal from './components/TimelineCompletoModal';

const { Text } = Typography;

const arrowLeftIcon = <ArrowLeftOutlined />;
const arrowLeftIcon2 = <ArrowLeftOutlined />;
const editIcon2 = <EditOutlined />;
const plusIcon2 = <PlusOutlined />;
const safetyIcon2 = <SafetyOutlined />;
const historyIcon2 = <HistoryOutlined />;
const warningIcon2 = <WarningOutlined />;

const DetalleEmbarazo: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const antdApp = useAntdApp();

  const [embarazo, setEmbarazo] = useState<Embarazo | null>(null);
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [controles, setControles] = useState<ControlPrenatal[]>([]);

  const loadingRef = useRef(true);
  const [loadingControles, setLoadingControles] = useState(false);
  const [modalRiesgoVisible, setModalRiesgoVisible] = useState(false);
  const [loadingRiesgo, setLoadingRiesgo] = useState(false);
  const [riesgoDetallado, setRiesgoDetallado] = useState<any>(null);
  const [modalTimelineVisible, setModalTimelineVisible] = useState(false);
  const [loadingTimeline, setLoadingTimeline] = useState(false);
  const [timelineData, setTimelineData] = useState<any>(null);

  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const fetchEmbarazo = async (embarazoId: number) => {
    loadingRef.current = true;
    try {
      const data = await embarazosService.getById(embarazoId);
      if (!isMounted.current) return;
      setEmbarazo(data);

      // Cargar datos de la paciente
      if (data.paciente) {
        // Extraer ID del paciente (puede ser número u objeto)
        const pacienteId = typeof data.paciente === 'number'
          ? data.paciente
          : data.paciente.id;

        const pacienteData = await pacientesService.getById(pacienteId);
        if (isMounted.current) setPaciente(pacienteData);
      }
    } catch (error) {
      if (isMounted.current) {
        antdApp.message.error('Error al cargar datos del embarazo');
      }
    } finally {
      if (isMounted.current) loadingRef.current = false;
    }
  };

  useEffect(() => {
    if (id) fetchEmbarazo(parseInt(id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const fetchControles = async (embarazoId: number) => {
    setLoadingControles(true);
    try {
      const controlesData = await controlesService.getByEmbarazo(embarazoId);
      if (isMounted.current) {
        setControles(Array.isArray(controlesData) ? controlesData : []);
      }
    } catch (error: any) {
      if (isMounted.current) {
        setControles([]);
      }
    } finally {
      if (isMounted.current) {
        setLoadingControles(false);
      }
    }
  };

  // âœ¨ NUEVA FUNCIÓN - Calcular riesgo detallado
  const handleCalcularRiesgo = async () => {
    if (!embarazo?.id) return;
    setModalRiesgoVisible(true);
    setLoadingRiesgo(true);
    try {
      const data = await embarazosService.calcularRiesgoDetallado(embarazo.id);
      if (isMounted.current) {
        setRiesgoDetallado(data);
        antdApp.message.success('Análisis de riesgo completado');
      }
    } catch (error) {
      if (isMounted.current) {
        antdApp.message.error('Error al calcular el riesgo detallado');
        setRiesgoDetallado(null);
      }
    } finally {
      if (isMounted.current) {
        setLoadingRiesgo(false);
      }
    }
  };

  // âœ¨ NUEVA FUNCIÓN - Ver timeline completo
  const handleVerTimeline = async () => {
    if (!embarazo?.id) return;
    setModalTimelineVisible(true);
    setLoadingTimeline(true);
    try {
      const data = await embarazosService.getTimelineCompleto(embarazo.id, {
        incluir_controles: true,
        incluir_ecografias: true,
        incluir_laboratorio: true,
        incluir_riesgos: true,
        incluir_complicaciones: true,
      });
      if (isMounted.current) {
        setTimelineData(data);
        antdApp.message.success('Timeline cargado correctamente');
      }
    } catch (error) {
      if (isMounted.current) {
        antdApp.message.error('Error al cargar el timeline completo');
        setTimelineData(null);
      }
    } finally {
      if (isMounted.current) {
        setLoadingTimeline(false);
      }
    }
  };

  // ========== HANDLERS ==========
  const handleBack = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.EMBARAZOS);
  };

  const handleEdit = () => {
    if (embarazo && embarazo.id) {
      navigate(FRONTEND_ROUTES.DASHBOARD.EMBARAZOS_EDITAR(embarazo.id));
    }
  };

  const handleNuevoControl = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.CONTROLES_NUEVO);
  };

  const handleVerControl = (controlId: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.CONTROLES_DETALLE(controlId));
  };

  if (loadingRef.current) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" tip="Cargando información del embarazo…"><div /></Spin>
      </div>
    );
  }

  if (!embarazo) {
    return (
      <div>
        <Button
          icon={arrowLeftIcon2}
          onClick={handleBack}
          style={{ marginBottom: 16 }}
        >
          Volver a la lista
        </Button>
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span>
                No se encontró el embarazo solicitado
                <br />
                <Text type="secondary">El embarazo no existe o ha sido eliminado</Text>
              </span>
            }
          >
            <Button type="primary" onClick={handleBack}>
              Volver a la lista
            </Button>
          </Empty>
        </Card>
      </div>
    );
  }

  // ========== CÁLCULOS ==========
  const eg = calcularSemanasGestacion(embarazo.fecha_ultima_menstruacion);
  const diasRestantes = calcularDiasRestantes(embarazo.fecha_probable_parto || new Date().toISOString());
  const progreso = calcularProgreso(embarazo.fecha_ultima_menstruacion);
  const trimestre = getTrimestre(eg.semanas);
  const estadoConfig = getEstadoConfig(embarazo.estado || 'activo');
  const riesgoConfig = getRiesgoConfig(embarazo.riesgo_embarazo || 'bajo');

  const nombrePaciente = paciente
    ? `${paciente.nombre} ${paciente.apellido_paterno} ${paciente.apellido_materno || ''}`.trim()
    : 'Cargando…';

  const formulaObstetrica = `G${embarazo.numero_gesta}P${embarazo.partos_previos || 0}C${embarazo.cesareas_previas || 0
    }A${embarazo.abortos_previos || 0}`;

  const imcClasificacion = embarazo.imc_pregestacional
    ? calcularIMCClasificacion(embarazo.imc_pregestacional)
    : null;

  // @ts-ignore
  const controlesConAlertas = controles.filter((c) => c.tiene_alertas).length;
  const ultimoControl = controles.length > 0 ? controles[controles.length - 1] : null;

  return (
    <div>
      {/* ========== HEADER CON ACCIONES ========== */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Button icon={arrowLeftIcon} onClick={handleBack}>
          Volver a la lista
        </Button>
        <Button type="primary" icon={editIcon2} onClick={handleEdit}>
          Editar Embarazo
        </Button>
        <Button type="default" icon={plusIcon2} onClick={handleNuevoControl}>
          Nuevo Control Prenatal
        </Button>
        <Button
          icon={safetyIcon2}
          onClick={handleCalcularRiesgo}
          style={{ borderColor: '#ff4d4f', color: '#ff4d4f' }}
        >
          Análisis de Riesgo Detallado
        </Button>
        <Button
          icon={historyIcon2}
          onClick={handleVerTimeline}
          style={{ borderColor: '#722ed1', color: '#722ed1' }}
        >
          Ver Timeline Completo
        </Button>
        <Button
          icon={<FilePdfOutlined />}
          onClick={() => descargarArchivo(`/embarazos/${id}/generar-pdf/`, `embarazo_${id}.pdf`)
            .then(() => antdApp.message.success('PDF descargado'))
            .catch(() => antdApp.message.error('No se pudo generar el PDF'))}
        >
          Descargar PDF
        </Button>
        <Button
          icon={<FileExcelOutlined />}
          onClick={() => descargarArchivo(`/embarazos/${id}/exportar-excel/`, `embarazo_${id}.xlsx`)
            .then(() => antdApp.message.success('Excel descargado'))
            .catch(() => antdApp.message.error('No se pudo generar el Excel'))}
        >
          Descargar Excel
        </Button>
        <Button
          icon={<FileTextOutlined />}
          onClick={() => descargarArchivo(`/embarazos/${id}/exportar-csv/`, `embarazo_${id}.csv`)
            .then(() => antdApp.message.success('CSV descargado'))
            .catch(() => antdApp.message.error('No se pudo generar el CSV'))}
        >
          Descargar CSV
        </Button>
      </Space>

      {/* ========== ALERTAS DE RIESGO ========== */}
      {embarazo.riesgo_embarazo === 'alto' && embarazo.estado === 'activo' && (
        <Alert
          message="Embarazo de Alto Riesgo"
          description="Este embarazo requiere seguimiento médico especializado y controles más frecuentes."
          type="error"
          showIcon
          icon={warningIcon2}
          style={{ marginBottom: 16 }}
        />
      )}

      {controlesConAlertas > 0 && (
        <Alert
          message={`Controles con Alertas: ${controlesConAlertas}`}
          description="Se han detectado alertas médicas en los controles prenatales. Revise el historial de controles."
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          closable
        />
      )}

      {/* ========== ESTADÍSTICAS RÁPIDAS ========== */}
      <DetalleEmbarazoStats
        eg={eg}
        diasRestantes={diasRestantes}
        progreso={progreso}
        trimestre={trimestre}
        embarazo={embarazo}
        controles={controles}
        controlesConAlertas={controlesConAlertas}
      />

      {/* ========== INFORMACIÓN PRINCIPAL ========== */}
      <DetalleEmbarazoInfo
        embarazo={embarazo}
        paciente={paciente}
        nombrePaciente={nombrePaciente}
        estadoConfig={estadoConfig}
        riesgoConfig={riesgoConfig}
        formulaObstetrica={formulaObstetrica}
        eg={eg}
        trimestre={trimestre}
        diasRestantes={diasRestantes}
        progreso={progreso}
        imcClasificacion={imcClasificacion}
      />

      {/* ========== TABS CON INFORMACIÓN ADICIONAL ========== */}
      <DetalleEmbarazoTabs
        controles={controles}
        loadingControles={loadingControles}
        ultimoControl={ultimoControl}
        handleVerControl={handleVerControl}
        handleNuevoControl={handleNuevoControl}
      />

      {/* ========== LÍNEA DE TIEMPO ========== */}
      <DetalleEmbarazoTimeline
        embarazo={embarazo}
        eg={eg}
        trimestre={trimestre}
        diasRestantes={diasRestantes}
        controles={controles}
        ultimoControl={ultimoControl}
      />

      {/* NUEVO MODAL - Análisis de Riesgo Detallado */}
      <RiesgoDetalladoModal
        open={modalRiesgoVisible}
        loadingRiesgo={loadingRiesgo}
        riesgoDetallado={riesgoDetallado}
        onClose={() => {
          setModalRiesgoVisible(false);
          setRiesgoDetallado(null);
        }}
      />

      {/* NUEVO MODAL - Timeline Completo */}
      <TimelineCompletoModal
        open={modalTimelineVisible}
        loadingTimeline={loadingTimeline}
        timelineData={timelineData}
        onClose={() => {
          setModalTimelineVisible(false);
          setTimelineData(null);
        }}
      />
    </div>
  );
};

export default DetalleEmbarazo;
