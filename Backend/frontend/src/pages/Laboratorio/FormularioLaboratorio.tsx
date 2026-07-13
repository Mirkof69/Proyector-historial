/**
 * =============================================================================
 * FORMULARIO DE EXAMEN DE LABORATORIO
 * =============================================================================
 * Formulario completo para crear/editar exámenes de laboratorio
 * Basado en los modelos del backend:
 * - TipoExamen, ValorReferencia, ExamenLaboratorio, ResultadoLaboratorio
 * =============================================================================
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { Card, Form, Input, Button, Space, Row, Col, Divider, Alert, Spin, Typography, Table, Tooltip } from "antd";
import {
  ArrowLeftOutlined,
  SaveOutlined,
  ExperimentOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { laboratorioService, TipoExamen, ValorReferencia, ResultadoLaboratorio } from '../../services/laboratorioService';
import { pacientesService, Paciente } from '../../services/pacientesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import { buildColumnasResultados } from './components/columnasResultadosLab';
import DatosGeneralesLab from './components/DatosGeneralesLab';

const { TextArea } = Input;
const { Title, Paragraph } = Typography;

const ARROW_LEFT_ICON_2 = <ArrowLeftOutlined />;
const WARNING_ICON_4 = <WarningOutlined />;
const PLUS_ICON_6 = <PlusOutlined />;
const DELETE_ICON_3 = <DeleteOutlined />;
const SAVE_ICON_2 = <SaveOutlined />;

const FormularioLaboratorio: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();
  const { id } = useParams<{ id: string }>();
  const [form] = Form.useForm();
  const isEditing = !!id;

  const [loading, setLoading] = useState(false);
  const loadingDataRef = useRef(isEditing);
  const [tiposExamen, setTiposExamen] = useState<TipoExamen[]>([]);
  const [valoresReferencia, setValoresReferencia] = useState<ValorReferencia[]>([]);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [resultados, setResultados] = useState<Partial<ResultadoLaboratorio>[]>([]);
  const [resultadosAnormales, setResultadosAnormales] = useState(0);
  const [resultadosCriticos, setResultadosCriticos] = useState(0);

  // ==========================================================================
  // CARGAR DATOS INICIALES
  // ==========================================================================
  const cargarDatosIniciales = useCallback(async () => {
    try {
      const [tiposData, pacientesData] = await Promise.all([
        laboratorioService.getTiposExamen(),
        pacientesService.getAll(),
      ]);
      setTiposExamen(tiposData);
      setPacientes(pacientesData);
    } catch (error) {
      message.error('Error al cargar datos iniciales');
    }
  }, []);

  const handleTipoExamenChange = useCallback(async (tipoExamenId: number) => {
    try {
      const valores = await laboratorioService.getValoresReferencia(tipoExamenId);
      setValoresReferencia(valores);
      if (!isEditing) {
        const nuevosResultados = valores.map((vr: ValorReferencia) => ({
          valor_referencia: vr.id,
          es_normal: true,
          es_critico: false,
        }));
        setResultados(nuevosResultados);
      }
    } catch (error) {
      message.error('Error al cargar parámetros del examen');
    }
  }, [isEditing]);

  const calcularEstadisticas = useCallback((results: Partial<ResultadoLaboratorio>[]) => {
    const anormales = results.filter((r) => !r.es_normal).length;
    const criticos = results.filter((r) => r.es_critico).length;
    setResultadosAnormales(anormales);
    setResultadosCriticos(criticos);
  }, []);

  const cargarExamen = useCallback(async () => {
    loadingDataRef.current = true;
    try {
      const data = await laboratorioService.getById(Number(id));
      form.setFieldsValue({
        ...data,
        fecha_solicitud: dayjs(data.fecha_solicitud),
        fecha_muestra: data.fecha_muestra ? dayjs(data.fecha_muestra) : null,
        fecha_resultado: data.fecha_resultado ? dayjs(data.fecha_resultado) : null,
      });

      // Cargar valores de referencia para el tipo de examen
      if (data.tipo_examen) {
        handleTipoExamenChange(data.tipo_examen);
      }

      // Cargar resultados si existen
      if (data.resultados) {
        setResultados(data.resultados);
        calcularEstadisticas(data.resultados);
      }

      message.success('Examen cargado correctamente');
    } catch (error) {
      message.error('Error al cargar el examen');
      navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO);
    } finally {
      loadingDataRef.current = false;
    }
  }, [id, navigate, handleTipoExamenChange, calcularEstadisticas, form]);

  useEffect(() => {
    cargarDatosIniciales();
    if (isEditing) {
      cargarExamen();
    }
  }, [id, cargarDatosIniciales, cargarExamen, isEditing]);

  // ==========================================================================
  // MANEJO DE RESULTADOS
  // ==========================================================================
  const handleResultadoChange = (index: number, field: string, value: any) => {
    const nuevosResultados = [...resultados];
    nuevosResultados[index] = {
      ...nuevosResultados[index],
      [field]: value,
    };

    // Auto-calcular si es normal/crítico basado en valor y rango
    if (field === 'valor_numerico') {
      const vr = valoresReferencia.find(
        (v) => v.id === nuevosResultados[index].valor_referencia
      );
      if (vr && value !== null && value !== undefined) {
        const valorNum = parseFloat(value);

        // Verificar si es crítico
        const esCriticoBajo = vr.es_critico_bajo && valorNum < vr.es_critico_bajo;
        const esCriticoAlto = vr.es_critico_alto && valorNum > vr.es_critico_alto;
        nuevosResultados[index].es_critico = !!(esCriticoBajo || esCriticoAlto);

        // Verificar si es normal
        const enRango =
          (vr.valor_minimo === null || vr.valor_minimo === undefined || valorNum >= vr.valor_minimo) &&
          (vr.valor_maximo === null || vr.valor_maximo === undefined || valorNum <= vr.valor_maximo);
        nuevosResultados[index].es_normal = enRango && !nuevosResultados[index].es_critico;
      }
    }

    setResultados(nuevosResultados);
    calcularEstadisticas(nuevosResultados);
  };

  // ==========================================================================
  // SUBMIT
  // ==========================================================================
  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const data = {
        ...values,
        fecha_solicitud: values.fecha_solicitud.format('YYYY-MM-DD HH:mm:ss'),
        fecha_muestra: values.fecha_muestra?.format('YYYY-MM-DD HH:mm:ss'),
        fecha_resultado: values.fecha_resultado?.format('YYYY-MM-DD HH:mm:ss'),
      };

      let response: any;
      if (isEditing) {
        response = await laboratorioService.update(Number(id), data);

        // Actualizar resultados
        await Promise.all(
          resultados.map((resultado) => {
            if (resultado.id) {
              return laboratorioService.updateResultado(
                Number(id),
                resultado.id,
                resultado
              );
            } else if (resultado.valor_numerico || resultado.valor_texto) {
              return laboratorioService.addResultado(Number(id), resultado);
            }
            return Promise.resolve();
          })
        );

        message.success('Examen actualizado correctamente');
      } else {
        response = await laboratorioService.create(data);

        await Promise.all(
          resultados.reduce<Array<Promise<any>>>((acc, resultado) => {
            if (resultado.valor_numerico || resultado.valor_texto) {
              acc.push(laboratorioService.addResultado((response as any).id!, resultado));
            }
            return acc;
          }, [])
        );

        message.success('Examen registrado correctamente');
      }

      setTimeout(() => {
        navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO_DETALLE((response as any).id!));
      }, 1000);
    } catch (error: any) {
      modal.error({
        title: 'Error al guardar',
        content: error.response?.data?.detail || error.message || 'Error desconocido',
      });
    } finally {
      setLoading(false);
    }
  };

  // ==========================================================================
  // RENDER
  // ==========================================================================
  if (loadingDataRef.current) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Cargando datos…</div>
      </div>
    );
  }

  const columnsResultados = buildColumnasResultados(valoresReferencia, resultados, handleResultadoChange);

  return (
    <div className="formulario-laboratorio-container">
      <Card
        title={
          <Space>
            <ExperimentOutlined style={{ fontSize: 24, color: '#722ed1' }} />
            <span style={{ fontSize: 20, fontWeight: 600 }}>
              {isEditing ? 'Editar Examen de Laboratorio' : 'Nuevo Examen de Laboratorio'}
            </span>
          </Space>
        }
        extra={
          <Button icon={ARROW_LEFT_ICON_2} onClick={() => navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO)}>
            Volver
          </Button>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            fecha_solicitud: dayjs(),
            estado: 'solicitado',
            prioridad: 'normal',
          }}
        >
          {/* ALERTAS */}
          {resultadosCriticos > 0 && (
            <Alert
              message={`⚠️ ${resultadosCriticos} resultado(s) crítico(s) detectado(s)`}
              type="error"
              showIcon
              icon={WARNING_ICON_4}
              style={{ marginBottom: 16 }}
            />
          )}
          {resultadosAnormales > 0 && (
            <Alert
              message={`${resultadosAnormales} resultado(s) anormal(es)`}
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          <Divider orientation="left">
            <Title level={5} style={{ margin: 0 }}>
              <InfoCircleOutlined /> Información del Examen
            </Title>
          </Divider>

          <Paragraph type="secondary" style={{ marginBottom: 16 }}>
            Complete los datos generales del examen de laboratorio. Los campos marcados con (*) son obligatorios.
          </Paragraph>

          {/* DATOS GENERALES */}
          <DatosGeneralesLab
            pacientes={pacientes}
            tiposExamen={tiposExamen}
            onTipoExamenChange={handleTipoExamenChange}
          />

          <Divider />

          {/* RESULTADOS */}
          {valoresReferencia.length > 0 && (
            <Card
              type="inner"
              title="Resultados del Examen"
              style={{ marginBottom: 16 }}
            >
              <Table
                columns={columnsResultados}
                dataSource={resultados}
                rowKey={(record: any) => record.id || `lab-${record.codigo || record.nombre || 'temp'}`}
                pagination={false}
                bordered
              />
            </Card>
          )}

          {/* OBSERVACIONES */}
          <Card type="inner" title="Observaciones" style={{ marginBottom: 16 }}>
            <Form.Item name="observaciones" label="Observaciones Generales">
              <TextArea rows={3} placeholder="Observaciones adicionales..." />
            </Form.Item>
          </Card>

          {/* BOTONES */}
          <Row justify="space-between">
            <Col>
              <Space>
                <Tooltip title="Agregar parámetros adicionales al examen">
                  <Button icon={PLUS_ICON_6} type="dashed">
                    Agregar Parámetro
                  </Button>
                </Tooltip>
                <Tooltip title="Eliminar este examen (solo si está en borrador)">
                  <Button icon={DELETE_ICON_3} danger type="text">
                    Eliminar Borrador
                  </Button>
                </Tooltip>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button onClick={() => navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO)}>
                  Cancelar
                </Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={SAVE_ICON_2}
                  loading={loading}
                >
                  Guardar Examen
                </Button>
              </Space>
            </Col>
          </Row>
        </Form>
      </Card>
    </div>
  );
};

export default FormularioLaboratorio;
