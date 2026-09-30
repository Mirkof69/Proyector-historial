import React, { useState } from 'react';
import { Alert, Button, Card, Col, InputNumber, Progress, Row, Select, Statistic, Tag, Upload } from 'antd';
import { ExperimentOutlined, InboxOutlined } from '@ant-design/icons';
import {
  iaMedicaService, ResultadoAnomaliasCerebrales, ResultadoCircunferencia, ResultadoPlano,
} from '../../../services/iaMedicaService';

/**
 * Las redes entrenadas con ecografías reales anotadas por expertos: plano
 * anatómico (FETAL_PLANES_DB), circunferencia cefálica (HC18) y cribado de
 * anomalías cerebrales. Cada resultado muestra al lado el error medido en
 * imágenes que la red no vio.
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

const pct = (v: number) => `${(v * 100).toFixed(1).replace('.', ',')} %`;

const NOMBRE_FAMILIA: Record<string, string> = {
  normal: 'Normal',
  ventriculomegalia_hidrocefalia: 'Ventriculomegalia / hidrocefalia',
  fosa_posterior: 'Fosa posterior',
  encefalocele: 'Encefalocele',
  lesion_quistica_vascular: 'Lesión quística o vascular',
};

const TarjetaAnomalias: React.FC<{ r: ResultadoAnomaliasCerebrales }> = ({ r }) => {
  const m = r.modelo.metricas_prueba;
  const hc = m.otro_hospital_hc18;
  return (
    <Card size="small" title="Cribado de anomalías cerebrales">
      {!r.aplicable ? (
        <p style={{ margin: 0 }}>
          No se analiza: la imagen no parece un corte axial de la cabeza. Si lo es (una malformación
          grave puede deformarla), la red no pudo evaluarla y el resultado no descarta nada.
        </p>
      ) : (
        <>
          <Statistic
            title="Resultado"
            value={r.alarma_anomalia ? (r.familia_sospechada_nombre ?? 'Posible anomalía') : 'Sin alarma'}
            valueStyle={{ color: r.alarma_anomalia ? 'var(--color-error, #b42318)' : undefined }}
            suffix={<Tag color={r.alarma_anomalia ? 'red' : 'default'}>
              P(anomalía) {pct(r.probabilidad_anomalia ?? 0)}
            </Tag>}
          />
          {!r.alarma_anomalia && (
            <p style={{ margin: '4px 0 0', fontSize: 12 }}>
              «Sin alarma» no descarta una anomalía: la sensibilidad en ecografías clínicas aún no está medida.
            </p>
          )}
          <div style={{ marginTop: 12, display: 'grid', gap: 4 }}>
            {Object.entries(r.probabilidades ?? {}).map(([familia, p]) => (
              <div key={familia} style={{ display: 'grid', gridTemplateColumns: '14rem 1fr', alignItems: 'center', gap: 8 }}>
                <span>{NOMBRE_FAMILIA[familia] ?? familia}</span>
                <Progress percent={Math.round(p * 1000) / 10} size="small" showInfo />
              </div>
            ))}
          </div>
        </>
      )}
      <p style={{ marginTop: 12, marginBottom: 0, fontSize: 12, opacity: 0.75 }}>
        Falsas alarmas medidas en cabezas normales que la red no vio:{' '}
        {hc && <>{pct(hc.valor)} en {hc.n.toLocaleString('es-BO')} de otro hospital (HC18) y </>}
        {pct(m.externa_falsos_positivos.valor)} en {m.externa_falsos_positivos.n.toLocaleString('es-BO')} de
        FETAL_PLANES. Entrenada con {m.n.anomalias} imágenes de anomalías de una compilación pública;
        su sensibilidad en ecografías clínicas no se puede medir aún con datos públicos. {r.uso}
      </p>
    </Card>
  );
};

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
  const [anomalias, setAnomalias] = useState<ResultadoAnomaliasCerebrales | null>(null);
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
    setAnomalias(null);
    try {
      const fichero = usaGuardadas ? await descargarComoArchivo(guardadas[elegida]) : (archivo as File);
      const [rPlano, rCirc, rAnom] = await Promise.all([
        iaMedicaService.clasificarPlano(fichero),
        tamanoPixel ? iaMedicaService.medirCircunferencia(fichero, tamanoPixel) : Promise.resolve(null),
        // Si la red de anomalías no está instalada (503), el resto sigue valiendo.
        iaMedicaService.detectarAnomaliasCerebrales(fichero).catch(() => null),
      ]);
      setPlano(rPlano);
      setCircunferencia(rCirc);
      setAnomalias(rAnom);
    } catch (e: any) {
      setError(mensajeDeError(e));
    } finally {
      setAnalizando(false);
    }
  };

  const avisos = [...new Set([...(plano?.avisos ?? []), ...(circunferencia?.avisos ?? []),
    ...(anomalias?.aplicable ? anomalias.avisos : [])])];

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
                onChange={(v) => { setElegida(v); setPlano(null); setCircunferencia(null); setAnomalias(null); }}
                options={guardadas.map((g, i) => ({ value: i, label: g.nombre }))} />
            </div>
          ) : (
          <div>
            <Upload.Dragger
              accept=".png,.jpg,.jpeg,.bmp,.tif,.dcm,.dicom"
              maxCount={1}
              showUploadList={false}
              beforeUpload={(f) => { setArchivo(f); setPlano(null); setCircunferencia(null); setAnomalias(null); return false; }}
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
          {anomalias && <TarjetaAnomalias r={anomalias} />}
          {circunferencia && <TarjetaCircunferencia r={circunferencia} />}
          {!plano && !error && (
            <p style={{ opacity: 0.75, margin: 0 }}>
              Reconoce el plano (abdomen, cerebro, fémur, tórax, cuello uterino u otro); en
              los cortes de la cabeza busca anomalías cerebrales y, si indica el tamaño de
              píxel, mide la circunferencia cefálica y calcula la edad gestacional. Es apoyo
              a la decisión, no un diagnóstico.
            </p>
          )}
        </Col>
      </Row>
    </Card>
  );
};

export default RedesEcografiaReal;
