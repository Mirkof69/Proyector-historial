/**
 * =============================================================================
 * GENERAR REPORTE - CONFIGURACIÓN Y GENERACIÓN
 * =============================================================================
 * Formulario para configurar parámetros y generar reportes
 * - Selección de tipo de reporte
 * - Configuración de parámetros (fechas, filtros)
 * - Selección de formato (PDF/Excel)
 * - Vista previa de datos
 * - Generación asíncrona
 * - Conexión: POST /reportes/generar/
 * =============================================================================
 */

import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Select,
  DatePicker,
  Space,
  Row,
  Col,
  Divider,
  message,
  Alert,
  Radio,
  Spin,
  Modal,
  Typography,
  Steps,
  Checkbox,
  Progress,
  Timeline,
  Tag,
  Descriptions, // ✅ AGREGAR ESTO
} from 'antd';
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
  SettingOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { reportesService } from '../../services/reportesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import './GenerarReporte.css';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;

interface FormValues {
  tipo_reporte: string;
  nombre: string;
  descripcion?: string;
  formato: string;
  rango_fechas: [dayjs.Dayjs, dayjs.Dayjs];
  incluir_graficos?: boolean;
  incluir_estadisticas?: boolean;
  agrupar_por?: string;
  filtros_adicionales?: string[];
}

const GenerarReportePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tipoReporteParam = searchParams.get('tipo');
  const [form] = Form.useForm();

  const [loading, setLoading] = useState(false);
  const [generando, setGenerando] = useState(false);
  const [pasoActual, setPasoActual] = useState(0);
  const [tipoSeleccionado, setTipoSeleccionado] = useState<string>('');
  const [progresoGeneracion, setProgresoGeneracion] = useState(0);
  const [reporteGenerado, setReporteGenerado] = useState<any>(null);
  const [vistaPrevia, setVistaPrevia] = useState<any>(null);

  // Tipos de reportes disponibles
  const tiposReporte = [
    {
      id: 'partos_mes',
      nombre: 'Partos del Mes',
      descripcion: 'Reporte mensual de todos los partos registrados con estadísticas',
      categoria: 'estadistico',
      icono: <BarChartOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
      campos_requeridos: ['rango_fechas'],
      opciones: ['incluir_graficos', 'incluir_estadisticas'],
    },
    {
      id: 'controles_prenatales',
      nombre: 'Controles Prenatales',
      descripcion: 'Resumen de controles prenatales realizados por período',
      categoria: 'estadistico',
      icono: <FileTextOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
      campos_requeridos: ['rango_fechas'],
      opciones: ['incluir_graficos', 'agrupar_por'],
    },
    {
      id: 'ecografias_mes',
      nombre: 'Ecografías del Mes',
      descripcion: 'Listado detallado de ecografías realizadas',
      categoria: 'listado',
      icono: <FileTextOutlined style={{ fontSize: 48, color: '#722ed1' }} />,
      campos_requeridos: ['rango_fechas'],
      opciones: ['agrupar_por'],
    },
    {
      id: 'laboratorios_pendientes',
      nombre: 'Laboratorios Pendientes',
      descripcion: 'Exámenes de laboratorio sin resultados',
      categoria: 'listado',
      icono: <FileTextOutlined style={{ fontSize: 48, color: '#fa8c16' }} />,
      campos_requeridos: [],
      opciones: [],
    },
    {
      id: 'pacientes_alto_riesgo',
      nombre: 'Pacientes de Alto Riesgo',
      descripcion: 'Embarazos clasificados como alto riesgo',
      categoria: 'listado',
      icono: <FileTextOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />,
      campos_requeridos: [],
      opciones: ['incluir_estadisticas'],
    },
    {
      id: 'indicadores_clinicos',
      nombre: 'Indicadores Clínicos',
      descripcion: 'Dashboard de indicadores de calidad asistencial',
      categoria: 'estadistico',
      icono: <BarChartOutlined style={{ fontSize: 48, color: '#13c2c2' }} />,
      campos_requeridos: ['rango_fechas'],
      opciones: ['incluir_graficos', 'incluir_estadisticas'],
    },
  ];

  const initializedRef = React.useRef(false);
  if (!initializedRef.current) {
    initializedRef.current = true;
    if (tipoReporteParam) {
      const tipoEncontrado = tiposReporte.find((t) => t.id === tipoReporteParam);
      if (tipoEncontrado) {
        setTipoSeleccionado(tipoReporteParam);
        form.setFieldsValue({
          tipo_reporte: tipoReporteParam,
          nombre: tipoEncontrado.nombre,
          descripcion: tipoEncontrado.descripcion,
          formato: 'pdf',
          rango_fechas: [dayjs().startOf('month'), dayjs().endOf('month')],
        });
        setPasoActual(1);
      }
    }
  }

  // ==========================================================================
  // HANDLERS
  // ==========================================================================
  const handleVolver = () => {
    if (generando) {
      Modal.confirm({
        title: '¿Cancelar generación?',
        content: 'El reporte se está generando. ¿Desea cancelar?',
        okText: 'Sí, cancelar',
        cancelText: 'No',
        onOk: () => navigate(FRONTEND_ROUTES.DASHBOARD.REPORTES),
      });
    } else {
      navigate(FRONTEND_ROUTES.DASHBOARD.REPORTES);
    }
  };

  const handleTipoReporteChange = (tipoId: string) => {
    const tipo = tiposReporte.find((t) => t.id === tipoId);
    if (tipo) {
      setTipoSeleccionado(tipoId);
      form.setFieldsValue({
        nombre: tipo.nombre,
        descripcion: tipo.descripcion,
      });
    }
  };

  const handleSiguientePaso = async () => {
    try {
      if (pasoActual === 0) {
        // Validar selección de tipo
        const tipoReporte = form.getFieldValue('tipo_reporte');
        if (!tipoReporte) {
          message.error('Seleccione un tipo de reporte');
          return;
        }
        setPasoActual(1);
      } else if (pasoActual === 1) {
        // Validar configuración
        await form.validateFields([
          'nombre',
          'formato',
          'rango_fechas',
        ]);
        setPasoActual(2);
        generarVistaPrevia();
      } else if (pasoActual === 2) {
        // Generar reporte
        generarReporte();
      }
    } catch (error) {
    }
  };

  const handlePasoAnterior = () => {
    if (pasoActual > 0) {
      setPasoActual(prev => prev - 1);
    }
  };

  const generarVistaPrevia = async () => {
    setLoading(true);
    try {
      const values = form.getFieldsValue();
      const preview = await reportesService.getReportePreview(values);
      setVistaPrevia(preview);
      message.success('Vista previa generada');
    } catch (error) {
      message.error('Error al generar vista previa');
    } finally {
      setLoading(false);
    }
  };

  const generarReporte = async () => {
    setGenerando(true);
    setProgresoGeneracion(0);

    try {
      const values: FormValues = await form.validateFields();
      const data = {
        ...values,
        rango_fechas: values.rango_fechas
          ? [
              values.rango_fechas[0].format('YYYY-MM-DD'),
              values.rango_fechas[1].format('YYYY-MM-DD'),
            ]
          : undefined,
      };


      // Simular progreso
      const interval = setInterval(() => {
        setProgresoGeneracion((prev) => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      const resultado = await reportesService.generateReporte(
        values.tipo_reporte as any, 
        data, 
        values.formato as any
      );
      clearInterval(interval);
      setProgresoGeneracion(100);
      setReporteGenerado(resultado);

      message.success('✅ Reporte generado correctamente');
      setPasoActual(3);
    } catch (error: any) {
      message.error(
        error?.response?.data?.error || error?.message || 'Error al generar el reporte'
      );
    } finally {
      setGenerando(false);
    }
  };

  const handleDescargarReporte = async () => {
    if (!reporteGenerado) return;

    try {
      await reportesService.downloadReporte(reporteGenerado.id);
      message.success('Reporte descargado correctamente');
    } catch (error) {
      message.error('Error al descargar el reporte');
    }
  };

  const handleGenerarOtro = () => {
    form.resetFields();
    setTipoSeleccionado('');
    setPasoActual(0);
    setReporteGenerado(null);
    setVistaPrevia(null);
    setProgresoGeneracion(0);
  };

  // ==========================================================================
  // RENDER DE PASOS
  // ==========================================================================
  const renderPaso0 = () => {
    return (
      <div>
        <Title level={4}>Seleccione el tipo de reporte</Title>
        <Paragraph type="secondary">
          Elija el tipo de reporte que desea generar
        </Paragraph>

        <Form.Item
          name="tipo_reporte"
          rules={[{ required: true, message: 'Seleccione un tipo de reporte' }]}
        >
          <Radio.Group
            style={{ width: '100%' }}
            onChange={(e) => handleTipoReporteChange(e.target.value)}
          >
            <Row gutter={[16, 16]}>
              {tiposReporte.map((tipo) => (
                <Col xs={24} sm={12} md={8} key={tipo.id}>
                  <Card
                    hoverable
                    className={
                      tipoSeleccionado === tipo.id ? 'reporte-card-selected' : ''
                    }
                  >
                    <Radio value={tipo.id} style={{ width: '100%' }}>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <div style={{ textAlign: 'center' }}>{tipo.icono}</div>
                        <Title level={5} style={{ marginBottom: 8 }}>
                          {tipo.nombre}
                        </Title>
                        <Paragraph
                          type="secondary"
                          style={{ marginBottom: 8, fontSize: 12 }}
                        >
                          {tipo.descripcion}
                        </Paragraph>
                        <Tag color={tipo.categoria === 'estadistico' ? 'blue' : 'green'}>
                          {tipo.categoria}
                        </Tag>
                      </Space>
                    </Radio>
                  </Card>
                </Col>
              ))}
            </Row>
          </Radio.Group>
        </Form.Item>
      </div>
    );
  };

  const renderPaso1 = () => {
    const tipoActual = tiposReporte.find((t) => t.id === tipoSeleccionado);

    return (
      <div>
        <Title level={4}>Configure los parámetros del reporte</Title>
        <Paragraph type="secondary">
          Complete la información necesaria para generar el reporte
        </Paragraph>

        <Row gutter={[16, 0]}>
          <Col xs={24}>
            <Form.Item
              name="nombre"
              label="Nombre del Reporte"
              rules={[{ required: true, message: 'Ingrese el nombre' }]}
              tooltip="Nombre descriptivo para identificar el reporte"
            >
              <Input
                placeholder="Ej: Partos Enero 2025"
                size="large"
                prefix={<FileTextOutlined />}
              />
            </Form.Item>
          </Col>

          <Col xs={24}>
            <Form.Item
              name="descripcion"
              label={
                <Space>
                  Descripción (Opcional)
                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                </Space>
              }
              tooltip="Descripción adicional del reporte"
            >
              <TextArea
                rows={3}
                placeholder="Descripción detallada del reporte..."
                showCount
                maxLength={200}
              />
            </Form.Item>
          </Col>

          <Col xs={24} md={12}>
            <Form.Item
              name="formato"
              label="Formato de Salida"
              rules={[{ required: true, message: 'Seleccione el formato' }]}
            >
              <Radio.Group size="large">
                <Radio value="pdf">
                  <Space>
                    <FilePdfOutlined style={{ color: '#ff4d4f' }} />
                    PDF
                  </Space>
                </Radio>
                <Radio value="excel">
                  <Space>
                    <FileExcelOutlined style={{ color: '#52c41a' }} />
                    Excel
                  </Space>
                </Radio>
              </Radio.Group>
            </Form.Item>
          </Col>

          {tipoActual?.campos_requeridos?.includes('rango_fechas') && (
            <Col xs={24} md={12}>
              <Form.Item
                name="rango_fechas"
                label="Rango de Fechas"
                rules={[{ required: true, message: 'Seleccione el rango' }]}
                tooltip="Período de tiempo para el reporte"
              >
                <RangePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  size="large"
                />
              </Form.Item>
            </Col>
          )}

          {tipoActual?.opciones && tipoActual.opciones.length > 0 && (
            <Col xs={24}>
              <Divider>Opciones Adicionales</Divider>

              {tipoActual.opciones.includes('incluir_graficos') && (
                <Form.Item name="incluir_graficos" valuePropName="checked">
                  <Checkbox>Incluir gráficos estadísticos</Checkbox>
                </Form.Item>
              )}

              {tipoActual.opciones.includes('incluir_estadisticas') && (
                <Form.Item name="incluir_estadisticas" valuePropName="checked">
                  <Checkbox>Incluir resumen estadístico</Checkbox>
                </Form.Item>
              )}

              {tipoActual.opciones.includes('agrupar_por') && (
                <Form.Item
                  name="agrupar_por"
                  label="Agrupar por"
                  tooltip="Criterio de agrupación de datos"
                >
                  <Select placeholder="Seleccione criterio" allowClear>
                    <Option value="semana">Semana</Option>
                    <Option value="mes">Mes</Option>
                    <Option value="medico">Médico</Option>
                    <Option value="tipo">Tipo</Option>
                  </Select>
                </Form.Item>
              )}
            </Col>
          )}
        </Row>
      </div>
    );
  };

  const renderPaso2 = () => {
    return (
      <div>
        <Title level={4}>Vista Previa</Title>
        <Paragraph type="secondary">
          Revise la configuración antes de generar el reporte
        </Paragraph>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>Generando vista previa…</div>
          </div>
        ) : vistaPrevia ? (
          <Card>
            <Descriptions column={{ xs: 1, sm: 2 }} bordered>
              <Descriptions.Item label="Tipo de Reporte">
                {vistaPrevia.tipo_nombre}
              </Descriptions.Item>
              <Descriptions.Item label="Formato">
                <Tag color={vistaPrevia.formato === 'pdf' ? 'red' : 'green'}>
                  {vistaPrevia.formato?.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Rango de Fechas">
                {vistaPrevia.fecha_inicio} - {vistaPrevia.fecha_fin}
              </Descriptions.Item>
              <Descriptions.Item label="Registros a Incluir">
                <Text strong>{vistaPrevia.total_registros}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Tamaño Estimado">
                {vistaPrevia.tamanio_estimado}
              </Descriptions.Item>
              <Descriptions.Item label="Tiempo Estimado">
                {vistaPrevia.tiempo_estimado}
              </Descriptions.Item>
            </Descriptions>

            <Alert
              message="Información"
              description={`El reporte incluirá ${vistaPrevia.total_registros} registros del período seleccionado.`}
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          </Card>
        ) : (
          <Alert
            message="No se pudo generar la vista previa"
            type="warning"
            showIcon
          />
        )}
      </div>
    );
  };

  const renderPaso3 = () => {
    return (
      <div>
        {generando ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <LoadingOutlined style={{ fontSize: 64, color: '#1890ff' }} />
            <Title level={3} style={{ marginTop: 24 }}>
              Generando Reporte…
            </Title>
            <Paragraph type="secondary">
              Por favor espere mientras se genera el reporte
            </Paragraph>
            <Progress
              percent={progresoGeneracion}
              status="active"
              strokeColor={{ from: '#108ee9', to: '#87d068' }}
              style={{ marginBottom: 32 }}
            />

            <Timeline
              mode="alternate"
              style={{ textAlign: 'left', marginTop: 24 }}
              items={[
                {
                  color: progresoGeneracion > 0 ? 'green' : 'gray',
                  children: (
                    <>
                      <Text strong>Validando datos</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {progresoGeneracion > 0 ? '✓ Completado' : 'En espera...'}
                      </Text>
                    </>
                  )
                },
                {
                  color: progresoGeneracion > 30 ? 'green' : progresoGeneracion > 0 ? 'blue' : 'gray',
                  children: (
                    <>
                      <Text strong>Consultando base de datos</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {progresoGeneracion > 30 ? '✓ Completado' : progresoGeneracion > 0 ? '⟳ En proceso...' : 'En espera...'}
                      </Text>
                    </>
                  )
                },
                {
                  color: progresoGeneracion > 60 ? 'green' : progresoGeneracion > 30 ? 'blue' : 'gray',
                  children: (
                    <>
                      <Text strong>Procesando información</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {progresoGeneracion > 60 ? '✓ Completado' : progresoGeneracion > 30 ? '⟳ En proceso...' : 'En espera...'}
                      </Text>
                    </>
                  )
                },
                {
                  color: progresoGeneracion > 90 ? 'green' : progresoGeneracion > 60 ? 'blue' : 'gray',
                  children: (
                    <>
                      <Text strong>Generando archivo</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {progresoGeneracion > 90 ? '✓ Completado' : progresoGeneracion > 60 ? '⟳ En proceso...' : 'En espera...'}
                      </Text>
                    </>
                  )
                },
                {
                  color: progresoGeneracion === 100 ? 'green' : 'gray',
                  children: (
                    <>
                      <Text strong>Finalizado</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {progresoGeneracion === 100 ? '✓ Listo para descargar' : 'En espera...'}
                      </Text>
                    </>
                  )
                }
              ]}
            />
          </div>
        ) : reporteGenerado ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <CheckCircleOutlined
              style={{ fontSize: 64, color: '#52c41a', marginBottom: 24 }}
            />
            <Title level={3}>¡Reporte Generado Exitosamente!</Title>
            <Paragraph type="secondary">
              El reporte se ha generado correctamente y está listo para descargar
            </Paragraph>

            <Card style={{ marginTop: 24, textAlign: 'left' }}>
              <Descriptions column={1} bordered>
                <Descriptions.Item label="Nombre">
                  {reporteGenerado.nombre}
                </Descriptions.Item>
                <Descriptions.Item label="Formato">
                  <Tag color={reporteGenerado.formato === 'pdf' ? 'red' : 'green'}>
                    {reporteGenerado.formato?.toUpperCase()}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Tamaño">
                  {reporteGenerado.tamanio}
                </Descriptions.Item>
                <Descriptions.Item label="Registros">
                  {reporteGenerado.total_registros}
                </Descriptions.Item>
                <Descriptions.Item label="Fecha Generación">
                  {dayjs(reporteGenerado.fecha_generacion).format(
                    'DD/MM/YYYY HH:mm'
                  )}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            <Space size="large" style={{ marginTop: 32 }}>
              <Button
                type="primary"
                size="large"
                icon={<DownloadOutlined />}
                onClick={handleDescargarReporte}
              >
                Descargar Reporte
              </Button>
              <Button size="large" onClick={handleGenerarOtro}>
                Generar Otro Reporte
              </Button>
              <Button size="large" onClick={handleVolver}>
                Volver al Listado
              </Button>
            </Space>
          </div>
        ) : null}
      </div>
    );
  };

  // ==========================================================================
  // RENDER PRINCIPAL
  // ==========================================================================
  return (
    <div className="generar-reporte-container">
      <Card
        title={
          <Space>
            <FileTextOutlined style={{ fontSize: 24, color: '#722ed1' }} />
            <span style={{ fontSize: 20, fontWeight: 600 }}>Generar Reporte</span>
          </Space>
        }
        extra={
          <Button icon={<ArrowLeftOutlined />} onClick={handleVolver}>
            Volver
          </Button>
        }
      >
        <Steps current={pasoActual} style={{ marginBottom: 32 }}>
          <Step
            title="Tipo de Reporte"
            icon={<FileTextOutlined />}
            description="Seleccione el tipo"
          />
          <Step
            title="Configuración"
            icon={<SettingOutlined />}
            description="Configure parámetros"
          />
          <Step
            title="Vista Previa"
            icon={<EyeOutlined />}
            description="Revise antes de generar"
          />
          <Step
            title="Generación"
            icon={generando ? <LoadingOutlined /> : <CheckCircleOutlined />}
            description="Genere el reporte"
          />
        </Steps>

        <Form form={form} layout="vertical">
          {pasoActual === 0 && renderPaso0()}
          {pasoActual === 1 && renderPaso1()}
          {pasoActual === 2 && renderPaso2()}
          {pasoActual === 3 && renderPaso3()}
        </Form>

        {pasoActual < 3 && (
          <>
            <Divider />
            <Space>
              {pasoActual > 0 && (
                <Button size="large" onClick={handlePasoAnterior}>
                  Anterior
                </Button>
              )}
              <Button
                type="primary"
                size="large"
                onClick={handleSiguientePaso}
                loading={loading || generando}
              >
                {pasoActual === 2 ? 'Generar Reporte' : 'Siguiente'}
              </Button>
            </Space>
          </>
        )}
      </Card>
    </div>
  );
};

export default GenerarReportePage;
