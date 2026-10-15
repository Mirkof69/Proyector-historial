import React from 'react';
import {
  Tag, Alert, Descriptions, Divider, Row, Col, Typography,
} from 'antd';
import {
  CheckCircleOutlined, WarningOutlined, CloseCircleOutlined,
  InfoCircleOutlined, FileTextOutlined, ExclamationCircleOutlined,
} from '@ant-design/icons';
import { ReporteNarrativoIA } from '../../services/iaMedicaService';

// ── Helpers puros de presentación (nivel de módulo: identidad estable) ───────
export const renderResultBadge = (resultado: string) => {
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

export const getResultIcon = (resultado: string) => {
  if (resultado === 'normal') return <CheckCircleOutlined className="result-icon" />;
  if (['anomalia_grave', 'requiere_revision'].includes(resultado)) return <CloseCircleOutlined className="result-icon" />;
  return <WarningOutlined className="result-icon" />;
};

export const getResultClass = (resultado: string) => {
  if (resultado === 'normal') return 'normal';
  if (['anomalia_grave', 'requiere_revision'].includes(resultado)) return 'danger';
  return 'warning';
};

// Reporte narrativo de IA local (LLM con visión, Ollama). Los campos
// diagnosticos (clasificacion_clinica, tipo_embarazo, patologias_detectadas,
// biometria) vienen siempre del backend ya groundeados en el CNN — esta
// funcion solo los muestra, nunca los recalcula. La seccion
// "hallazgos_visuales_complementarios" se muestra aparte, con badge "no
// validado", para no confundirla con el diagnostico confirmado.
export const renderNarrativeReport = (reporte: ReporteNarrativoIA) => {
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
        <FileTextOutlined className="ia-icono-narrativa" />
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

