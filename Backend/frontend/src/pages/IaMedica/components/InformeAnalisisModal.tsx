import React from 'react';
import {
  Alert, Button, Col, Descriptions, Divider, Image, List, Modal, Progress, Row, Space, Tag, Typography,
} from 'antd';
import { DownloadOutlined, ExperimentOutlined, FileTextOutlined } from '@ant-design/icons';
import { InformeRedesMedidas, ReporteNarrativoIA } from '../../../services/iaMedicaService';
import { API_URL } from '../../../services/api';
import { renderNarrativeReport, veredictoDelInforme } from '../iaMedicaHelpers';

const { Text, Paragraph } = Typography;

interface Props {
  abierto: boolean;
  informe: InformeRedesMedidas | null;
  imagenUrl: string;
  reporteNarrativo?: ReporteNarrativoIA | null;
  generandoNarrativa?: boolean;
  /** Sin él (imagen que no está guardada) no se ofrece la redacción con IA local. */
  onGenerarNarrativa?: () => void;
  onCerrar: () => void;
}

export const urlMedia = (url?: string | null) => {
  if (!url) return '';
  return /^(https?:|data:|blob:)/.test(url) ? url : `${API_URL.replace(/\/api\/?$/, '')}${url}`;
};

const ETIQUETAS_MEDIDA: Record<string, string> = {
  circunferencia_cefalica_mm: 'Circunferencia cefálica',
  diametro_biparietal_mm: 'Diámetro biparietal',
  edad_gestacional_por_hc_semanas: 'Edad gestacional por HC (Hadlock 1984)',
  edad_gestacional_por_dbp_semanas: 'Edad gestacional por DBP (Hadlock 1982)',
  indice_cardiotoracico_areas: 'Índice cardiotorácico (áreas)',
  indice_cardiotoracico_circunferencias: 'Índice cardiotorácico (circunferencias)',
  plano_adecuado_para_ca: 'Corte adecuado para medir la CA',
  relacion_ejes: 'Relación de ejes del cráneo',
  longitud_femur_mm: 'Longitud del fémur',
  circunferencia_abdominal_mm: 'Circunferencia abdominal',
  diametro_abdominal_transverso_mm: 'Diámetro abdominal transverso',
  diametro_abdominal_anteroposterior_mm: 'Diámetro abdominal anteroposterior',
  fl_px: 'Longitud del fémur (px, sin escala)',
  tad_px: 'Diámetro transverso (px, sin escala)',
  apad_px: 'Diámetro anteroposterior (px, sin escala)',
  lesion_ancho_mm: 'Ancho de la lesión',
  lesion_alto_mm: 'Alto de la lesión',
  lesion_ancho_px: 'Ancho de la lesión (px, sin escala)',
  lesion_alto_px: 'Alto de la lesión (px, sin escala)',
  ancho_mm: 'Ancho del mioma',
  alto_mm: 'Alto del mioma',
  ancho_px: 'Ancho del mioma (px, sin escala)',
  alto_px: 'Alto del mioma (px, sin escala)',
};

const valorMedida = (clave: string, v: unknown, informe: InformeRedesMedidas): React.ReactNode => {
  const m = informe.medidas;
  if (typeof v === 'boolean') return v ? <Tag color="green">Sí</Tag> : <Tag color="orange">No</Tag>;
  if (clave === 'circunferencia_cefalica_mm') return `${v} mm ± ${m.margen_hc_mm}`;
  if (clave === 'diametro_biparietal_mm') return `${v} mm ± ${m.margen_dbp_mm}`;
  if (clave === 'longitud_femur_mm') return `${v} mm ± ${m.margen_lf_mm}`;
  if (clave === 'circunferencia_abdominal_mm') return `${v} mm ± ${m.margen_ca_mm}`;
  if (clave.endsWith('_mm')) return `${v} mm`;
  if (clave.includes('semanas')) return `${v} semanas`;
  if (clave === 'indice_cardiotoracico_areas') {
    const [min, max] = m.referencia_areas ?? [0.25, 0.35];
    return <Space>{String(v)} ± {m.margen}<Tag color={Number(v) > max ? 'orange' : 'green'}>referencia {min}–{max}</Tag></Space>;
  }
  return String(v);
};

