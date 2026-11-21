import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, Button, Card, Col, Row, Skeleton, Space, Tag, Typography } from 'antd';
import {
  ApartmentOutlined, AimOutlined, ArrowRightOutlined, BorderOuterOutlined, CloseCircleOutlined,
  ExperimentOutlined, ReadOutlined, TableOutlined,
} from '@ant-design/icons';
import { iaMedicaService, ModeloCatalogo, ModeloDescartado } from '../../services/iaMedicaService';
import { FICHAS, GRUPOS, NO_ES_IA, NOMBRE_RED, TipoRed } from './guiaContenido';
import './GuiaIA.css';

const { Title, Paragraph, Text } = Typography;

/** Un paso de un esquema «entrada → proceso → salida». */
const Flujo: React.FC<{ pasos: { titulo: string; detalle: string }[]; etiqueta: string }> = ({ pasos, etiqueta }) => (
  <ol className="guia-flujo" aria-label={etiqueta}>
    {pasos.map((p, i) => (
      <li key={p.titulo} className="guia-flujo-paso">
        <span className="guia-flujo-numero" aria-hidden="true">{i + 1}</span>
        <span>
          <Text strong>{p.titulo}</Text>
          <br />
          <Text type="secondary">{p.detalle}</Text>
        </span>
      </li>
    ))}
  </ol>
);

const ICONO_RED: Record<TipoRed, React.ReactNode> = {
  cnn: <ApartmentOutlined />, unet: <BorderOuterOutlined />, puntos: <AimOutlined />, tabla: <TableOutlined />,
};

