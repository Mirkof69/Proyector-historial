/**
 * =============================================================================
 * FORMULARIO DE RESULTADOS DE LABORATORIO — flujo guiado de resultado crítico
 * =============================================================================
 * Al ingresar cada valor se evalúa en vivo contra el rango de referencia y los
 * umbrales críticos del parámetro. Si algún valor es CRÍTICO, antes de guardar
 * se exige una confirmación explícita que deja claro que se notificará al
 * médico responsable (el backend genera la alerta automáticamente).
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { Form, Input, InputNumber, Button, Row, Col, Alert, Spin, Space, Divider, Tag, Modal } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { SaveOutlined, LoadingOutlined, WarningOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { laboratorioService, ValorReferencia } from '../../services/laboratorioService';

const loadingIndicator = <LoadingOutlined style={{ fontSize: 24 }} spin />;

type EvaluacionValor = 'normal' | 'alterado' | 'critico';

/** Evalúa un valor medido contra el rango normal y los umbrales críticos. */
const evaluarValor = (vr: ValorReferencia, valor: number | undefined | null): EvaluacionValor | null => {
  if (valor === undefined || valor === null || Number.isNaN(valor)) return null;
  if (vr.es_critico_bajo !== undefined && vr.es_critico_bajo !== null && valor <= vr.es_critico_bajo) return 'critico';
  if (vr.es_critico_alto !== undefined && vr.es_critico_alto !== null && valor >= vr.es_critico_alto) return 'critico';
  if (vr.valor_minimo !== undefined && vr.valor_minimo !== null && valor < vr.valor_minimo) return 'alterado';
  if (vr.valor_maximo !== undefined && vr.valor_maximo !== null && valor > vr.valor_maximo) return 'alterado';
  return 'normal';
};

const TagEvaluacion: React.FC<{ evaluacion: EvaluacionValor | null }> = ({ evaluacion }) => {
  if (evaluacion === null) return null;
  if (evaluacion === 'critico') {
    return <Tag color="red" icon={<ExclamationCircleOutlined />} className="status-pulse">VALOR CRÍTICO</Tag>;
  }
  if (evaluacion === 'alterado') {
    return <Tag color="orange" icon={<WarningOutlined />}>Fuera de rango</Tag>;
  }
  return <Tag color="green" icon={<CheckCircleOutlined />}>Dentro de rango</Tag>;
};

interface FormularioResultadosProps {
  examenId: number;
  tipoExamenId: number;
  tipoExamenNombre: string;
  onResultadosGuardados: () => void;
}

