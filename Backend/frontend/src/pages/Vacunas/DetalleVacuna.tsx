import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Card,
    Row,
    Col,
    Button,
    Descriptions,
    Tag,
    Divider,
    Space,
    Typography,
    Skeleton,
    Alert,
    Badge,
    Timeline,
    Result
} from 'antd';
import {
    ArrowLeftOutlined,
    EditOutlined,
    PrinterOutlined,
    UserOutlined,
    CalendarOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    WarningOutlined,
    FilePdfOutlined,
    SafetyOutlined,
    InfoCircleOutlined,
    HomeOutlined,
    FileSearchOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { vacunasService, RegistroVacuna } from '../../services/vacunasService';
import { useAntdApp } from '../../hooks/useMessage';
import './Vacunas.css';

dayjs.extend(relativeTime);

const { Title, Text } = Typography;

interface RegistroVacunaExtended extends RegistroVacuna {
    paciente_info?: {
        nombre_completo: string;
        id_clinico: string;
        ci: string;
        edad?: number;
        sexo?: string;
    };
    tipo_vacuna_info?: {
        nombre: string;
        descripcion: string;
        dosis_requeridas: number;
        intervalo_dosis_dias: number;
        obligatoria_embarazo: boolean;
    };
    aplicada_por_nombre?: string;
}

const ARROW_LEFT_ICON_5 = <ArrowLeftOutlined />;
const PRINTER_ICON_3 = <PrinterOutlined />;
const EDIT_ICON_4 = <EditOutlined />;
const WARNING_ICON_6 = <WarningOutlined className="status-pulse" />;
const CHECK_CIRCLE_ICON_6 = <CheckCircleOutlined style={{ color: '#52c41a' }} />;
const HOME_ICON_3 = <HomeOutlined />;
const FILE_SEARCH_ICON_2 = <FileSearchOutlined />;

const DetalleVacuna: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { message } = useAntdApp();

    const [vacuna, setVacuna] = useState<RegistroVacunaExtended | null>(null);
    const [loading, setLoading] = useState<boolean>(true);

    const cargarVacuna = useCallback(async () => {
        if (!id) return;
        try {
            setLoading(true);
            const data = await vacunasService.getRegistroById(parseInt(id));
            setVacuna(data as RegistroVacunaExtended);
        } catch (error) {
            message.error('No se pudo encontrar el registro de inmunización');
            navigate('/dashboard/vacunas');
        } finally {
            setLoading(false);
        }
    }, [id, message, navigate]);

    useEffect(() => {
        cargarVacuna();
    }, [cargarVacuna]);

    const estadoDosis = useMemo(() => {
        if (!vacuna) return null;
        if (!vacuna.proxima_dosis_fecha) {
            return { color: 'success', text: 'ESQUEMA COMPLETO', icon: <CheckCircleOutlined /> };
        }
        const dias = dayjs(vacuna.proxima_dosis_fecha).diff(dayjs(), 'days');
        if (dias < 0) return { color: 'error', text: `ATRASADA (${Math.abs(dias)}d)`, icon: <WarningOutlined /> };
        if (dias <= 7) return { color: 'warning', text: `PRÓXIMA DOSIS (${dias}d)`, icon: <ClockCircleOutlined /> };
        return { color: 'processing', text: 'PROGRAMADA', icon: <CalendarOutlined /> };
    }, [vacuna]);

    const handleImprimir = () => {
        window.print();
    };

    if (loading) {
        return (
            <div style={{ padding: '24px' }}>
                <Skeleton active avatar paragraph={{ rows: 10 }} />
            </div>
        );
    }

    if (!vacuna) return null;

    return (
        <div className="animate-fade-in print-container" style={{ padding: '24px' }}>
            <Card className="shadow-card overflow-hidden">
                {/* HEADER SECTION */}
                <div className="blue-gradient-header no-print" style={{ margin: '-24px -24px 24px -24px', padding: '32px' }}>
                    <Row justify="space-between" align="middle">
                        <Col>
                            <Space align="center" size="large">
                                <Button
                                    icon={ARROW_LEFT_ICON_5}
                                    onClick={() => navigate('/dashboard/vacunas')}
                                    className="back-button-white"
                                />
                                <div className="header-icon-container">
                                    <FilePdfOutlined style={{ fontSize: '32px', color: '#fff' }} />
                                </div>
                                <div>
                                    <Title level={2} style={{ color: '#fff', margin: 0 }}>Certificado de Inmunización</Title>
                                    <Text style={{ color: 'rgba(255,255,255,0.85)' }}>Registro ID: #{vacuna.id} • {dayjs(vacuna.fecha_aplicacion).format('DD MMM YYYY')}</Text>
                                </div>
                            </Space>
                        </Col>
                        <Col>
                            <Space>
                                <Button
                                    size="large"
                                    icon={PRINTER_ICON_3}
                                    onClick={handleImprimir}
                                >
                                    Imprimir Certificado
                                </Button>
                                <Button
                                    type="primary"
                                    size="large"
                                    icon={EDIT_ICON_4}
                                    onClick={() => navigate(`/dashboard/vacunas/${vacuna.id}/editar`)}
                                    className="btn-success-gradient"
                                >
                                    Editar Registro
                                </Button>
                            </Space>
                        </Col>
                    </Row>
                </div>

                {/* PRINT ONLY HEADER */}
                <div className="print-only" style={{ textAlign: 'center', marginBottom: 30 }}>
                    <Title level={2}>CERTIFICADO OFICIAL DE VACUNACIÓN</Title>
                    <Divider />
                </div>

                <Row gutter={[24, 24]}>
                    {/* MAIN CONTENT COLUMN */}
                    <Col xs={24} lg={16}>
                        {/* ALERT BOXES */}
                        {vacuna.reacciones_adversas && (
                            <Alert
                                message="Evento Supuestamente Atribuible a Vacunación o Inmunización (ESAVI)"
                                description={vacuna.reacciones_adversas}
                                type="warning"
                                showIcon
                                icon={WARNING_ICON_6}
                                style={{ marginBottom: 24, borderRadius: '12px' }}
                            />
                        )}

                        <Card title={<Space><UserOutlined /> Identificación del Paciente</Space>} className="detail-section-card">
                            <Descriptions column={{ xs: 1, sm: 2 }} bordered>
                                <Descriptions.Item label="Nombre Completo" span={2}>
                                    <Text strong style={{ fontSize: '1.1em' }}>{vacuna.paciente_info?.nombre_completo || vacuna.paciente_nombre}</Text>
                                </Descriptions.Item>
                                <Descriptions.Item label="ID Clínico">{vacuna.paciente_info?.id_clinico || '-'}</Descriptions.Item>
                                <Descriptions.Item label="Cédula de Identidad">{vacuna.paciente_info?.ci || '-'}</Descriptions.Item>
                                <Descriptions.Item label="Edad al momento">{vacuna.paciente_info?.edad ? `${vacuna.paciente_info.edad} años` : '-'}</Descriptions.Item>
                                <Descriptions.Item label="Sexo">{vacuna.paciente_info?.sexo || '-'}</Descriptions.Item>
                            </Descriptions>
                        </Card>

                        <Card title={<Space><SafetyOutlined /> Detalles de la Inmunización</Space>} className="detail-section-card" style={{ marginTop: 24 }}>
                            <Descriptions column={{ xs: 1, sm: 2 }} bordered>
                                <Descriptions.Item label="Biológico" span={2}>
                                    <Space>
                                        <Badge color="blue" />
                                        <Text strong style={{ fontSize: '1.1em', color: '#096dd9' }}>{vacuna.tipo_vacuna_info?.nombre || vacuna.tipo_vacuna_nombre}</Text>
                                    </Space>
                                </Descriptions.Item>
                                <Descriptions.Item label="Dosis Aplicada">
                                    <Tag color="blue" style={{ fontSize: '14px', borderRadius: '4px' }}>
                                        Dosis {vacuna.numero_dosis} de {vacuna.tipo_vacuna_info?.dosis_requeridas || '?'}
                                    </Tag>
                                </Descriptions.Item>
                                <Descriptions.Item label="Laboratorio / Fabricante">
                                    {vacuna.laboratorio || '-'}
                                </Descriptions.Item>
                                <Descriptions.Item label="Número de Lote">
                                    <Text code>{vacuna.lote || '-'}</Text>
                                </Descriptions.Item>
                                <Descriptions.Item label="Fecha de Aplicación">
                                    {dayjs(vacuna.fecha_aplicacion).format('DD/MM/YYYY HH:mm')}
                                </Descriptions.Item>
                                <Descriptions.Item label="Vía de Administración">
                                    {vacuna.via_administracion?.toUpperCase()}
                                </Descriptions.Item>
                                <Descriptions.Item label="Sitio de Aplicación">
                                    {vacuna.sitio_aplicacion?.replace(/_/g, ' ') || '-'}
                                </Descriptions.Item>
                            </Descriptions>

                            {vacuna.observaciones && (
                                <div style={{ marginTop: 20 }}>
                                    <Text type="secondary"><InfoCircleOutlined /> Observaciones:</Text>
                                    <p style={{ marginTop: 8, padding: '12px', background: '#f9f9f9', borderRadius: '8px', boxShadow: 'inset 4px 0 0 #d9d9d9' }}>
                                        {vacuna.observaciones}
                                    </p>
                                </div>
                            )}
                        </Card>
                    </Col>

                    {/* SIDEBAR COLUMN */}
                    <Col xs={24} lg={8}>
                        <Card title={<Space><ClockCircleOutlined /> Estado y Seguimiento</Space>} className="sidebar-card">
                            <div style={{ textAlign: 'center', padding: '20px 0' }}>
                                <div style={{ fontSize: '3em', marginBottom: '10px' }}>{estadoDosis?.icon}</div>
                                <Tag color={estadoDosis?.color} style={{ fontSize: '1em', padding: '4px 12px', borderRadius: '20px' }}>
                                    {estadoDosis?.text}
                                </Tag>
                            </div>

                            <Divider style={{ margin: '12px 0' }} />

                            {vacuna.proxima_dosis_fecha ? (
                                <div style={{ background: '#f0f9ff', padding: '16px', borderRadius: '12px', border: '1px solid #bae6fd' }}>
                                    <Text type="secondary">Próximo Refuerzo:</Text>
                                    <div style={{ fontSize: '1.4em', fontWeight: 'bold', color: '#0369a1', margin: '4px 0' }}>
                                        {dayjs(vacuna.proxima_dosis_fecha).format('DD [de] MMMM, YYYY')}
                                    </div>
                                    <Text italic style={{ fontSize: '0.85em' }}>
                                        Faltan {dayjs(vacuna.proxima_dosis_fecha).diff(dayjs(), 'days')} días para la aplicación.
                                    </Text>
                                </div>
                            ) : (
                                <Result
                                    status="success"
                                    title="Esquema Completado"
                                    subTitle="El paciente ha recibido todas las dosis requeridas para este inmunógeno."
                                    icon={CHECK_CIRCLE_ICON_6}
                                />
                            )}

                            <Divider />

                            <Timeline
                                style={{ marginTop: 24 }}
                                items={[
                                    {
                                        color: 'green',
                                        children: (
                                            <>
                                                <Text strong>Dosis Aplicada</Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: '0.85em' }}>
                                                    {dayjs(vacuna.fecha_aplicacion).format('DD/MM/YYYY')}
                                                </Text>
                                            </>
                                        )
                                    },
                                    {
                                        color: vacuna.proxima_dosis_fecha ? 'blue' : 'gray',
                                        children: (
                                            <>
                                                <Text strong>{vacuna.proxima_dosis_fecha ? 'Próxima Dosis' : 'Fin del Esquema'}</Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: '0.85em' }}>
                                                    {vacuna.proxima_dosis_fecha ? dayjs(vacuna.proxima_dosis_fecha).format('DD/MM/YYYY') : '-'}
                                                </Text>
                                            </>
                                        )
                                    }
                                ]}
                            />
                        </Card>

                        <Card title={<Space><UserOutlined /> Personal de Salud</Space>} className="sidebar-card" style={{ marginTop: 24 }}>
                            <Descriptions column={1} size="small">
                                <Descriptions.Item label="Aplicado por">
                                    <Text strong>{vacuna.aplicada_por_nombre || 'Personal Autorizado'}</Text>
                                </Descriptions.Item>
                                <Descriptions.Item label="Institución">
                                    CENTRO MÉDICO FETAL MEDICAL
                                </Descriptions.Item>
                            </Descriptions>
                            <div style={{ marginTop: 30, textAlign: 'center', borderTop: '1px solid #f0f0f0', paddingTop: 20 }}>
                                <div className="signature-placeholder" style={{ height: 60, width: '100%', marginBottom: 10 }}></div>
                                <Text type="secondary" style={{ fontSize: '0.8em' }}>Sello y Firma Autorizada</Text>
                            </div>
                        </Card>
                    </Col>
                </Row>

                {/* FOOTER ACCIONES */}
                <div className="no-print" style={{ marginTop: 24, padding: '20px', background: '#f8fafc', borderRadius: '12px', textAlign: 'right' }}>
                    <Space>
                        <Button icon={HOME_ICON_3} onClick={() => navigate('/dashboard')}>Inicio</Button>
                        <Button icon={FILE_SEARCH_ICON_2} onClick={() => navigate('/dashboard/vacunas')}>Volver al Listado</Button>
                    </Space>
                </div>
            </Card>
        </div>
    );
};

export default DetalleVacuna;
