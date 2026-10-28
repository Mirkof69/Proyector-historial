import React, { useEffect, useState } from 'react';
import { Alert, Button, Card, Col, InputNumber, Progress, Row, Select, Space, Statistic, Tag, Upload } from 'antd';
import { ExperimentOutlined, InboxOutlined, ScanOutlined } from '@ant-design/icons';
import {
  iaMedicaService, InformeRedesMedidas, ResultadoAnomaliasCerebrales, ResultadoCircunferencia, ResultadoPlano,
} from '../../../services/iaMedicaService';
import InformeAnalisisModal from './InformeAnalisisModal';
import '../IaMedica.css';

/**
 * Las redes entrenadas con ecografías reales anotadas por expertos.
 * - «Analizar»: plano anatómico (FETAL_PLANES_DB), cribado de anomalías
 *   cerebrales y, con el tamaño de píxel, circunferencia cefálica por regresión (HC18).
 * - «Informe completo»: el análisis de punta a punta (plano → U-Net de ese plano
 *   → medidas): cabeza (HC, DBP), tórax (índice cardiotorácico), abdomen (corte
 *   adecuado y CA por puntos) y fémur (LF por puntos). Antes este camino solo
 *   existía en la galería, después de elegir una paciente y subir la imagen.
 * Cada resultado muestra al lado el error medido en imágenes que la red no vio.
 */

const mensajeDeError = (error: any): string =>
  error?.response?.data?.error || error?.message || 'Error desconocido';

