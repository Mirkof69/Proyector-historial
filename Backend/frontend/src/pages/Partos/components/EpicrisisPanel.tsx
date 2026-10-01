import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Button, Card, Checkbox, Col, DatePicker, Descriptions, Divider, Empty, Form, Input, InputNumber, Modal, Row,
  Select, Space, Spin, Tag, Typography,
} from 'antd';
import { EditOutlined, FilePdfOutlined, SafetyCertificateOutlined, FileAddOutlined } from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import {
  CampoAdicionalEpicrisis, Epicrisis, mensajeDeError, partoDetalleService,
} from '../../../services/partoDetalleService';
import { descargarArchivo } from '../../../utils/descargarArchivo';
import { useAntdApp } from '../../../hooks/useMessage';

const { Text, Paragraph } = Typography;

const CONDICION = [
  { value: 'sana', label: 'Sana' }, { value: 'con_patologia', label: 'Con patología' },
  { value: 'traslado', label: 'Trasladada' }, { value: 'fallecida', label: 'Fallecida' },
];
const TIPO_EGRESO = [
  { value: 'alta_medica', label: 'Alta médica' }, { value: 'alta_solicitada', label: 'Alta solicitada' },
  { value: 'referencia', label: 'Referencia a otro establecimiento' }, { value: 'fuga', label: 'Fuga' },
  { value: 'fallecimiento', label: 'Fallecimiento' },
];
const METODOS = [
  { value: 'ninguno', label: 'Ninguno' }, { value: 'diu_post_evento', label: 'DIU post evento obstétrico' },
  { value: 'diu', label: 'DIU' }, { value: 'implante', label: 'Implante subdérmico' },
  { value: 'inyectable', label: 'Inyectable' }, { value: 'oral', label: 'Anticonceptivo oral' },
  { value: 'barrera', label: 'Barrera (condón)' }, { value: 'ligadura_tubaria', label: 'Ligadura tubaria' },
  { value: 'mela', label: 'MELA (lactancia y amenorrea)' }, { value: 'otro', label: 'Otro' },
];
const PRONOSTICO = [{ value: 'bueno', label: 'Bueno' }, { value: 'reservado', label: 'Reservado' }, { value: 'malo', label: 'Malo' }];
const etiqueta = (lista: { value: string; label: string }[], v?: string) => lista.find((o) => o.value === v)?.label ?? '—';

type Valores = Omit<Partial<Epicrisis>, 'fecha_egreso' | 'proximo_control'> & {
  fecha_egreso?: Dayjs; proximo_control?: Dayjs | null; extra?: Record<string, any>;
};

const CampoExtra: React.FC<{ campo: CampoAdicionalEpicrisis }> = ({ campo }) => {
  const reglas = campo.obligatorio ? [{ required: true, message: `«${campo.etiqueta}» es obligatorio` }] : [];
  const nombre = ['extra', campo.clave];
  const comun = { name: nombre, label: campo.etiqueta, extra: campo.ayuda || undefined, rules: reglas };
  switch (campo.tipo) {
    case 'parrafo': return <Form.Item {...comun}><Input.TextArea rows={2} /></Form.Item>;
    case 'numero': return <Form.Item {...comun}><InputNumber style={{ width: '100%' }} /></Form.Item>;
    case 'fecha': return <Form.Item {...comun}><DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} /></Form.Item>;
    case 'si_no': return <Form.Item {...comun} valuePropName="checked" rules={[]}><Checkbox>Sí</Checkbox></Form.Item>;
    case 'opcion': return <Form.Item {...comun}><Select allowClear options={campo.opciones.map((o) => ({ value: o, label: o }))} /></Form.Item>;
    default: return <Form.Item {...comun}><Input /></Form.Item>;
  }
};

/**
 * Epicrisis (resumen de egreso) del parto: lo que exige el expediente clínico
 * y la sección de egreso de la Historia Clínica Perinatal. Se redacta a partir
 * de una sugerencia con lo que el sistema ya sabe del parto; una vez FIRMADA
 * ya no se edita (solo el administrador la reabre, con motivo y auditoría).
 * Los campos propios del hospital se dibujan solos desde su definición.
 */
