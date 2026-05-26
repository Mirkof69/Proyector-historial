import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Form,
  Input,
  InputNumber,
  Select,
  Button,
  Card,
  Space,
  Row,
  Col,
  Alert,
  Divider,
  DatePicker,
  Radio,
  Progress,
  Typography,
  Skeleton,
  Empty,
  Descriptions,
  Tag
} from 'antd';
import {
  SaveOutlined,
  CloseOutlined,
  MedicineBoxOutlined,
  UserOutlined,
  WarningOutlined,
  SafetyOutlined,
  CalendarOutlined,
  InfoCircleOutlined,
  ArrowLeftOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { vacunasService, RegistroVacunaCreate, TipoVacuna } from '../../services/vacunasService';
import { pacientesService } from '../../services/pacientesService';
import { datosClinicosService } from '../../services/datosClinicosService';
import { authService } from '../../services/authService';
import { useAntdApp } from '../../hooks/useMessage';
import './Vacunas.css';

const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;

const FormularioVacuna: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const { id } = useParams<{ id: string }>();

  // Estados
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [pacientes, setPacientes] = useState<any[]>([]);
  const [tiposVacunas, setTiposVacunas] = useState<TipoVacuna[]>([]);
  const [vacunaSeleccionada, setVacunaSeleccionada] = useState<TipoVacuna | null>(null);
  const [proximaDosisCalculada, setProximaDosisCalculada] = useState<string>('');
  const [progresoDosis, setProgresoDosis] = useState<number>(0);
  const [alertas, setAlertas] = useState<string[]>([]);
  const [historialVacunacion, setHistorialVacunacion] = useState<{
    mensaje: string;
    tipo: 'success' | 'info' | 'warning';
    totalVacunas?: number;
  } | null>(null);

  const cargarRegistroRef = useRef<(registroId: number, tipos?: TipoVacuna[]) => Promise<void>>(async () => {});

  const cargarDatos = useCallback(async (registroId?: number) => {
    try {
      setLoading(true);
      const [pacientesData, vacunasData] = await Promise.all([
        pacientesService.getAll(),
        vacunasService.getTiposVacunas({ page_size: 1000 })
      ]);

      const pacientesArr = Array.isArray(pacientesData) ? pacientesData : [];
      const vacunas = vacunasData.results || vacunasData;
      const tiposArr = Array.isArray(vacunas) ? vacunas : [];
      
      setPacientes(pacientesArr);
      setTiposVacunas(tiposArr);

      if (registroId && tiposArr.length > 0) {
        await cargarRegistroRef.current(registroId, tiposArr);
      }
    } catch (error) {
      message.error('Error al cargar datos del sistema');
    } finally {
      setLoading(false);
    }
  }, [message]);

  const cargarRegistro = useCallback(async (registroId: number, tipos?: TipoVacuna[]) => {
    try {
      setLoading(true);
      const registro = await vacunasService.getRegistroById(registroId);

      const formValues = {
        ...registro,
        fecha_aplicacion: registro.fecha_aplicacion ? dayjs(registro.fecha_aplicacion) : null,
        proxima_dosis_fecha: registro.proxima_dosis_fecha ? dayjs(registro.proxima_dosis_fecha) : null,
      };

      form.setFieldsValue(formValues);

      const tiposToUse = tipos || tiposVacunas;
      if (registro.tipo_vacuna && tiposToUse.length > 0) {
        const vacuna = tiposToUse.find(v => v.id === registro.tipo_vacuna);
        if (vacuna) {
          setVacunaSeleccionada(vacuna);
          setProgresoDosis(Math.min((registro.numero_dosis / vacuna.dosis_requeridas) * 100, 100));
        }
      }
    } catch (error) {
      message.error('No se pudo cargar la información del registro');
    } finally {
      setLoading(false);
    }
  }, [form, message, tiposVacunas]);

  useEffect(() => {
    cargarRegistroRef.current = cargarRegistro;
  }, [cargarRegistro]);

  useEffect(() => {
    if (id) {
      cargarDatos(parseInt(id));
    } else {
      cargarDatos();
    }
  }, [id, cargarDatos]);

  const calcularProgresoDosis = useCallback((dosisActual: number, dosisRequeridas: number) => {
    const progreso = (dosisActual / dosisRequeridas) * 100;
    setProgresoDosis(Math.min(progreso, 100));
  }, []);

  const handlePacienteChange = useCallback(async (pacienteId: number) => {
    if (id) return;

    setLoading(true);
    setHistorialVacunacion(null);

    try {
      const [historial, datosCompletos] = await Promise.all([
        vacunasService.getRegistrosPorPaciente(pacienteId, { page_size: 1000 }),
        datosClinicosService.obtenerDatosCompletos(pacienteId)
      ]);

      const registros = historial.results || [];
      const { antecedentes, embarazoActual } = datosCompletos;
      const mensajes: string[] = [];

      let tieneAlertas = false;

      if (registros.length > 0) {
        const vacunasUnicas = new Set(registros.map((r: any) => r.tipo_vacuna));
        mensajes.push(`${registros.length} dosis registradas (${vacunasUnicas.size} tipos)`);
      }

      if (embarazoActual?.embarazo) {
        mensajes.push('Embarazo activo');
        form.setFieldValue('embarazo', embarazoActual.embarazo.id);
      }

      if (antecedentes.alergias) {
        mensajes.push(`Alergias: ${antecedentes.alergias}`);
        tieneAlertas = true;
      }

      setHistorialVacunacion({
        mensaje: mensajes.length > 0 ? mensajes.join(' | ') : 'Sin antecedentes de inmunización registrados.',
        tipo: tieneAlertas ? 'warning' : 'info',
        totalVacunas: registros.length
      });
    } catch (error) {
    } finally {
      setLoading(false);
    }
  }, [id, form]);

  const handleVacunaChange = useCallback((tipoVacunaId: number) => {
    const vacuna = tiposVacunas.find(v => v.id === tipoVacunaId);
    setVacunaSeleccionada(vacuna || null);

    const fechaAplicacion = form.getFieldValue('fecha_aplicacion');
    if (vacuna && vacuna.intervalo_dosis_dias && fechaAplicacion) {
      const proximaFecha = dayjs(fechaAplicacion).add(vacuna.intervalo_dosis_dias, 'day');
      setProximaDosisCalculada(proximaFecha.toISOString());
      form.setFieldValue('proxima_dosis_fecha', proximaFecha);
    }

    const numeroDosis = form.getFieldValue('numero_dosis') || 1;
    if (vacuna) {
      calcularProgresoDosis(numeroDosis, vacuna.dosis_requeridas);
      setAlertas([
        ...(vacuna.contraindicaciones ? [`Contraindicaciones: ${vacuna.contraindicaciones}`] : []),
        ...(vacuna.efectos_secundarios ? [`Efectos secundarios: ${vacuna.efectos_secundarios}`] : [])
      ]);
    }
  }, [tiposVacunas, form, calcularProgresoDosis]);

  const handleDosisChange = useCallback((dosis: number | null) => {
    if (vacunaSeleccionada && dosis !== null) {
      calcularProgresoDosis(dosis, vacunaSeleccionada.dosis_requeridas);
      if (dosis > vacunaSeleccionada.dosis_requeridas) {
        message.warning(`El esquema de esta vacuna contempla ${vacunaSeleccionada.dosis_requeridas} dosis.`);
      }
    }
  }, [vacunaSeleccionada, calcularProgresoDosis, message]);

  const handleFechaAplicacionChange = useCallback((fecha: dayjs.Dayjs | null) => {
    if (fecha && vacunaSeleccionada?.intervalo_dosis_dias) {
      const proximaFecha = dayjs(fecha).add(vacunaSeleccionada.intervalo_dosis_dias, 'day');
      setProximaDosisCalculada(proximaFecha.toISOString());
      form.setFieldValue('proxima_dosis_fecha', proximaFecha);
    }
  }, [vacunaSeleccionada, form]);

  const handleSubmit = async (values: any) => {
    setSubmitting(true);
    try {
      const registroData: RegistroVacunaCreate = {
        ...values,
        fecha_aplicacion: values.fecha_aplicacion ? values.fecha_aplicacion.toISOString() : new Date().toISOString(),
        proxima_dosis_fecha: values.proxima_dosis_fecha ? values.proxima_dosis_fecha.toISOString() : undefined,
        aplicado_por: authService.getCurrentUser()?.id || 1,
      };

      if (id) {
        await vacunasService.actualizarRegistro(parseInt(id), registroData);
        message.success('Registro de inmunización actualizado');
      } else {
        await vacunasService.crearRegistro(registroData);
        message.success('Registro de inmunización exitoso');
      }
      navigate('/dashboard/vacunas');
    } catch (error: any) {
      message.error('Error al guardar el registro');
    } finally {
      setSubmitting(false);
    }
  };

  const viasAdministracion = vacunasService.getViasAdministracion();

  return (
    <div className="animate-fade-in" style={{ padding: '24px' }}>
      <Card className="shadow-card overflow-hidden">
        <div className="blue-gradient-header" style={{ margin: '-24px -24px 24px -24px', padding: '32px' }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Space align="center" size="large">
                <Button
                  icon={<ArrowLeftOutlined />}
                  onClick={() => navigate('/dashboard/vacunas')}
                  className="back-button-white"
                />
                <div className="header-icon-container">
                  <SafetyOutlined style={{ fontSize: '32px', color: '#fff' }} />
                </div>
                <div>
                  <Title level={2} style={{ color: '#fff', margin: 0 }}>
                    {id ? 'Editar Registro' : 'Nueva Inmunización'}
                  </Title>
                  <Text style={{ color: 'rgba(255,255,255,0.85)' }}>Registro oficial de aplicación de vacunas y biológicos</Text>
                </div>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button
                  size="large"
                  icon={<CloseOutlined />}
                  onClick={() => navigate('/dashboard/vacunas')}
                >
                  Cancelar
                </Button>
                <Button
                  type="primary"
                  size="large"
                  icon={<SaveOutlined />}
                  onClick={() => form.submit()}
                  loading={submitting}
                  className="btn-success-gradient"
                >
                  {id ? 'Actualizar Registro' : 'Guardar Inmunización'}
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        {loading ? (
          <Skeleton active paragraph={{ rows: 12 }} style={{ padding: '24px' }} />
        ) : (
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{
              fecha_aplicacion: dayjs(),
              numero_dosis: 1,
              via_administracion: 'intramuscular',
            }}
            className="premium-form"
          >
            <Row gutter={24}>
              <Col xs={24} lg={16}>
                <Card title={<Space><UserOutlined /> Identificación y Biológico</Space>} className="form-section-card">
                  <Row gutter={16}>
                    <Col xs={24} md={12}>
                      <Form.Item
                        label="Paciente"
                        name="paciente"
                        rules={[{ required: true, message: 'Requerido' }]}
                      >
                        <Select
                          placeholder="Buscar paciente..."
                          showSearch
                          size="large"
                          onChange={handlePacienteChange}
                          filterOption={(input, option) =>
                            (option?.children as any).toLowerCase().includes(input.toLowerCase())
                          }
                        >
                          {pacientes.map((p) => (
                            <Option key={p.id} value={p.id}>
                              {p.nombre_completo || `${p.nombre} ${p.apellido_paterno}`} - {p.ci || p.id_clinico}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col xs={24} md={12}>
                      <Form.Item
                        label="Inmunógeno (Vacuna)"
                        name="tipo_vacuna"
                        rules={[{ required: true, message: 'Requerido' }]}
                      >
                        <Select
                          placeholder="Seleccionar vacuna..."
                          showSearch
                          size="large"
                          onChange={handleVacunaChange}
                          filterOption={(input, option) =>
                            (option?.children as any).toLowerCase().includes(input.toLowerCase())
                          }
                        >
                          {tiposVacunas.map((v) => (
                            <Option key={v.id} value={v.id}>
                              {v.nombre}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>

                  {historialVacunacion && (
                    <Alert
                      message={historialVacunacion.mensaje}
                      type={historialVacunacion.tipo}
                      showIcon
                      style={{ marginBottom: 20, borderRadius: '8px' }}
                    />
                  )}

                  <Row gutter={16}>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        label="Fecha y Hora de Aplicación"
                        name="fecha_aplicacion"
                        rules={[{ required: true, message: 'Requerido' }]}
                      >
                        <DatePicker
                          showTime
                          format="DD/MM/YYYY HH:mm"
                          style={{ width: '100%' }}
                          size="large"
                          onChange={handleFechaAplicacionChange}
                        />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        label="Número de Dosis"
                        name="numero_dosis"
                        rules={[{ required: true, message: 'Requerido' }]}
                      >
                        <InputNumber
                          min={1}
                          style={{ width: '100%' }}
                          size="large"
                          onChange={handleDosisChange}
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                </Card>

                <Card title={<Space><MedicineBoxOutlined /> Logística y Aplicación</Space>} className="form-section-card" style={{ marginTop: 24 }}>
                  <Row gutter={16}>
                    <Col xs={24} md={12}>
                      <Form.Item
                        label="Laboratorio / Fabricante"
                        name="laboratorio"
                        rules={[{ required: true, message: 'Requerido' }]}
                      >
                        <Input placeholder="Ej: Pfizer, Astra-Zeneca..." size="large" />
                      </Form.Item>
                    </Col>
                    <Col xs={24} md={12}>
                      <Form.Item
                        label="Lote"
                        name="lote"
                        rules={[{ required: true, message: 'Requerido' }]}
                      >
                        <Input placeholder="Ej: AB1234..." size="large" />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col xs={24} md={12}>
                      <Form.Item
                        label="Vía de Administración"
                        name="via_administracion"
                        rules={[{ required: true, message: 'Requerido' }]}
                      >
                        <Radio.Group buttonStyle="solid" style={{ width: '100%' }}>
                          {viasAdministracion.map(v => (
                            <Radio.Button key={v.value} value={v.value} style={{ width: '33.33%', textAlign: 'center' }}>
                              {v.label}
                            </Radio.Button>
                          ))}
                        </Radio.Group>
                      </Form.Item>
                    </Col>
                    <Col xs={24} md={12}>
                      <Form.Item
                        label="Sitio de Aplicación"
                        name="sitio_aplicacion"
                        rules={[{ required: true, message: 'Requerido' }]}
                      >
                        <Select placeholder="Seleccionar sitio..." size="large">
                          <Option value="deltoides_derecho">Deltoides derecho</Option>
                          <Option value="deltoides_izquierdo">Deltoides izquierdo</Option>
                          <Option value="muslo_derecho">Muslo derecho</Option>
                          <Option value="muslo_izquierdo">Muslo izquierdo</Option>
                          <Option value="otro">Otro</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>
                </Card>

                <Card title={<Space><ClockCircleOutlined /> Seguimiento y Observaciones</Space>} className="form-section-card" style={{ marginTop: 24 }}>
                  <Row gutter={16}>
                    <Col xs={24} md={12}>
                      <Form.Item
                        label="Próxima Dosis (Programación)"
                        name="proxima_dosis_fecha"
                      >
                        <DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} size="large" />
                      </Form.Item>
                    </Col>
                    <Col xs={24} md={12}>
                      {proximaDosisCalculada && (
                        <div style={{ background: '#f0f9ff', padding: '12px', borderRadius: '8px', border: '1px solid #bae6fd', marginTop: '28px' }}>
                          <Text type="secondary"><CalendarOutlined /> Sugerencia por esquema: </Text>
                          <Text strong>{dayjs(proximaDosisCalculada).format('DD/MM/YYYY')}</Text>
                        </div>
                      )}
                    </Col>
                  </Row>

                  <Form.Item label="Reacciones Adversas (ESAVI)" name="reacciones_adversas">
                    <TextArea rows={3} placeholder="Describa cualquier reacción..." />
                  </Form.Item>

                  <Form.Item label="Observaciones Clínicas" name="observaciones">
                    <TextArea rows={3} placeholder="Notas adicionales..." />
                  </Form.Item>
                </Card>
              </Col>

              <Col xs={24} lg={8}>
                <Card title={<Space><InfoCircleOutlined /> Guía del Esquema</Space>} className="sidebar-card">
                  {vacunaSeleccionada ? (
                    <div className="vacuna-guide-content">
                      <div className="progreso-container" style={{ textAlign: 'center', marginBottom: 24 }}>
                        <Progress
                          type="dashboard"
                          percent={progresoDosis}
                          strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
                        />
                        <div style={{ marginTop: 8 }}>
                          <Text strong>Cobertura: {progresoDosis.toFixed(0)}%</Text>
                          <br />
                          <Text type="secondary">
                            Dosis {form.getFieldValue('numero_dosis') || 0} de {vacunaSeleccionada.dosis_requeridas}
                          </Text>
                        </div>
                      </div>

                      <Descriptions column={1} size="small" bordered>
                        <Descriptions.Item label="Intervalo Min.">{vacunaSeleccionada.intervalo_dosis_dias || 0} días</Descriptions.Item>
                        <Descriptions.Item label="Embarazo">
                          {vacunaSeleccionada.obligatoria_embarazo ? <Tag color="error">Recomendada</Tag> : <Tag>Opcional</Tag>}
                        </Descriptions.Item>
                      </Descriptions>

                      {alertas.length > 0 && (
                        <div style={{ marginTop: 20 }}>
                          <Divider style={{ margin: '12px 0' }} />
                          {alertas.map((a) => (
                            <div key={`alerta-${a}`} style={{ marginBottom: 10, display: 'flex', gap: 8 }}>
                              <WarningOutlined style={{ color: '#faad14' }} />
                              <Text style={{ fontSize: '0.85em' }}>{a}</Text>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <Empty description="Seleccione una vacuna" />
                  )}
                </Card>
              </Col>
            </Row>
          </Form>
        )}
      </Card>
    </div>
  );
};

export default FormularioVacuna;