const TarjetaPlano: React.FC<{ r: ResultadoPlano }> = ({ r }) => (
  <Card size="small" title="Plano anatómico">
    <Statistic title="La imagen muestra" value={r.plano} suffix={
      <Tag color={r.confianza >= 0.7 ? 'success' : 'warning'}>{Math.round(r.confianza * 100)} %</Tag>
    } />
    <div className="ia-barras">
      {Object.entries(r.probabilidades).map(([plano, p]) => (
        <div key={plano} className="ia-barra">
          <span>{plano}</span>
          <Progress percent={Math.round(p * 1000) / 10} size="small" showInfo />
        </div>
      ))}
    </div>
    <p className="ia-nota-metrica">
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
    <p className="ia-nota-metrica">
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
        <p className="ia-sin-margen">
          No se analiza: la imagen no parece un corte axial de la cabeza. Si lo es (una malformación
          grave puede deformarla), la red no pudo evaluarla y el resultado no descarta nada.
        </p>
      ) : (
        <>
          <Statistic
            className={r.alarma_anomalia ? 'ia-valor-alarma' : undefined}
            title="Resultado"
            value={r.alarma_anomalia ? (r.familia_sospechada_nombre ?? 'Posible anomalía') : 'Sin alarma'}
            suffix={<Tag color={r.alarma_anomalia ? 'error' : 'default'}>
              P(anomalía) {pct(r.probabilidad_anomalia ?? 0)}
            </Tag>}
          />
          {!r.alarma_anomalia && (
            <p className="ia-ayuda">
              «Sin alarma» no descarta una anomalía: la sensibilidad en ecografías clínicas aún no está medida.
            </p>
          )}
          <div className="ia-barras">
            {Object.entries(r.probabilidades ?? {}).map(([familia, p]) => (
              <div key={familia} className="ia-barra">
                <span>{NOMBRE_FAMILIA[familia] ?? familia}</span>
                <Progress percent={Math.round(p * 1000) / 10} size="small" showInfo />
              </div>
            ))}
          </div>
        </>
      )}
      <p className="ia-nota-metrica">
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
  // Sin min/max en el InputNumber: 0 o -0,1 se cambiaban en silencio a 0,01 y
  // se medía con ese valor (BUG-011). Mismo rango que acepta el servicio de IA.
  const pixelInvalido = tamanoPixel !== null && !(tamanoPixel >= 0.01 && tamanoPixel <= 2);
  const [plano, setPlano] = useState<ResultadoPlano | null>(null);
  const [circunferencia, setCircunferencia] = useState<ResultadoCircunferencia | null>(null);
  const [anomalias, setAnomalias] = useState<ResultadoAnomaliasCerebrales | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analizando, setAnalizando] = useState(false);
  const [informe, setInforme] = useState<InformeRedesMedidas | null>(null);
  const [urlInforme, setUrlInforme] = useState('');
  const [analizandoCompleto, setAnalizandoCompleto] = useState(false);

  const guardadas = imagenes ?? [];
  const usaGuardadas = guardadas.length > 0;

  // La vista previa local del archivo se libera al cambiarla o al salir.
  useEffect(() => () => { if (urlInforme.startsWith('blob:')) URL.revokeObjectURL(urlInforme); }, [urlInforme]);

  const limpiar = () => { setPlano(null); setCircunferencia(null); setAnomalias(null); setError(null); };
  const ficheroElegido = async (): Promise<File> =>
    (usaGuardadas ? descargarComoArchivo(guardadas[elegida]) : Promise.resolve(archivo as File));

  const informeCompleto = async () => {
    if (!archivo && !usaGuardadas) return;
    setAnalizandoCompleto(true);
    setError(null);
    try {
      const fichero = await ficheroElegido();
      const r = await iaMedicaService.analyzeWithAI(fichero, undefined, tamanoPixel);
      setUrlInforme(usaGuardadas ? guardadas[elegida].url : URL.createObjectURL(fichero));
      setInforme(r.ai_analysis);
    } catch (e: any) {
      setError(mensajeDeError(e));
    } finally {
      setAnalizandoCompleto(false);
    }
  };

  const analizar = async () => {
    if (!archivo && !usaGuardadas) return;
    setAnalizando(true);
    limpiar();
    try {
      const fichero = await ficheroElegido();
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
    >
      <Row gutter={[16, 16]}>
        <Col xs={24} md={10} className="ia-redes-columna">
          {usaGuardadas ? (
            <div>
              <label htmlFor="imagen-guardada" className="ia-redes-etiqueta">Imagen de la ecografía</label>
              <Select id="imagen-guardada" value={elegida} className="ia-ancho-completo"
                onChange={(v) => { setElegida(v); limpiar(); }}
                options={guardadas.map((g, i) => ({ value: i, label: g.nombre }))} />
            </div>
          ) : (
          <div>
            <Upload.Dragger
              accept=".png,.jpg,.jpeg,.bmp,.tif,.dcm,.dicom"
              maxCount={1}
              showUploadList={false}
              beforeUpload={(f) => { setArchivo(f); limpiar(); return false; }}
            >
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">{archivo ? archivo.name : 'Arrastre una ecografía o haga clic'}</p>
              <p className="ant-upload-hint">PNG, JPG o DICOM · máx. 10 MB</p>
            </Upload.Dragger>
          </div>
          )}
          <div>
            <label htmlFor="tamano-pixel" className="ia-redes-etiqueta">
              Tamaño de píxel (mm) — para dar las medidas en milímetros
            </label>
            <InputNumber id="tamano-pixel" step={0.001} value={tamanoPixel}
              status={pixelInvalido ? 'error' : undefined} aria-invalid={pixelInvalido}
              aria-describedby="tamano-pixel-ayuda"
              onChange={(v) => setTamanoPixel(v)} placeholder="p. ej. 0.128" className="ia-ancho-completo" />
            {pixelInvalido ? (
              <p id="tamano-pixel-ayuda" className="ia-ayuda ia-ayuda--error" role="alert">
                El tamaño de píxel debe ser mayor que 0: entre 0,01 y 2 mm. Corríjalo o déjelo vacío.
              </p>
            ) : (
              <p id="tamano-pixel-ayuda" className="ia-ayuda">
                Lo da el ecógrafo o la cabecera DICOM. Sin él se reconoce el plano y las medidas salen en píxeles.
              </p>
            )}
          </div>
          <Space direction="vertical" className="ia-ancho-completo">
            <Button type="primary" block disabled={(!archivo && !usaGuardadas) || pixelInvalido}
              loading={analizando} onClick={analizar}>
              Analizar
            </Button>
            <Button block icon={<ScanOutlined />} disabled={(!archivo && !usaGuardadas) || pixelInvalido}
              loading={analizandoCompleto} onClick={informeCompleto}>
              Informe completo
            </Button>
            <p className="ia-ayuda">
              «Analizar»: plano, cribado cerebral y circunferencia cefálica. «Informe completo»: la red del
              plano dibuja las estructuras y mide (cabeza, tórax, abdomen o fémur).
            </p>
          </Space>
        </Col>
        <Col xs={24} md={14} className="ia-redes-columna">
          {error && <Alert type="error" showIcon message="No se pudo analizar" description={error} />}
          {avisos.map((a) => <Alert key={a} type="warning" showIcon message={a} />)}
          {plano && <TarjetaPlano r={plano} />}
          {anomalias && <TarjetaAnomalias r={anomalias} />}
          {circunferencia && <TarjetaCircunferencia r={circunferencia} />}
          {!plano && !error && (
            <p className="ia-texto-secundario">
              Reconoce el plano (abdomen, cerebro, fémur, tórax, cuello uterino u otro); en
              los cortes de la cabeza busca anomalías cerebrales y, si indica el tamaño de
              píxel, mide la circunferencia cefálica y calcula la edad gestacional. Es apoyo
              a la decisión, no un diagnóstico.
            </p>
          )}
        </Col>
      </Row>
      <InformeAnalisisModal
        abierto={!!informe}
        informe={informe}
        imagenUrl={urlInforme}
        onCerrar={() => setInforme(null)}
      />
    </Card>
  );
};

export default RedesEcografiaReal;
