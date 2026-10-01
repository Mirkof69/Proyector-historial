import React from 'react';
import {
  Card, Descriptions, Space, Tag, Alert, Row, Col, Timeline, Typography,
  Badge, Statistic, Collapse, Tabs, Empty,
} from 'antd';
import {
  MedicineBoxOutlined, CalendarOutlined, ClockCircleOutlined, UserOutlined,
  HeartOutlined, CheckCircleOutlined, ExclamationCircleOutlined, InfoCircleOutlined,
  WarningOutlined, SmileOutlined, FileTextOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Parto } from '../../../services/partosService';
import { Paciente } from '../../../services/pacientesService';
import { getViaPartoColor, getApgarInterpretacion } from '../detallePartoUtils';

const { Title, Text, Paragraph } = Typography;

interface DetallePartoViewProps {
  parto: Parto;
  paciente: Paciente | null;
  rn: any;
  duracionTP: string | null;
  categoriaEG: { text: string; color: string } | null;
  apgar5Interpretacion: { text: string; color: string; icon: React.ReactNode };
}

const COLOR_ALERTA: Record<string, string> = { success: 'var(--color-success, #52c41a)', warning: 'var(--color-warning, #faad14)', error: 'var(--color-error, #ff4d4f)' };

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
      <Space direction="vertical" style={{ width: '100%' }}>
        <Title level={2} style={{ margin: 0, color: COLOR_ALERTA[interpretacion.color] }}>{valor}</Title>
        <Alert message={interpretacion.text} type={interpretacion.color as any} showIcon icon={interpretacion.icon} />
      </Space>
    </Card>
  );
};

const textoTipoParto = (tipo?: string) => tipo?.replace(/_/g, ' ').toUpperCase();
/** «alojamiento_conjunto» → «Alojamiento conjunto». */
const legible = (valor?: string | null) => (valor ? valor.charAt(0).toUpperCase() + valor.slice(1).replace(/_/g, ' ') : '');

const RecienNacidoCard: React.FC<{ rn: any; indice: number; total: number }> = ({ rn, indice, total }) => (
  <Card
    title={
      <Space>
        <SmileOutlined />
        {total > 1 ? `Recién nacido ${rn.numero_gemelo || indice + 1} de ${total}` : 'Recién nacido'}
        {rn.sexo && <Tag>{rn.sexo === 'masculino' ? 'Masculino' : rn.sexo === 'femenino' ? 'Femenino' : rn.sexo}</Tag>}
        {rn.estado_nacimiento && <Tag color={rn.estado_nacimiento === 'vivo' ? 'green' : 'red'}>{legible(rn.estado_nacimiento)}</Tag>}
      </Space>
    }
    style={{ marginBottom: 16 }}
  >
    <Descriptions column={{ xs: 1, sm: 2, xl: 3 }} layout="vertical" bordered size="small" style={{ marginBottom: 16 }}>
      <Descriptions.Item label="Peso">
        {rn.peso_nacimiento ? <Space>{rn.peso_nacimiento} g{rn.clasificacion_peso && <Tag>{String(rn.clasificacion_peso).replace(/[^\p{L}\p{N}\s()<>≥≤.,-]/gu, '').trim()}</Tag>}</Space> : 'No registrado'}
      </Descriptions.Item>
      <Descriptions.Item label="Talla">{rn.talla_nacimiento ? `${rn.talla_nacimiento} cm` : 'No registrada'}</Descriptions.Item>
      <Descriptions.Item label="Perímetro cefálico">{rn.perimetro_cefalico ? `${rn.perimetro_cefalico} cm` : 'No registrado'}</Descriptions.Item>
      <Descriptions.Item label="Reanimación">
        {rn.requirio_reanimacion ? <Tag color="orange">Sí{rn.tipo_reanimacion ? ` · ${legible(rn.tipo_reanimacion)}` : ''}</Tag> : 'No'}
      </Descriptions.Item>
      <Descriptions.Item label="Malformaciones">
        {rn.malformaciones_congenitas ? <Tag color="red">{rn.descripcion_malformaciones || 'Sí'}</Tag> : 'No'}
      </Descriptions.Item>
      <Descriptions.Item label="Destino">{legible(rn.destino_rn) || '—'}</Descriptions.Item>
    </Descriptions>
    <Row gutter={[16, 16]}>
      <Col xs={24} md={8}><Apgar titulo="Apgar al minuto" valor={rn.apgar_1_minuto} /></Col>
      <Col xs={24} md={8}><Apgar titulo="Apgar a los 5 minutos" valor={rn.apgar_5_minutos} /></Col>
      <Col xs={24} md={8}><Apgar titulo="Apgar a los 10 minutos" valor={rn.apgar_10_minutos} /></Col>
    </Row>
    {rn.complicaciones_neonatales && (
      <Alert style={{ marginTop: 16 }} type="warning" showIcon message="Complicaciones neonatales"
        description={<Paragraph style={{ margin: 0 }}>{rn.complicaciones_neonatales}</Paragraph>} />
    )}
    {rn.observaciones_rn && <Paragraph style={{ marginTop: 16, marginBottom: 0 }}>{rn.observaciones_rn}</Paragraph>}
  </Card>
);

