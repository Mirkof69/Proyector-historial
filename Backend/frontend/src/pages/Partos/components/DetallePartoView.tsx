import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Card, Descriptions, Space, Tag, Alert, Row, Col, Timeline, Typography,
  Badge, Statistic, Collapse, Tabs, Empty, Button,
} from 'antd';
import {
  MedicineBoxOutlined, CalendarOutlined, ClockCircleOutlined, UserOutlined,
  HeartOutlined, CheckCircleOutlined, ExclamationCircleOutlined, InfoCircleOutlined,
  WarningOutlined, SmileOutlined, FileTextOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Parto } from '../../../services/partosService';
import { Paciente } from '../../../services/pacientesService';
import { Embarazo } from '../../../services/embarazosService';
import { useAuth } from '../../../hooks/useAuth';
import { getViaPartoColor, getApgarInterpretacion } from '../detallePartoUtils';
import PartogramaPanel from './PartogramaPanel';
import EpicrisisPanel from './EpicrisisPanel';
import EdadGestacionalRNModal from './EdadGestacionalRNModal';

const { Title, Text, Paragraph } = Typography;

interface DetallePartoViewProps {
  parto: Parto;
  paciente: Paciente | null;
  embarazo?: Embarazo | null;
  rn: any;
  duracionTP: string | null;
  categoriaEG: { text: string; color: string } | null;
  apgar5Interpretacion: { text: string; color: string; icon: React.ReactNode };
}


/**
 * Apgar mostrado sin inventar: si no se registró dice «No registrado».
 * Antes se usaba `|| 0` y un Apgar faltante aparecía como 0, que en clínica
 * significa un recién nacido sin signos vitales.
 */
const Apgar: React.FC<{ titulo: string; valor: number | null | undefined }> = ({ titulo, valor }) => {
  if (valor === null || valor === undefined) {
    return (
      <Card type="inner" title={titulo}>
        <Text type="secondary">No registrado</Text>
      </Card>
    );
  }
  const interpretacion = getApgarInterpretacion(valor);
  return (
    <Card type="inner" title={titulo}>
      <Space direction="vertical" className="partos-ancho">
        <Title level={2} className={`partos-apgar partos-apgar--${interpretacion.color}`}>{valor}</Title>
        <Alert message={interpretacion.text} type={interpretacion.color as any} showIcon icon={interpretacion.icon} />
      </Space>
    </Card>
  );
};

const textoTipoParto = (tipo?: string) => tipo?.replace(/_/g, ' ').toUpperCase();
/** «alojamiento_conjunto» → «Alojamiento conjunto». */
const legible = (valor?: string | null) => (valor ? valor.charAt(0).toUpperCase() + valor.slice(1).replace(/_/g, ' ') : '');

const CLASE_EG: Record<string, { texto: string; color: string }> = {
  pretermino: { texto: 'Pretérmino', color: 'warning' },
  termino: { texto: 'A término', color: 'success' },
  postermino: { texto: 'Postérmino', color: 'warning' },
};