/** De quién es el análisis, cuándo se hizo y quién lo pidió (solo los guardados lo traen). */
const DatosDelRegistro: React.FC<{ informe: InformeRedesMedidas }> = ({ informe }) => {
  const { paciente } = informe;
  if (!paciente) return null;
  return (
    <Descriptions bordered size="small" column={{ xs: 1, sm: 2, lg: 3 }} className="ia-informe-registro">
      <Descriptions.Item label="Paciente">{paciente.nombre}</Descriptions.Item>
      {paciente.ci && <Descriptions.Item label="CI">{paciente.ci}</Descriptions.Item>}
      {paciente.edad != null && <Descriptions.Item label="Edad">{paciente.edad} años</Descriptions.Item>}
      {informe.semana_gestacional != null && (
        <Descriptions.Item label="Semana gestacional">{informe.semana_gestacional}</Descriptions.Item>
      )}
      {informe.fecha_analisis && (
        <Descriptions.Item label="Fecha del análisis">
          {new Date(informe.fecha_analisis).toLocaleString('es-BO')}
        </Descriptions.Item>
      )}
      {informe.realizado_por && <Descriptions.Item label="Realizado por">{informe.realizado_por}</Descriptions.Item>}
    </Descriptions>
  );
};

interface ContenidoProps {
  informe: InformeRedesMedidas;
  imagenUrl: string;
  /** La pantalla ya muestra el plano y el cribado cerebral en sus propias tarjetas. */
  detalleAparte?: boolean;
  reporteNarrativo?: ReporteNarrativoIA | null;
}

/**
 * La vista del análisis: el veredicto arriba, la imagen con las estructuras que
 * dibujó la red, para que el médico vea DE DÓNDE sale cada medida, y qué red se
 * usó y cuánto acertó en pacientes que no vio. Es la misma recién analizada y
 * reabierta desde el historial.
 */