const ComoFunciona: React.FC = () => (
  <section aria-labelledby="como-funciona" className="guia-seccion">
    <Title level={2} id="como-funciona" className="guia-titulo-seccion">Cómo funcionan</Title>
    <Paragraph className="guia-parrafo">
      Todos los modelos del sistema son <Text strong>supervisados</Text>: aprendieron de miles de ejemplos que un
      experto ya había etiquetado (por ejemplo, «este corte es un fémur», «este es el contorno del cráneo», «este
      registro es patológico»). Al entrenar, el modelo ajusta sus parámetros para equivocarse lo menos posible
      contra esas etiquetas. Después se lo mide en pacientes que nunca vio: esa medida es la que aparece en cada
      tarjeta.
    </Paragraph>
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card title={<Space>{ICONO_RED.cnn}{NOMBRE_RED.cnn}</Space>} className="guia-tarjeta">
          <Paragraph className="guia-parrafo">
            Mira la ecografía como lo haría alguien que aprende a leerla: primero detalles pequeños, luego formas,
            luego el conjunto. Cada capa pasa sobre la imagen unos «filtros» que se activan con un patrón; las
            primeras capas detectan bordes y texturas, las siguientes combinan esos bordes en formas (el óvalo del
            cráneo, la burbuja del estómago) y la última decide.
          </Paragraph>
          <Flujo etiqueta="Pasos de una red convolucional" pasos={[
            { titulo: 'Imagen', detalle: 'La ecografía en escala de grises.' },
            { titulo: 'Filtros', detalle: 'Bordes, texturas, ecos brillantes y zonas oscuras.' },
            { titulo: 'Rasgos', detalle: 'Formas anatómicas: cráneo, estómago, diáfisis del fémur.' },
            { titulo: 'Decisión', detalle: 'Plano, tipo de lesión o alarma, con su probabilidad.' },
          ]} />
        </Card>
      </Col>
      <Col xs={24} lg={12}>
        <Card title={<Space>{ICONO_RED.unet}{NOMBRE_RED.unet}</Space>} className="guia-tarjeta">
          <Paragraph className="guia-parrafo">
            Es una CNN que, en lugar de una sola respuesta, colorea cada píxel: «esto es cráneo», «esto es corazón».
            Primero comprime la imagen para entender qué hay y luego la vuelve a ampliar para dibujar el contorno
            exacto. Sobre ese contorno el sistema mide, en milímetros si conoce el tamaño del píxel. Usted ve el dibujo
            y puede comprobar de dónde salió cada medida.
          </Paragraph>
          <Flujo etiqueta="Pasos de una segmentación U-Net" pasos={[
            { titulo: 'Imagen', detalle: 'Un corte del plano correcto.' },
            { titulo: 'Contorno', detalle: 'La red dibuja cada estructura.' },
            { titulo: 'Medida', detalle: 'Elipse, diámetros o ángulo en mm o grados.' },
            { titulo: 'Fórmula', detalle: 'Edad gestacional o índice con la fórmula publicada.' },
          ]} />
        </Card>
      </Col>
      <Col xs={24} lg={12}>
        <Card title={<Space>{ICONO_RED.puntos}{NOMBRE_RED.puntos}</Space>} className="guia-tarjeta">
          <Paragraph className="guia-parrafo">
            Para el fémur y el abdomen no hace falta el contorno, sino dónde van los calibradores. La red produce un
            «mapa de calor» por cada punto (más brillante donde es más probable el extremo del hueso o del diámetro),
            el sistema toma el punto más probable y mide la distancia entre ellos, como lo haría el ecografista.
          </Paragraph>
          <Flujo etiqueta="Pasos de una red de puntos" pasos={[
            { titulo: 'Imagen', detalle: 'Corte del fémur o del abdomen.' },
            { titulo: 'Mapas de calor', detalle: 'Uno por calibrador.' },
            { titulo: 'Puntos', detalle: 'El lugar más probable de cada extremo.' },
            { titulo: 'Distancia', detalle: 'Longitud femoral o circunferencia abdominal.' },
          ]} />
        </Card>
      </Col>
      <Col xs={24} lg={12}>
        <Card title={<Space>{ICONO_RED.tabla}{NOMBRE_RED.tabla}</Space>} className="guia-tarjeta">
          <Paragraph className="guia-parrafo">
            La cardiotocografía no usa imagen: usa las cifras que calcula el monitor (línea de base, aceleraciones,
            desaceleraciones, variabilidad). El modelo es un <Text strong>gradient boosting</Text>: muchos árboles de
            decisión pequeños, del tipo «si la variabilidad es baja y hay desaceleraciones prolongadas…», donde cada
            árbol corrige los errores de los anteriores. Aprendió de registros clasificados por consenso de tres
            obstetras.
          </Paragraph>
          <Flujo etiqueta="Pasos del modelo de cardiotocografía" pasos={[
            { titulo: 'Variables', detalle: 'Las del informe automático del monitor.' },
            { titulo: 'Árboles', detalle: 'Cada uno suma o resta evidencia.' },
            { titulo: 'Clase', detalle: 'Normal, sospechosa o patológica, con probabilidades.' },
          ]} />
        </Card>
      </Col>
    </Row>
    <Alert
      type="info"
      showIcon
      message="Por qué no se usa aprendizaje no supervisado para decidir"
      description={(
        <>
          El aprendizaje no supervisado agrupa casos parecidos sin que nadie diga qué es cada grupo. Sirve para
          explorar datos, pero un grupo no es un diagnóstico y no hay contra qué medir cuánto acierta. Para apoyar
          una decisión clínica el sistema solo usa modelos que se pueden comparar con la etiqueta de un experto en
          pacientes que no vieron, y publica esa comparación.
        </>
      )}
    />
  </section>
);

interface TarjetaProps { modelo: ModeloCatalogo; onUsar: (ruta: string) => void }

