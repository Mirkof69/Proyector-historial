import React, { useState, useEffect, useCallback } from 'react';
import { Form, Button, Card, Space, Row, Col, Alert, Typography, Steps } from 'antd';
import {
    SaveOutlined, CloseOutlined, WarningOutlined, MedicineBoxOutlined,
    UserOutlined, HeartOutlined, FileTextOutlined, ArrowLeftOutlined, ArrowRightOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { triajeService, TriajeEnfermeria } from '../../services/triajeService';
import { pacientesService } from '../../services/pacientesService';
import { datosClinicosService } from '../../services/datosClinicosService';
import { useAntdApp } from '../../hooks/useMessage';
import SeccionDatosPacienteTriaje from './components/SeccionDatosPacienteTriaje';
import SeccionSignosVitalesTriaje from './components/SeccionSignosVitalesTriaje';
import SeccionMotivoTriaje from './components/SeccionMotivoTriaje';

const { Title, Text } = Typography;

// Flujo guiado: la enfermera avanza paso a paso y el sistema valida cada paso
// antes de dejar avanzar — pensado para uso bajo presión (menos campos a la
// vista = menos errores). Los campos de pasos ocultos siguen montados para no
// perder valores.
const PASOS_TRIAJE = [
    {
        titulo: 'Paciente',
        descripcion: 'Identificación y prioridad',
        icono: <UserOutlined />,
        campos: ['paciente', 'prioridad', 'nivel_conciencia'],
    },
    {
        titulo: 'Signos vitales',
        descripcion: 'Medición y registro',
        icono: <HeartOutlined />,
        campos: [
            'presion_sistolica', 'presion_diastolica', 'temperatura',
            'frecuencia_cardiaca', 'frecuencia_respiratoria',
            'saturacion_oxigeno', 'dolor_escala', 'peso_kg', 'talla_cm',
        ],
    },
    {
        titulo: 'Motivo y evaluación',
        descripcion: 'Motivo de consulta y observaciones',
        icono: <FileTextOutlined />,
        campos: ['motivo_visita', 'observaciones'],
    },
];

const FormularioTriaje: React.FC = () => {
    const [form] = Form.useForm();
    const navigate = useNavigate();
    const { id } = useParams<{ id: string }>();
    const { message } = useAntdApp();

    const [loading, setLoading] = useState(false);
    const [pasoActual, setPasoActual] = useState(0);
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

    // Avanza solo si los campos del paso actual validan; el error queda a la
    // vista y el foco va al primer campo inválido.
    const siguientePaso = async () => {
        try {
            await form.validateFields(PASOS_TRIAJE[pasoActual].campos);
            setPasoActual(pasoActual + 1);
        } catch {
            message.warning('Complete los campos requeridos de este paso antes de continuar');
        }
    };

    // Permite volver atrás con el Steps clickeable; para saltar hacia adelante
    // exige validar los pasos intermedios.
    const irAPaso = async (paso: number) => {
        if (paso <= pasoActual) {
            setPasoActual(paso);
            return;
        }
        try {
            for (let i = pasoActual; i < paso; i++) {
                await form.validateFields(PASOS_TRIAJE[i].campos);
            }
            setPasoActual(paso);
        } catch {
            message.warning('Complete los campos requeridos antes de avanzar');
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

                <Steps
                    current={pasoActual}
                    onChange={irAPaso}
                    style={{ marginBottom: 32 }}
                    items={PASOS_TRIAJE.map((p) => ({
                        title: p.titulo,
                        description: p.descripcion,
                        icon: p.icono,
                    }))}
                />

                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                    onValuesChange={handleValuesChange}
                    autoComplete="off"
                    requiredMark="optional"
                >
                    {/* Los pasos ocultos quedan montados (display:none) para conservar valores */}
                    <div style={{ display: pasoActual === 0 ? 'block' : 'none' }}>
                        <SeccionDatosPacienteTriaje
                            pacientes={pacientes}
                            dataLoading={dataLoading}
                            loading={loading}
                            disabled={!!id}
                            onPacienteChange={handlePacienteChange}
                            datosAnteriores={datosAnteriores}
                            onCloseDatosAnteriores={() => setDatosAnteriores(null)}
                        />
                    </div>

                    <div style={{ display: pasoActual === 1 ? 'block' : 'none' }}>
                        <SeccionSignosVitalesTriaje imc={imc} />
                    </div>

                    <div style={{ display: pasoActual === 2 ? 'block' : 'none' }}>
                        <SeccionMotivoTriaje />
                    </div>

                    <div style={{ marginTop: 24, padding: '16px', background: '#f9f9f9', borderRadius: '8px' }}>
                        <Row justify="space-between" align="middle">
                            <Col>
                                {pasoActual > 0 && (
                                    <Button size="large" icon={<ArrowLeftOutlined />} onClick={() => setPasoActual(pasoActual - 1)}>
                                        Paso anterior
                                    </Button>
                                )}
                            </Col>
                            <Col>
                                <Space size="large">
                                    <Button size="large" onClick={() => navigate('/dashboard/triaje')}>
                                        Cancelar
                                    </Button>
                                    {pasoActual < PASOS_TRIAJE.length - 1 ? (
                                        <Button
                                            type="primary"
                                            size="large"
                                            style={{ minWidth: 200 }}
                                            onClick={siguientePaso}
                                        >
                                            Continuar <ArrowRightOutlined />
                                        </Button>
                                    ) : (
                                        <Button
                                            type="primary"
                                            htmlType="submit"
                                            loading={loading}
                                            icon={<SaveOutlined />}
                                            size="large"
                                            className="btn-primary-gradient"
                                            style={{ minWidth: 200 }}
                                        >
                                            {id ? 'Guardar cambios del triaje' : 'Registrar triaje'}
                                        </Button>
                                    )}
                                </Space>
                            </Col>
                        </Row>
                    </div>
                </Form>
            </Card>
        </div>
    );
};

export default FormularioTriaje;
