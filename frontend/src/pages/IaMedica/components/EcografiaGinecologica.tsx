import React, { useEffect, useState } from 'react';
import {
  Alert, Button, Card, Col, Descriptions, Image, InputNumber, Progress, Radio, Row, Space, Tag, Typography, Upload,
} from 'antd';
import type { UploadFile } from 'antd';
import { UploadOutlined, WomanOutlined } from '@ant-design/icons';
import api, { API_URL } from '../../../services/api';
import { useAntdApp } from '../../../hooks/useMessage';
import { mensajeDeError } from '../../../services/partoDetalleService';
import { PacienteSelect } from '../../../components/clinico/SelectoresClinicos';

const { Text, Paragraph } = Typography;

export type TareaGinecologica = 'ovario' | 'mioma' | 'ovario-pco';

interface Probabilidad { tipo?: string; categoria?: string; probabilidad: number }
interface ModeloUsado { archivo: string; dataset?: string; metricas_prueba?: Record<string, unknown> }
export interface ResultadoGinecologico {
  tarea: string;
  lesion_encontrada?: boolean;
  mioma_ubicado?: boolean;
  tipo_probable?: string;
  categoria_probable?: string;
  probabilidades?: Probabilidad[];
  malignidad?: { probabilidad: number; alarma: boolean; umbral: number;
    sensibilidad_medida?: number; especificidad_medida?: number };
  medidas?: Record<string, number | number[]>;
  hallazgos: string[];
  avisos: string[];
  superposicion_url?: string;
  modelos: ModeloUsado[];
  guardado?: boolean;
}

const TAREAS: { valor: TareaGinecologica; nombre: string; ayuda: string }[] = [
  { valor: 'ovario', nombre: 'Masa ovárica', ayuda: 'Dibuja la lesión, sugiere su tipo (8 clases) y avisa si parece maligna.' },
  { valor: 'mioma', nombre: 'Mioma uterino', ayuda: 'Ubica el mioma en un útero que lo tiene. No sirve para descartarlo.' },
  { valor: 'ovario-pco', nombre: 'Ovario poliquístico', ayuda: 'Normal, folículo dominante o morfología poliquística.' },
];

const pct = (v?: number) => (v === undefined || v === null ? '—' : `${(v * 100).toFixed(1)} %`);
const urlMedia = (url?: string) => (!url ? '' : url.startsWith('http') ? url : `${API_URL.replace(/\/api\/?$/, '')}${url}`);
const ETIQUETAS_MEDIDA: Record<string, string> = {
  lesion_ancho_mm: 'Ancho de la lesión (mm)', lesion_alto_mm: 'Alto de la lesión (mm)',
  lesion_ancho_px: 'Ancho de la lesión (px)', lesion_alto_px: 'Alto de la lesión (px)',
  ancho_mm: 'Ancho del mioma (mm)', alto_mm: 'Alto del mioma (mm)', ancho_px: 'Ancho del mioma (px)',
  alto_px: 'Alto del mioma (px)',
};

/**
 * Ecografía ginecológica con redes entrenadas con datos reales (microservicio
 * de IA, app/ginecologia.py). Cada resultado muestra cuánto acertó la red en
 * pacientes que no vio, y sus límites. Con una paciente elegida, la imagen y el
 * análisis quedan en su historial.
 */