export const InformeAnalisisContenido: React.FC<ContenidoProps> = ({
  informe, imagenUrl, detalleAparte, reporteNarrativo,
}) => {
  const medidas = Object.entries(informe.medidas).filter(([k]) => k in ETIQUETAS_MEDIDA);
  const anomalias = informe.anomalias_cerebrales;
  const veredicto = veredictoDelInforme(informe);

  return (
    <div className="ia-informe">
      <Alert type={veredicto.tipo} showIcon message={<Text strong>{veredicto.titulo}</Text>} description={veredicto.detalle} />
      <DatosDelRegistro informe={informe} />
      {informe.hallazgos.map((h) => <Alert key={h} type="warning" showIcon message={h} />)}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={11}>
          <Image.PreviewGroup>
            <Row gutter={8}>
              <Col span={12}><Text type="secondary">Original</Text><Image src={imagenUrl} alt="Ecografía original" /></Col>
              <Col span={12}>
                <Text type="secondary">Lo que vio la red</Text>
                {informe.superposicion_url
                  ? <Image src={urlMedia(informe.superposicion_url)} alt="Estructuras segmentadas" />
                  : <Paragraph type="secondary">Sin segmentación para este plano.</Paragraph>}
              </Col>
            </Row>
          </Image.PreviewGroup>
          {!detalleAparte && (
            <>
              <Divider orientation="left">{informe.version_flujo?.startsWith('ginecologia') ? 'Clasificación' : 'Plano anatómico'}</Divider>
              <Space direction="vertical" className="ia-ancho-completo">
                <Text strong>{informe.plano.plano} · {(informe.plano.confianza * 100).toFixed(1)} %</Text>
                {Object.entries(informe.plano.probabilidades).slice(0, 4).map(([p, v]) => (
                  <div key={p}><Text type="secondary">{p}</Text><Progress percent={Math.round(v * 1000) / 10} size="small" /></div>
                ))}
              </Space>
            </>
          )}
        </Col>
        <Col xs={24} md={13} className="ia-informe">
          <Descriptions title="Medidas" bordered size="small" column={1}>
            {medidas.length ? medidas.map(([k, v]) => (
              <Descriptions.Item key={k} label={ETIQUETAS_MEDIDA[k]}>{valorMedida(k, v, informe)}</Descriptions.Item>
            )) : <Descriptions.Item label="—">Sin medidas para este plano</Descriptions.Item>}
          </Descriptions>
          {Object.keys(informe.estructuras_vistas).length > 0 && (
            <div>
              <Text strong>Estructuras: </Text>
              {Object.entries(informe.estructuras_vistas).map(([e, vista]) => (
                <Tag key={e} color={vista ? 'green' : 'default'}>{e}{vista ? '' : ' (no vista)'}</Tag>
              ))}
            </div>
          )}
          {!detalleAparte && anomalias?.aplicable && (
            <Alert showIcon type={anomalias.alarma_anomalia ? 'error' : 'success'}
              message={anomalias.alarma_anomalia
                ? `Cribado cerebral: posible ${anomalias.familia_sospechada_nombre}`
                : 'Cribado cerebral: sin anomalía visible'}
              description={`Probabilidad de anomalía ${(anomalias.probabilidad_anomalia * 100).toFixed(1)} %${
                anomalias.umbral != null ? ` (umbral ${anomalias.umbral * 100} %)` : ''}. Lo confirma un especialista.`} />
          )}
          {informe.avisos.length > 0 && (
            <List size="small" header={<Text strong>Avisos</Text>} bordered
              dataSource={informe.avisos} renderItem={(a) => <List.Item>{a}</List.Item>} />
          )}
          <Divider orientation="left">Redes usadas y su fiabilidad medida</Divider>
          <List size="small" dataSource={informe.modelos_usados} renderItem={(m) => (
            <List.Item>
              <Space direction="vertical" size={0}>
                <Text strong>{m.archivo}</Text>
                <Text type="secondary">{m.dataset}{m.sha256 ? ` · huella ${m.sha256.slice(0, 12)}` : ''}</Text>
              </Space>
            </List.Item>
          )} />
          {informe.informe_texto && <Paragraph type="secondary">{informe.informe_texto}</Paragraph>}
          {informe.tiempo_ms > 0 && <Text type="secondary">Tiempo de análisis: {informe.tiempo_ms} ms</Text>}
        </Col>
      </Row>
      {reporteNarrativo && renderNarrativeReport(reporteNarrativo)}
    </div>
  );
};

/** El informe en una ventana: para abrir un análisis desde el historial. */
const InformeAnalisisModal: React.FC<Props> = ({
  abierto, informe, imagenUrl, reporteNarrativo, generandoNarrativa, onGenerarNarrativa, onCerrar,
}) => {
  const descargar = () => {
    if (!informe) return;
    const blob = new Blob([JSON.stringify(informe, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `informe_ia_${informe.filename ?? 'ecografia'}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <Modal
      title={<Space><ExperimentOutlined />Análisis de la ecografía con redes medidas</Space>}
      open={abierto}
      onCancel={onCerrar}
      width={1100}
      footer={[
        <Button key="json" icon={<DownloadOutlined />} onClick={descargar} disabled={!informe}>Informe JSON</Button>,
        onGenerarNarrativa && (
          <Button key="narrativa" icon={<FileTextOutlined />} loading={generandoNarrativa} onClick={onGenerarNarrativa} disabled={!informe}>
            {reporteNarrativo ? 'Regenerar redacción (IA local)' : 'Redactar informe (IA local)'}
          </Button>
        ),
        <Button key="cerrar" type="primary" onClick={onCerrar}>Cerrar</Button>,
      ].filter(Boolean)}
    >
      {informe && <InformeAnalisisContenido informe={informe} imagenUrl={imagenUrl} reporteNarrativo={reporteNarrativo} />}
    </Modal>
  );
};

export default InformeAnalisisModal;
