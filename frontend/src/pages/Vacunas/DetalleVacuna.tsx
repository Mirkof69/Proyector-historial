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
const CHECK_CIRCLE_ICON_6 = <CheckCircleOutlined className="vacunas-exito" />;
const HOME_ICON_3 = <HomeOutlined />;
const FILE_SEARCH_ICON_2 = <FileSearchOutlined />;

const handleImprimir = () => {
  window.print();
};

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

    if (loading) {
        return (
            <div className="vacunas-page__cargando">
                <Skeleton active avatar paragraph={{ rows: 10 }} />
            </div>
        );
    }

    if (!vacuna) return null;

    return (
        <div className="vacunas-page page-container print-container">
            {/* ENCABEZADO */}
            <header className="vacunas-page__cabecera no-print">
                <div>
                    <Title level={2}>Certificado de Inmunización</Title>
                    <Text type="secondary" className="tabular-nums">Registro ID: #{vacuna.id} • {dayjs(vacuna.fecha_aplicacion).format('DD MMM YYYY')}</Text>
                </div>
                <Space wrap>
                    <Button
                        icon={ARROW_LEFT_ICON_5}
                        onClick={() => navigate('/dashboard/vacunas')}
                        aria-label="Volver"
                    />
                    <Button
                        icon={PRINTER_ICON_3}
                        onClick={handleImprimir}
                    >
                        Imprimir Certificado
                    </Button>
                    <Button
                        type="primary"
                        icon={EDIT_ICON_4}
                        onClick={() => navigate(`/dashboard/vacunas/${vacuna.id}/editar`)}
                    >
                        Editar Registro
                    </Button>
                </Space>
            </header>

            {/* PRINT ONLY HEADER */}
            <div className="vacunas-solo-impresion">
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
                            className="vacunas-separado"
                        />
                    )}

                    <Card title={<Space><UserOutlined /> Identificación del Paciente</Space>}>
                        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
                            <Descriptions.Item label="Nombre Completo" span={2}>
                                <Text strong className="vacunas-detalle__nombre">{vacuna.paciente_info?.nombre_completo || vacuna.paciente_nombre}</Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="ID Clínico"><span className="texto-mono">{vacuna.paciente_info?.id_clinico || '-'}</span></Descriptions.Item>
                            <Descriptions.Item label="Cédula de Identidad"><span className="texto-mono">{vacuna.paciente_info?.ci || '-'}</span></Descriptions.Item>
                            <Descriptions.Item label="Edad al momento">{vacuna.paciente_info?.edad ? `${vacuna.paciente_info.edad} años` : '-'}</Descriptions.Item>
                            <Descriptions.Item label="Sexo">{vacuna.paciente_info?.sexo || '-'}</Descriptions.Item>
                        </Descriptions>
                    </Card>

                    <Card title={<Space><SafetyOutlined /> Detalles de la Inmunización</Space>} className="vacunas-arriba">
                        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
                            <Descriptions.Item label="Biológico" span={2}>
                                <Text strong className="vacunas-detalle__nombre">{vacuna.tipo_vacuna_info?.nombre || vacuna.tipo_vacuna_nombre}</Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="Dosis Aplicada">
                                <Tag>
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
                            <div className="vacunas-arriba">
                                <Text type="secondary"><InfoCircleOutlined /> Observaciones:</Text>
                                <p className="vacunas-detalle__observaciones">
                                    {vacuna.observaciones}
                                </p>
                            </div>
                        )}
                    </Card>
                </Col>

                {/* SIDEBAR COLUMN */}
                <Col xs={24} lg={8}>
                    <Card title={<Space><ClockCircleOutlined /> Estado y Seguimiento</Space>}>
                        <div className="vacunas-detalle__estado">
                            <div className="vacunas-detalle__estado-icono">{estadoDosis?.icon}</div>
                            <Tag color={estadoDosis?.color}>
                                {estadoDosis?.text}
                            </Tag>
                        </div>

                        <Divider />

                        {vacuna.proxima_dosis_fecha ? (
                            <div className="vacunas-detalle__proxima">
                                <Text type="secondary">Próximo Refuerzo:</Text>
                                <div className="vacunas-detalle__proxima-fecha">
                                    {dayjs(vacuna.proxima_dosis_fecha).format('DD [de] MMMM, YYYY')}
                                </div>
                                <Text italic className="vacunas-page__secundario">
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
                            items={[
                                {
                                    color: 'green',
                                    children: (
                                        <>
                                            <Text strong>Dosis Aplicada</Text>
                                            <br />
                                            <Text type="secondary" className="vacunas-page__fecha">
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
                                            <Text type="secondary" className="vacunas-page__fecha">
                                                {vacuna.proxima_dosis_fecha ? dayjs(vacuna.proxima_dosis_fecha).format('DD/MM/YYYY') : '-'}
                                            </Text>
                                        </>
                                    )
                                }
                            ]}
                        />
                    </Card>

                    <Card title={<Space><UserOutlined /> Personal de Salud</Space>} className="vacunas-arriba">
                        <Descriptions column={1} size="small">
                            <Descriptions.Item label="Aplicado por">
                                <Text strong>{vacuna.aplicada_por_nombre || 'Personal Autorizado'}</Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="Institución">
                                CENTRO MÉDICO FETAL MEDICAL
                            </Descriptions.Item>
                        </Descriptions>
                        <div className="vacunas-detalle__firma">
                            <div className="vacunas-detalle__firma-espacio"></div>
                            <Text type="secondary" className="vacunas-page__secundario">Sello y Firma Autorizada</Text>
                        </div>
                    </Card>
                </Col>
            </Row>

            {/* FOOTER ACCIONES */}
            <div className="vacunas-detalle__pie no-print">
                <Button icon={HOME_ICON_3} onClick={() => navigate('/dashboard')}>Inicio</Button>
                <Button icon={FILE_SEARCH_ICON_2} onClick={() => navigate('/dashboard/vacunas')}>Volver al Listado</Button>
            </div>
        </div>
    );
};

export default DetalleVacuna;
