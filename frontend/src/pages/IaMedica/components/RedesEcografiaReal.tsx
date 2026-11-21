import React, { useEffect, useState } from 'react';
import { Alert, Button, Card, Col, InputNumber, Progress, Row, Select, Space, Spin, Statistic, Tag, Upload } from 'antd';
import { ExperimentOutlined, InboxOutlined, ScanOutlined } from '@ant-design/icons';
import {
  iaMedicaService, InformeRedesMedidas, ResultadoAnomaliasCerebrales, ResultadoCircunferencia, ResultadoPlano,
} from '../../../services/iaMedicaService';
import { PacienteSelect } from '../../../components/clinico/SelectoresClinicos';
import { InformeAnalisisContenido } from './InformeAnalisisModal';
import '../IaMedica.css';

/**
 * Las redes entrenadas con ecografías reales anotadas por expertos.
 * «Analizar» muestra de una vez la vista del análisis y su resultado:
 * - de punta a punta (plano → U-Net de ese plano → medidas): cabeza (HC, DBP),
 *   tórax (índice cardiotorácico), abdomen (corte adecuado y CA por puntos) y
 *   fémur (LF por puntos), con la imagen y las estructuras que dibujó la red;
 * - plano anatómico (FETAL_PLANES_DB), cribado de anomalías cerebrales y, con el
 *   tamaño de píxel, circunferencia cefálica por regresión (HC18).
 * Con una paciente elegida, la imagen y el análisis quedan en su historial.
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
  /** Un análisis quedó en el historial de una paciente. */
  onGuardado?: () => void;
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