const RecienNacidoCard: React.FC<{ rn: any; indice: number; total: number; onEvaluarEG?: () => void }> = ({
  rn, indice, total, onEvaluarEG,
}) => (
  <Card
    title={
      <Space>
        <SmileOutlined />
        {total > 1 ? `Recién nacido ${rn.numero_gemelo || indice + 1} de ${total}` : 'Recién nacido'}
        {rn.sexo && <Tag>{rn.sexo === 'masculino' ? 'Masculino' : rn.sexo === 'femenino' ? 'Femenino' : rn.sexo}</Tag>}
        {rn.estado_nacimiento && <Tag color={rn.estado_nacimiento === 'vivo' ? 'success' : 'error'}>{legible(rn.estado_nacimiento)}</Tag>}
      </Space>
    }
    className="partos-separado"
  >
    <Descriptions column={{ xs: 1, sm: 2, xl: 3 }} layout="vertical" bordered size="small" className="partos-separado">
      <Descriptions.Item label="Peso">
        {rn.peso_nacimiento ? <Space>{rn.peso_nacimiento} g{rn.clasificacion_peso && <Tag>{String(rn.clasificacion_peso).replace(/[^\p{L}\p{N}\s()<>≥≤.,-]/gu, '').trim()}</Tag>}</Space> : 'No registrado'}
      </Descriptions.Item>
      <Descriptions.Item label="Talla">{rn.talla_nacimiento ? `${rn.talla_nacimiento} cm` : 'No registrada'}</Descriptions.Item>
      <Descriptions.Item label="Perímetro cefálico">{rn.perimetro_cefalico ? `${rn.perimetro_cefalico} cm` : 'No registrado'}</Descriptions.Item>
      <Descriptions.Item label="Reanimación">
        {rn.requirio_reanimacion ? <Tag color="warning">Sí{rn.tipo_reanimacion ? ` · ${legible(rn.tipo_reanimacion)}` : ''}</Tag> : 'No'}
      </Descriptions.Item>
      <Descriptions.Item label="Malformaciones">
        {rn.malformaciones_congenitas ? <Tag color="error">{rn.descripcion_malformaciones || 'Sí'}</Tag> : 'No'}
      </Descriptions.Item>
      <Descriptions.Item label="Destino">{legible(rn.destino_rn) || '—'}</Descriptions.Item>
      <Descriptions.Item label="Edad gestacional por examen">
        {rn.edad_gestacional_examen_semanas ? (
          <Space wrap>
            {rn.edad_gestacional_examen_semanas} semanas
            <Tag>{rn.metodo_edad_gestacional === 'ballard' ? 'Ballard' : 'Capurro'}</Tag>
            {CLASE_EG[rn.clasificacion_edad_gestacional] && (
              <Tag color={CLASE_EG[rn.clasificacion_edad_gestacional].color}>{CLASE_EG[rn.clasificacion_edad_gestacional].texto}</Tag>
            )}
          </Space>
        ) : 'No evaluada'}
        {onEvaluarEG && rn.id && (
          <Button size="small" type="link" onClick={onEvaluarEG}>
            {rn.edad_gestacional_examen_semanas ? 'Cambiar' : 'Registrar Capurro / Ballard'}
          </Button>
        )}
      </Descriptions.Item>
    </Descriptions>
    <Row gutter={[16, 16]}>
      <Col xs={24} md={8}><Apgar titulo="Apgar al minuto" valor={rn.apgar_1_minuto} /></Col>
      <Col xs={24} md={8}><Apgar titulo="Apgar a los 5 minutos" valor={rn.apgar_5_minutos} /></Col>
      <Col xs={24} md={8}><Apgar titulo="Apgar a los 10 minutos" valor={rn.apgar_10_minutos} /></Col>
    </Row>
    {rn.complicaciones_neonatales && (
      <Alert className="partos-arriba" type="warning" showIcon message="Complicaciones neonatales"
        description={<Paragraph className="partos-sin-margen">{rn.complicaciones_neonatales}</Paragraph>} />
    )}
    {rn.observaciones_rn && <Paragraph className="partos-arriba partos-texto-pre">{rn.observaciones_rn}</Paragraph>}
  </Card>
);

/**
 * Detalle del parto en cinco pestañas, en el orden en que ocurre la atención:
 * admisión → trabajo de parto (con partograma) → recién nacidos (con Capurro o
 * Ballard) → alumbramiento y complicaciones → epicrisis (resumen de egreso).
 * La pestaña abierta queda en la URL (?pestana=), para volver al mismo lugar.
 */
const PESTANAS = ['admision', 'trabajo-parto', 'recien-nacidos', 'alumbramiento', 'epicrisis'];
const si = (v?: boolean | null) => (v === true ? 'Sí' : v === false ? 'No' : '—');

