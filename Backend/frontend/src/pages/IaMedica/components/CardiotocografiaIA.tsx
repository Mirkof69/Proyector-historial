import React, { useEffect, useState } from 'react';
import {
  Alert, Button, Card, Col, Descriptions, Form, InputNumber, Progress, Row, Space, Spin, Tag, Typography, theme,
} from 'antd';
import { ExperimentOutlined } from '@ant-design/icons';
import api from '../../../services/api';
import { useAntdApp } from '../../../hooks/useMessage';
import { mensajeDeError } from '../../../services/partoDetalleService';

const { Text, Paragraph } = Typography;

interface Variable { clave: string; etiqueta: string; unidad: string; minimo: number; maximo: number }
interface FichaModelo {
  version?: string; algoritmo?: string; dataset?: string; registros_prueba?: number; limites?: string[]; error?: string;
  prueba?: { exactitud: number; exactitud_ic95: [number, number]; f1_macro: number; sensibilidad: Record<string, number>;
    sensibilidad_patologica_ic95: [number, number] };
}
interface Resultado {
  clase: 'normal' | 'sospechosa' | 'patologica';
  clase_nombre: string;
  probabilidades: Record<string, number>;
  advertencias: string[];
}

const COLOR: Record<string, string> = { normal: 'success', sospechosa: 'warning', patologica: 'error' };
const pct = (v?: number) => (v === undefined ? '—' : `${(v * 100).toFixed(1)} %`);

/**
 * Clasificador supervisado de cardiotocografía (ia_medica/ml/cardiotocografia.py).
 * El formulario se arma con las variables que pide el modelo EN USO
 * (GET /api/ia/cardiotocografia/), así nunca se desalinea si se reentrena.
 * Muestra siempre cuánto acertó el modelo en registros que no vio.
 */
const CardiotocografiaIA: React.FC = () => {
  const { message } = useAntdApp();
  const { token } = theme.useToken();
  const colorBarra: Record<string, string> = {
    normal: token.colorSuccess, sospechosa: token.colorWarning, patologica: token.colorError,
  };
  const [variables, setVariables] = useState<Variable[]>([]);
  const [modelo, setModelo] = useState<FichaModelo | null>(null);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [cargando, setCargando] = useState(true);
  const [clasificando, setClasificando] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    api.get('/ia/cardiotocografia/')
      .then((r) => { setVariables(r.data.variables); setModelo(r.data.modelo); })
      .catch((e) => message.error(mensajeDeError(e, 'No se pudo cargar el modelo de cardiotocografía')))
      .finally(() => setCargando(false));
  }, [message]);

  const clasificar = async (valores: Record<string, number>) => {
    setClasificando(true);
    try {
      setResultado((await api.post('/ia/cardiotocografia/', valores)).data);
    } catch (e) {
      setResultado(null);
      message.error(mensajeDeError(e, 'No se pudo clasificar el registro'));
    } finally {
      setClasificando(false);
    }
  };

  if (cargando) return <Spin />;

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} xl={15}>
        <Card title={<Space><ExperimentOutlined />Cardiotocografía: datos del registro</Space>}>
          <Paragraph type="secondary">
            Copie los valores del informe automático del monitor (SisPorto u otro análisis computarizado).
            Las tasas van por segundo, como las entrega el análisis.
          </Paragraph>
          {modelo?.error ? <Alert type="warning" showIcon message={modelo.error} /> : (
            <Form form={form} layout="vertical" onFinish={clasificar}>
              <Row gutter={12}>
                {variables.map((v) => (
                  <Col xs={24} sm={12} lg={8} key={v.clave}>
                    <Form.Item name={v.clave} label={`${v.etiqueta}${v.unidad ? ` (${v.unidad})` : ''}`}
                      rules={[{ required: true, message: 'Obligatorio' }]}>
                      <InputNumber min={v.minimo} max={v.maximo} step={v.unidad === 'por segundo' ? 0.001 : 1}
                        style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                ))}
              </Row>
              <Button type="primary" htmlType="submit" loading={clasificando}>Clasificar</Button>
            </Form>
          )}
        </Card>
      </Col>
      <Col xs={24} xl={9}>
        {resultado && (
          <Card title="Resultado" style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Tag color={COLOR[resultado.clase]} className="ia-ctg-clase">{resultado.clase_nombre}</Tag>
              {Object.entries(resultado.probabilidades).map(([clase, p]) => (
                <div key={clase}>
                  <Text>{clase === 'patologica' ? 'Patológica' : clase === 'sospechosa' ? 'Sospechosa' : 'Normal'}</Text>
                  <Progress percent={Math.round(p * 1000) / 10} strokeColor={colorBarra[clase]} />
                </div>
              ))}
              {resultado.advertencias.map((a) => <Alert key={a} type="info" showIcon message={a} />)}
            </Space>
          </Card>
        )}
        {modelo?.prueba && (
          <Card title="Fiabilidad medida del modelo">
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="Exactitud en registros no vistos">
                {pct(modelo.prueba.exactitud)} <Text type="secondary">(IC95 {pct(modelo.prueba.exactitud_ic95[0])}–{pct(modelo.prueba.exactitud_ic95[1])})</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Detecta patológicas">
                {pct(modelo.prueba.sensibilidad.patologica)} <Text type="secondary">(IC95 {pct(modelo.prueba.sensibilidad_patologica_ic95[0])}–{pct(modelo.prueba.sensibilidad_patologica_ic95[1])})</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Detecta sospechosas">{pct(modelo.prueba.sensibilidad.sospechosa)}</Descriptions.Item>
              <Descriptions.Item label="Registros de prueba">{modelo.registros_prueba}</Descriptions.Item>
              <Descriptions.Item label="Modelo">{modelo.algoritmo} · v{modelo.version}</Descriptions.Item>
              <Descriptions.Item label="Datos">{modelo.dataset}</Descriptions.Item>
            </Descriptions>
            {modelo.limites?.length ? (
              <Alert style={{ marginTop: 12 }} type="warning" showIcon message="Límites"
                description={<ul style={{ margin: 0, paddingLeft: 18 }}>{modelo.limites.map((l) => <li key={l}>{l}</li>)}</ul>} />
            ) : null}
          </Card>
        )}
      </Col>
    </Row>
  );
};

export default CardiotocografiaIA;