const TarjetaModelo: React.FC<TarjetaProps> = ({ modelo, onUsar }) => {
  const ficha = FICHAS[modelo.codigo];
  return (
    <Card
      className="guia-tarjeta guia-modelo"
      title={<span className="guia-modelo-nombre">{modelo.nombre}</span>}
      extra={modelo.disponible ? <Tag color="success">En servicio</Tag> : <Tag>No disponible</Tag>}
      actions={ficha ? [
        <Button key="usar" type="link" icon={<ArrowRightOutlined />} aria-label={`Usar ahora: ${modelo.nombre}`}
          onClick={() => onUsar(ficha.donde.ruta)}>
          Usar ahora
        </Button>,
      ] : undefined}
    >
      <dl className="guia-datos">
        <dt>Tipo</dt>
        <dd>{ficha ? NOMBRE_RED[ficha.red] : modelo.tipo} · {modelo.tipo}</dd>
        {ficha && (<><dt>Qué hace</dt><dd>{ficha.queHace}</dd></>)}
        <dt>Fiabilidad medida</dt>
        <dd>
          {modelo.metrica_principal
            ? <Text className="guia-metrica">{modelo.metrica_principal}</Text>
            : <Text type="secondary">Sin cifra: el servicio de IA no respondió o la red no está instalada.</Text>}
          {modelo.datos && <><br /><Text type="secondary">Datos: {modelo.datos}{modelo.datos_reales ? '' : ' (simulados)'}</Text></>}
        </dd>
        {ficha && ficha.limites.length > 0 && (
          <>
            <dt>Límites</dt>
            <dd><ul className="guia-lista">{ficha.limites.map((l) => <li key={l}>{l}</li>)}</ul></dd>
          </>
        )}
        {ficha && (<><dt>Dónde se usa</dt><dd>{ficha.donde.pasos}</dd></>)}
      </dl>
    </Card>
  );
};

/**
 * Guía de IA para el personal clínico: qué es una CNN, una U-Net, una red de
 * puntos y un modelo supervisado de tabla; una tarjeta por modelo con su
 * fiabilidad MEDIDA y el botón que lleva a la pantalla donde se usa; y los
 * modelos que se evaluaron y se descartaron, con el motivo.
 *
 * Las cifras llegan de GET /api/ia/imagenes/modelos/ (ia_medica/services/
 * catalogo_modelos.py, que las lee de las métricas del entrenamiento). Si el
 * servicio no responde, la guía lo dice y no muestra ningún número.
 */
