import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert, Button, Card, Col, DatePicker, Empty, Form, Image, Input, InputNumber, Modal, Row, Select, Space, Table, Tag,
  Typography, Upload,
} from 'antd';
import { PlusOutlined, ReloadOutlined, FilePdfOutlined, ScanOutlined } from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import {
  CartesianGrid, Legend, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import {
  partoDetalleService, RegistroPartograma, MedidaAnguloProgresion, mensajeDeError,
} from '../../../services/partoDetalleService';
import { API_URL } from '../../../services/api';
import { curvaPartograma } from '../partogramaUtils';
import { descargarArchivo } from '../../../utils/descargarArchivo';
import { useAntdApp } from '../../../hooks/useMessage';

const { Text } = Typography;

interface Props {
  partoId: number;
  inicioTrabajoParto?: string | null;
  puedeEditar: boolean;
}

interface Formulario {
  hora_registro: Dayjs;
  dilatacion_cervical: number;
  borramiento_cervical?: number;
  angulo_progresion?: number;
  estacion_fetal: string;
  contracciones_10min: number;
  duracion_contracciones?: number;
  intensidad_contracciones?: string;
  fcf_baseline?: number;
  variabilidad_fcf?: string;
  desaceleraciones?: string;
  presion_arterial_sistolica?: number;
  presion_arterial_diastolica?: number;
  pulso_materno?: number;
  temperatura?: number;
  oxitocina_dosis?: string;
  observaciones?: string;
}

const ESTACIONES = ['-3', '-2', '-1', '0', '+1', '+2', '+3'];

/**
 * Partograma del parto: curva de dilatación con las líneas de alerta y acción
 * de la OMS, frecuencia cardíaca fetal con su rango normal (110–160 lpm) y la
 * tabla de tactos. Antes vivía en una pantalla aparte que pedía una URL que no
 * existe (/partos/{id}/partograma/) y leía campos que la API no envía: siempre
 * se veía vacía, y no había dónde registrar un tacto.
 */
const PartogramaPanel: React.FC<Props> = ({ partoId, inicioTrabajoParto, puedeEditar }) => {
  const { message } = useAntdApp();
  const [registros, setRegistros] = useState<RegistroPartograma[]>([]);
  const [cargando, setCargando] = useState(false);
  const [abierto, setAbierto] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [form] = Form.useForm<Formulario>();
  const [midiendo, setMidiendo] = useState(false);
  const [medida, setMedida] = useState<MedidaAnguloProgresion | null>(null);

  const medirAngulo = async (archivo: File) => {
    setMidiendo(true);
    setMedida(null);
    try {
      const m = await partoDetalleService.medirAnguloProgresion(archivo);
      setMedida(m);
      if (m.medidas.angulo_progresion_grados) form.setFieldValue('angulo_progresion', m.medidas.angulo_progresion_grados);
    } catch (e) {
      message.error(mensajeDeError(e, 'No se pudo medir el ángulo'));
    } finally {
      setMidiendo(false);
    }
    return false;
  };

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      setRegistros(await partoDetalleService.partograma(partoId));
    } catch {
      message.error('No se pudo cargar el partograma');
    } finally {
      setCargando(false);
    }
  }, [partoId, message]);

  useEffect(() => { cargar(); }, [cargar]);

  const curva = useMemo(() => curvaPartograma(registros), [registros]);

  const guardar = async (valores: Formulario) => {
    const inicio = inicioTrabajoParto ? dayjs(inicioTrabajoParto)
      : registros.length ? dayjs(registros[0].hora_registro) : valores.hora_registro;
    setGuardando(true);
    try {
      await partoDetalleService.crearRegistroPartograma({
        ...valores,
        parto: partoId,
        hora_registro: valores.hora_registro.toISOString(),
        horas_trabajo_parto: Math.max(0, Math.min(48, valores.hora_registro.diff(inicio, 'hour'))),
      } as Partial<RegistroPartograma>);
      message.success('Tacto registrado');
      setAbierto(false);
      setMedida(null);
      form.resetFields();
      cargar();
    } catch (e) {
      message.error(mensajeDeError(e, 'No se pudo registrar el tacto'));
    } finally {
      setGuardando(false);
    }
  };

  const columnas = [
    { title: 'Hora', dataIndex: 'hora_registro', render: (v: string) => dayjs(v).format('DD/MM HH:mm') },
    { title: 'Dilatación', dataIndex: 'dilatacion_cervical', render: (v: number) => `${v} cm` },
    { title: 'Borramiento', dataIndex: 'borramiento_cervical', render: (v?: number | null) => (v == null ? '—' : `${v} %`) },
    { title: 'Estación', dataIndex: 'estacion_fetal' },
    { title: 'Contracciones / 10 min', dataIndex: 'contracciones_10min' },
    { title: 'FCF', dataIndex: 'fcf_baseline', render: (v?: number | null) => (v == null ? '—' : `${v} lpm`) },
    {
      title: 'AoP', dataIndex: 'angulo_progresion',
      render: (v?: string | number | null) => (v == null ? '—' : <Tag color={Number(v) >= 120 ? 'green' : 'default'}>{v}°</Tag>),
    },
    {
      title: 'PA', key: 'pa',
      render: (_: unknown, r: RegistroPartograma) => (r.presion_arterial_sistolica
        ? `${r.presion_arterial_sistolica}/${r.presion_arterial_diastolica ?? '—'}` : '—'),
    },
    {
      title: 'Alertas', key: 'alertas',
      render: (_: unknown, r: RegistroPartograma) => (
        <Space size={4} wrap>
          {r.alerta_progreso_lento && <Tag color="orange">Progreso lento</Tag>}
          {r.alerta_fcf_anormal && <Tag color="red">FCF anormal</Tag>}
          {r.alerta_signos_vitales && <Tag color="red">Signos vitales</Tag>}
          {!r.alerta_progreso_lento && !r.alerta_fcf_anormal && !r.alerta_signos_vitales && <Text type="secondary">—</Text>}
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="Partograma"
      extra={(
        <Space wrap>
          <Button icon={<ReloadOutlined />} onClick={cargar} loading={cargando} aria-label="Recargar partograma" />
          <Button icon={<FilePdfOutlined />} disabled={!registros.length}
            onClick={() => descargarArchivo(`/partos/${partoId}/partograma-pdf/`, `partograma_${partoId}.pdf`)}>
            PDF
          </Button>
          {puedeEditar && <Button type="primary" icon={<PlusOutlined />} onClick={() => setAbierto(true)}>Registrar tacto</Button>}
        </Space>
      )}
    >
      {registros.length === 0 ? (
        <Empty description="Sin tactos registrados. Cada tacto agrega un punto a la curva." />
      ) : (
        <>
          {curva.cruzaAccion && (
            <Alert type="error" showIcon style={{ marginBottom: 12 }} message="La dilatación cruzó la línea de acción"
              description="Más de 4 horas de retraso respecto de 1 cm/h: reevalúe la conducta (OMS)." />
          )}
          {!curva.cruzaAccion && curva.cruzaAlerta && (
            <Alert type="warning" showIcon style={{ marginBottom: 12 }} message="La dilatación cruzó la línea de alerta"
              description="El progreso es menor de 1 cm/h en fase activa." />
          )}
          {curva.alerta.length === 0 && (
            <Alert type="info" showIcon style={{ marginBottom: 12 }}
              message="Aún en fase latente: las líneas de alerta y acción empiezan en el primer tacto con 4 cm o más." />
          )}
          <Row gutter={[16, 16]}>
            <Col xs={24} xl={14}>
              <Text strong>Dilatación cervical (cm)</Text>
              {curva.velocidadActiva !== null && <Text type="secondary"> · {curva.velocidadActiva} cm/h en fase activa</Text>}
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <LineChart margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" dataKey="horas" domain={[0, 'dataMax']} allowDuplicatedCategory={false}
                      label={{ value: 'Horas desde el primer tacto', position: 'insideBottom', offset: -4 }} />
                    <YAxis type="number" domain={[0, 10]} ticks={[0, 2, 4, 6, 8, 10]} />
                    <Tooltip formatter={(v: number) => `${v} cm`} labelFormatter={(h: number) => `${h} h`} />
                    <Legend verticalAlign="top" height={28} />
                    <Line data={curva.puntos} dataKey="dilatacion" name="Dilatación" stroke="#1d4ed8" strokeWidth={2} dot />
                    {curva.alerta.length > 0 && (
                      <Line data={curva.alerta} dataKey="dilatacion" name="Alerta" stroke="#d97706" strokeDasharray="6 4" dot={false} />
                    )}
                    {curva.accion.length > 0 && (
                      <Line data={curva.accion} dataKey="dilatacion" name="Acción" stroke="#dc2626" strokeDasharray="6 4" dot={false} />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Col>
            <Col xs={24} xl={10}>
              <Text strong>Frecuencia cardíaca fetal (lpm)</Text>
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <LineChart data={curva.puntos.filter((p) => p.fcf !== null)} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <ReferenceArea y1={110} y2={160} fill="#16a34a" fillOpacity={0.08} />
                    <XAxis type="number" dataKey="horas" domain={[0, 'dataMax']} />
                    <YAxis domain={[80, 200]} />
                    <Tooltip formatter={(v: number) => `${v} lpm`} labelFormatter={(h: number) => `${h} h`} />
                    <Line dataKey="fcf" name="FCF" stroke="#be123c" strokeWidth={2} dot />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <Text type="secondary">Banda verde: rango normal 110–160 lpm.</Text>
            </Col>
          </Row>
          <Table style={{ marginTop: 16 }} size="small" rowKey="id" columns={columnas} dataSource={registros}
            pagination={false} scroll={{ x: 760 }} />
        </>
      )}

      <Modal title="Registrar tacto" open={abierto} onCancel={() => { setAbierto(false); setMedida(null); }} okText="Guardar"
        onOk={() => form.submit()} confirmLoading={guardando} width={720} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={guardar}
          initialValues={{ hora_registro: dayjs(), estacion_fetal: '0', contracciones_10min: 3 }}>
          <Row gutter={12}>
            <Col xs={24} sm={12}>
              <Form.Item name="hora_registro" label="Fecha y hora" rules={[{ required: true }]}>
                <DatePicker showTime format="DD/MM/YYYY HH:mm" style={{ width: '100%' }}
                  disabledDate={(d) => d.isAfter(dayjs())} />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="dilatacion_cervical" label="Dilatación (cm)" rules={[{ required: true, message: 'Indique la dilatación' }]}>
                <InputNumber min={0} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="borramiento_cervical" label="Borramiento (%)">
                <InputNumber min={0} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="estacion_fetal" label="Estación" rules={[{ required: true }]}>
                <Select options={ESTACIONES.map((e) => ({ value: e, label: e }))} />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="contracciones_10min" label="Contracciones / 10 min" rules={[{ required: true }]}>
                <InputNumber min={0} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="duracion_contracciones" label="Duración (s)">
                <InputNumber min={10} max={120} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="intensidad_contracciones" label="Intensidad">
                <Select allowClear options={[{ value: 'leves', label: 'Leves' }, { value: 'moderadas', label: 'Moderadas' },
                  { value: 'fuertes', label: 'Fuertes' }]} />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="fcf_baseline" label="FCF (lpm)">
                <InputNumber min={80} max={200} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="variabilidad_fcf" label="Variabilidad">
                <Select allowClear options={[{ value: 'ausente', label: 'Ausente' }, { value: 'minima', label: 'Mínima' },
                  { value: 'moderada', label: 'Moderada' }, { value: 'marcada', label: 'Marcada' }]} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="desaceleraciones" label="Desaceleraciones">
                <Input placeholder="Tempranas, tardías, variables…" maxLength={100} />
              </Form.Item>
            </Col>
            <Col xs={8} sm={4}>
              <Form.Item name="presion_arterial_sistolica" label="PA sist.">
                <InputNumber min={70} max={250} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={8} sm={4}>
              <Form.Item name="presion_arterial_diastolica" label="PA diast.">
                <InputNumber min={40} max={150} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={8} sm={4}>
              <Form.Item name="pulso_materno" label="Pulso">
                <InputNumber min={40} max={150} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="temperatura" label="Temperatura (°C)">
                <InputNumber min={35} max={42} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item name="oxitocina_dosis" label="Oxitocina (mU/min)">
                <Input maxLength={50} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item name="angulo_progresion" label="Ángulo de progresión (°)"
                extra="Ecografía intraparto transperineal. ≥ 120° se asocia a parto vaginal espontáneo.">
                <InputNumber min={60} max={180} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={16}>
              <Form.Item label="Medir con la ecografía">
                <Upload accept="image/*" showUploadList={false} beforeUpload={medirAngulo}>
                  <Button icon={<ScanOutlined />} loading={midiendo}>Subir imagen y medir</Button>
                </Upload>
              </Form.Item>
            </Col>
            {medida && (
              <Col span={24}>
                <Alert
                  style={{ marginBottom: 12 }}
                  type={medida.medidas.angulo_progresion_grados ? 'info' : 'warning'}
                  showIcon
                  message={medida.medidas.angulo_progresion_grados
                    ? `${medida.medidas.angulo_progresion_grados}° ± ${medida.medidas.margen_grados}° (red entrenada con IUGC 2024)`
                    : 'No se pudo medir'}
                  description={(
                    <Space direction="vertical" style={{ width: '100%' }}>
                      {medida.medidas.interpretacion && <Text>{medida.medidas.interpretacion}</Text>}
                      {medida.avisos.map((a) => <Text key={a} type="secondary">{a}</Text>)}
                      <Text type="secondary">
                        Revise el dibujo antes de guardar: es una medida de apoyo, no una decisión.
                      </Text>
                      {medida.superposicion_url && (
                        <Image width={260} src={`${API_URL.replace(/\/api\/?$/, '')}${medida.superposicion_url}`}
                          alt="Ángulo de progresión dibujado" />
                      )}
                    </Space>
                  )}
                />
              </Col>
            )}
            <Col span={24}>
              <Form.Item name="observaciones" label="Observaciones">
                <Input.TextArea rows={2} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </Card>
  );
};

export default PartogramaPanel;
