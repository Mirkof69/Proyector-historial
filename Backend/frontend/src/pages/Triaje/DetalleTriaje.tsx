import React, { useState, useCallback, useMemo, useRef } from 'react';
import { Card, Descriptions, Tag, Button, Space, Alert, Row, Col, Progress, Divider, Typography, Skeleton } from 'antd';
import {
    ArrowLeftOutlined,
    HeartOutlined,
    UserOutlined,
    WarningOutlined,
    PrinterOutlined,
    EditOutlined,
    DashboardOutlined,
    MedicineBoxOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { triajeService, TriajeEnfermeria } from '../../services/triajeService';
import { useAntdApp } from '../../hooks/useMessage';

const { Title, Text } = Typography;

const DetalleTriaje: React.FC = () => {
    const navigate = useNavigate();
    const { id } = useParams<{ id: string }>();
    const { message } = useAntdApp();

    const [loading, setLoading] = useState(true);
    const [triaje, setTriaje] = useState<TriajeEnfermeria | null>(null);

    const cargarTriaje = useCallback(async (triajeId: number) => {
        setLoading(true);
        try {
            const data = await triajeService.getById(triajeId);
            setTriaje(data);
        } catch (error) {
            message.error('Error al cargar la información del triaje');
        } finally {
            setLoading(false);
        }
    }, [message]);

    const loadedIdRef = useRef<number | null>(null);
    if (id && loadedIdRef.current !== parseInt(id)) {
        loadedIdRef.current = parseInt(id);
        cargarTriaje(parseInt(id));
    }

    const getClasificacionIMC = useMemo(() => (imc: number) => {
        if (imc < 18.5) return { text: 'Bajo peso', color: 'blue' };
        if (imc < 25) return { text: 'Normal', color: 'green' };
        if (imc < 30) return { text: 'Sobrepeso', color: 'orange' };
        if (imc < 35) return { text: 'Obesidad I', color: 'volcano' };
        if (imc < 40) return { text: 'Obesidad II', color: 'red' };
        return { text: 'Obesidad III', color: 'red-inverse' };
    }, []);

    const getClasificacionPresion = useMemo(() => (sistolica: number, diastolica: number) => {
        if (sistolica >= 180 || diastolica >= 120) return { text: 'Crisis Hipertensiva', color: 'red-inverse' };
        if (sistolica >= 140 || diastolica >= 90) return { text: 'Hipertensión Stage 2', color: 'red' };
        if (sistolica >= 130 || diastolica >= 80) return { text: 'Hipertensión Stage 1', color: 'volcano' };
        if (sistolica >= 120 && diastolica < 80) return { text: 'Elevada', color: 'orange' };
        return { text: 'Normal', color: 'green' };
    }, []);

    const alertas = useMemo(() => {
        if (!triaje) return [];
        const items: string[] = [];

        if (triaje.presion_sistolica >= 140 || triaje.presion_diastolica >= 90) {
            items.push('Presión arterial elevada (Riesgo de Preeclampsia si es gestante)');
        }
        if (triaje.temperatura >= 38) {
            items.push('Proceso febril detectado');
        }
        if (triaje.frecuencia_cardiaca > 100) {
            items.push('Taquicardia sinusal');
        } else if (triaje.frecuencia_cardiaca < 60 && triaje.frecuencia_cardiaca > 0) {
            items.push('Bradicardia');
        }
        if (triaje.saturacion_oxigeno && triaje.saturacion_oxigeno < 95) {
            items.push('Saturación de oxígeno por debajo del rango normal');
        }
        if (triaje.alertas && Array.isArray(triaje.alertas)) {
            items.push(...triaje.alertas);
        }

        return items;
    }, [triaje]);

    if (loading) {
        return (
            <div style={{ padding: 24 }}>
                <Card className="shadow-card">
                    <Skeleton active avatar paragraph={{ rows: 10 }} />
                </Card>
            </div>
        );
    }

    if (!triaje) {
        return (
            <div style={{ padding: 24 }}>
                <Alert
                    message="Triaje no encontrado"
                    description="No se pudo encontrar el registro solicitado o ha sido eliminado."
                    type="error"
                    showIcon
                    action={
                        <Button type="primary" onClick={() => navigate('/dashboard/triaje')}>
                            Volver a la lista
                        </Button>
                    }
                />
            </div>
        );
    }

    const clasificacionIMC = triaje.imc ? getClasificacionIMC(Number(triaje.imc)) : null;
    const clasificacionPresion = getClasificacionPresion(triaje.presion_sistolica, triaje.presion_diastolica);

    return (
        <div className="animate-fade-in" style={{ padding: 24 }}>
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col span={24}>
                    <Card className="shadow-card overflow-hidden">
                        <div className="blue-gradient-header" style={{ margin: '-24px -24px 24px -24px', padding: '24px' }}>
                            <Row justify="space-between" align="middle">
                                <Col>
                                    <Space size="large">
                                        <Button
                                            icon={<ArrowLeftOutlined />}
                                            onClick={() => navigate('/dashboard/triaje')}
                                            ghost
                                        />
                                        <div>
                                            <Title level={2} style={{ color: '#fff', margin: 0 }}>
                                                Detalle de Evaluación de Triaje
                                            </Title>
                                            <Text style={{ color: 'rgba(255,255,255,0.8)' }}>
                                                ID Registro: #{triaje.id} | Fecha: {dayjs(triaje.fecha_registro).format('DD/MM/YYYY HH:mm')}
                                            </Text>
                                        </div>
                                    </Space>
                                </Col>
                                <Col>
                                    <Space>
                                        <Button icon={<PrinterOutlined />} onClick={() => window.print()}>
                                            Imprimir Informe
                                        </Button>
                                        <Button
                                            type="primary"
                                            icon={<EditOutlined />}
                                            onClick={() => navigate(`/dashboard/triaje/${triaje.id}/editar`)}
                                        >
                                            Editar Registro
                                        </Button>
                                    </Space>
                                </Col>
                            </Row>
                        </div>

                        {alertas.length > 0 && (
                            <Alert
                                message={<Text strong>Intervención Requerida / Alertas Clínicas</Text>}
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

                        <Row gutter={[24, 24]}>
                            <Col xs={24} lg={16}>
                                <section className="detail-section">
                                    <Title level={4}><UserOutlined /> Identificación del Paciente</Title>
                                    <Descriptions bordered column={{ xs: 1, sm: 2 }} className="custom-descriptions">
                                        <Descriptions.Item label="Nombre Completo" span={2}>
                                            <Text strong style={{ fontSize: '1.1em' }}>
                                                {triaje.paciente_info?.nombre_completo || triaje.paciente_nombre || 'No especificado'}
                                            </Text>
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Nro. Historia">
                                            {(triaje.paciente_info as any)?.id_clinico || (triaje.paciente_info as any)?.ci || '-'}
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Responsable Triaje">
                                            {triaje.enfermera_info?.nombre || 'Personal de Enfermería'}
                                        </Descriptions.Item>
                                    </Descriptions>

                                    <Divider />

                                    <Title level={4}><HeartOutlined /> Evaluación de Signos Vitales</Title>
                                    <Descriptions bordered column={{ xs: 1, sm: 2 }} className="custom-descriptions">
                                        <Descriptions.Item label="Presión Arterial">
                                            <Space>
                                                <Text strong>{triaje.presion_sistolica}/{triaje.presion_diastolica} mmHg</Text>
                                                <Tag color={clasificacionPresion.color}>{clasificacionPresion.text}</Tag>
                                            </Space>
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Temperatura">
                                            <Text strong>{triaje.temperatura}°C</Text>
                                            {triaje.temperatura >= 38 && <Tag color="red" style={{ marginLeft: 8 }}>Febrícula/Fiebre</Tag>}
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Frecuencia Cardíaca">
                                            <Text strong>{triaje.frecuencia_cardiaca} bpm</Text>
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Frecuencia Respiratoria">
                                            <Text strong>{triaje.frecuencia_respiratoria} rpm</Text>
                                        </Descriptions.Item>
                                        {triaje.saturacion_oxigeno && (
                                            <Descriptions.Item label="Saturación O₂">
                                                <Text strong>{triaje.saturacion_oxigeno}%</Text>
                                                {triaje.saturacion_oxigeno < 95 && <Tag color="red">Hipoxia</Tag>}
                                            </Descriptions.Item>
                                        )}
                                        {triaje.dolor_escala !== null && triaje.dolor_escala !== undefined && (
                                            <Descriptions.Item label="Escala de Dolor">
                                                <Text strong>{triaje.dolor_escala}/10</Text>
                                                <Tag color={triaje.dolor_escala! >= 7 ? 'red' : triaje.dolor_escala! >= 4 ? 'orange' : 'green'}>
                                                    {triaje.dolor_escala! >= 7 ? 'Severo' : triaje.dolor_escala! >= 4 ? 'Moderado' : 'Leve'}
                                                </Tag>
                                            </Descriptions.Item>
                                        )}
                                    </Descriptions>

                                    <Divider />

                                    <Title level={4}><DashboardOutlined /> Antropometría</Title>
                                    <Descriptions bordered column={{ xs: 1, sm: 3 }} className="custom-descriptions">
                                        <Descriptions.Item label="Peso Antropomético">
                                            <Text strong>{triaje.peso_kg}</Text> kg
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Talla/Estatura">
                                            <Text strong>{triaje.talla_cm}</Text> cm
                                        </Descriptions.Item>
                                        {triaje.perimetro_abdominal_cm && (
                                            <Descriptions.Item label="P. Abdominal">
                                                {triaje.perimetro_abdominal_cm} cm
                                            </Descriptions.Item>
                                        )}
                                        {triaje.imc && (
                                            <Descriptions.Item label="Estado Nutricional (IMC)" span={3}>
                                                <Space size="large">
                                                    <Text strong style={{ fontSize: '1.2em' }}>{Number(triaje.imc).toFixed(2)}</Text>
                                                    {clasificacionIMC && (
                                                        <Tag color={clasificacionIMC.color} style={{ padding: '4px 12px', fontSize: '1em' }}>
                                                            {clasificacionIMC.text.toUpperCase()}
                                                        </Tag>
                                                    )}
                                                </Space>
                                            </Descriptions.Item>
                                        )}
                                    </Descriptions>

                                    <Divider />

                                    <Title level={4}><MedicineBoxOutlined /> Evaluación Subjetiva y Motivo</Title>
                                    <Descriptions bordered column={1} className="custom-descriptions">
                                        <Descriptions.Item label="Motivo de la Visita">
                                            <div style={{ whiteSpace: 'pre-wrap', minHeight: '60px' }}>
                                                {triaje.motivo_visita || triaje.motivo_consulta || 'Sin especificar'}
                                            </div>
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Nivel de Conciencia">
                                            <Tag color="geekblue" style={{ fontSize: '1.1em', padding: '5px 15px' }}>
                                                {(triaje.nivel_conciencia || 'alerta').toUpperCase()}
                                            </Tag>
                                        </Descriptions.Item>
                                        {triaje.observaciones && (
                                            <Descriptions.Item label="Observaciones de Enfermería">
                                                <div style={{ fontStyle: 'italic' }}>{triaje.observaciones}</div>
                                            </Descriptions.Item>
                                        )}
                                    </Descriptions>
                                </section>
                            </Col>

                            <Col xs={24} lg={8}>
                                <Card title="Panel de Riesgo Clínico" className="gradient-card" style={{ height: '100%' }}>
                                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                                        <div className="stat-indicator">
                                            <Text type="secondary">Estabilidad Hemodinámica</Text>
                                            <Progress
                                                percent={triaje.presion_sistolica >= 140 ? 40 : 100}
                                                status={triaje.presion_sistolica >= 140 ? 'exception' : 'success'}
                                                strokeWidth={12}
                                            />
                                        </div>

                                        <div className="stat-indicator">
                                            <Text type="secondary">Nivel Térmico</Text>
                                            <Progress
                                                percent={triaje.temperatura >= 38 ? 100 : (triaje.temperatura / 40) * 100}
                                                status={triaje.temperatura >= 38 ? 'exception' : 'active'}
                                                strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
                                                strokeWidth={12}
                                            />
                                        </div>

                                        <div className="stat-indicator">
                                            <Text type="secondary">Oxigenación Periférica</Text>
                                            <Progress
                                                type="dashboard"
                                                percent={triaje.saturacion_oxigeno || 0}
                                                width={100}
                                                strokeColor={triaje.saturacion_oxigeno && triaje.saturacion_oxigeno < 95 ? '#ff4d4f' : '#52c41a'}
                                            />
                                        </div>

                                        <Card size="small" style={{ background: 'rgba(255,255,255,0.5)', border: 'none' }}>
                                            <div style={{ textAlign: 'center' }}>
                                                <Text type="secondary">Estado de Priorización</Text>
                                                <div style={{ marginTop: 8 }}>
                                                    <Tag color={
                                                        triaje.prioridad === 'urgente' ? 'red' :
                                                            triaje.prioridad === 'alto' ? 'volcano' :
                                                                triaje.prioridad === 'normal' ? 'blue' : 'green'
                                                    } style={{ fontSize: '1.2em', padding: '8px 20px', width: '100%', textAlign: 'center' }}>
                                                        {(triaje.prioridad || 'NORMAL').toUpperCase()}
                                                    </Tag>
                                                </div>
                                            </div>
                                        </Card>

                                        <Button
                                            block
                                            size="large"
                                            type="dashed"
                                            onClick={() => navigate(`/dashboard/pacientes/${triaje.paciente}`)}
                                        >
                                            Ver Historial del Paciente
                                        </Button>
                                    </Space>
                                </Card>
                            </Col>
                        </Row>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default DetalleTriaje;