const GuiaIA: React.FC = () => {
  const navigate = useNavigate();
  const [modelos, setModelos] = useState<ModeloCatalogo[] | null>(null);
  const [descartados, setDescartados] = useState<ModeloDescartado[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    let vivo = true;
    iaMedicaService.getModelos()
      .then((r) => {
        if (!vivo) return;
        setModelos(r.modelos_builtin ?? []);
        setDescartados(r.modelos_descartados ?? []);
      })
      .catch(() => { if (vivo) { setError(true); setModelos([]); } });
    return () => { vivo = false; };
  }, []);

  const porGrupo = useMemo(() => {
    const lista = modelos ?? [];
    const grupos = GRUPOS.map((g) => ({ ...g, modelos: lista.filter((m) => FICHAS[m.codigo]?.grupo === g.clave) }));
    const otros = lista.filter((m) => !FICHAS[m.codigo]);
    return otros.length
      ? [...grupos, { clave: 'otros', titulo: 'Otros modelos', descripcion: 'Modelos nuevos aún sin ficha en la guía.', modelos: otros }]
      : grupos;
  }, [modelos]);

  return (
    <div className="guia-ia page-container">
      <header className="guia-encabezado">
        <div>
          <Title level={1} className="guia-titulo"><ReadOutlined /> Guía de IA</Title>
          <Paragraph className="guia-subtitulo">
            Qué hace cada modelo de inteligencia artificial del sistema, cuánto se le puede creer y dónde usarlo.
          </Paragraph>
        </div>
        <Button type="primary" icon={<ExperimentOutlined />} onClick={() => navigate('/dashboard/ia-medica/imagenes')}>
          Ir a Análisis CNN (IA)
        </Button>
      </header>

      <Alert
        type="warning"
        showIcon
        message="La IA apoya, no diagnostica"
        description="Cada resultado es una segunda opinión con su margen de error medido. La decisión clínica y la responsabilidad son del médico (Ley 3131)."
      />

      <nav aria-label="En esta página" className="guia-indice">
        <a href="#como-funciona">Cómo funcionan</a>
        <a href="#modelos">Modelos en servicio</a>
        <a href="#descartados">Evaluados y descartados</a>
        <a href="#no-es-ia">Lo que no es IA</a>
      </nav>

      <ComoFunciona />

      <section aria-labelledby="modelos" className="guia-seccion">
        <Title level={2} id="modelos" className="guia-titulo-seccion">Modelos en servicio</Title>
        <Paragraph className="guia-parrafo">
          «Fiabilidad medida» es el resultado en pacientes o registros que el modelo no vio al entrenar, tal como lo
          dejó el entrenamiento. Si una cifra cambia al reentrenar, cambia aquí sola.
        </Paragraph>
        {error && (
          <Alert type="error" showIcon message="No se pudo cargar la lista de modelos"
            description="Sin conexión con el servidor no se muestra ninguna cifra. Las explicaciones de arriba siguen valiendo." />
        )}
        {modelos === null ? <Skeleton active paragraph={{ rows: 6 }} /> : porGrupo.filter((g) => g.modelos.length).map((g) => (
          <div key={g.clave} className="guia-grupo">
            <Title level={3} className="guia-titulo-grupo">{g.titulo}</Title>
            <Paragraph type="secondary" className="guia-parrafo">{g.descripcion}</Paragraph>
            <Row gutter={[16, 16]}>
              {g.modelos.map((m) => (
                <Col xs={24} lg={12} key={m.codigo}><TarjetaModelo modelo={m} onUsar={navigate} /></Col>
              ))}
            </Row>
          </div>
        ))}
      </section>

      <section aria-labelledby="descartados" className="guia-seccion">
        <Title level={2} id="descartados" className="guia-titulo-seccion">Evaluados y descartados</Title>
        <Paragraph className="guia-parrafo">
          Se entrenaron y se midieron con datos reales, y no pasaron a servicio. No se pueden usar desde ninguna
          pantalla.
        </Paragraph>
        {modelos === null ? <Skeleton active /> : descartados.length === 0 ? (
          <Text type="secondary">No se pudo cargar la lista.</Text>
        ) : (
          <Row gutter={[16, 16]}>
            {descartados.map((d) => (
              <Col xs={24} md={12} xl={8} key={d.codigo}>
                <Card className="guia-tarjeta guia-descartado"
                  title={<span className="guia-modelo-nombre">{d.nombre}</span>}
                  extra={<Tag icon={<CloseCircleOutlined />}>Descartado</Tag>}>
                  <dl className="guia-datos">
                    <dt>Tipo</dt><dd>{d.tipo}</dd>
                    <dt>Datos</dt><dd>{d.datos}</dd>
                    <dt>Lo que se midió</dt><dd><Text className="guia-metrica">{d.metrica}</Text></dd>
                    <dt>Por qué se descartó</dt><dd>{d.motivo}</dd>
                  </dl>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </section>

      <section aria-labelledby="no-es-ia" className="guia-seccion">
        <Title level={2} id="no-es-ia" className="guia-titulo-seccion">Lo que no es IA</Title>
        <Row gutter={[16, 16]}>
          {NO_ES_IA.map((n) => (
            <Col xs={24} md={8} key={n.nombre}>
              <Card className="guia-tarjeta" title={<span className="guia-modelo-nombre">{n.nombre}</span>}
                actions={[<Button key="ir" type="link" onClick={() => navigate(n.ruta)}>Abrir</Button>]}>
                <Paragraph className="guia-parrafo">{n.que_es}</Paragraph>
              </Card>
            </Col>
          ))}
        </Row>
      </section>
    </div>
  );
};

export default GuiaIA;
