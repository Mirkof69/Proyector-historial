import React, { useState } from 'react';
import { Alert, Button, Card, Col, InputNumber, Progress, Row, Select, Statistic, Tag, Upload } from 'antd';
import { ExperimentOutlined, InboxOutlined } from '@ant-design/icons';
import {
  iaMedicaService, ResultadoCircunferencia, ResultadoPlano,
} from '../../../services/iaMedicaService';

/**
 * Las dos redes entrenadas con ecografías reales anotadas por expertos:
 * plano anatómico (FETAL_PLANES_DB) y circunferencia cefálica (HC18).
 * Cada resultado muestra al lado el error medido en madres que la red no vio.
 */

const mensajeDeError = (error: any): string =>
  error?.response?.data?.error || error?.message || 'Error desconocido';

const TarjetaPlano: React.FC<{ r: ResultadoPlano }> = ({ r }) => (
  <Card size="small" title="Plano anatómico">
    <Statistic title="La imagen muestra" value={r.plano} suffix={
      <Tag color={r.confianza >= 0.7 ? 'green' : 'orange'}>{Math.round(r.confianza * 100)}%</Tag>
    } />
    <div style={{ marginTop: 12, display: 'grid', gap: 4 }}>
      {Object.entries(r.probabilidades).map(([plano, p]) => (
        <div key={plano} style={{ display: 'grid', gridTemplateColumns: '11rem 1fr', alignItems: 'center', gap: 8 }}>
          <span>{plano}</span>
          <Progress percent={Math.round(p * 1000) / 10} size="small" showInfo />
        </div>
      ))}
    </div>
    <p style={{ marginTop: 12, marginBottom: 0, fontSize: 12, opacity: 0.75 }}>
      Acierta el {(r.modelo.metricas_prueba.exactitud * 100).toFixed(1)}% en{' '}
      {r.modelo.metricas_prueba.imagenes_prueba.toLocaleString('es-BO')} imágenes de{' '}
      {r.modelo.metricas_prueba.madres_prueba} madres que no vio al entrenar. {r.modelo.dataset}.
    </p>
  </Card>
);

const TarjetaCircunferencia: React.FC<{ r: ResultadoCircunferencia }> = ({ r }) => (
  <Card size="small" title="Circunferencia cefálica">
    <Row gutter={16}>
      <Col span={12}>
        <Statistic title="Circunferencia" value={r.circunferencia_cefalica_mm} precision={1}
          suffix={`mm ± ${r.margen_mm}`} />
      </Col>
      <Col span={12}>
        <Statistic title="Edad gestacional" value={r.edad_gestacional_semanas ?? '—'}
          precision={r.edad_gestacional_semanas === null ? undefined : 1} suffix="semanas" />
      </Col>
    </Row>
    <p style={{ marginTop: 12, marginBottom: 0, fontSize: 12, opacity: 0.75 }}>
      Error medio {r.modelo.metricas_prueba.error_medio_mm} mm (R²{' '}
      {r.modelo.metricas_prueba.r2}) en {r.modelo.metricas_prueba.imagenes_prueba} imágenes de{' '}
      {r.modelo.metricas_prueba.madres_prueba} madres que no vio. Edad: {r.formula_edad}.
    </p>
  </Card>
);

/** Una imagen ya guardada (p. ej. de la ficha de una ecografía). */
export interface ImagenGuardada {
  url: string;
  nombre: string;
}

interface RedesEcografiaRealProps {
  /** Si se pasan, se analizan estas imágenes en vez de pedir que se suba una. */
  imagenes?: ImagenGuardada[];
}

/** Descarga una imagen protegida de /media/ (con la cookie de sesión) como File. */
const descargarComoArchivo = async (img: ImagenGuardada): Promise<File> => {
  const respuesta = await fetch(img.url, { credentials: 'include' });
  if (!respuesta.ok) throw new Error(`No se pudo leer la imagen (HTTP ${respuesta.status})`);
  const blob = await respuesta.blob();
  // El nombre del archivo (con su extensión) sale de la URL: el servicio de IA
  // valida la extensión, y el título de la imagen no la tiene.
  const archivo = new URL(img.url, window.location.href).pathname.split('/').pop() || 'imagen.png';
  return new File([blob], archivo, { type: blob.type || 'image/png' });
};