const RedesEcografiaReal: React.FC<RedesEcografiaRealProps> = ({ imagenes, onGuardado }) => {
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
  const [paciente, setPaciente] = useState<{ id: number; nombre: string } | null>(null);
  // Volver a analizar el mismo archivo no debe subir otra copia a su historial.
  const [imagenSubida, setImagenSubida] = useState<number | null>(null);
  const [guardadoEn, setGuardadoEn] = useState<string | null>(null);
  const [vistaPrevia, setVistaPrevia] = useState('');

  const guardadas = imagenes ?? [];
  const usaGuardadas = guardadas.length > 0;

  // La vista previa local del archivo se libera al cambiarla o al salir.
  useEffect(() => {
    if (!archivo) return undefined;
    const url = URL.createObjectURL(archivo);
    setVistaPrevia(url);
    return () => URL.revokeObjectURL(url);
  }, [archivo]);

  const limpiar = () => {
    setPlano(null); setCircunferencia(null); setAnomalias(null); setError(null); setInforme(null); setGuardadoEn(null);
  };
  const ficheroElegido = async (): Promise<File> =>
    (usaGuardadas ? descargarComoArchivo(guardadas[elegida]) : Promise.resolve(archivo as File));

  /** Deja la imagen en el historial de la paciente elegida y devuelve su id. */
  const guardarImagen = async (fichero: File): Promise<number | null> => {
    if (usaGuardadas || !paciente) return null;
    if (imagenSubida) return imagenSubida;
    const datos = new FormData();
    datos.append('imagen', fichero);
    datos.append('paciente', String(paciente.id));
    datos.append('tipo_imagen', 'eco_2d');
    const { id } = await iaMedicaService.uploadImagen(datos);
    setImagenSubida(id);
    return id;
  };

  const analizar = async () => {
    if (!archivo && !usaGuardadas) return;
    setAnalizando(true);
    limpiar();
    try {
      const fichero = await ficheroElegido();
      const idImagen = await guardarImagen(fichero);
      const [rInforme, rPlano, rCirc, rAnom] = await Promise.all([
        idImagen
          ? iaMedicaService.analyzeWithAI(undefined, String(idImagen), tamanoPixel)
          : iaMedicaService.analyzeWithAI(fichero, undefined, tamanoPixel),
        iaMedicaService.clasificarPlano(fichero),
        tamanoPixel ? iaMedicaService.medirCircunferencia(fichero, tamanoPixel) : Promise.resolve(null),
        // Si la red de anomalías no está instalada (503), el resto sigue valiendo.
        iaMedicaService.detectarAnomaliasCerebrales(fichero).catch(() => null),
      ]);
      setInforme(rInforme.ai_analysis);
      setPlano(rPlano);
      setCircunferencia(rCirc);
      setAnomalias(rAnom);
      if (rInforme.guardado && paciente) {
        setGuardadoEn(paciente.nombre);
        onGuardado?.();
      }
    } catch (e: any) {
      setError(mensajeDeError(e));
    } finally {
      setAnalizando(false);
    }
  };

  // Los del informe ya salen dentro de él.
  const avisos = [...new Set([...(plano?.avisos ?? []), ...(circunferencia?.avisos ?? []),
    ...(anomalias?.aplicable ? anomalias.avisos : [])])].filter((a) => !informe?.avisos.includes(a));
  const urlImagen = usaGuardadas ? guardadas[elegida]?.url : vistaPrevia;

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
              beforeUpload={(f) => { setArchivo(f); setImagenSubida(null); limpiar(); return false; }}
            >
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">{archivo ? archivo.name : 'Arrastre una ecografía o haga clic'}</p>
              <p className="ant-upload-hint">PNG, JPG o DICOM · máx. 10 MB</p>
            </Upload.Dragger>
          </div>
          )}
          {!usaGuardadas && (
            <div>
              <label htmlFor="analisis-paciente" className="ia-redes-etiqueta">Paciente</label>
              <PacienteSelect
                placeholder="Buscar paciente por nombre o CI"
                value={paciente?.id}
                onChange={(id, p) => {
                  setPaciente(id ? { id, nombre: p?.nombre_completo ?? `Paciente ${id}` } : null);
                  setImagenSubida(null);
                  setGuardadoEn(null);
                }}
              />
              <p className="ia-ayuda">
                {paciente ? 'El análisis quedará en su historial.' : 'Sin paciente se analiza pero no se guarda.'}
              </p>
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
            <Button type="primary" block icon={<ScanOutlined />} disabled={(!archivo && !usaGuardadas) || pixelInvalido}
              loading={analizando} onClick={analizar}>
              Analizar
            </Button>
          </Space>
        </Col>
        <Col xs={24} md={14} className="ia-redes-columna">
          {urlImagen ? (
            <img className="ia-vista-previa" src={urlImagen} alt="Ecografía elegida" />
          ) : (
            <p className="ia-texto-secundario">
              Reconoce el plano (abdomen, cerebro, fémur, tórax, cuello uterino u otro), dibuja las
              estructuras y mide; en los cortes de la cabeza busca anomalías cerebrales. Con el tamaño
              de píxel da las medidas en milímetros y la edad gestacional. Es apoyo a la decisión,
              no un diagnóstico.
            </p>
          )}
        </Col>
      </Row>
      <div className="ia-resultado" aria-live="polite">
        {analizando && <Spin tip="Analizando la imagen…"><div className="ia-resultado-espera" /></Spin>}
        {error && <Alert type="error" showIcon message="No se pudo analizar" description={error} />}
        {guardadoEn && <Alert type="success" showIcon message={`Guardado en el historial de ${guardadoEn}`} />}
        {informe && <InformeAnalisisContenido informe={informe} imagenUrl={urlImagen} detalleAparte />}
        {avisos.map((a) => <Alert key={a} type="warning" showIcon message={a} />)}
        {(plano || anomalias || circunferencia) && (
          <Row gutter={[16, 16]}>
            {plano && <Col xs={24} lg={12}><TarjetaPlano r={plano} /></Col>}
            {anomalias && <Col xs={24} lg={12}><TarjetaAnomalias r={anomalias} /></Col>}
            {circunferencia && <Col xs={24} lg={12}><TarjetaCircunferencia r={circunferencia} /></Col>}
          </Row>
        )}
      </div>
    </Card>
  );
};

export default RedesEcografiaReal;