const EcografiaGinecologica: React.FC<{ onGuardado?: () => void }> = ({ onGuardado }) => {
  const { message } = useAntdApp();
  const [tarea, setTarea] = useState<TareaGinecologica>('ovario');
  const [archivo, setArchivo] = useState<UploadFile | null>(null);
  const [pixel, setPixel] = useState<number | null>(null);
  const [resultado, setResultado] = useState<ResultadoGinecologico | null>(null);
  const [paciente, setPaciente] = useState<{ id: number; nombre: string } | null>(null);
  const [guardadoEn, setGuardadoEn] = useState<string | null>(null);
  const [vistaPrevia, setVistaPrevia] = useState('');
  const fichero = archivo?.originFileObj;

  // La vista previa local del archivo se libera al cambiarla o al salir.
  useEffect(() => {
    if (!fichero) { setVistaPrevia(''); return undefined; }
    const url = URL.createObjectURL(fichero);
    setVistaPrevia(url);
    return () => URL.revokeObjectURL(url);
  }, [fichero]);

  const limpiar = () => { setResultado(null); setGuardadoEn(null); };
  const [analizando, setAnalizando] = useState(false);

  const analizar = async () => {
    if (!archivo?.originFileObj) return;
    const datos = new FormData();
    datos.append('file', archivo.originFileObj);
    if (pixel) datos.append('tamano_pixel_mm', String(pixel));
    if (paciente) datos.append('paciente_id', String(paciente.id));
    setAnalizando(true);
    try {
      const { data } = await api.post<ResultadoGinecologico>(`/ia/ginecologia/${tarea}/`, datos,
        { headers: { 'Content-Type': 'multipart/form-data' } });
      setResultado(data);
      setGuardadoEn(data.guardado && paciente ? paciente.nombre : null);
      if (data.guardado) onGuardado?.();
    } catch (e) {
      limpiar();
      message.error(mensajeDeError(e, 'No se pudo analizar la ecografía'));
    } finally {
      setAnalizando(false);
    }
  };

  const ayuda = TAREAS.find((t) => t.valor === tarea)?.ayuda;
  const medidas = Object.entries(resultado?.medidas ?? {}).filter(([k]) => k in ETIQUETAS_MEDIDA);

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={10}>
        <Card title={<Space><WomanOutlined />Ecografía ginecológica</Space>}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <div>
              <Text strong>¿Qué quiere analizar?</Text>
              <Radio.Group
                style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 8 }}
                value={tarea}
                onChange={(e) => { setTarea(e.target.value); limpiar(); }}
              >
                {TAREAS.map((t) => <Radio key={t.valor} value={t.valor}>{t.nombre}</Radio>)}
              </Radio.Group>
              <Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>{ayuda}</Paragraph>
            </div>
            <Upload
              accept="image/png,image/jpeg,image/bmp"
              maxCount={1}
              beforeUpload={() => false}
              fileList={archivo ? [archivo] : []}
              onChange={({ fileList }) => { setArchivo(fileList[0] ?? null); limpiar(); }}
            >
              <Button icon={<UploadOutlined />}>Elegir la imagen de la ecografía</Button>
            </Upload>
            {vistaPrevia && <img className="ia-vista-previa" src={vistaPrevia} alt="Ecografía elegida" />}
            <div>
              <Text>Paciente</Text>
              <PacienteSelect
                placeholder="Buscar paciente por nombre o CI"
                value={paciente?.id}
                onChange={(id, p) => {
                  setPaciente(id ? { id, nombre: p?.nombre_completo ?? `Paciente ${id}` } : null);
                  setGuardadoEn(null);
                }}
              />
              <Paragraph type="secondary" className="ia-sin-margen">
                {paciente ? 'El análisis quedará en su historial.' : 'Sin paciente se analiza pero no se guarda.'}
              </Paragraph>
            </div>
            {tarea !== 'ovario-pco' && (
              <div>
                <Text>Milímetros por píxel (opcional)</Text>
                <InputNumber
                  aria-label="Milímetros por píxel"
                  style={{ width: '100%', marginTop: 4 }}
                  min={0.01} max={2} step={0.01} value={pixel}
                  onChange={(v) => setPixel(v)}
                  placeholder="Del ecógrafo o del DICOM; sin él, la medida sale en píxeles"
                />
              </div>
            )}
            <Button type="primary" block loading={analizando} disabled={!archivo} onClick={analizar}>
              Analizar
            </Button>
          </Space>
        </Card>
      </Col>

      <Col xs={24} lg={14}>
        {!resultado ? (
          <Card>
            <Paragraph type="secondary" style={{ margin: 0 }}>
              Elija el tipo de análisis y una imagen. El resultado es un apoyo: la conducta la decide el especialista.
            </Paragraph>
          </Card>
        ) : (
          <Card title="Resultado">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              {guardadoEn && <Alert type="success" showIcon message={`Guardado en el historial de ${guardadoEn}`} />}
              {resultado.malignidad && (
                <Alert
                  // Sin alarma no es «verde»: la red no detecta todos los carcinomas.
                  type={resultado.malignidad.alarma ? 'error' : 'info'}
                  showIcon
                  message={resultado.malignidad.alarma
                    ? 'Alarma: rasgos compatibles con carcinoma seroso de alto grado'
                    : 'Sin alarma de malignidad (no la descarta)'}
                  description={`Probabilidad ${pct(resultado.malignidad.probabilidad)} (alarma desde ${pct(resultado.malignidad.umbral)}). `
                    + `En pacientes que la red no vio: detectó el ${pct(resultado.malignidad.sensibilidad_medida)} de los carcinomas, `
                    + `con ${pct(resultado.malignidad.especificidad_medida)} de especificidad.`}
                />
              )}
              {resultado.hallazgos.map((h) => <Alert key={h} type="warning" showIcon message={h} />)}

              {(resultado.tipo_probable || resultado.categoria_probable) && (
                <div>
                  <Text type="secondary">{resultado.tipo_probable ? 'Tipo probable' : 'Categoría probable'}</Text>
                  <div><Tag color="blue" style={{ fontSize: 15, padding: '4px 10px' }}>
                    {resultado.tipo_probable ?? resultado.categoria_probable}
                  </Tag></div>
                  <Space direction="vertical" style={{ width: '100%', marginTop: 8 }}>
                    {resultado.probabilidades?.map((p) => (
                      <div key={p.tipo ?? p.categoria}>
                        <Text>{p.tipo ?? p.categoria}</Text>
                        <Progress percent={Math.round(p.probabilidad * 1000) / 10} size="small" />
                      </div>
                    ))}
                  </Space>
                </div>
              )}

              {resultado.mioma_ubicado === false && (
                <Alert type="info" showIcon message="La red no ubicó un mioma en esta imagen. Eso no descarta que lo haya." />
              )}
              {resultado.lesion_encontrada === false && (
                <Alert type="info" showIcon message="La red no encontró una lesión: el tipo se calculó con la imagen entera." />
              )}

              {medidas.length > 0 && (
                <Descriptions size="small" column={{ xs: 1, sm: 2 }} bordered>
                  {medidas.map(([k, v]) => (
                    <Descriptions.Item key={k} label={ETIQUETAS_MEDIDA[k]}>{String(v)}</Descriptions.Item>
                  ))}
                </Descriptions>
              )}

              <Row gutter={8}>
                {vistaPrevia && <Col span={12}><Text type="secondary">Original</Text><Image src={vistaPrevia} alt="Ecografía original" /></Col>}
                {resultado.superposicion_url && (
                  <Col span={12}>
                    <Text type="secondary">Lo que vio la red</Text>
                    <Image src={urlMedia(resultado.superposicion_url)} alt="Ecografía con la lesión dibujada" />
                  </Col>
                )}
              </Row>

              {resultado.avisos.map((a) => <Alert key={a} type="info" message={a} />)}

              <Text type="secondary">
                Redes usadas: {resultado.modelos.map((m) => m.archivo).join(', ')}
                {resultado.modelos[0]?.dataset ? ` · datos: ${resultado.modelos.map((m) => m.dataset).join(' · ')}` : ''}
              </Text>
            </Space>
          </Card>
        )}
      </Col>
    </Row>
  );
};

export default EcografiaGinecologica;
