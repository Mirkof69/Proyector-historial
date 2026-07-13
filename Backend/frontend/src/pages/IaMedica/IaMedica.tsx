import React, { useReducer, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import {Upload, Button, Tag, Modal, Spin, Typography,
  Row, Col, Empty, Tooltip, Alert, Progress, Table, Descriptions,
  Divider, Badge, Select, Space} from "antd";
import {
  InboxOutlined, RobotOutlined, FundProjectionScreenOutlined,
  CheckCircleOutlined, WarningOutlined, CloseCircleOutlined,
  DownloadOutlined, ReloadOutlined, FileImageOutlined,
  DashboardOutlined, EyeOutlined, DeleteOutlined, ExperimentOutlined,
  HeartOutlined, AlertOutlined, LinkOutlined, NodeIndexOutlined,
  InfoCircleOutlined, FileTextOutlined, ExclamationCircleOutlined
} from '@ant-design/icons';
import {
  iaMedicaService,
  ImagenEcografica,
  AnalisisCNN,
  AnalisisCNNCompleto,
  ReporteNarrativoIA,
  EstadisticasIA,
  Pathology,
  ShapRiskScores,
  BiometryResult
} from '../../services/iaMedicaService';
import pacientesService from '../../services/pacientesService';
import { API_URL } from '../../services/api';
import './IaMedica.css';

const { Title } = Typography;
const { Dragger } = Upload;

// ── Tabla de percentiles normales de biometría fetal (referencia OMS) ─────────
const BIOMETRY_REFERENCE: Record<keyof BiometryResult, { label: string; unit: string; min: number; max: number }> = {
  BPD_mm:          { label: 'Diámetro Biparietal (BPD)', unit: 'mm',  min: 45,   max: 95  },
  HC_mm:           { label: 'Circunferencia Cefálica (HC)', unit: 'mm', min: 170, max: 360 },
  AC_mm:           { label: 'Circunferencia Abdominal (AC)', unit: 'mm', min: 150, max: 350 },
  FL_mm:           { label: 'Longitud Femoral (FL)', unit: 'mm',  min: 30,   max: 80  },
  peso_estimado_g: { label: 'Peso Estimado', unit: 'g',   min: 500,  max: 4000 },
};

const SHAP_RISK_LABELS: Record<string, string> = {
  riesgo_preeclampsia:        'Riesgo de Preeclampsia',
  riesgo_parto_prematuro:     'Riesgo de Parto Prematuro',
  riesgo_hemorragia:          'Riesgo de Hemorragia',
  riesgo_diabetes_gestacional:'Riesgo de Diabetes Gestacional',
  riesgo_mortalidad_perinatal:'Riesgo de Mortalidad Perinatal',
  riesgo_global:              'Score de Riesgo Global',
};

interface GradCamOverlayProps {
  ai: AnalisisCNNCompleto;
  originalUrl: string;
}

const GradCamOverlay: React.FC<GradCamOverlayProps> = ({ ai, originalUrl }) => {
  const { message } = useAntdApp();
  if (!ai.gradcam_base64) return null;
  return (
    <div style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
      <img
        src={originalUrl}
        alt="Ecografía original"
        style={{ width: '100%', display: 'block', borderRadius: 4 }}
      />
      <img
        src={`data:image/png;base64,${ai.gradcam_base64}`}
        alt="Grad-CAM overlay"
        style={{
          position: 'absolute',
          top: 0, left: 0,
          width: '100%',
          opacity: 0.55,
          mixBlendMode: 'multiply',
          borderRadius: 4,
        }}
      />
      <div className="gradcam-badge">
        Grad-CAM: {ai.modelo_version || 'EfficientNet-B4'}
      </div>
    </div>
  );
};

interface IaMedicaState {
  imagenes: ImagenEcografica[];
  estadisticas: EstadisticasIA | null;
  loading: boolean;
  uploading: boolean;
  analyzingId: number | null;
  isModalVisible: boolean;
  selectedAnalysis: {imagen?: ImagenEcografica, analisis: AnalisisCNN} | null;
  isCnnModalVisible: boolean;
  cnnAnalysis: AnalisisCNNCompleto | null;
  cnnImageUrl: string;
  cnnImageId: number | null;
  analyzingCnnId: number | null;
  narrativeReport: ReporteNarrativoIA | null;
  loadingNarrative: boolean;
}

type IaMedicaAction =
  | { type: 'SET_IMAGENES'; payload: ImagenEcografica[] }
  | { type: 'SET_ESTADISTICAS'; payload: EstadisticasIA | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_UPLOADING'; payload: boolean }
  | { type: 'SET_ANALYZING_ID'; payload: number | null }
  | { type: 'SET_IS_MODAL_VISIBLE'; payload: boolean }
  | { type: 'SET_SELECTED_ANALYSIS'; payload: {imagen?: ImagenEcografica, analisis: AnalisisCNN} | null }
  | { type: 'SET_IS_CNN_MODAL_VISIBLE'; payload: boolean }
  | { type: 'SET_CNN_ANALYSIS'; payload: AnalisisCNNCompleto | null }
  | { type: 'SET_CNN_IMAGE_URL'; payload: string }
  | { type: 'SET_CNN_IMAGE_ID'; payload: number | null }
  | { type: 'SET_ANALYZING_CNN_ID'; payload: number | null }
  | { type: 'SET_NARRATIVE_REPORT'; payload: ReporteNarrativoIA | null }
  | { type: 'SET_LOADING_NARRATIVE'; payload: boolean };

const initialState: IaMedicaState = {
  imagenes: [],
  estadisticas: null,
  loading: true,
  uploading: false,
  analyzingId: null,
  isModalVisible: false,
  selectedAnalysis: null,
  isCnnModalVisible: false,
  cnnAnalysis: null,
  cnnImageUrl: '',
  cnnImageId: null,
  analyzingCnnId: null,
  narrativeReport: null,
  loadingNarrative: false,
};

function reducer(state: IaMedicaState, action: IaMedicaAction): IaMedicaState {
  switch (action.type) {
    case 'SET_IMAGENES':
      return { ...state, imagenes: action.payload };
    case 'SET_ESTADISTICAS':
      return { ...state, estadisticas: action.payload };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_UPLOADING':
      return { ...state, uploading: action.payload };
    case 'SET_ANALYZING_ID':
      return { ...state, analyzingId: action.payload };
    case 'SET_IS_MODAL_VISIBLE':
      return { ...state, isModalVisible: action.payload };
    case 'SET_SELECTED_ANALYSIS':
      return { ...state, selectedAnalysis: action.payload };
    case 'SET_IS_CNN_MODAL_VISIBLE':
      return { ...state, isCnnModalVisible: action.payload };
    case 'SET_CNN_ANALYSIS':
      return { ...state, cnnAnalysis: action.payload };
    case 'SET_CNN_IMAGE_URL':
      return { ...state, cnnImageUrl: action.payload };
    case 'SET_CNN_IMAGE_ID':
      return { ...state, cnnImageId: action.payload };
    case 'SET_ANALYZING_CNN_ID':
      return { ...state, analyzingCnnId: action.payload };
    case 'SET_NARRATIVE_REPORT':
      return { ...state, narrativeReport: action.payload };
    case 'SET_LOADING_NARRATIVE':
      return { ...state, loadingNarrative: action.payload };
    default:
      return state;
  }
}

// ── Helpers puros de presentación (nivel de módulo: identidad estable) ───────
const safeProb = (p: number | undefined | null) => Math.max(0, Math.min(1, p ?? 0));

const renderShapRiskBars = (shap: ShapRiskScores) => {
  const entries = Object.entries(shap).filter(([k]) => k in SHAP_RISK_LABELS);
  return (
    <div>
      <Divider orientation="left" style={{ fontSize: 13 }}>
        <ExperimentOutlined /> SHAP: Scores de Riesgo Materno
      </Divider>
      {entries.map(([key, value]) => {
        const pct = Math.min(Math.round(value * 100), 100);
        const status = pct >= 70 ? 'exception' : pct >= 40 ? 'normal' : 'success';
        const color = pct >= 70 ? '#ff4d4f' : pct >= 40 ? '#faad14' : '#52c41a';
        return (
          <div key={key} style={{ marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
              <span>{SHAP_RISK_LABELS[key] || key}</span>
              <Badge
                color={color}
                text={<span style={{ color, fontWeight: 600 }}>{pct}%</span>}
              />
            </div>
            <Progress
              percent={pct}
              status={status as any}
              strokeColor={color}
              size="small"
              showInfo={false}
            />
          </div>
        );
      })}
    </div>
  );
};

const renderResultBadge = (resultado: string) => {
  switch (resultado) {
    case 'normal':
      return <Tag color="success" icon={<CheckCircleOutlined />}>Normal</Tag>;
    case 'anomalia_leve':
    case 'anomalia_moderada':
      return <Tag color="warning" icon={<WarningOutlined />}>Anomalía</Tag>;
    case 'anomalia_grave':
    case 'requiere_revision':
      return <Tag color="error" icon={<CloseCircleOutlined />}>Crítico</Tag>;
    default:
      return <Tag color="default">Indeterminado</Tag>;
  }
};

const getResultIcon = (resultado: string) => {
  if (resultado === 'normal') return <CheckCircleOutlined className="result-icon" />;
  if (['anomalia_grave', 'requiere_revision'].includes(resultado)) return <CloseCircleOutlined className="result-icon" />;
  return <WarningOutlined className="result-icon" />;
};

const getResultClass = (resultado: string) => {
  if (resultado === 'normal') return 'normal';
  if (['anomalia_grave', 'requiere_revision'].includes(resultado)) return 'danger';
  return 'warning';
};

const IaMedica: React.FC = () => {
  const { message } = useAntdApp();
  const [state, dispatch] = useReducer(reducer, initialState);
  const [selectedPacienteId, setSelectedPacienteId] = React.useState<number | null>(null);
  const [pacientesSearch, setPacientesSearch] = React.useState<{id: number; nombre: string}[]>([]);
  const [searchingPaciente, setSearchingPaciente] = React.useState(false);
  const [vincularModalVisible, setVincularModalVisible] = React.useState(false);
  const [imagenAVincular, setImagenAVincular] = React.useState<ImagenEcografica | null>(null);
  const [vinculando, setVinculando] = React.useState(false);
  const [ecografiasVinculadas, setEcografiasVinculadas] = React.useState<Record<number, number>>({});

  const fetchData = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const [imgsData, statsData] = await Promise.all([
        iaMedicaService.getImagenes(),
        iaMedicaService.getEstadisticas()
      ]);
      dispatch({ type: 'SET_IMAGENES', payload: imgsData.results || imgsData });
      dispatch({ type: 'SET_ESTADISTICAS', payload: statsData });
    } catch (error) {
      message.error('Error al cargar datos del módulo IA');
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handlePatientSearch = async (query: string) => {
    if (!query || query.length < 2) return;
    setSearchingPaciente(true);
    try {
      const results = await pacientesService.listar();
      const q = query.toLowerCase();
      const filtered = results.filter((p: any) =>
        `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`.toLowerCase().includes(q)
      );
      setPacientesSearch(filtered.map((p: any) => ({
        id: p.id,
        nombre: p.nombre_completo || `${p.nombre} ${p.apellido_paterno}`.trim()
      })));
    } catch { /* silent */ }
    finally { setSearchingPaciente(false); }
  };

  const handleUpload = async (file: File) => {
    if (!selectedPacienteId) {
      message.warning('Seleccione un paciente antes de subir la imagen');
      return false;
    }
    dispatch({ type: 'SET_UPLOADING', payload: true });
    try {
      const formData = new FormData();
      formData.append('imagen', file);
      formData.append('paciente', String(selectedPacienteId));
      formData.append('tipo_imagen', 'eco_2d');

      await iaMedicaService.uploadImagen(formData);
      message.success('Imagen subida correctamente');
      fetchData();
    } catch (error: any) {
      message.error(`Error al subir la imagen: ${error?.response?.data ? JSON.stringify(error.response.data) : error.message}`);
    } finally {
      dispatch({ type: 'SET_UPLOADING', payload: false });
    }
    return false; // Prevenir upload default de antd
  };

  const handleAnalyze = async (id: number) => {
    dispatch({ type: 'SET_ANALYZING_ID', payload: id });
    try {
      const result = await iaMedicaService.analizarImagen(id, 'efficientnet');
      const imagenDetalle = await iaMedicaService.getImagenDetalle(id);
      message.success('Análisis completado');
      dispatch({ type: 'SET_SELECTED_ANALYSIS', payload: { analisis: result, imagen: imagenDetalle } });
      dispatch({ type: 'SET_IS_MODAL_VISIBLE', payload: true });
      fetchData();
    } catch (error) {
      message.error('Error durante el análisis CNN');
    } finally {
      dispatch({ type: 'SET_ANALYZING_ID', payload: null });
    }
  };

  const showAnalysis = async (id: number) => {
    try {
      const result = await iaMedicaService.getResultadoAnalisis(id);
      const imagenDetalle = await iaMedicaService.getImagenDetalle(id);
      dispatch({ type: 'SET_SELECTED_ANALYSIS', payload: { ...result, imagen: imagenDetalle } });
      dispatch({ type: 'SET_IS_MODAL_VISIBLE', payload: true });
    } catch (error) {
      message.error('No se pudo cargar el análisis');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await iaMedicaService.deleteImagen(id);
      message.success('Imagen eliminada');
      fetchData();
    } catch (error) {
      message.error('Error al eliminar imagen');
    }
  };

  const handleExport = async () => {
    try {
      await iaMedicaService.exportarDataset();
      message.success('Dataset exportado correctamente');
    } catch (error) {
      message.error('Error al exportar dataset');
    }
  };

  const handleVincularClick = (img: ImagenEcografica) => {
    setImagenAVincular(img);
    setVincularModalVisible(true);
  };

  const handleVincularConfirm = async () => {
    if (!imagenAVincular) return;
    setVinculando(true);
    try {
      const result = await iaMedicaService.vincularAEcografia(
        imagenAVincular.id,
        imagenAVincular.paciente,
      );
      if (result.ecografia_id) {
        setEcografiasVinculadas(prev => ({
          ...prev,
          [imagenAVincular.id]: result.ecografia_id,
        }));
        message.success(`Ecografía #${result.ecografia_id} creada con análisis IA`);
      } else {
        message.success('Vinculado correctamente');
      }
      setVincularModalVisible(false);
      setImagenAVincular(null);
    } catch (error: any) {
      message.error(`Error al vincular: ${error?.response?.data?.error || error.message}`);
    } finally {
      setVinculando(false);
    }
  };

  const handleVincularPacienteSearch = async (query: string) => {
    if (!query || query.length < 2) return;
    try {
      const results = await pacientesService.listar();
      const q = query.toLowerCase();
      const filtered = results.filter((p: any) =>
        `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`.toLowerCase().includes(q)
      );
      setPacientesSearch(filtered.map((p: any) => ({
        id: p.id,
        nombre: p.nombre_completo || `${p.nombre} ${p.apellido_paterno}`.trim()
      })));
    } catch { /* silent */ }
  };

  // Análisis completo EfficientNet-B4 con Grad-CAM + SHAP + biometría
  const handleAnalyzeCNN = async (img: ImagenEcografica) => {
    dispatch({ type: 'SET_ANALYZING_CNN_ID', payload: img.id });
    try {
      const imageUrl = `${API_URL.replace('/api', '')}${img.url_imagen}`;
      const response = await iaMedicaService.analyzeWithAI(undefined, String(img.id));
      dispatch({ type: 'SET_CNN_ANALYSIS', payload: response.ai_analysis });
      dispatch({ type: 'SET_CNN_IMAGE_URL', payload: imageUrl });
      dispatch({ type: 'SET_CNN_IMAGE_ID', payload: img.id });
      dispatch({ type: 'SET_NARRATIVE_REPORT', payload: null });
      dispatch({ type: 'SET_IS_CNN_MODAL_VISIBLE', payload: true });
      message.success('Análisis EfficientNet-B4 completado');
      fetchData();
    } catch (error: any) {
      message.error(`Error en análisis CNN: ${error?.message || 'Error desconocido'}`);
    } finally {
      dispatch({ type: 'SET_ANALYZING_CNN_ID', payload: null });
    }
  };

  // Reporte narrativo de IA local (LLM con visión, Ollama) — siempre
  // grounded en el resultado real del CNN que ya se muestra arriba; nunca
  // se llama sin haber corrido antes el analisis CNN sobre esta imagen.
  const handleGenerarReporteNarrativo = async () => {
    if (!state.cnnImageId) {
      message.error('Primero debe completarse el análisis CNN de esta imagen.');
      return;
    }
    dispatch({ type: 'SET_LOADING_NARRATIVE', payload: true });
    try {
      const reporte = await iaMedicaService.generarReporteNarrativo(state.cnnImageId);
      dispatch({ type: 'SET_NARRATIVE_REPORT', payload: reporte });
      if (reporte._error_llm) {
        message.warning('El reporte narrativo se generó parcialmente: ' + reporte._error_llm);
      } else {
        message.success('Reporte narrativo generado');
      }
    } catch (error: any) {
      message.error(`Error generando el reporte narrativo: ${error?.message || 'Error desconocido'}`);
    } finally {
      dispatch({ type: 'SET_LOADING_NARRATIVE', payload: false });
    }
  };

  // Reporte narrativo de IA local (LLM con visión, Ollama). Los campos
  // diagnosticos (clasificacion_clinica, tipo_embarazo, patologias_detectadas,
  // biometria) vienen siempre del backend ya groundeados en el CNN — esta
  // funcion solo los muestra, nunca los recalcula. La seccion
  // "hallazgos_visuales_complementarios" se muestra aparte, con badge "no
  // validado", para no confundirla con el diagnostico confirmado.
  const renderNarrativeReport = (reporte: ReporteNarrativoIA) => {
    const colorClasificacion = (v: string) => {
      const l = v.toLowerCase();
      if (l.includes('normal')) return 'success';
      if (l.includes('patolog')) return 'error';
      if (l.includes('seguim') || l.includes('no concluy')) return 'warning';
      return 'default';
    };
    const colorRiesgo = (v: string) => {
      const l = v.toLowerCase();
      if (l.includes('bajo')) return 'success';
      if (l.includes('alto')) return 'error';
      if (l.includes('moderado')) return 'warning';
      return 'default';
    };
    return (
      <div style={{ marginTop: 24, borderTop: '1px solid var(--ia-border)', paddingTop: 20 }}>
        <Divider orientation="left">
          <FileTextOutlined style={{ color: '#722ed1', marginRight: 8 }} />
          Reporte narrativo
        </Divider>

        {reporte._error_llm && (
          <Alert
            type="warning"
            icon={<ExclamationCircleOutlined />}
            showIcon
            message="El componente narrativo tuvo un problema; el diagnóstico mostrado abajo sigue siendo el del CNN, ya verificado"
            description={reporte._error_llm}
            style={{ marginBottom: 16 }}
          />
        )}

        <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Tag color={colorClasificacion(reporte.clasificacion_clinica)} style={{ fontSize: 13, padding: '4px 10px' }}>{reporte.clasificacion_clinica}</Tag>
          </Col>
          <Col span={6}><Typography.Text type="secondary">Tipo de embarazo:</Typography.Text> <strong>{reporte.tipo_embarazo}</strong></Col>
          <Col span={6}><Typography.Text type="secondary">Trimestre:</Typography.Text> <strong>{reporte.trimestre}</strong></Col>
          <Col span={6}><Tag color={colorRiesgo(reporte.clasificacion_riesgo)}>{reporte.clasificacion_riesgo}</Tag></Col>
        </Row>

        <Descriptions size="small" column={2} bordered style={{ marginBottom: 16 }}>
          <Descriptions.Item label="Edad gestacional">{reporte.edad_gestacional}</Descriptions.Item>
          <Descriptions.Item label="Tipo de imagen">{reporte.tipo_imagen}</Descriptions.Item>
          <Descriptions.Item label="Diagnóstico presuntivo" span={2}>{reporte.diagnostico_presuntivo}</Descriptions.Item>
        </Descriptions>

        <Typography.Paragraph style={{ fontSize: 13 }}>
          <strong>Descripción ecográfica: </strong>{reporte.descripcion_ecografia}
        </Typography.Paragraph>

        {reporte.patologias_detectadas.length > 0 && (
          <div style={{ marginBottom: 14 }}>
            <Typography.Text strong>Patologías detectadas (confirmadas por el CNN):</Typography.Text>
            {reporte.patologias_detectadas.map((p) => (
              <div key={p}><Tag color="error">{p}</Tag></div>
            ))}
          </div>
        )}

        {reporte.hallazgos.length > 0 && (
          <div style={{ marginBottom: 14 }}>
            <Typography.Text strong>Hallazgos:</Typography.Text>
            <ul style={{ marginTop: 4 }}>{reporte.hallazgos.map((h) => <li key={h} style={{ fontSize: 13 }}>{h}</li>)}</ul>
          </div>
        )}

        <Row gutter={16} style={{ marginBottom: 14 }}>
          {reporte.signos_normales.length > 0 && (
            <Col span={12}>
              <Typography.Text strong style={{ color: 'var(--ia-success)' }}>Signos normales:</Typography.Text>
              <ul style={{ marginTop: 4 }}>{reporte.signos_normales.map((s) => <li key={s} style={{ fontSize: 13 }}>{s}</li>)}</ul>
            </Col>
          )}
          {reporte.signos_alarma.length > 0 && (
            <Col span={12}>
              <Typography.Text strong style={{ color: 'var(--ia-warning)' }}>Signos de alarma:</Typography.Text>
              <ul style={{ marginTop: 4 }}>{reporte.signos_alarma.map((s) => <li key={s} style={{ fontSize: 13 }}>{s}</li>)}</ul>
            </Col>
          )}
        </Row>

        {reporte.hallazgos_visuales_complementarios.length > 0 && (
          <Alert
            type="info"
            icon={<InfoCircleOutlined />}
            showIcon
            message={<span>Impresión visual complementaria <Tag color="purple">no validada clínicamente</Tag></span>}
            description={
              <div>
                <p style={{ fontSize: 12, marginBottom: 6 }}>
                  El LLM local observó algo adicional fuera de las patologías que el CNN confirma. No es un diagnóstico, requiere confirmación.
                </p>
                <ul style={{ margin: 0 }}>{reporte.hallazgos_visuales_complementarios.map((h) => <li key={h} style={{ fontSize: 12 }}>{h}</li>)}</ul>
              </div>
            }
            style={{ marginBottom: 14 }}
          />
        )}

        <Descriptions title="Biometría (según CNN)" size="small" column={2} bordered style={{ marginBottom: 14 }}>
          <Descriptions.Item label="DBP">{reporte.biometria.DBP || 'No disponible'}</Descriptions.Item>
          <Descriptions.Item label="CC">{reporte.biometria.CC || 'No disponible'}</Descriptions.Item>
          <Descriptions.Item label="CA">{reporte.biometria.CA || 'No disponible'}</Descriptions.Item>
          <Descriptions.Item label="LF">{reporte.biometria.LF || 'No disponible'}</Descriptions.Item>
          <Descriptions.Item label="Líquido amniótico">{reporte.biometria.LA}</Descriptions.Item>
          <Descriptions.Item label="Peso estimado">{reporte.biometria.peso_estimado || 'No disponible'}</Descriptions.Item>
        </Descriptions>

        <Descriptions size="small" column={2} bordered style={{ marginBottom: 14 }}>
          <Descriptions.Item label="Pronóstico" span={2}>{reporte.pronostico}</Descriptions.Item>
          <Descriptions.Item label="Tipo de seguimiento" span={2}>{reporte.tipo_seguimiento}</Descriptions.Item>
        </Descriptions>

        {reporte.recomendaciones.length > 0 && (
          <div style={{ marginBottom: 14 }}>
            <Typography.Text strong style={{ color: 'var(--ia-success)' }}>Recomendaciones:</Typography.Text>
            <ol style={{ marginTop: 4 }}>{reporte.recomendaciones.map((r) => <li key={r} style={{ fontSize: 13 }}>{r}</li>)}</ol>
          </div>
        )}

        {reporte.nota_tecnica && (
          <Alert type="info" message="Nota técnica" description={reporte.nota_tecnica} style={{ marginBottom: 14 }} />
        )}

        <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 8 }}>
          Aviso médico-legal: este reporte narrativo es generado por IA (CNN verificado + LLM local de apoyo redaccional) con fines de apoyo diagnóstico.
          No reemplaza el criterio clínico del médico especialista. El diagnóstico definitivo y las decisiones terapéuticas son responsabilidad exclusiva del profesional tratante.
        </Typography.Paragraph>
      </div>
    );
  };

  const renderBiometryTable = (biometry: AnalisisCNNCompleto['biometry']) => {
    if (!biometry) return null;

    if (biometry.disponible === false) {
      return (
        <>
          <Divider orientation="left" style={{ fontSize: 13 }}>
            <DashboardOutlined /> Biometría Fetal
          </Divider>
          <Alert
            type="info"
            showIcon
            message="Biometría no disponible"
            description={biometry.motivo || 'El módulo de biometría fetal aún no está entrenado con datos reales.'}
          />
        </>
      );
    }

    const dataSource = (Object.keys(BIOMETRY_REFERENCE) as Array<keyof BiometryResult>)
      .filter(k => biometry[k] !== undefined && biometry[k] !== null)
      .map(k => {
        const ref = BIOMETRY_REFERENCE[k];
        const val = biometry[k] as number;
        const inRange = val >= ref.min && val <= ref.max;
        return {
          key: k,
          medida: ref.label,
          valor: `${val.toFixed(1)} ${ref.unit}`,
          rango: `${ref.min}–${ref.max} ${ref.unit}`,
          estado: inRange
            ? <Tag color="success">Normal</Tag>
            : <Tag color="error">Fuera de rango</Tag>,
        };
      });

    if (dataSource.length === 0) return null;

    const columns = [
      { title: 'Medida', dataIndex: 'medida', key: 'medida', width: '40%' },
      { title: 'Valor', dataIndex: 'valor', key: 'valor', width: '20%', align: 'right' as const },
      { title: 'Rango Normal', dataIndex: 'rango', key: 'rango', width: '25%' },
      { title: 'Estado', dataIndex: 'estado', key: 'estado', width: '15%' },
    ];

    return (
      <>
        <Divider orientation="left" style={{ fontSize: 13 }}>
          <DashboardOutlined /> Biometría Fetal
        </Divider>
        {biometry.metodo === 'estimacion_sintetica_no_validada' && (
          <div style={{ fontSize: 11, color: 'var(--ia-text-tertiary)', marginBottom: 6 }}>
            <InfoCircleOutlined style={{ marginRight: 4 }} />
            Estimación orientativa, no reemplaza una medición real.
          </div>
        )}
        <Table
          dataSource={dataSource}
          columns={columns}
          size="small"
          pagination={false}
          bordered
        />
        {biometry.alerts && biometry.alerts.length > 0 && (
          <Alert
            type="warning"
            style={{ marginTop: 8 }}
            message="Alertas de biometría"
            description={
              <ul style={{ margin: 0, paddingLeft: 16 }}>
                {biometry.alerts.map((a: string) => <li key={`alert-${a}`}>{a}</li>)}
              </ul>
            }
          />
        )}
      </>
    );
  };

const renderPathologyAlert = (pathologies: Pathology[]) => {
    const detected = pathologies.filter(p => safeProb(p.confidence) >= 0.50 && p.pathology !== 'normal' && p.pathology !== 'baja_confianza');
    if (detected.length === 0) return null;

    const hasCritical = detected.some(p => safeProb(p.confidence) >= 0.80);
    return (
      <Alert
        type={hasCritical ? 'error' : 'warning'}
        icon={<AlertOutlined />}
        showIcon
        style={{ marginBottom: 12 }}
        message={
          hasCritical
            ? 'ALERTA MEDICA: Patologías de alto riesgo detectadas'
            : 'Patologías detectadas, requieren evaluación médica'
        }
        description={
          <div>
            {detected.map(p => (
              <div key={p.pathology} style={{ marginBottom: 4 }}>
                <Tag color={safeProb(p.confidence) >= 0.80 ? 'red' : 'orange'}>
                  {p.pathology.replace(/_/g, ' ').toUpperCase()}
                </Tag>
                <span style={{ fontSize: 12 }}>
                  Probabilidad: {(safeProb(p.confidence) * 100).toFixed(1)}%
                  {p.icd10 && <> &nbsp;|&nbsp; ICD-10: <strong>{p.icd10}</strong></>}
                </span>
              </div>
            ))}
            <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
              La IA es herramienta de apoyo. El medico tiene responsabilidad legal del diagnostico (Ley 3131 Bolivia).
            </div>
          </div>
        }
      />
    );
  };

  return (
    <div className="ia-medica-container page-container">
      <div className="ia-medica-header">
        <h1><RobotOutlined /> IA Médica: Análisis de Imágenes CNN</h1>
        <div>
          <Button icon={<ReloadOutlined />} onClick={fetchData} style={{ marginRight: 8 }}>
            Actualizar
          </Button>
          <Button type="primary" icon={<DownloadOutlined />} onClick={handleExport}>
            Exportar Dataset
          </Button>
        </div>
      </div>

      {state.estadisticas && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon primary"><FileImageOutlined /></div>
            <div className="stat-content">
              <h3>Total Imágenes</h3>
              <p>{state.estadisticas.total_imagenes}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon primary"><FundProjectionScreenOutlined /></div>
            <div className="stat-content">
              <h3>Análisis CNN Realizados</h3>
              <p>{state.estadisticas.total_analisis}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon success"><CheckCircleOutlined /></div>
            <div className="stat-content">
              <h3>Casos Normales</h3>
              <p>{state.estadisticas.analisis_normales}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon warning"><WarningOutlined /></div>
            <div className="stat-content">
              <h3>Anomalías Detectadas</h3>
              <p>{state.estadisticas.analisis_anomalias}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon primary"><DashboardOutlined /></div>
            <div className="stat-content">
              <h3>Confianza Promedio</h3>
              <p>{state.estadisticas.confianza_promedio}%</p>
            </div>
          </div>
        </div>
      )}

      <div className="gallery-container">
        <div className="gallery-toolbar">
          <Title level={4} style={{ margin: 0 }}>Galería de Ecografías</Title>
        </div>

        <Row gutter={[24, 24]}>
          <Col xs={24} md={8} lg={6}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Select
                showSearch
                placeholder="Buscar y seleccionar paciente..."
                value={selectedPacienteId}
                onChange={setSelectedPacienteId}
                onSearch={handlePatientSearch}
                loading={searchingPaciente}
                filterOption={false}
                notFoundContent={searchingPaciente ? <Spin size="small" /> : 'Escriba al menos 2 caracteres'}
                style={{ width: '100%' }}
                allowClear
              >
                {pacientesSearch.map(p => (
                  <Select.Option key={p.id} value={p.id}>{p.nombre}</Select.Option>
                ))}
              </Select>
              <Dragger
                customRequest={({ file }) => handleUpload(file as File)}
                showUploadList={false}
                style={{ height: '100%', minHeight: '250px' }}
                disabled={!selectedPacienteId}
              >
                {state.uploading ? (
                  <div><Spin size="large" /><p style={{ marginTop: 16 }}>Subiendo…</p></div>
                ) : (
                  <div>
                    <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                    <p className="ant-upload-text">{selectedPacienteId ? 'Clic o arrastrar imagen aquí' : 'Seleccione un paciente primero'}</p>
                    <p className="ant-upload-hint">Soporta JPG, PNG, DICOM (Max: 10MB)</p>
                  </div>
                )}
              </Dragger>
            </Space>
          </Col>

          {state.loading ? (
            <Col span={16} style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
            </Col>
          ) : state.imagenes.length === 0 ? (
            <Col span={16}>
              <Empty description="No hay imágenes subidas aún" />
            </Col>
          ) : (
            state.imagenes.map(img => (
              <Col xs={24} sm={12} md={8} lg={6} key={img.id}>
                <div className="image-card">
                  <div className="image-card-header">
                    <img src={`${API_URL.replace('/api', '')}${img.url_imagen}`} alt="Ecografía" />
                    <div className="image-status-badge">
                      {img.tiene_analisis ? renderResultBadge(img.analisis_resultado!.resultado) : <Tag color="processing">Pendiente</Tag>}
                    </div>
                  </div>
                  <div className="image-card-body">
                    <div className="image-title">{img.paciente_nombre}</div>
                    <div className="image-meta">
                      <span><FileImageOutlined /> {img.tamanio_mb} MB • {img.tipo_imagen.replace('_', ' ')}</span>
                      <span>{new Date(img.fecha_subida).toISOString().slice(0, 10)}</span>
                    </div>

                    {img.tiene_analisis && (
                      <div className="cnn-result">
                        <span className={`cnn-score ${getResultClass(img.analisis_resultado!.resultado)}`}>
                          <RobotOutlined /> Confianza: {img.analisis_resultado!.confianza}%
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="image-card-footer">
                    {!img.tiene_analisis ? (
                      <Button
                        type="primary"
                        block
                        icon={<RobotOutlined />}
                        loading={state.analyzingId === img.id}
                        onClick={() => handleAnalyze(img.id)}
                        style={{ marginBottom: 4 }}
                      >
                        Analizar (legado)
                      </Button>
                    ) : (
                      <Button
                        type="default"
                        block
                        icon={<EyeOutlined />}
                        onClick={() => showAnalysis(img.id)}
                        style={{ marginBottom: 4 }}
                      >
                        Ver Resultado
                      </Button>
                    )}
                    <Tooltip title="Analizar con EfficientNet-B4 + Grad-CAM + SHAP">
                      <Button
                        type="primary"
                        block
                        icon={<ExperimentOutlined />}
                        loading={state.analyzingCnnId === img.id}
                        onClick={() => handleAnalyzeCNN(img)}
                        style={{ background: '#722ed1', borderColor: '#722ed1', marginBottom: 4 }}
                      >
                        EffNetB4 + Grad-CAM
                      </Button>
                    </Tooltip>
                    {ecografiasVinculadas[img.id] ? (
                      <Tooltip title={`Ver Ecografía #${ecografiasVinculadas[img.id]}`}>
                        <Button
                          type="link"
                          block
                          icon={<NodeIndexOutlined />}
                          style={{ color: '#52c41a', marginBottom: 4 }}
                          onClick={() => {
                            window.open(`/ecografias/${ecografiasVinculadas[img.id]}`, '_blank');
                          }}
                        >
                          Eco #{ecografiasVinculadas[img.id]}
                        </Button>
                      </Tooltip>
                    ) : (
                      <Button
                        block
                        icon={<LinkOutlined />}
                        onClick={() => handleVincularClick(img)}
                        style={{ marginBottom: 4 }}
                      >
                        Vincular a Ecografía
                      </Button>
                    )}
                    <Tooltip title="Eliminar">
                      <Button danger icon={<DeleteOutlined />} onClick={() => handleDelete(img.id)} />
                    </Tooltip>
                  </div>
                </div>
              </Col>
            ))
          )}
        </Row>
      </div>

      {/* ── Modal Análisis EfficientNet-B4 completo (Grad-CAM + SHAP + Biometría) ── */}
      <Modal
        title={
          <span>
            <ExperimentOutlined style={{ color: '#722ed1', marginRight: 8 }} />
            Analisis EfficientNet-B4: Grad-CAM, SHAP y Biometria
          </span>
        }
        open={state.isCnnModalVisible}
        onCancel={() => { dispatch({ type: 'SET_IS_CNN_MODAL_VISIBLE', payload: false }); dispatch({ type: 'SET_CNN_ANALYSIS', payload: null }); dispatch({ type: 'SET_NARRATIVE_REPORT', payload: null }); dispatch({ type: 'SET_CNN_IMAGE_ID', payload: null }); }}
        width={1100}
        footer={[
          <Button
            key="narrative"
            icon={<FileTextOutlined />}
            loading={state.loadingNarrative}
            disabled={state.cnnAnalysis?.ultrasound_validation?.es_ecografia_obstetrica_valida === undefined}
            onClick={handleGenerarReporteNarrativo}
          >
            {state.narrativeReport ? 'Regenerar reporte narrativo (IA local)' : 'Generar reporte narrativo (IA local)'}
          </Button>,
          <Button key="close" onClick={() => { dispatch({ type: 'SET_IS_CNN_MODAL_VISIBLE', payload: false }); dispatch({ type: 'SET_CNN_ANALYSIS', payload: null }); dispatch({ type: 'SET_NARRATIVE_REPORT', payload: null }); dispatch({ type: 'SET_CNN_IMAGE_ID', payload: null }); }}>
            Cerrar
          </Button>,
        ]}
        className="cnn-analysis-modal"
      >
        {state.cnnAnalysis && (
          <Row gutter={[16, 16]}>
            {/* Columna izquierda: imagen con Grad-CAM overlay */}
            <Col xs={24} md={10}>
              <GradCamOverlay ai={state.cnnAnalysis} originalUrl={state.cnnImageUrl} />
              {!state.cnnAnalysis.gradcam_base64 && (
                <img
                  src={state.cnnImageUrl}
                  alt="Ecografia"
                  style={{ width: '100%', borderRadius: 4 }}
                />
              )}
              <Descriptions size="small" column={1} style={{ marginTop: 8 }} bordered>
                <Descriptions.Item label="Modelo">
                  {state.cnnAnalysis.modelo_version || 'EfficientNet-B4'}
                </Descriptions.Item>
                <Descriptions.Item label="Score global">
                  <Progress
                    percent={Math.round((state.cnnAnalysis.score_global || 0) * 100)}
                    size="small"
                    strokeColor={
                      (state.cnnAnalysis.score_global || 0) >= 0.7 ? '#ff4d4f' : '#52c41a'
                    }
                  />
                </Descriptions.Item>
              </Descriptions>
            </Col>

            {/* Columna derecha: alertas, patologías, SHAP, biometría */}
            <Col xs={24} md={14}>
              {/* Validación de ecografía */}
              {state.cnnAnalysis.ultrasound_validation?.es_ecografia_obstetrica_valida === false ? (
                <>
                  <Alert
                    type="warning"
                    icon={<WarningOutlined />}
                    showIcon
                    message="La imagen NO es una ecografía obstétrica válida"
                    description={
                      <div>
                        <p>{state.cnnAnalysis.ultrasound_validation.motivo || 'La imagen subida no corresponde a una ecografía médica.'}</p>
                        {state.cnnAnalysis.ultrasound_validation.sharpness !== undefined && (
                          <p style={{ fontSize: 12, color: '#8c8c8c' }}>
                            Sharpness: {state.cnnAnalysis.ultrasound_validation.sharpness} |
                            Contraste: {state.cnnAnalysis.ultrasound_validation.contrast}
                          </p>
                        )}
                        {(state.cnnAnalysis.ultrasound_validation.motivo_validez || state.cnnAnalysis.ultrasound_validation.motivo) && (
                          <p style={{ fontSize: 12, color: '#8c8c8c' }}>
                            Motivo: {state.cnnAnalysis.ultrasound_validation.motivo_validez || state.cnnAnalysis.ultrasound_validation.motivo}
                          </p>
                        )}
                      </div>
                    }
                    style={{ marginBottom: 12 }}
                  />
                  {state.cnnAnalysis.pathology_detection?.mensaje && (
                    <Alert
                      type="info"
                      icon={<InfoCircleOutlined />}
                      showIcon
                      message="Sin análisis de patologías"
                      description={state.cnnAnalysis.pathology_detection.mensaje}
                      style={{ marginBottom: 12 }}
                    />
                  )}
                  {state.cnnAnalysis.clinical_recommendations?.estudios_adicionales && (
                    <div style={{ marginTop: 12, padding: 12, background: 'var(--ia-bg-alt)', borderRadius: 6, border: '1px solid var(--ia-warning)' }}>
                      <Typography.Text strong style={{ color: 'var(--ia-warning)' }}>Recomendaciones:</Typography.Text>
                      {state.cnnAnalysis.clinical_recommendations.estudios_adicionales.map((rec: string) => (
                        <div key={rec} style={{ fontSize: 13, marginTop: 4, color: 'var(--ia-text-secondary)' }}>
                          <InfoCircleOutlined style={{ marginRight: 6, color: 'var(--ia-warning)' }} />
                          {rec}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <>
                  {/* Calidad insuficiente (ej. resolucion baja) pero la imagen SI es una ecografia
                      valida: el analisis se muestra igual, esto es solo informativo. */}
                  {state.cnnAnalysis.ultrasound_validation?.calidad_suficiente === false && (
                    <Alert
                      type="warning"
                      icon={<WarningOutlined />}
                      showIcon
                      message="Calidad de imagen reducida"
                      description={
                        <div>
                          <p>
                            {state.cnnAnalysis.ultrasound_validation.motivo_calidad ||
                              'La calidad de la imagen es menor a la recomendada. El análisis se realizó igualmente, pero la confiabilidad puede ser menor.'}
                          </p>
                          <p style={{ fontSize: 12, color: 'var(--ia-text-secondary)' }}>
                            Se recomienda repetir la captura con mejor resolución cuando sea posible.
                          </p>
                        </div>
                      }
                      style={{ marginBottom: 12 }}
                    />
                  )}
                  {/* Senal real detectada por debajo del umbral clinico de confirmacion:
                      no se fuerza un diagnostico, pero se muestra de forma transparente en
                      vez de quedar oculta detras de "baja confianza". */}
                  {(() => {
                    const top = state.cnnAnalysis.pathology_detection?.pathologies?.[0];
                    const allProbs = state.cnnAnalysis.pathology_detection?.all_probabilities;
                    if (top?.pathology !== 'baja_confianza' || !allProbs) return null;
                    // Umbrales calibrados reales (Microservicio_IA/app/config.py) — el corte de
                    // "vale la pena mostrar" debe ser proporcional al umbral real de cada clase,
                    // no un valor fijo. Un 43% de embarazo_multiple (umbral 0.95) esta muy lejos
                    // de confirmarse y genera confusion si se muestra igual que un 43% de
                    // polihidramnios (umbral 0.25, que ya estaria CONFIRMADO a ese nivel).
                    // Regla: solo mostrar si la señal alcanzo al menos el 70% del camino hacia
                    // su propio umbral de confirmacion.
                    const UMBRALES_REALES: Record<string, number> = {
                      hidrocefalia: 0.65, anencefalia: 0.65, espina_bifida: 0.65, labio_leporino: 0.55,
                      atresia_duodenal: 0.65, cardiopatia_congenita: 0.65, oligohidramnios: 0.35,
                      polihidramnios: 0.25, restriccion_crecimiento: 0.40, macrosomia_fetal: 0.40,
                      placenta_previa: 0.85, preeclampsia_signos: 0.65, muerte_fetal: 0.60,
                      embarazo_multiple: 0.95,
                    };
                    const señales = Object.entries(allProbs)
                      .filter(([k, v]) => {
                        if (k === 'normal' || k === 'no_ecografia') return false;
                        const umbral = UMBRALES_REALES[k] ?? 0.5;
                        return (v ?? 0) >= umbral * 0.7;
                      })
                      .sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0));
                    if (señales.length === 0) return null;
                    return (
                      <Alert
                        type="info"
                        icon={<InfoCircleOutlined />}
                        showIcon
                        message="Señal detectada por debajo del umbral de confirmación clínica"
                        description={
                          <div>
                            <p>
                              El modelo no confirma un diagnóstico (no alcanza el umbral clínico calibrado para esa patología),
                              pero detectó señal real en:
                            </p>
                            {señales.map(([k, v]) => (
                              <p key={k} style={{ margin: '2px 0' }}>
                                <strong style={{ textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</strong>: {((v ?? 0) * 100).toFixed(1)}%
                              </p>
                            ))}
                            <p style={{ fontSize: 12, color: 'var(--ia-text-secondary)' }}>Requiere evaluación especializada para confirmar o descartar.</p>
                          </div>
                        }
                        style={{ marginBottom: 12 }}
                      />
                    );
                  })()}
                  {/* Alert médico de patologías detectadas */}
                  {state.cnnAnalysis.pathology_detection?.pathologies &&
                    renderPathologyAlert(state.cnnAnalysis.pathology_detection.pathologies)}

                  {/* Lista de todas las patologías con sus probabilidades */}
                  {state.cnnAnalysis.pathology_detection?.pathologies &&
                    state.cnnAnalysis.pathology_detection.pathologies.length > 0 && (
                      <>
                        <Divider orientation="left" style={{ fontSize: 13 }}>
                          <HeartOutlined /> Deteccion de Patologias (umbral calibrado por patologia)
                        </Divider>
                        {state.cnnAnalysis.pathology_detection.pathologies.map((p, idx) => (
                          <div key={p?.pathology || `patologia-${idx}`} style={{ marginBottom: 10, padding: 8, background: 'var(--ia-bg-alt)', borderRadius: 4, border: '1px solid var(--ia-border)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                              <span style={{ fontWeight: 600, textTransform: 'capitalize', color: 'var(--ia-text)' }}>{p?.pathology?.replace(/_/g, ' ') || ''}</span>
                              <span style={{ fontWeight: 600, color: 'var(--ia-text)' }}>
                                {(safeProb(p.confidence) * 100).toFixed(1)}%
                                {p.icd10 && <Tag color="blue" style={{ marginLeft: 6, fontSize: 12 }}>{p.icd10}</Tag>}
                              </span>
                            </div>
                            <Progress
                              percent={Math.round(safeProb(p.confidence) * 100)}
                              size="small"
                              status={
                                p.pathology === 'normal' ? 'success'
                                  : p.pathology === 'baja_confianza' ? 'normal'
                                  : 'exception'
                              }
                              showInfo={false}
                            />
                            {p.ultrasound_type && (
                              <div style={{ fontSize: 11, color: 'var(--ia-text-secondary)', marginTop: 2 }}>
                                <strong style={{ color: 'var(--ia-text)' }}>Tipo ecografía:</strong> {p.ultrasound_type}
                                {p.gestational_weeks && <span> | <strong style={{ color: 'var(--ia-text)' }}>Semanas:</strong> {p.gestational_weeks}</span>}
                              </div>
                            )}
                            {p.ultrasound_markers && (
                              <div style={{ fontSize: 11, color: 'var(--ia-text-tertiary)', marginTop: 1 }}>
                                <strong style={{ color: 'var(--ia-text)' }}>Marcadores:</strong> {p.ultrasound_markers}
                              </div>
                            )}
                            {p.recommendation && (
                              <div style={{ fontSize: 11, color: 'var(--ia-info)', marginTop: 1 }}>
                                {p.recommendation}
                              </div>
                            )}
                          </div>
                        ))}
                      </>
                    )}

                  {/* SHAP Risk Scores */}
                  {state.cnnAnalysis.shap_risk_scores &&
                    renderShapRiskBars(state.cnnAnalysis.shap_risk_scores)}

                  {/* Tabla de biometría fetal */}
                  {state.cnnAnalysis.biometry && renderBiometryTable(state.cnnAnalysis.biometry)}
                </>
              )}
            </Col>
          </Row>
        )}

        {state.narrativeReport && renderNarrativeReport(state.narrativeReport)}
      </Modal>

      {/* Modal Vincular a Ecografía */}
      <Modal
        title={<span><LinkOutlined /> Vincular Imagen a Ecografía</span>}
        open={vincularModalVisible}
        onCancel={() => { setVincularModalVisible(false); setImagenAVincular(null); }}
        width={500}
        onOk={handleVincularConfirm}
        confirmLoading={vinculando}
        okText="Crear Ecografía"
        okButtonProps={{ icon: <LinkOutlined /> }}
      >
        {imagenAVincular && (
          <div>
            <Descriptions size="small" column={1} bordered style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Imagen IA ID">{imagenAVincular.id}</Descriptions.Item>
              <Descriptions.Item label="Paciente">
                <Tag color="blue">{imagenAVincular.paciente_nombre}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Tipo">{imagenAVincular.tipo_imagen}</Descriptions.Item>
              <Descriptions.Item label="Fecha">
                {imagenAVincular.fecha_captura || imagenAVincular.fecha_subida.slice(0, 10)}
              </Descriptions.Item>
              <Descriptions.Item label="Tiene análisis CNN">
                {imagenAVincular.tiene_analisis ? (
                  <Tag color="success">Sí</Tag>
                ) : (
                  <Tag color="warning">No</Tag>
                )}
              </Descriptions.Item>
            </Descriptions>
            <Alert
              type="info"
              showIcon
              description={
                `Se creará una Ecografía en el módulo de ecografías para ${imagenAVincular.paciente_nombre}.
                ${imagenAVincular.tiene_analisis ? ' El análisis CNN se copiará a la nueva ecografía.' : ''}`
              }
            />
          </div>
        )}
      </Modal>

      {/* Modal de Análisis CNN (legado ia_medica app) */}
      <Modal
        title="Resultado del Análisis CNN"
        open={state.isModalVisible}
        onCancel={() => dispatch({ type: 'SET_IS_MODAL_VISIBLE', payload: false })}
        width={1000}
        footer={[
          <Button key="close" onClick={() => dispatch({ type: 'SET_IS_MODAL_VISIBLE', payload: false })}>Cerrar</Button>,
          <Button key="export" type="primary" icon={<DownloadOutlined />}>Exportar Reporte</Button>
        ]}
        className="cnn-analysis-modal"
      >
        {state.selectedAnalysis && (
          <div className="analysis-container">
            {state.selectedAnalysis.imagen && (
              <div className="image-preview-section">
                <img src={`${API_URL.replace('/api', '')}${state.selectedAnalysis.imagen.url_imagen}`} alt="Ecografía" />
              </div>
            )}
            
            <div className="results-section">
              {state.selectedAnalysis.analisis.sugerencia_diagnostica_data && (
                <div className="diagnosis-suggestion" style={{ background: 'var(--ia-info-bg)', padding: 12, borderRadius: 8, marginBottom: 12, border: '1px solid var(--ia-info)' }}>
                  <h4 style={{ margin: 0, color: 'var(--ia-info)' }}><RobotOutlined /> Diagnóstico Sugerido</h4>
                  <p style={{ margin: '4px 0', fontSize: 16, fontWeight: 600, color: 'var(--ia-text)' }}>
                    {state.selectedAnalysis.analisis.sugerencia_diagnostica_data.patologia.replace(/_/g, ' ').toUpperCase()}
                    <Tag color="blue" style={{ marginLeft: 8 }}>
                      {Math.round(state.selectedAnalysis.analisis.sugerencia_diagnostica_data.confianza * 100)}%
                    </Tag>
                  </p>
                  <p style={{ margin: 0, fontSize: 12, color: 'var(--ia-text-secondary)' }}>
                    ICD-10: {state.selectedAnalysis.analisis.sugerencia_diagnostica_data.icd10}
                    {state.selectedAnalysis.analisis.sugerencia_diagnostica_data.descripcion && ` — ${state.selectedAnalysis.analisis.sugerencia_diagnostica_data.descripcion}`}
                  </p>
                  {state.selectedAnalysis.analisis.sugerencia_diagnostica_data.recomendacion && (
                    <div style={{ marginTop: 8, fontSize: 12, padding: '8px 12px', background: 'var(--ia-bg-alt)', color: 'var(--ia-text)', borderRadius: 6 }}>
                      <InfoCircleOutlined style={{ marginRight: 6 }} />
                      {state.selectedAnalysis.analisis.sugerencia_diagnostica_data.recomendacion}
                    </div>
                  )}
                </div>
              )}
              <div className={`result-header ${getResultClass(state.selectedAnalysis.analisis.resultado)}`}>
                {getResultIcon(state.selectedAnalysis.analisis.resultado)}
                <div className="result-info">
                  <h3>Diagnóstico IA: {state.selectedAnalysis.analisis.resultado.replace('_', ' ').toUpperCase()}</h3>
                  <p>Modelo: {state.selectedAnalysis.analisis.modelo_usado.toUpperCase()} • Confianza: {state.selectedAnalysis.analisis.confianza_porcentaje}%</p>
                </div>
              </div>

              <div className="findings-list">
                <h4><FundProjectionScreenOutlined /> Estructuras Detectadas</h4>
                {Object.entries(state.selectedAnalysis.analisis.estructuras_detectadas).map(([key, val]: any) => (
                  <div className="finding-item" key={key}>
                    <span className="finding-name">{key.replace('_', ' ')}</span>
                    <span className="finding-conf">{(val.confianza * 100).toFixed(1)}% {val.normal ? 'Normal' : 'Anomalo'}</span>
                  </div>
                ))}
              </div>

              {state.selectedAnalysis.analisis.anomalias_detectadas.length > 0 && (
                <div className="findings-list" style={{ borderColor: '#fecaca' }}>
                  <h4 style={{ color: '#dc2626' }}><WarningOutlined /> Anomalías Detectadas</h4>
                  {state.selectedAnalysis.analisis.anomalias_detectadas.map((anom: any) => (
                    <div className="finding-item" key={anom.tipo}>
                      <span className="finding-name">{anom.tipo.replace('_', ' ')}</span>
                      <span className="finding-conf">{(anom.confianza * 100).toFixed(1)}% • {anom.severidad}</span>
                    </div>
                  ))}
                </div>
              )}

              {state.selectedAnalysis.analisis.recomendaciones.length > 0 && (
                <div className="recommendations-box">
                  <h4><CheckCircleOutlined /> Recomendaciones Médicas</h4>
                  <ul>
                    {state.selectedAnalysis.analisis.recomendaciones.map((rec: string) => (
                      <li key={rec}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default IaMedica;