/**
 * Detalle del parto en pestañas. Antes era una sola página larga que además
 * mostraba solo el PRIMER recién nacido (en un parto gemelar el segundo no
 * aparecía), un Apgar faltante como 0 y el médico como «ID: 5».
 */
const DetallePartoView: React.FC<DetallePartoViewProps> = ({
  parto, paciente, rn, duracionTP, categoriaEG, apgar5Interpretacion,
}) => {
  const recienNacidos: any[] = parto.recien_nacidos?.length ? parto.recien_nacidos : (rn ? [rn] : []);
  const medico = (parto as any).medico_responsable_info?.nombre;
  const alertas = parto.alertas_parto ?? [];
  const recomendaciones = parto.recomendaciones_por_edad ?? [];
  const complicacionesNeonatales = recienNacidos.filter((r) => r.complicaciones_neonatales);
  const apgar5 = rn?.apgar_5_minutos ?? parto.apgar_5min;

  const resumen = (
    <>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="Tipo de parto" value={textoTipoParto(parto.tipo_parto)} valueStyle={{ fontSize: 16 }}
              prefix={<Tag color={getViaPartoColor(parto.tipo_parto || '')}>{parto.tipo_parto?.split('_')[0].toUpperCase()}</Tag>} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="Presentación" value={parto.presentacion_fetal?.toUpperCase() || '—'} valueStyle={{ fontSize: 16 }} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="Duración del trabajo de parto" value={duracionTP || 'No registrado'}
              valueStyle={{ fontSize: 18 }} prefix={<ClockCircleOutlined />} />
          </Card>
        </Col>
      </Row>

      {paciente && (
        <Card title={<Space><UserOutlined />Paciente</Space>} style={{ marginBottom: 16 }}>
          <Descriptions column={{ xs: 1, sm: 3 }} bordered size="small">
            <Descriptions.Item label="Nombre">
              <Text strong>{paciente.nombre} {paciente.apellido_paterno} {paciente.apellido_materno}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="ID clínico"><Tag color="blue">{paciente.id_clinico}</Tag></Descriptions.Item>
            <Descriptions.Item label="CI">{paciente.ci}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      <Card title={<Space><MedicineBoxOutlined />Datos del parto</Space>}>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered size="small">
          <Descriptions.Item label="Fecha y hora">
            <Space><CalendarOutlined />{dayjs(parto.fecha_parto).format('DD/MM/YYYY HH:mm')}</Space>
          </Descriptions.Item>
          <Descriptions.Item label="Edad gestacional">
            <Space>{parto.edad_gestacional_parto || '—'}{categoriaEG && <Tag color={categoriaEG.color}>{categoriaEG.text}</Tag>}</Space>
          </Descriptions.Item>
          <Descriptions.Item label="Médico responsable">{medico || 'No registrado'}</Descriptions.Item>
          <Descriptions.Item label="N.º de parto">{(parto as any).numero_parto || '—'}</Descriptions.Item>
          {parto.fecha_inicio_trabajo_parto && (
            <Descriptions.Item label="Inicio del trabajo de parto">
              {dayjs(parto.fecha_inicio_trabajo_parto).format('DD/MM/YYYY HH:mm')}
            </Descriptions.Item>
          )}
          {parto.estado_membranas && (
            <Descriptions.Item label="Membranas">{legible(parto.estado_membranas)}</Descriptions.Item>
          )}
          {parto.caracteristicas_liquido && (
            <Descriptions.Item label="Líquido amniótico">{parto.caracteristicas_liquido}</Descriptions.Item>
          )}
          {parto.tipo_alumbramiento && (
            <Descriptions.Item label="Alumbramiento">{legible(parto.tipo_alumbramiento)}</Descriptions.Item>
          )}
        </Descriptions>
      </Card>
    </>
  );

  const alertasYRecomendaciones = (
    <>
      {alertas.length === 0 && recomendaciones.length === 0 && (
        <Empty description="Sin alertas ni recomendaciones para este parto" />
      )}
      {alertas.length > 0 && (
        <Card
          title={<Space><WarningOutlined />Alertas médicas
            {parto.tiene_alertas_criticas && <Badge count="CRÍTICO" style={{ backgroundColor: 'var(--color-error, #f5222d)' }} />}</Space>}
          style={{ marginBottom: 16 }}
        >
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            {alertas.map((alerta: any) => (
              <Alert key={alerta.tipo + alerta.mensaje} message={alerta.mensaje}
                description={alerta.recomendacion && <div><strong>Recomendación:</strong> {alerta.recomendacion}</div>}
                type={alerta.nivel === 'error' ? 'error' : 'warning'} showIcon
                icon={alerta.tipo === 'critica' ? <ExclamationCircleOutlined /> : <WarningOutlined />} />
            ))}
          </Space>
          {parto.tipo_parto_segun_edad && (
            <Alert message={parto.tipo_parto_segun_edad.descripcion} type="info" showIcon style={{ marginTop: 16 }} />
          )}
        </Card>
      )}
      {recomendaciones.length > 0 && (
        <Card title={<Space><InfoCircleOutlined />Recomendaciones por edad gestacional</Space>}>
          <Alert message="Recomendaciones generales según la edad gestacional; las decide el médico tratante."
            type="info" showIcon style={{ marginBottom: 16 }} />
          <Collapse accordion defaultActiveKey={['0']}
            items={recomendaciones.map((rec: any) => ({
              key: rec.id || rec.periodo,
              label: <Space>{['urgente', 'atencion'].includes(rec.tipo) ? <WarningOutlined /> : <InfoCircleOutlined />}
                <strong>{rec.periodo}:</strong> {rec.titulo}</Space>,
              children: (
                <Alert
                  type={rec.tipo === 'urgente' ? 'error' : ['atencion', 'importante'].includes(rec.tipo) ? 'warning' : 'info'}
                  message={rec.titulo} showIcon
                  description={<ul style={{ marginBottom: 0, paddingLeft: 20 }}>
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
        <Alert type="error" showIcon message="Complicaciones maternas" style={{ marginBottom: 16 }}
          description={<Paragraph style={{ margin: 0 }}>{parto.complicaciones_maternas}</Paragraph>} />
      )}
      {complicacionesNeonatales.map((r, i) => (
        <Alert key={r.id ?? i} type="warning" showIcon style={{ marginBottom: 16 }}
          message={`Complicaciones neonatales${recienNacidos.length > 1 ? ` (recién nacido ${r.numero_gemelo || i + 1})` : ''}`}
          description={<Paragraph style={{ margin: 0 }}>{r.complicaciones_neonatales}</Paragraph>} />
      ))}
      {parto.observaciones_parto && (
        <Card title={<Space><FileTextOutlined />Observaciones</Space>}>
          <Paragraph style={{ margin: 0 }}>{parto.observaciones_parto}</Paragraph>
        </Card>
      )}
    </>
  );

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={16}>
        <Tabs
          defaultActiveKey="resumen"
          items={[
            { key: 'resumen', label: 'Resumen', children: resumen },
            {
              key: 'recien-nacidos',
              label: `Recién nacido${recienNacidos.length > 1 ? `s (${recienNacidos.length})` : ''}`,
              children: recienNacidos.length
                ? recienNacidos.map((r, i) => <RecienNacidoCard key={r.id ?? i} rn={r} indice={i} total={recienNacidos.length} />)
                : <Empty description="No hay recién nacidos registrados en este parto" />,
            },
            {
              key: 'alertas',
              label: <Space size={4}>Alertas y recomendaciones{alertas.length > 0 && <Badge count={alertas.length} />}</Space>,
              children: alertasYRecomendaciones,
            },
            {
              key: 'complicaciones',
              label: <Space size={4}>Complicaciones y notas
                {(parto.complicaciones_maternas || complicacionesNeonatales.length > 0) && <Badge status="error" />}</Space>,
              children: complicaciones,
            },
          ]}
        />
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
                color: 'purple', dot: <SmileOutlined />,
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
