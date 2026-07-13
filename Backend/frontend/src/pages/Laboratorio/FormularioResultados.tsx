/**
 * =============================================================================
 * FORMULARIO DE RESULTADOS DE LABORATORIO
 * =============================================================================
 * Formulario para ingresar resultados de un examen de laboratorio
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { Form, Input, InputNumber, Button, Row, Col, Alert, Spin, Space, Divider } from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { SaveOutlined, LoadingOutlined } from '@ant-design/icons';
import { laboratorioService, ValorReferencia } from '../../services/laboratorioService';

const loadingIndicator = <LoadingOutlined style={{ fontSize: 24 }} spin />;

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
  const [loading, setLoading] = useState(false);
  const [loadingValores, setLoadingValores] = useState(true);
  const [valoresReferencia, setValoresReferencia] = useState<ValorReferencia[]>([]);

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

  const handleSubmit = async (values: any) => {
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
        message.warning('Debe ingresar al menos un resultado');
        return;
      }

      await laboratorioService.crearResultadoMultiple(examenId, resultados, true);
      message.success('Resultados guardados exitosamente');
      form.resetFields();
      onResultadosGuardados();
    } catch (error: any) {
      message.error(error?.response?.data?.message || 'Error al guardar los resultados');
    } finally {
      setLoading(false);
    }
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

  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit}>
      <Alert
        message={`Examen: ${tipoExamenNombre}`}
        description="Ingrese los valores obtenidos para cada parámetro. Los valores fuera de rango se marcarán automáticamente."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Divider orientation="left">Resultados</Divider>

      {valoresReferencia.map((vr) => (
        <Row key={vr.id} gutter={16} style={{ marginBottom: 8 }}>
          <Col xs={24} sm={8}>
            <Form.Item
              label={vr.parametro}
              name={`resultado_${vr.id}`}
              rules={[{ required: false }]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="Ingrese valor"
                step="any"
                addonAfter={vr.unidad !== 'cualitativo' ? vr.unidad : undefined}
              />
            </Form.Item>
          </Col>
          <Col xs={24} sm={6}>
            <div style={{ marginTop: 30 }}>
              <span style={{ color: '#8c8c8c', fontSize: 13 }}>
                Rango: {vr.valor_minimo !== null && vr.valor_maximo !== null
                  ? `${vr.valor_minimo} - ${vr.valor_maximo}`
                  : vr.valor_normal || 'N/A'}
              </span>
            </div>
          </Col>
          <Col xs={24} sm={10}>
            <Form.Item
              label="Observaciones"
              name={`observacion_${vr.id}`}
            >
              <Input placeholder="Observaciones opcionales" />
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
          >
            Guardar Resultados
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
};

export default FormularioResultados;