const EpicrisisPanel: React.FC<{ partoId: number; puedeEditar: boolean }> = ({ partoId, puedeEditar }) => {
  const { message } = useAntdApp();
  const [epicrisis, setEpicrisis] = useState<Epicrisis | null>(null);
  const [campos, setCampos] = useState<CampoAdicionalEpicrisis[]>([]);
  const [cargando, setCargando] = useState(true);
  const [editando, setEditando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [form] = Form.useForm<Valores>();

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const [e, c] = await Promise.all([partoDetalleService.epicrisisDelParto(partoId), partoDetalleService.camposAdicionales()]);
      setEpicrisis(e);
      setCampos(c);
    } catch {
      message.error('No se pudo cargar la epicrisis');
    } finally {
      setCargando(false);
    }
  }, [partoId, message]);

  useEffect(() => { cargar(); }, [cargar]);

  const aFormulario = (e: Partial<Epicrisis>): Valores => ({
    ...e,
    fecha_egreso: e.fecha_egreso ? dayjs(e.fecha_egreso) : dayjs(),
    proximo_control: e.proximo_control ? dayjs(e.proximo_control) : null,
    extra: Object.fromEntries(campos.map((c) => {
      const v = e.campos_adicionales?.[c.clave];
      return [c.clave, c.tipo === 'fecha' && v ? dayjs(String(v)) : v];
    })),
  });

  const redactar = async () => {
    try {
      const sugerencia = await partoDetalleService.sugerenciaEpicrisis(partoId);
      form.setFieldsValue(aFormulario({
        tipo_egreso: 'alta_medica', pronostico: 'bueno', metodo_anticonceptivo: 'ninguno',
        lactancia_materna_exclusiva: true, ...sugerencia,
      }));
      setEditando(true);
    } catch (e) {
      message.error(mensajeDeError(e, 'No se pudo preparar la epicrisis'));
    }
  };

  const editar = () => {
    if (!epicrisis) return;
    form.setFieldsValue(aFormulario(epicrisis));
    setEditando(true);
  };

  const guardar = async (v: Valores) => {
    const { extra, ...resto } = v;
    const datos: Partial<Epicrisis> = {
      ...resto,
      parto: partoId,
      fecha_egreso: v.fecha_egreso?.toISOString(),
      proximo_control: v.proximo_control ? v.proximo_control.format('YYYY-MM-DD') : null,
      campos_adicionales: Object.fromEntries(campos
        .map((c) => [c.clave, extra?.[c.clave]])
        .filter(([, valor]) => valor !== undefined && valor !== null && valor !== '')
        .map(([clave, valor]) => [clave, dayjs.isDayjs(valor) ? (valor as Dayjs).format('YYYY-MM-DD') : valor])),
    };
    setGuardando(true);
    try {
      setEpicrisis(await partoDetalleService.guardarEpicrisis(datos, epicrisis?.id));
      setEditando(false);
      message.success('Epicrisis guardada');
    } catch (e) {
      message.error(mensajeDeError(e, 'No se pudo guardar la epicrisis'));
    } finally {
      setGuardando(false);
    }
  };

  const firmar = () => {
    if (!epicrisis) return;
    let matricula = epicrisis.matricula_profesional || '';
    Modal.confirm({
      title: 'Firmar la epicrisis',
      content: (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>Una vez firmada no se puede modificar. Ingrese su matrícula profesional:</Text>
          <Input defaultValue={matricula} onChange={(e) => { matricula = e.target.value; }} placeholder="Matrícula" />
        </Space>
      ),
      okText: 'Firmar',
      onOk: async () => {
        try {
          setEpicrisis(await partoDetalleService.firmarEpicrisis(epicrisis.id, matricula));
          message.success('Epicrisis firmada');
        } catch (e) {
          message.error(mensajeDeError(e, 'No se pudo firmar'));
          throw e;
        }
      },
    });
  };

  if (cargando) return <Spin />;

  if (editando) {
    return (
      <Card title={epicrisis ? 'Editar epicrisis' : 'Nueva epicrisis'}>
        <Form form={form} layout="vertical" onFinish={guardar}>
          <Row gutter={12}>
            <Col xs={24} sm={12}><Form.Item name="fecha_egreso" label="Fecha y hora de egreso" rules={[{ required: true }]}>
              <DatePicker showTime format="DD/MM/YYYY HH:mm" style={{ width: '100%' }} /></Form.Item></Col>
            <Col xs={12} sm={6}><Form.Item name="tipo_egreso" label="Tipo de egreso"><Select options={TIPO_EGRESO} /></Form.Item></Col>
            <Col xs={12} sm={6}><Form.Item name="condicion_materna_egreso" label="Condición de la madre"><Select options={CONDICION} /></Form.Item></Col>
            <Form.Item noStyle shouldUpdate={(a, b) => a.tipo_egreso !== b.tipo_egreso}>
              {({ getFieldValue }) => getFieldValue('tipo_egreso') === 'referencia' && (
                <Col span={24}><Form.Item name="establecimiento_referencia" label="Establecimiento al que se refiere"
                  rules={[{ required: true, message: 'Indique el establecimiento' }]}><Input /></Form.Item></Col>
              )}
            </Form.Item>
            <Col xs={24} sm={18}><Form.Item name="diagnostico_ingreso" label="Diagnóstico de ingreso" rules={[{ required: true }]}>
              <Input /></Form.Item></Col>
            <Col xs={24} sm={6}><Form.Item name="cie10_ingreso" label="CIE-10" extra="Ej.: O80, O14.1"><Input maxLength={7} /></Form.Item></Col>
            <Col xs={24} sm={18}><Form.Item name="diagnostico_egreso" label="Diagnóstico de egreso" rules={[{ required: true }]}>
              <Input /></Form.Item></Col>
            <Col xs={24} sm={6}><Form.Item name="cie10_egreso" label="CIE-10"><Input maxLength={7} /></Form.Item></Col>
            <Col span={24}><Form.Item name="resumen_clinico" label="Resumen clínico (motivo de ingreso y evolución)"
              rules={[{ required: true }]}><Input.TextArea rows={4} /></Form.Item></Col>
            <Col xs={24} md={12}><Form.Item name="examenes_relevantes" label="Exámenes relevantes"><Input.TextArea rows={2} /></Form.Item></Col>
            <Col xs={24} md={12}><Form.Item name="tratamiento_recibido" label="Tratamiento recibido"><Input.TextArea rows={2} /></Form.Item></Col>
            <Col xs={24} md={12}><Form.Item name="procedimientos" label="Procedimientos"><Input.TextArea rows={2} /></Form.Item></Col>
            <Col xs={24} md={12}><Form.Item name="complicaciones" label="Complicaciones"><Input.TextArea rows={2} /></Form.Item></Col>
          </Row>
          <Divider orientation="left">Al egreso</Divider>
          <Row gutter={12}>
            <Col xs={24} sm={8}><Form.Item name="consejeria_anticoncepcion" valuePropName="checked">
              <Checkbox>Recibió consejería en anticoncepción</Checkbox></Form.Item></Col>
            <Col xs={24} sm={8}><Form.Item name="metodo_anticonceptivo" label="Método elegido"><Select options={METODOS} /></Form.Item></Col>
            <Col xs={24} sm={8}><Form.Item name="lactancia_materna_exclusiva" valuePropName="checked">
              <Checkbox>Lactancia materna exclusiva</Checkbox></Form.Item></Col>
            <Col span={24}><Form.Item name="indicaciones_alta" label="Indicaciones al alta (medicación y cuidados)"><Input.TextArea rows={3} /></Form.Item></Col>
            <Col xs={24} sm={8}><Form.Item name="signos_alarma_explicados" valuePropName="checked">
              <Checkbox>Se explicaron los signos de alarma</Checkbox></Form.Item></Col>
            <Col xs={12} sm={8}><Form.Item name="proximo_control" label="Próximo control">
              <DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} /></Form.Item></Col>
            <Col xs={12} sm={8}><Form.Item name="lugar_proximo_control" label="Lugar"><Input /></Form.Item></Col>
            <Col xs={12} sm={8}><Form.Item name="pronostico" label="Pronóstico"><Select options={PRONOSTICO} /></Form.Item></Col>
            <Col xs={12} sm={8}><Form.Item name="matricula_profesional" label="Matrícula profesional"><Input maxLength={30} /></Form.Item></Col>
          </Row>
          {campos.length > 0 && (
            <>
              <Divider orientation="left">Datos propios del establecimiento</Divider>
              <Row gutter={12}>{campos.map((c) => <Col xs={24} sm={12} key={c.clave}><CampoExtra campo={c} /></Col>)}</Row>
            </>
          )}
          <Space>
            <Button type="primary" htmlType="submit" loading={guardando}>Guardar borrador</Button>
            <Button onClick={() => setEditando(false)}>Cancelar</Button>
          </Space>
        </Form>
      </Card>
    );
  }

  if (!epicrisis) {
    return (
      <Empty description="Este parto aún no tiene epicrisis">
        {puedeEditar && <Button type="primary" icon={<FileAddOutlined />} onClick={redactar}>Redactar epicrisis</Button>}
      </Empty>
    );
  }

  const firmada = epicrisis.estado === 'firmada';
  return (
    <Card
      title={<Space>Epicrisis {firmada ? <Tag color="green" icon={<SafetyCertificateOutlined />}>Firmada</Tag> : <Tag color="gold">Borrador</Tag>}</Space>}
      extra={(
        <Space wrap>
          <Button icon={<FilePdfOutlined />}
            onClick={() => descargarArchivo(`/partos/epicrisis/${epicrisis.id}/pdf/`, `epicrisis_parto_${partoId}.pdf`)}>PDF</Button>
          {puedeEditar && !firmada && <Button icon={<EditOutlined />} onClick={editar}>Editar</Button>}
          {puedeEditar && !firmada && <Button type="primary" icon={<SafetyCertificateOutlined />} onClick={firmar}>Firmar</Button>}
        </Space>
      )}
    >
      {firmada && (
        <Alert type="success" showIcon style={{ marginBottom: 16 }}
          message={`Firmada por ${epicrisis.medico_nombre} · Matrícula ${epicrisis.matricula_profesional} · ${dayjs(epicrisis.fecha_firma).format('DD/MM/YYYY HH:mm')}`}
          description="Es parte del expediente: ya no se modifica. Si hay un error, el administrador puede reabrirla." />
      )}
      <Descriptions bordered size="small" column={{ xs: 1, sm: 2 }}>
        <Descriptions.Item label="Ingreso">{epicrisis.fecha_ingreso ? dayjs(epicrisis.fecha_ingreso).format('DD/MM/YYYY HH:mm') : '—'}</Descriptions.Item>
        <Descriptions.Item label="Egreso">{dayjs(epicrisis.fecha_egreso).format('DD/MM/YYYY HH:mm')}
          {epicrisis.dias_internacion !== null && <Text type="secondary"> · {epicrisis.dias_internacion} días</Text>}</Descriptions.Item>
        <Descriptions.Item label="Diagnóstico de ingreso">{epicrisis.diagnostico_ingreso} {epicrisis.cie10_ingreso && <Tag>{epicrisis.cie10_ingreso}</Tag>}</Descriptions.Item>
        <Descriptions.Item label="Diagnóstico de egreso">{epicrisis.diagnostico_egreso} {epicrisis.cie10_egreso && <Tag>{epicrisis.cie10_egreso}</Tag>}</Descriptions.Item>
        <Descriptions.Item label="Tipo de egreso">{etiqueta(TIPO_EGRESO, epicrisis.tipo_egreso)}
          {epicrisis.establecimiento_referencia && ` → ${epicrisis.establecimiento_referencia}`}</Descriptions.Item>
        <Descriptions.Item label="Condición de la madre">{etiqueta(CONDICION, epicrisis.condicion_materna_egreso)}</Descriptions.Item>
        <Descriptions.Item label="Anticoncepción">{epicrisis.consejeria_anticoncepcion ? 'Con consejería' : 'Sin consejería'} · {etiqueta(METODOS, epicrisis.metodo_anticonceptivo)}</Descriptions.Item>
        <Descriptions.Item label="Lactancia exclusiva">{epicrisis.lactancia_materna_exclusiva ? 'Sí' : 'No'}</Descriptions.Item>
        <Descriptions.Item label="Próximo control">{epicrisis.proximo_control ? dayjs(epicrisis.proximo_control).format('DD/MM/YYYY') : '—'}
          {epicrisis.lugar_proximo_control && ` · ${epicrisis.lugar_proximo_control}`}</Descriptions.Item>
        <Descriptions.Item label="Pronóstico">{etiqueta(PRONOSTICO, epicrisis.pronostico)}</Descriptions.Item>
        {campos.filter((c) => epicrisis.campos_adicionales?.[c.clave] !== undefined).map((c) => {
          const v = epicrisis.campos_adicionales[c.clave];
          return <Descriptions.Item key={c.clave} label={c.etiqueta}>{v === true ? 'Sí' : v === false ? 'No' : String(v)}</Descriptions.Item>;
        })}
      </Descriptions>
      {([['Resumen clínico', epicrisis.resumen_clinico], ['Procedimientos', epicrisis.procedimientos],
        ['Tratamiento recibido', epicrisis.tratamiento_recibido], ['Exámenes relevantes', epicrisis.examenes_relevantes],
        ['Complicaciones', epicrisis.complicaciones], ['Indicaciones al alta', epicrisis.indicaciones_alta]] as const)
        .filter(([, texto]) => texto)
        .map(([titulo, texto]) => (
          <div key={titulo} style={{ marginTop: 12 }}>
            <Text strong>{titulo}</Text>
            <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>{texto}</Paragraph>
          </div>
        ))}
    </Card>
  );
};

export default EpicrisisPanel;
