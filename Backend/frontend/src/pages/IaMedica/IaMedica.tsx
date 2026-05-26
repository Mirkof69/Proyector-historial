import React, { useReducer, useEffect } from 'react';
import {
  Upload, Button, Tag, Modal, Spin, Typography, message,
  Row, Col, Empty, Tooltip, Alert, Progress, Table, Descriptions,
  Divider, Badge
} from 'antd';
import {
  InboxOutlined, RobotOutlined, FundProjectionScreenOutlined,
  CheckCircleOutlined, WarningOutlined, CloseCircleOutlined,
  DownloadOutlined, ReloadOutlined, FileImageOutlined,
  DashboardOutlined, EyeOutlined, DeleteOutlined, ExperimentOutlined,
  HeartOutlined, AlertOutlined
} from '@ant-design/icons';
import {
  iaMedicaService,
  ImagenEcografica,
  AnalisisCNN,
  AnalisisCNNCompleto,
  EstadisticasIA,
  Pathology,
  ShapRiskScores,
  BiometryResult
} from '../../services/iaMedicaService';
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
  riesgo_preeclampsia:   'Riesgo de Preeclampsia',
  riesgo_parto_prematuro:'Riesgo de Parto Prematuro',
  riesgo_rciu:           'Riesgo de RCIU',
  riesgo_placenta_previa:'Riesgo de Placenta Previa',
  riesgo_global:         'Score de Riesgo Global',
};

interface GradCamOverlayProps {
  ai: AnalisisCNNCompleto;
  originalUrl: string;
}

const GradCamOverlay: React.FC<GradCamOverlayProps> = ({ ai, originalUrl }) => {
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
        Grad-CAM: {ai.model_version || 'EfficientNet-B4'}
      </div>
    </div>
  );
};

