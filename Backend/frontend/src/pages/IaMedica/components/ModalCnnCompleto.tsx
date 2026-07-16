import React from 'react';
import { Button, Tag, Modal, Typography, Row, Col, Alert, Progress, Descriptions, Divider } from 'antd';
import {
  WarningOutlined, ExperimentOutlined, HeartOutlined,
  InfoCircleOutlined, FileTextOutlined,
} from '@ant-design/icons';
import { AnalisisCNNCompleto, ReporteNarrativoIA } from '../../../services/iaMedicaService';
import { IaMedicaAction } from '../iaMedicaReducer';
import GradCamOverlay from './GradCamOverlay';
import {
  safeProb, renderShapRiskBars, renderBiometryTable, renderPathologyAlert, renderNarrativeReport,
} from '../iaMedicaHelpers';

interface ModalCnnCompletoProps {
  isCnnModalVisible: boolean;
  cnnAnalysis: AnalisisCNNCompleto | null;
  cnnImageUrl: string;
  narrativeReport: ReporteNarrativoIA | null;
  loadingNarrative: boolean;
  dispatch: React.Dispatch<IaMedicaAction>;
  handleGenerarReporteNarrativo: () => void;
}

const ModalCnnCompleto: React.FC<ModalCnnCompletoProps> = ({
  isCnnModalVisible, cnnAnalysis, cnnImageUrl, narrativeReport, loadingNarrative,
  dispatch, handleGenerarReporteNarrativo,
}) => (
  <Modal
    title={
      <span>
        <ExperimentOutlined style={{ color: '#722ed1', marginRight: 8 }} />
        Analisis EfficientNet-B4: Grad-CAM, SHAP y Biometria
      </span>
    }
    open={isCnnModalVisible}
    onCancel={() => { dispatch({ type: 'SET_IS_CNN_MODAL_VISIBLE', payload: false }); dispatch({ type: 'SET_CNN_ANALYSIS', payload: null }); dispatch({ type: 'SET_NARRATIVE_REPORT', payload: null }); dispatch({ type: 'SET_CNN_IMAGE_ID', payload: null }); }}
    width={1100}
    footer={[
      <Button
        key="narrative"
        icon={<FileTextOutlined />}
        loading={loadingNarrative}
        disabled={cnnAnalysis?.ultrasound_validation?.es_ecografia_obstetrica_valida === undefined}
        onClick={handleGenerarReporteNarrativo}
      >
        {narrativeReport ? 'Regenerar reporte narrativo (IA local)' : 'Generar reporte narrativo (IA local)'}
      </Button>,
      <Button key="close" onClick={() => { dispatch({ type: 'SET_IS_CNN_MODAL_VISIBLE', payload: false }); dispatch({ type: 'SET_CNN_ANALYSIS', payload: null }); dispatch({ type: 'SET_NARRATIVE_REPORT', payload: null }); dispatch({ type: 'SET_CNN_IMAGE_ID', payload: null }); }}>
        Cerrar
      </Button>,
    ]}
    className="cnn-analysis-modal"
  >
    {cnnAnalysis && (
      <Row gutter={[16, 16]}>
        {/* Columna izquierda: imagen con Grad-CAM overlay */}
        <Col xs={24} md={10}>
          <GradCamOverlay ai={cnnAnalysis} originalUrl={cnnImageUrl} />
          {!cnnAnalysis.gradcam_base64 && (
            <img
              src={cnnImageUrl}
              alt="Ecografia"
              style={{ width: '100%', borderRadius: 4 }}
            />
          )}
          <Descriptions size="small" column={1} style={{ marginTop: 8 }} bordered>
            <Descriptions.Item label="Modelo">
              {cnnAnalysis.modelo_version || 'EfficientNet-B4'}
            </Descriptions.Item>
            <Descriptions.Item label="Score global">
              <Progress
                percent={Math.round((cnnAnalysis.score_global || 0) * 100)}
                size="small"
                strokeColor={
                  (cnnAnalysis.score_global || 0) >= 0.7 ? '#ff4d4f' : '#52c41a'
                }
              />
            </Descriptions.Item>
          </Descriptions>
        </Col>

        {/* Columna derecha: alertas, patologías, SHAP, biometría */}
        <Col xs={24} md={14}>
          {/* Validación de ecografía */}
          {cnnAnalysis.ultrasound_validation?.es_ecografia_obstetrica_valida === false ? (
            <>
              <Alert
                type="warning"
                icon={<WarningOutlined />}
                showIcon
                message="La imagen NO es una ecografía obstétrica válida"
                description={
                  <div>
                    <p>{cnnAnalysis.ultrasound_validation.motivo || 'La imagen subida no corresponde a una ecografía médica.'}</p>
                    {cnnAnalysis.ultrasound_validation.sharpness !== undefined && (
                      <p style={{ fontSize: 12, color: '#8c8c8c' }}>
                        Sharpness: {cnnAnalysis.ultrasound_validation.sharpness} |
                        Contraste: {cnnAnalysis.ultrasound_validation.contrast}
                      </p>
                    )}
                    {(cnnAnalysis.ultrasound_validation.motivo_validez || cnnAnalysis.ultrasound_validation.motivo) && (
                      <p style={{ fontSize: 12, color: '#8c8c8c' }}>
                        Motivo: {cnnAnalysis.ultrasound_validation.motivo_validez || cnnAnalysis.ultrasound_validation.motivo}
                      </p>
                    )}
                  </div>
                }
                style={{ marginBottom: 12 }}
              />
              {cnnAnalysis.pathology_detection?.mensaje && (
                <Alert
                  type="info"
                  icon={<InfoCircleOutlined />}
                  showIcon
                  message="Sin análisis de patologías"
                  description={cnnAnalysis.pathology_detection.mensaje}
                  style={{ marginBottom: 12 }}
                />
              )}
              {cnnAnalysis.clinical_recommendations?.estudios_adicionales && (
                <div style={{ marginTop: 12, padding: 12, background: 'var(--ia-bg-alt)', borderRadius: 6, border: '1px solid var(--ia-warning)' }}>
                  <Typography.Text strong style={{ color: 'var(--ia-warning)' }}>Recomendaciones:</Typography.Text>
                  {cnnAnalysis.clinical_recommendations.estudios_adicionales.map((rec: string) => (
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
              {cnnAnalysis.ultrasound_validation?.calidad_suficiente === false && (
                <Alert
                  type="warning"
                  icon={<WarningOutlined />}
                  showIcon
                  message="Calidad de imagen reducida"
                  description={
                    <div>
                      <p>
                        {cnnAnalysis.ultrasound_validation.motivo_calidad ||
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
                const top = cnnAnalysis.pathology_detection?.pathologies?.[0];
                const allProbs = cnnAnalysis.pathology_detection?.all_probabilities;
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
              {cnnAnalysis.pathology_detection?.pathologies &&
                renderPathologyAlert(cnnAnalysis.pathology_detection.pathologies)}

              {/* Lista de todas las patologías con sus probabilidades */}
              {cnnAnalysis.pathology_detection?.pathologies &&
                cnnAnalysis.pathology_detection.pathologies.length > 0 && (
                  <>
                    <Divider orientation="left" style={{ fontSize: 13 }}>
                      <HeartOutlined /> Deteccion de Patologias (umbral calibrado por patologia)
                    </Divider>
                    {cnnAnalysis.pathology_detection.pathologies.map((p, idx) => (
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
              {cnnAnalysis.shap_risk_scores &&
                renderShapRiskBars(cnnAnalysis.shap_risk_scores)}

              {/* Tabla de biometría fetal */}
              {cnnAnalysis.biometry && renderBiometryTable(cnnAnalysis.biometry)}
            </>
          )}
        </Col>
      </Row>
    )}

    {narrativeReport && renderNarrativeReport(narrativeReport)}
  </Modal>
);

export default ModalCnnCompleto;