const DetallePartoView: React.FC<DetallePartoViewProps> = ({
  parto, paciente, embarazo, rn, duracionTP, categoriaEG, apgar5Interpretacion,
}) => {
  const { user } = useAuth();
  const puedeEditar = user?.rol === 'medico' || user?.rol === 'administrador';
  const [params, setParams] = useSearchParams();
  const pestana = PESTANAS.includes(params.get('pestana') || '') ? (params.get('pestana') as string) : 'admision';
  const [recienNacidos, setRecienNacidos] = useState<any[]>(
    parto.recien_nacidos?.length ? parto.recien_nacidos : (rn ? [rn] : []),
  );
  useEffect(() => {
    setRecienNacidos(parto.recien_nacidos?.length ? parto.recien_nacidos : (rn ? [rn] : []));
  }, [parto, rn]);
  const [evaluandoRN, setEvaluandoRN] = useState<any | null>(null);
  const p = parto as any;
  const medico = p.medico_responsable_info?.nombre;
  const alertas = parto.alertas_parto ?? [];
  const recomendaciones = parto.recomendaciones_por_edad ?? [];
  const complicacionesNeonatales = recienNacidos.filter((r) => r.complicaciones_neonatales);
  const apgar5 = rn?.apgar_5_minutos ?? parto.apgar_5min;
  const fecha = (v?: string | null) => (v ? dayjs(v).format('DD/MM/YYYY HH:mm') : '—');

  const admision = (
    <>
      {paciente && (
        <Card title={<Space><UserOutlined />Paciente</Space>} className="partos-separado">
          <Descriptions column={{ xs: 1, sm: 3 }} bordered size="small">
            <Descriptions.Item label="Nombre">
              <Text strong>{paciente.nombre} {paciente.apellido_paterno} {paciente.apellido_materno}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="ID clínico"><span className="texto-mono">{paciente.id_clinico}</span></Descriptions.Item>
            <Descriptions.Item label="CI">{paciente.ci}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
      <Card title={<Space><FileTextOutlined />Antecedentes obstétricos</Space>} className="partos-separado">
        {embarazo ? (
          <Descriptions column={{ xs: 1, md: 2 }} bordered size="small">
            <Descriptions.Item label="Fórmula obstétrica">
              G{embarazo.numero_gesta} P{embarazo.numero_para ?? 0} A{embarazo.numero_abortos ?? 0} C{embarazo.numero_cesareas ?? 0}
            </Descriptions.Item>
            <Descriptions.Item label="FUM">
              {embarazo.fecha_ultima_menstruacion ? dayjs(embarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY') : '—'}
            </Descriptions.Item>
            <Descriptions.Item label="Tipo de embarazo">{legible(embarazo.tipo_embarazo) || '—'}</Descriptions.Item>
            <Descriptions.Item label="Riesgo">
              {embarazo.riesgo_embarazo ? (
                <Tag color={['alto', 'muy_alto'].includes(String(embarazo.riesgo_embarazo)) ? 'error' : 'success'}>
                  {legible(String(embarazo.riesgo_embarazo))}
                </Tag>
              ) : '—'}
            </Descriptions.Item>
          </Descriptions>
        ) : <Text type="secondary">El parto no está vinculado a un embarazo registrado.</Text>}
      </Card>
      <Card title={<Space><MedicineBoxOutlined />Ingreso</Space>}>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered size="small">
          <Descriptions.Item label="Fecha de ingreso">{fecha(p.fecha_ingreso)}</Descriptions.Item>
          <Descriptions.Item label="Edad gestacional">
            <Space>{parto.edad_gestacional_parto || '—'}{categoriaEG && <Tag color={categoriaEG.color}>{categoriaEG.text}</Tag>}</Space>
          </Descriptions.Item>
          <Descriptions.Item label="Inicio del trabajo de parto">{fecha(parto.fecha_inicio_trabajo_parto)}</Descriptions.Item>
          <Descriptions.Item label="Inicio">
            {p.induccion_parto ? `Inducido${p.metodo_induccion ? ` (${legible(p.metodo_induccion)})` : ''}`
              : p.trabajo_parto_espontaneo === false ? 'No espontáneo' : 'Espontáneo'}
          </Descriptions.Item>
          <Descriptions.Item label="Membranas">{legible(parto.estado_membranas) || '—'}</Descriptions.Item>
          <Descriptions.Item label="Rotura de membranas">{fecha(p.hora_rotura_membranas)}</Descriptions.Item>
          <Descriptions.Item label="Líquido amniótico">{parto.caracteristicas_liquido || '—'}</Descriptions.Item>
          <Descriptions.Item label="Médico responsable">{medico || 'No registrado'}</Descriptions.Item>
          <Descriptions.Item label="N.º de parto">{p.numero_parto || '—'}</Descriptions.Item>
        </Descriptions>
      </Card>
    </>
  );

  const trabajoDeParto = (
    <>
      <div className="partos-page__cifras partos-page__cifras--texto partos-separado">
          <Card size="small">
            <Statistic title="Tipo de parto" value={textoTipoParto(parto.tipo_parto)}
              prefix={<Tag color={getViaPartoColor(parto.tipo_parto || '')}>{parto.tipo_parto?.split('_')[0].toUpperCase()}</Tag>} />
          </Card>
          <Card size="small">
            <Statistic title="Presentación / posición"
              value={`${parto.presentacion_fetal ? legible(parto.presentacion_fetal) : '—'}${p.posicion_fetal ? ` · ${legible(p.posicion_fetal)}` : ''}`} />
          </Card>
          <Card size="small">
            <Statistic title={<><ClockCircleOutlined />Duración del trabajo de parto</>} value={duracionTP || 'No registrado'} />
          </Card>
      </div>
      <Card className="partos-separado">
        <Descriptions column={{ xs: 1, md: 2 }} bordered size="small">
          <Descriptions.Item label="Fecha y hora del parto"><Space><CalendarOutlined />{fecha(parto.fecha_parto)}</Space></Descriptions.Item>
          <Descriptions.Item label="Período expulsivo">
            {p.duracion_periodo_expulsivo_minutos != null ? `${p.duracion_periodo_expulsivo_minutos} min` : '—'}
          </Descriptions.Item>
          <Descriptions.Item label="Monitoreo fetal continuo">{si(p.monitoreo_fetal_continuo)}</Descriptions.Item>
          <Descriptions.Item label="Analgesia">
            {p.analgesia_utilizada ? `Sí${p.tipo_analgesia ? ` (${legible(p.tipo_analgesia)})` : ''}` : 'No'}
          </Descriptions.Item>
          <Descriptions.Item label="Oxitocina">
            {p.oxitocina_utilizada ? `Sí${p.dosis_oxitocina ? ` · ${p.dosis_oxitocina}` : ''}` : 'No'}
          </Descriptions.Item>
          {p.indicaciones_cesarea && <Descriptions.Item label="Indicación de cesárea">{p.indicaciones_cesarea}</Descriptions.Item>}
        </Descriptions>
      </Card>
      <PartogramaPanel partoId={parto.id as number} inicioTrabajoParto={parto.fecha_inicio_trabajo_parto} puedeEditar={puedeEditar} />
    </>
  );

  const alumbramiento = (
    <Card title="Alumbramiento" className="partos-separado">
      <Descriptions column={{ xs: 1, md: 2 }} bordered size="small">
        <Descriptions.Item label="Tipo">{legible(parto.tipo_alumbramiento) || '—'}</Descriptions.Item>
        <Descriptions.Item label="Placenta completa">{si(p.placenta_completa)}</Descriptions.Item>
        <Descriptions.Item label="Peso de la placenta">{p.peso_placenta ? `${p.peso_placenta} g` : '—'}</Descriptions.Item>
        <Descriptions.Item label="Pérdida sanguínea">
          {p.perdida_sanguinea_estimada != null ? `${p.perdida_sanguinea_estimada} ml` : '—'}
        </Descriptions.Item>
        <Descriptions.Item label="Hemorragia posparto">{p.hemorragia_postparto ? <Tag color="error">Sí</Tag> : 'No'}</Descriptions.Item>
        <Descriptions.Item label="Episiotomía">{p.episiotomia ? `Sí${p.tipo_episiotomia ? ` (${p.tipo_episiotomia})` : ''}` : 'No'}</Descriptions.Item>
        <Descriptions.Item label="Desgarros">{p.desgarros ? `Sí${p.grado_desgarros ? ` · grado ${p.grado_desgarros}` : ''}` : 'No'}</Descriptions.Item>
        {p.otros_medicamentos && <Descriptions.Item label="Otros medicamentos">{p.otros_medicamentos}</Descriptions.Item>}
      </Descriptions>
    </Card>
  );

  const alertasYRecomendaciones = (
    <>
      {alertas.length === 0 && recomendaciones.length === 0 && (
        <Empty description="Sin alertas ni recomendaciones para este parto" />
      )}
      {alertas.length > 0 && (
        <Card
          title={<Space><WarningOutlined />Alertas médicas
            {parto.tiene_alertas_criticas && <Badge className="partos-critico" count="CRÍTICO" />}</Space>}
          className="partos-separado"
        >
          <Space direction="vertical" className="partos-ancho" size="middle">
            {alertas.map((alerta: any) => (
              <Alert key={alerta.tipo + alerta.mensaje} message={alerta.mensaje}
                description={alerta.recomendacion && <div><strong>Recomendación:</strong> {alerta.recomendacion}</div>}
                type={alerta.nivel === 'error' ? 'error' : 'warning'} showIcon
                icon={alerta.tipo === 'critica' ? <ExclamationCircleOutlined /> : <WarningOutlined />} />
            ))}
          </Space>
          {parto.tipo_parto_segun_edad && (
            <Alert message={parto.tipo_parto_segun_edad.descripcion} type="info" showIcon className="partos-arriba" />
          )}
        </Card>
      )}
      {recomendaciones.length > 0 && (
        <Card title={<Space><InfoCircleOutlined />Recomendaciones por edad gestacional</Space>}>
          <Alert message="Recomendaciones generales según la edad gestacional; las decide el médico tratante."
            type="info" showIcon className="partos-separado" />
          <Collapse accordion defaultActiveKey={['0']}
            items={recomendaciones.map((rec: any) => ({
              key: rec.id || rec.periodo,
              label: <Space>{['urgente', 'atencion'].includes(rec.tipo) ? <WarningOutlined /> : <InfoCircleOutlined />}
                <strong>{rec.periodo}:</strong> {rec.titulo}</Space>,
              children: (
                <Alert
                  type={rec.tipo === 'urgente' ? 'error' : ['atencion', 'importante'].includes(rec.tipo) ? 'warning' : 'info'}
                  message={rec.titulo} showIcon
                  description={<ul className="partos-lista">
                    {rec.recomendaciones.map((r: string) => <li key={`${rec.periodo}-${r}`}>{r}</li>)}
                  </ul>}
                />
              ),
            }))}
          />
        </Card>
      )}
    </>
  );

  const complicaciones = (
    <>
      {!parto.complicaciones_maternas && complicacionesNeonatales.length === 0 && !parto.observaciones_parto && (
        <Empty description="Sin complicaciones ni observaciones registradas" />
      )}
      {parto.complicaciones_maternas && (
        <Alert type="error" showIcon message="Complicaciones maternas" className="partos-separado"
          description={<Paragraph className="partos-sin-margen">{parto.complicaciones_maternas}</Paragraph>} />
      )}
      {complicacionesNeonatales.map((r, i) => (
        <Alert key={r.id ?? i} type="warning" showIcon className="partos-separado"
          message={`Complicaciones neonatales${recienNacidos.length > 1 ? ` (recién nacido ${r.numero_gemelo || i + 1})` : ''}`}
          description={<Paragraph className="partos-sin-margen">{r.complicaciones_neonatales}</Paragraph>} />
      ))}
      {parto.observaciones_parto && (
        <Card title={<Space><FileTextOutlined />Observaciones</Space>}>
          <Paragraph className="partos-sin-margen">{parto.observaciones_parto}</Paragraph>
        </Card>
      )}
    </>
  );

  const cambiarPestana = (clave: string) => {
    const nuevos = new URLSearchParams(params);
    nuevos.set('pestana', clave);
    setParams(nuevos, { replace: true });
  };

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={16}>
        <Tabs
          activeKey={pestana}
          onChange={cambiarPestana}
          items={[
            { key: 'admision', label: 'Admisión', children: admision },
            { key: 'trabajo-parto', label: 'Trabajo de parto', children: trabajoDeParto },
            {
              key: 'recien-nacidos',
              label: `Recién nacido${recienNacidos.length > 1 ? `s (${recienNacidos.length})` : ''}`,
              children: recienNacidos.length
                ? recienNacidos.map((r, i) => (
                  <RecienNacidoCard key={r.id ?? i} rn={r} indice={i} total={recienNacidos.length}
                    onEvaluarEG={puedeEditar ? () => setEvaluandoRN(r) : undefined} />
                ))
                : <Empty description="No hay recién nacidos registrados en este parto" />,
            },
            {
              key: 'alumbramiento',
              label: (
                <Space size={4}>Alumbramiento y complicaciones
                  {(alertas.length > 0 || parto.complicaciones_maternas || complicacionesNeonatales.length > 0) && <Badge status="error" />}
                </Space>
              ),
              children: <>{alumbramiento}{complicaciones}<div className="partos-arriba">{alertasYRecomendaciones}</div></>,
            },
            { key: 'epicrisis', label: 'Epicrisis', children: <EpicrisisPanel partoId={parto.id as number} puedeEditar={puedeEditar} /> },
          ]}
        />
        {evaluandoRN && (
          <EdadGestacionalRNModal rn={evaluandoRN} abierto onCerrar={() => setEvaluandoRN(null)}
            onGuardado={(nuevo) => setRecienNacidos((lista) => lista.map((x) => (x.id === nuevo.id ? { ...x, ...nuevo } : x)))} />
        )}
      </Col>

      <Col xs={24} lg={8}>
        <Card title={<Space><InfoCircleOutlined />Resumen rápido</Space>}>
          <Timeline
            items={[
              {
                color: 'blue', dot: <CalendarOutlined />,
                children: <><Text strong>Fecha del parto</Text><br /><Text>{dayjs(parto.fecha_parto).format('DD/MM/YYYY HH:mm')}</Text></>,
              },
              {
                color: 'green', dot: <CheckCircleOutlined />,
                children: <><Text strong>Tipo de parto</Text><br />
                  <Tag color={getViaPartoColor(parto.tipo_parto || '')}>{textoTipoParto(parto.tipo_parto)}</Tag></>,
              },
              {
                color: 'gray', dot: <SmileOutlined />,
                children: <><Text strong>Recién nacido{recienNacidos.length > 1 ? 's' : ''}</Text><br />
                  {recienNacidos.length ? recienNacidos.map((r, i) => (
                    <div key={r.id ?? i}><Text>
                      {r.sexo === 'masculino' ? 'Masculino' : r.sexo === 'femenino' ? 'Femenino' : 'Sexo no registrado'}
                      {' · '}{r.peso_nacimiento ? `${r.peso_nacimiento} g` : 'peso no registrado'}
                    </Text></div>
                  )) : <Text>Sin datos</Text>}</>,
              },
              {
                color: apgar5 === null || apgar5 === undefined ? 'gray'
                  : apgar5Interpretacion.color === 'success' ? 'green' : apgar5Interpretacion.color === 'warning' ? 'orange' : 'red',
                dot: <HeartOutlined />,
                children: <><Text strong>Apgar 5 min</Text><br />
                  <Text>{apgar5 === null || apgar5 === undefined ? 'No registrado' : `${apgar5} · ${apgar5Interpretacion.text}`}</Text></>,
              },
            ]}
          />
        </Card>
      </Col>
    </Row>
  );
};

export default DetallePartoView;