const FormularioResultados: React.FC<FormularioResultadosProps> = ({
  examenId,
  tipoExamenId,
  tipoExamenNombre,
  onResultadosGuardados,
}) => {
  const { message } = useAntdApp();
  const [form] = Form.useForm();
  const [modal, contextHolder] = Modal.useModal();
  const [loading, setLoading] = useState(false);
  const [loadingValores, setLoadingValores] = useState(true);
  const [valoresReferencia, setValoresReferencia] = useState<ValorReferencia[]>([]);
  const [evaluaciones, setEvaluaciones] = useState<Record<number, EvaluacionValor | null>>({});

  useEffect(() => {
    const cargarValoresReferencia = async () => {
      setLoadingValores(true);
      try {
        const data = await laboratorioService.getValoresReferenciaPorTipo(tipoExamenId);
        setValoresReferencia(data?.results || data || []);
      } catch (error) {
        message.error('Error al cargar los valores de referencia');
        setValoresReferencia([]);
      } finally {
        setLoadingValores(false);
      }
    };

    cargarValoresReferencia();
  }, [tipoExamenId, message]);

  // Evaluación clínica en vivo: cada valor ingresado se clasifica al instante.
  const handleValuesChange = (_: any, allValues: any) => {
    const nuevas: Record<number, EvaluacionValor | null> = {};
    for (const vr of valoresReferencia) {
      const valor = allValues[`resultado_${vr.id}`];
      nuevas[vr.id] = evaluarValor(vr, typeof valor === 'number' ? valor : undefined);
    }
    setEvaluaciones(nuevas);
  };

  const guardarResultados = async (values: any) => {
    setLoading(true);
    try {
      const resultados = valoresReferencia
        .map((vr) => {
          const valor = values[`resultado_${vr.id}`];
          if (valor === undefined || valor === null || valor === '') return null;

          return {
            valor_referencia: vr.id,
            valor_numerico: typeof valor === 'number' ? valor : undefined,
            valor_texto: typeof valor === 'string' ? valor : undefined,
            unidad: vr.unidad,
            observaciones: values[`observacion_${vr.id}`] || undefined,
          };
        })
        .filter((r): r is NonNullable<typeof r> => r !== null);

      if (resultados.length === 0) {
        message.warning('Debe registrar al menos un resultado');
        return;
      }

      await laboratorioService.crearResultadoMultiple(examenId, resultados, true);
      message.success('Resultados registrados correctamente');
      form.resetFields();
      setEvaluaciones({});
      onResultadosGuardados();
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Error al registrar los resultados');
    } finally {
      setLoading(false);
    }
  };

  // Paso guiado de confirmación: un valor crítico nunca se guarda "sin querer".
  const handleSubmit = (values: any) => {
    const criticos = valoresReferencia.filter((vr) => evaluaciones[vr.id] === 'critico');
    if (criticos.length === 0) {
      guardarResultados(values);
      return;
    }
    modal.confirm({
      title: 'Resultado CRÍTICO detectado',
      icon: <ExclamationCircleOutlined style={{ color: '#f5222d' }} />,
      width: 520,
      content: (
        <div>
          <p>Los siguientes parámetros están en <strong>rango crítico</strong> y requieren aviso inmediato al médico responsable:</p>
          <ul style={{ paddingLeft: 20 }}>
            {criticos.map((vr) => (
              <li key={vr.id}>
                <strong>{vr.parametro}</strong>: {values[`resultado_${vr.id}`]} {vr.unidad !== 'cualitativo' ? vr.unidad : ''}
                {' '}(referencia: {vr.valor_minimo ?? '—'}–{vr.valor_maximo ?? '—'})
              </li>
            ))}
          </ul>
          <p style={{ marginBottom: 0 }}>Al confirmar, el sistema registrará los resultados y <strong>generará la alerta médica automáticamente</strong>.</p>
        </div>
      ),
      okText: 'Confirmar y notificar al médico',
      okButtonProps: { danger: true },
      cancelText: 'Revisar valores',
      onOk: () => guardarResultados(values),
    });
  };

  if (loadingValores) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <Spin indicator={loadingIndicator} />
        <div style={{ marginTop: 8 }}>Cargando parámetros del examen…</div>
      </div>
    );
  }

  if (valoresReferencia.length === 0) {
    return (
      <Alert
        message="Sin parámetros configurados"
        description="Este tipo de examen no tiene valores de referencia configurados. Contacte al administrador."
        type="warning"
        showIcon
      />
    );
  }

  const hayCriticos = Object.values(evaluaciones).some((e) => e === 'critico');

  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit} onValuesChange={handleValuesChange}>
      {contextHolder}
      <Alert
        message={`Examen: ${tipoExamenNombre}`}
        description="Registre el valor medido de cada parámetro. El sistema lo evalúa al instante contra el rango de referencia y los umbrales críticos."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {hayCriticos && (
        <Alert
          message="Hay valores en rango CRÍTICO"
          description="Verifique la medición antes de guardar. Al confirmar se notificará automáticamente al médico responsable."
          type="error"
          showIcon
          icon={<WarningOutlined className="status-pulse" />}
          style={{ marginBottom: 16 }}
        />
      )}

      <Divider orientation="left">Resultados</Divider>

      {valoresReferencia.map((vr) => (
        <Row key={vr.id} gutter={16} style={{ marginBottom: 8 }}>
          <Col xs={24} sm={8}>
            <Form.Item
              label={vr.parametro}
              name={`resultado_${vr.id}`}
              rules={[{ required: false }]}
              validateStatus={
                evaluaciones[vr.id] === 'critico' ? 'error'
                  : evaluaciones[vr.id] === 'alterado' ? 'warning'
                    : undefined
              }
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="Valor medido"
                step="any"
                addonAfter={vr.unidad !== 'cualitativo' ? vr.unidad : undefined}
              />
            </Form.Item>
          </Col>
          <Col xs={24} sm={6}>
            <div style={{ marginTop: 30 }}>
              <Space direction="vertical" size={2}>
                <span style={{ color: '#8c8c8c', fontSize: 13 }}>
                  Referencia: {vr.valor_minimo !== null && vr.valor_maximo !== null
                    ? `${vr.valor_minimo} – ${vr.valor_maximo}`
                    : vr.valor_normal || 'N/A'}
                </span>
                <TagEvaluacion evaluacion={evaluaciones[vr.id] ?? null} />
              </Space>
            </div>
          </Col>
          <Col xs={24} sm={10}>
            <Form.Item
              label="Observación clínica"
              name={`observacion_${vr.id}`}
            >
              <Input placeholder="Ej.: muestra hemolizada, paciente en ayunas…" />
            </Form.Item>
          </Col>
        </Row>
      ))}

      <Divider />

      <Form.Item>
        <Space>
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined />}
            loading={loading}
            size="large"
            danger={hayCriticos}
          >
            {hayCriticos ? 'Guardar y notificar valores críticos' : 'Guardar resultados'}
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
};

export default FormularioResultados;
