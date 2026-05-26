import React, { useState, useEffect, useCallback } from 'react';
import { Form, Input, InputNumber, Select, Button, Card, Space, Row, Col, Alert, Divider, Typography, Skeleton, Tag } from 'antd';
import { SaveOutlined, CloseOutlined, HeartOutlined, UserOutlined, WarningOutlined, MedicineBoxOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { triajeService, TriajeEnfermeria } from '../../services/triajeService';
import { pacientesService } from '../../services/pacientesService';
import { datosClinicosService } from '../../services/datosClinicosService';
import { useAntdApp } from '../../hooks/useMessage';

const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;

const FormularioTriaje: React.FC = () => {
    const [form] = Form.useForm();
    const navigate = useNavigate();
    const { id } = useParams<{ id: string }>();
    const { message } = useAntdApp();

    const [loading, setLoading] = useState(false);
    const [dataLoading, setDataLoading] = useState(false);
    const [pacientes, setPacientes] = useState<any[]>([]);
    const [imc, setImc] = useState<number | null>(null);
    const [alertas, setAlertas] = useState<string[]>([]);
    const [datosAnteriores, setDatosAnteriores] = useState<{
        mensaje: string;
        tipo: 'success' | 'info' | 'warning';
    } | null>(null);

    const cargarDatos = useCallback(async () => {
        setDataLoading(true);
        try {
            const pacientesData = await pacientesService.getAll();
            setPacientes(pacientesData);
        } catch (error) {
            message.error('Error al cargar la lista de pacientes');
        } finally {
            setDataLoading(false);
        }
    }, [message]);

    const calcularAlertas = useCallback((valores?: any) => {
        const alertasDetectadas: string[] = [];
        const data = valores || form.getFieldsValue();

        if (data.presion_sistolica >= 140 || data.presion_diastolica >= 90) {
            alertasDetectadas.push('⚠️ Presión arterial elevada (Posible Hipertensión)');
        }

        if (data.temperatura >= 38) {
            alertasDetectadas.push('⚠️ Fiebre detectada');
        } else if (data.temperatura < 35 && data.temperatura > 0) {
            alertasDetectadas.push('⚠️ Hipotermia detectada');
        }

        if (data.frecuencia_cardiaca > 100) {
            alertasDetectadas.push('⚠️ Taquicardia detectada');
        } else if (data.frecuencia_cardiaca < 60 && data.frecuencia_cardiaca > 0) {
            alertasDetectadas.push('⚠️ Bradicardia detectada');
        }

        if (data.saturacion_oxigeno && data.saturacion_oxigeno < 95) {
            alertasDetectadas.push('⚠️ Saturación de oxígeno baja (Hipoxia)');
        }

        setAlertas(alertasDetectadas);
    }, [form]);

    const cargarTriaje = useCallback(async (triajeId: number) => {
        setLoading(true);
        try {
            const triaje = await triajeService.getById(triajeId);
            form.setFieldsValue(triaje);
            if (triaje.imc) setImc(triaje.imc);
            calcularAlertas(triaje);
        } catch (error) {
            message.error('Error al cargar el registro de triaje');
        } finally {
            setLoading(false);
        }
    }, [form, message, calcularAlertas]);

    useEffect(() => {
        cargarDatos();
        if (id) {
            cargarTriaje(parseInt(id));
        }
    }, [id, cargarDatos, cargarTriaje]);

    const handlePacienteChange = async (pacienteId: number) => {
        if (id) return;

        setLoading(true);
        setDatosAnteriores(null);

        try {
            const datosCompletos = await datosClinicosService.obtenerDatosCompletos(pacienteId);
            const { signosVitales, antecedentes, embarazoActual, alertas: alertasGeneradas, fuentes } = datosCompletos;

            const tieneAntecedentesRiesgo = antecedentes && (antecedentes.enfermedades_cronicas || antecedentes.enfermedades_previas);
            const tieneEmbarazoActivo = !!embarazoActual;

            const alertasIniciales: string[] = [];
            if (tieneAntecedentesRiesgo) {
                alertasIniciales.push('⚠️ Paciente con antecedentes médicos de riesgo');
            }
            if (tieneEmbarazoActivo) {
                alertasIniciales.push('🤰 Paciente con embarazo activo registrado');
            }

            setAlertas([...alertasIniciales, ...alertasGeneradas]);

            const datosFormulario: any = {
                peso_kg: signosVitales.peso_kg,
                talla_cm: signosVitales.talla_cm,
                perimetro_abdominal_cm: signosVitales.perimetro_abdominal_cm,
                presion_sistolica: signosVitales.presion_sistolica,
                presion_diastolica: signosVitales.presion_diastolica,
                temperatura: signosVitales.temperatura,
                frecuencia_cardiaca: signosVitales.frecuencia_cardiaca,
                frecuencia_respiratoria: signosVitales.frecuencia_respiratoria,
                saturacion_oxigeno: signosVitales.saturacion_oxigeno,
                dolor_escala: signosVitales.dolor_escala,
            };

            form.setFieldsValue(datosFormulario);
            if (signosVitales.imc) setImc(signosVitales.imc);

            if (fuentes.length > 0) {
                setDatosAnteriores({
                    mensaje: `✓ Antecedentes recuperados de registros previos`,
                    tipo: 'info'
                });
            }
        } catch (error) {
        } finally {
            setLoading(false);
        }
    };

    const calcularIMC = useCallback(() => {
        const peso = form.getFieldValue('peso_kg');
        const talla = form.getFieldValue('talla_cm');

        if (peso && talla) {
            const tallaMetros = talla / 100;
            const imcCalculado = peso / (tallaMetros * tallaMetros);
            setImc(parseFloat(imcCalculado.toFixed(2)));
        }
    }, [form]);

    const handleValuesChange = (changedValues: any, allValues: any) => {
        if ('peso_kg' in changedValues || 'talla_cm' in changedValues) {
            calcularIMC();
        }

        if ('presion_sistolica' in changedValues || 'presion_diastolica' in changedValues ||
            'temperatura' in changedValues || 'frecuencia_cardiaca' in changedValues ||
            'saturacion_oxigeno' in changedValues) {
            calcularAlertas(allValues);
        }
    };

    const handleSubmit = async (values: any) => {
        setLoading(true);
        try {
            const triajeData: Partial<TriajeEnfermeria> = {
                ...values,
                imc: imc || undefined,
                alertas: alertas,
            };

            if (id) {
                await triajeService.update(parseInt(id), triajeData);
                message.success('Triaje actualizado correctamente');
            } else {
                await triajeService.create(triajeData);
                message.success('Triaje registrado correctamente');
            }

            navigate('/dashboard/triaje');
        } catch (error: any) {
            message.error('Error al procesar el registro de triaje');
        } finally {
            setLoading(false);
        }
    };

    const getClasificacionIMC = (imcValue: number): string => {
        if (imcValue < 18.5) return 'Bajo peso';
        if (imcValue < 25) return 'Normal';
        if (imcValue < 30) return 'Sobrepeso';
        if (imcValue < 35) return 'Obesidad I';
        if (imcValue < 40) return 'Obesidad II';
        return 'Obesidad III';
    };

    return (
        <div className="animate-fade-in" style={{ padding: 24 }}>
            <Card className="shadow-card overflow-hidden">
                <div className="blue-gradient-header" style={{ margin: '-24px -24px 24px -24px', padding: '24px' }}>
                    <Row justify="space-between" align="middle">
                        <Col>
                            <Title level={2} style={{ color: '#fff', margin: 0 }}>
                                <MedicineBoxOutlined /> {id ? 'Editar Triaje' : 'Nuevo Triaje de Enfermería'}
                            </Title>
                            <Text style={{ color: 'rgba(255,255,255,0.8)' }}>
                                Evaluación clínica y control de signos vitales
                            </Text>
                        </Col>
                        <Col>
                            <Button ghost icon={<CloseOutlined />} onClick={() => navigate('/dashboard/triaje')}>
                                Cancelar
                            </Button>
                        </Col>
                    </Row>
                </div>

                {alertas.length > 0 && (
                    <Alert
                        message={<Text strong>Alertas de Riesgo Detectadas</Text>}
                        description={
                            <ul style={{ margin: 0, paddingLeft: 20 }}>
                                {alertas.map((alerta) => (
                                    <li key={alerta}>{alerta}</li>
                                ))}
                            </ul>
                        }
                        type="error"
                        showIcon
                        icon={<WarningOutlined className="status-pulse" />}
                        style={{ marginBottom: 24, borderRadius: '8px' }}
                    />
                )}

                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                    onValuesChange={handleValuesChange}
                    autoComplete="off"
                    requiredMark="optional"
                >
                    <Row gutter={24}>
                        <Col xs={24} md={14}>
                            <Card type="inner" title={<><UserOutlined /> Datos del Paciente</>} className="h-full">
                                {dataLoading ? (
                                    <Skeleton active />
                                ) : (
                                    <Form.Item
                                        label="Seleccionar Paciente"
                                        name="paciente"
                                        rules={[{ required: true, message: 'Es obligatorio seleccionar un paciente' }]}
                                    >
                                        <Select
                                            placeholder="Buscar paciente por nombre o CI..."
                                            showSearch
                                            size="large"
                                            optionFilterProp="children"
                                            onChange={handlePacienteChange}
                                            loading={loading}
                                            disabled={!!id}
                                        >
                                            {pacientes.map((p) => (
                                                <Option key={p.id} value={p.id}>
                                                    {p.nombre_completo || `${p.nombre} ${p.apellido_paterno}`} - {p.id_clinico || p.ci}
                                                </Option>
                                            ))}
                                        </Select>
                                    </Form.Item>
                                )}
                                {datosAnteriores && (
                                    <Alert
                                        message={datosAnteriores.mensaje}
                                        type={datosAnteriores.tipo}
                                        showIcon
                                        closable
                                        onClose={() => setDatosAnteriores(null)}
                                        style={{ marginTop: 8 }}
                                    />
                                )}
                            </Card>
                        </Col>
                        <Col xs={24} md={10}>
                            <Card type="inner" title={<><ClockCircleOutlined /> Prioridad y Estado</>} className="h-full">
                                <Row gutter={16}>
                                    <Col span={12}>
                                        <Form.Item
                                            label="Prioridad"
                                            name="prioridad"
                                            initialValue="normal"
                                            rules={[{ required: true }]}
                                        >
                                            <Select size="large">
                                                <Option value="urgente"><Tag color="red">URGENTE</Tag></Option>
                                                <Option value="alto"><Tag color="orange">ALTO</Tag></Option>
                                                <Option value="normal"><Tag color="blue">NORMAL</Tag></Option>
                                                <Option value="bajo"><Tag color="green">BAJO</Tag></Option>
                                            </Select>
                                        </Form.Item>
                                    </Col>
                                    <Col span={12}>
                                        <Form.Item
                                            label="Nivel Conciencia"
                                            name="nivel_conciencia"
                                            initialValue="alerta"
                                        >
                                            <Select size="large">
                                                <Option value="alerta">Alerta</Option>
                                                <Option value="somnoliento">Somnoliento</Option>
                                                <Option value="estuporoso">Estuporoso</Option>
                                                <Option value="inconsciente">Inconsciente</Option>
                                            </Select>
                                        </Form.Item>
                                    </Col>
                                </Row>
                            </Card>
                        </Col>
                    </Row>

                    <Divider orientation="left"><HeartOutlined /> Signos Vitales y Antropometría</Divider>

                    <Row gutter={[24, 0]}>
                        <Col xs={24} lg={16}>
                            <Card type="inner" className="mb-4">
                                <Row gutter={16}>
                                    <Col xs={12} sm={6}>
                                        <Form.Item label="P. Sistólica" name="presion_sistolica" rules={[{ required: true }]}>
                                            <InputNumber className="w-full" size="large" addonAfter="mmHg" />
                                        </Form.Item>
                                    </Col>
                                    <Col xs={12} sm={6}>
                                        <Form.Item label="P. Diastólica" name="presion_diastolica" rules={[{ required: true }]}>
                                            <InputNumber className="w-full" size="large" addonAfter="mmHg" />
                                        </Form.Item>
                                    </Col>
                                    <Col xs={12} sm={6}>
                                        <Form.Item label="Temperatura" name="temperatura" rules={[{ required: true }]}>
                                            <InputNumber className="w-full" size="large" addonAfter="°C" step={0.1} />
                                        </Form.Item>
                                    </Col>
                                    <Col xs={12} sm={6}>
                                        <Form.Item label="F. Cardíaca" name="frecuencia_cardiaca" rules={[{ required: true }]}>
                                            <InputNumber className="w-full" size="large" addonAfter="bpm" />
                                        </Form.Item>
                                    </Col>
                                    <Col xs={12} sm={6}>
                                        <Form.Item label="F. Resp." name="frecuencia_respiratoria" rules={[{ required: true }]}>
                                            <InputNumber className="w-full" size="large" addonAfter="rpm" />
                                        </Form.Item>
                                    </Col>
                                    <Col xs={12} sm={6}>
                                        <Form.Item label="Saturación" name="saturacion_oxigeno">
                                            <InputNumber className="w-full" size="large" addonAfter="%" />
                                        </Form.Item>
                                    </Col>
                                    <Col xs={12} sm={6}>
                                        <Form.Item label="Dolor (0-10)" name="dolor_escala">
                                            <InputNumber className="w-full" size="large" min={0} max={10} />
                                        </Form.Item>
                                    </Col>
                                </Row>
                            </Card>
                        </Col>
                        <Col xs={24} lg={8}>
                            <Card type="inner" className="mb-4">
                                <Row gutter={16}>
                                    <Col span={12}>
                                        <Form.Item label="Peso" name="peso_kg" rules={[{ required: true }]}>
                                            <InputNumber className="w-full" size="large" addonAfter="kg" step={0.1} />
                                        </Form.Item>
                                    </Col>
                                    <Col span={12}>
                                        <Form.Item label="Talla" name="talla_cm" rules={[{ required: true }]}>
                                            <InputNumber className="w-full" size="large" addonAfter="cm" />
                                        </Form.Item>
                                    </Col>
                                    <Col span={24}>
                                        {imc !== null && (
                                            <div className="imc-display" style={{
                                                padding: '12px',
                                                borderRadius: '8px',
                                                backgroundColor: '#f0f5ff',
                                                border: '1px solid #adc6ff',
                                                textAlign: 'center'
                                            }}>
                                                <Text type="secondary">IMC Calculado:</Text>
                                                <Title level={4} style={{ margin: 0 }}>{imc}</Title>
                                                <Tag color="processing">{getClasificacionIMC(imc)}</Tag>
                                            </div>
                                        )}
                                    </Col>
                                </Row>
                            </Card>
                        </Col>
                    </Row>

                    <Divider orientation="left"><MedicineBoxOutlined /> Motivo de Consulta y Observaciones</Divider>

                    <Row gutter={16}>
                        <Col span={24}>
                            <Form.Item
                                label="Motivo de la Visita"
                                name="motivo_visita"
                                rules={[{ required: true, message: 'Debe ingresar el motivo de consulta' }]}
                            >
                                <TextArea
                                    rows={4}
                                    placeholder="Describa el motivo principal de la visita y síntomas actuales..."
                                    className="custom-textarea"
                                    maxLength={1000}
                                    showCount
                                />
                            </Form.Item>
                        </Col>
                        <Col span={24}>
                            <Form.Item label="Observaciones de Enfermería" name="observaciones">
                                <TextArea rows={2} placeholder="Observaciones adicionales, hallazgos físicos notables, etc." />
                            </Form.Item>
                        </Col>
                    </Row>

                    <div style={{ marginTop: 24, padding: '16px', background: '#f9f9f9', borderRadius: '8px', textAlign: 'right' }}>
                        <Space size="large">
                            <Button size="large" onClick={() => navigate('/dashboard/triaje')}>
                                Cancelar
                            </Button>
                            <Button
                                type="primary"
                                htmlType="submit"
                                loading={loading}
                                icon={<SaveOutlined />}
                                size="large"
                                className="btn-primary-gradient"
                                style={{ minWidth: 200 }}
                            >
                                {id ? 'Guardar Cambios' : 'Registrar Triaje'}
                            </Button>
                        </Space>
                    </div>
                </Form>
            </Card>
        </div>
    );
};

export default FormularioTriaje;