const RedesEcografiaReal: React.FC<RedesEcografiaRealProps> = ({ imagenes }) => {
  const [archivo, setArchivo] = useState<File | null>(null);
  const [elegida, setElegida] = useState(0);
  const [tamanoPixel, setTamanoPixel] = useState<number | null>(null);
  const [plano, setPlano] = useState<ResultadoPlano | null>(null);
  const [circunferencia, setCircunferencia] = useState<ResultadoCircunferencia | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analizando, setAnalizando] = useState(false);

  const guardadas = imagenes ?? [];
  const usaGuardadas = guardadas.length > 0;

  const analizar = async () => {
    if (!archivo && !usaGuardadas) return;
    setAnalizando(true);
    setError(null);
    setPlano(null);
    setCircunferencia(null);
    try {
      const fichero = usaGuardadas ? await descargarComoArchivo(guardadas[elegida]) : (archivo as File);
      const [rPlano, rCirc] = await Promise.all([
        iaMedicaService.clasificarPlano(fichero),
        tamanoPixel ? iaMedicaService.medirCircunferencia(fichero, tamanoPixel) : Promise.resolve(null),
      ]);
      setPlano(rPlano);
      setCircunferencia(rCirc);
    } catch (e: any) {
      setError(mensajeDeError(e));
    } finally {
      setAnalizando(false);
    }
  };

  const avisos = [...(plano?.avisos ?? []), ...(circunferencia?.avisos ?? [])];

  return (
    <Card
      title={<span><ExperimentOutlined /> Redes entrenadas con ecografías reales</span>}
      style={{ marginBottom: 24 }}
    >
      <Row gutter={[16, 16]}>
        <Col xs={24} md={10} style={{ display: 'grid', gap: 12, alignContent: 'start' }}>
          {usaGuardadas ? (
            <div>
              <label htmlFor="imagen-guardada" style={{ display: 'block', marginBottom: 4 }}>Imagen de la ecografía</label>
              <Select id="imagen-guardada" value={elegida} style={{ width: '100%' }}
                onChange={(v) => { setElegida(v); setPlano(null); setCircunferencia(null); }}
                options={guardadas.map((g, i) => ({ value: i, label: g.nombre }))} />
            </div>
          ) : (
          <div>
            <Upload.Dragger
              accept=".png,.jpg,.jpeg,.bmp,.tif,.dcm,.dicom"
              maxCount={1}
              showUploadList={false}
              beforeUpload={(f) => { setArchivo(f); setPlano(null); setCircunferencia(null); return false; }}
            >
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">{archivo ? archivo.name : 'Arrastre una ecografía o haga clic'}</p>
              <p className="ant-upload-hint">PNG, JPG o DICOM · máx. 10 MB</p>
            </Upload.Dragger>
          </div>
          )}
          <div>
            <label htmlFor="tamano-pixel" style={{ display: 'block', marginBottom: 4 }}>
              Tamaño de píxel (mm) — solo para medir la cabeza
            </label>
            <InputNumber id="tamano-pixel" min={0.01} max={2} step={0.001} value={tamanoPixel}
              onChange={(v) => setTamanoPixel(v)} placeholder="p. ej. 0.128" style={{ width: '100%' }} />
            <p style={{ fontSize: 12, opacity: 0.75, margin: '4px 0 0' }}>
              Lo da el ecógrafo o la cabecera DICOM. Sin él solo se reconoce el plano.
            </p>
          </div>
          <Button type="primary" block disabled={!archivo && !usaGuardadas}
            loading={analizando} onClick={analizar}>
            Analizar
          </Button>
        </Col>
        <Col xs={24} md={14} style={{ display: 'grid', gap: 12, alignContent: 'start' }}>
          {error && <Alert type="error" showIcon message="No se pudo analizar" description={error} />}
          {avisos.map((a) => <Alert key={a} type="warning" showIcon message={a} />)}
          {plano && <TarjetaPlano r={plano} />}
          {circunferencia && <TarjetaCircunferencia r={circunferencia} />}
          {!plano && !error && (
            <p style={{ opacity: 0.75, margin: 0 }}>
              Reconoce el plano (abdomen, cerebro, fémur, tórax, cuello uterino u otro) y,
              si indica el tamaño de píxel, mide la circunferencia cefálica y calcula la edad
              gestacional. Es apoyo a la decisión, no un diagnóstico.
            </p>
          )}
        </Col>
      </Row>
    </Card>
  );
};

export default RedesEcografiaReal;