const IaMedica: React.FC = () => {
  interface IaMedicaState {
    imagenes: ImagenEcografica[];
    estadisticas: EstadisticasIA | null;
    loading: boolean;
    uploading: boolean;
    analyzingId: number | null;
    isModalVisible: boolean;
    selectedAnalysis: {imagen: ImagenEcografica, analisis: AnalisisCNN} | null;
    isCnnModalVisible: boolean;
    cnnAnalysis: AnalisisCNNCompleto | null;
    cnnImageUrl: string;
    analyzingCnnId: number | null;
  }

  type IaMedicaAction =
    | { type: 'SET_IMAGENES'; payload: ImagenEcografica[] }
    | { type: 'SET_ESTADISTICAS'; payload: EstadisticasIA | null }
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'SET_UPLOADING'; payload: boolean }
    | { type: 'SET_ANALYZING_ID'; payload: number | null }
    | { type: 'SET_IS_MODAL_VISIBLE'; payload: boolean }
    | { type: 'SET_SELECTED_ANALYSIS'; payload: {imagen: ImagenEcografica, analisis: AnalisisCNN} | null }
    | { type: 'SET_IS_CNN_MODAL_VISIBLE'; payload: boolean }
    | { type: 'SET_CNN_ANALYSIS'; payload: AnalisisCNNCompleto | null }
    | { type: 'SET_CNN_IMAGE_URL'; payload: string }
    | { type: 'SET_ANALYZING_CNN_ID'; payload: number | null };

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
    analyzingCnnId: null,
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
      case 'SET_ANALYZING_CNN_ID':
        return { ...state, analyzingCnnId: action.payload };
      default:
        return state;
    }
  }

  const [state, dispatch] = useReducer(reducer, initialState);

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

  const handleUpload = async (file: File) => {
    dispatch({ type: 'SET_UPLOADING', payload: true });
    try {
      const formData = new FormData();
      formData.append('imagen', file);
      // Simular paciente ID (en produccion vendría de un selector)
      formData.append('paciente', '1'); 
      formData.append('tipo_imagen', 'eco_2d');

      await iaMedicaService.uploadImagen(formData);
      message.success('Imagen subida correctamente');
      fetchData();
    } catch (error) {
      message.error('Error al subir la imagen');
    } finally {
      dispatch({ type: 'SET_UPLOADING', payload: false });
    }
    return false; // Prevenir upload default de antd
  };

  const handleAnalyze = async (id: number) => {
    dispatch({ type: 'SET_ANALYZING_ID', payload: id });
    try {
      const result = await iaMedicaService.analizarImagen(id, 'efficientnet_b4');
      message.success(`Análisis completado: ${result.analisis.resultado}`);
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
      dispatch({ type: 'SET_SELECTED_ANALYSIS', payload: result });
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

  // Análisis completo EfficientNet-B4 con Grad-CAM + SHAP + biometría
  const handleAnalyzeCNN = async (img: ImagenEcografica) => {
    dispatch({ type: 'SET_ANALYZING_CNN_ID', payload: img.id });
    try {
      // Descargar el archivo de imagen desde Django para enviarlo al microservicio
      const imageUrl = `http://localhost:8000${img.url_imagen}`;
      const imageResp = await fetch(imageUrl, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
      });
      if (!imageResp.ok) {
        throw new Error(`No se pudo obtener la imagen (HTTP ${imageResp.status})`);
      }
      const imageBlob = await imageResp.blob();
      const file = new File([imageBlob], img.nombre_original || 'ecografia.jpg', {
        type: imageBlob.type,
      });

      const response = await iaMedicaService.analyzeWithAI(file, String(img.id));
      dispatch({ type: 'SET_CNN_ANALYSIS', payload: response.ai_analysis });
      dispatch({ type: 'SET_CNN_IMAGE_URL', payload: imageUrl });
      dispatch({ type: 'SET_IS_CNN_MODAL_VISIBLE', payload: true });
      message.success('Análisis EfficientNet-B4 completado');
    } catch (error: any) {
      message.error(`Error en análisis CNN: ${error?.message || 'Error desconocido'}`);
    } finally {
      dispatch({ type: 'SET_ANALYZING_CNN_ID', payload: null });
    }
  };

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

  const renderBiometryTable = (biometry: AnalisisCNNCompleto['biometry']) => {
    if (!biometry?.measurements) return null;
    const measurements = biometry.measurements;
    const dataSource = (Object.keys(BIOMETRY_REFERENCE) as Array<keyof BiometryResult>)
      .filter(k => measurements[k] !== undefined && measurements[k] !== null)
      .map(k => {
        const ref = BIOMETRY_REFERENCE[k];
        const val = measurements[k] as number;
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
                {biometry.alerts.map((a) => <li key={`alert-${a}`}>{a}</li>)}
              </ul>
            }
          />
        )}
      </>
    );
  };

  const renderPathologyAlert = (pathologies: Pathology[]) => {
    const detected = pathologies.filter(p => p.probability >= 0.50 && p.name !== 'normal');
    if (detected.length === 0) return null;

    const hasCritical = detected.some(p => p.probability >= 0.80);
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
              <div key={p.name} style={{ marginBottom: 4 }}>
                <Tag color={p.probability >= 0.80 ? 'red' : 'orange'}>
                  {p.name.replace(/_/g, ' ').toUpperCase()}
                </Tag>
                <span style={{ fontSize: 12 }}>
                  Probabilidad: {(p.probability * 100).toFixed(1)}%
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
            <Dragger
              customRequest={({ file }) => handleUpload(file as File)}
              showUploadList={false}
              style={{ height: '100%', minHeight: '300px' }}
            >
              {state.uploading ? (
                <div><Spin size="large" /><p style={{ marginTop: 16 }}>Subiendo…</p></div>
              ) : (
                <div>
                  <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                  <p className="ant-upload-text">Clic o arrastrar imagen aquí</p>
                  <p className="ant-upload-hint">Soporta JPG, PNG, DICOM (Max: 10MB)</p>
                </div>
              )}
            </Dragger>
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
                    <img src={`http://localhost:8000${img.url_imagen}`} alt="Ecografía" />
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
        onCancel={() => { dispatch({ type: 'SET_IS_CNN_MODAL_VISIBLE', payload: false }); dispatch({ type: 'SET_CNN_ANALYSIS', payload: null }); }}
        width={1100}
        footer={[
          <Button key="close" onClick={() => { dispatch({ type: 'SET_IS_CNN_MODAL_VISIBLE', payload: false }); dispatch({ type: 'SET_CNN_ANALYSIS', payload: null }); }}>
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
                  {state.cnnAnalysis.model_version || 'EfficientNet-B4'}
                </Descriptions.Item>
                <Descriptions.Item label="Tiempo inferencia">
                  {state.cnnAnalysis.inference_time_ms
                    ? `${state.cnnAnalysis.inference_time_ms} ms`
                    : 'N/A'}
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
              {/* Alert médico de patologías detectadas */}
              {state.cnnAnalysis.pathology_detection?.pathologies &&
                renderPathologyAlert(state.cnnAnalysis.pathology_detection.pathologies)}

              {/* Lista de todas las patologías con sus probabilidades */}
              {state.cnnAnalysis.pathology_detection?.pathologies &&
                state.cnnAnalysis.pathology_detection.pathologies.length > 0 && (
                  <>
                    <Divider orientation="left" style={{ fontSize: 13 }}>
                      <HeartOutlined /> Deteccion de Patologias (umbral &ge;50%)
                    </Divider>
                    {state.cnnAnalysis.pathology_detection.pathologies.map(p => (
                      <div key={p.name} style={{ marginBottom: 6 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                          <span>{p.name.replace(/_/g, ' ')}</span>
                          <span style={{ fontWeight: 600 }}>
                            {(p.probability * 100).toFixed(1)}%
                            {p.icd10 && <Tag color="blue" style={{ marginLeft: 6, fontSize: 12 }}>{p.icd10}</Tag>}
                          </span>
                        </div>
                        <Progress
                          percent={Math.round(p.probability * 100)}
                          size="small"
                          status={p.probability >= 0.50 && p.name !== 'normal' ? 'exception' : 'success'}
                          showInfo={false}
                        />
                      </div>
                    ))}
                  </>
                )}

              {/* SHAP Risk Scores */}
              {state.cnnAnalysis.shap_risk_scores &&
                renderShapRiskBars(state.cnnAnalysis.shap_risk_scores)}

              {/* Tabla de biometría fetal */}
              {state.cnnAnalysis.biometry && renderBiometryTable(state.cnnAnalysis.biometry)}
            </Col>
          </Row>
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
            <div className="image-preview-section">
              <img src={`http://localhost:8000${state.selectedAnalysis.imagen.url_imagen}`} alt="Ecografía" />
              {/* Aquí se podrían renderizar los bounding boxes sobre la imagen */}
            </div>
            
            <div className="results-section">
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
                    <span className="finding-conf">{(val.confianza * 100).toFixed(1)}% {val.normal ? '✅ Normal' : '⚠️ Anómalo'}</span>
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
