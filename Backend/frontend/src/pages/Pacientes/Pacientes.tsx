/**
 * =============================================================================
 * MÓDULO MAESTRO: GESTIÓN DE PACIENTES (ENTERPRISE EDITION)
 * =============================================================================
 * Autor: Fetal Medical System AI
 * Descripción:
 * Módulo integral para la administración de pacientes. Incluye lógica de negocio
 * compleja, validaciones estrictas, reportes integrados y gestión de estado local.
 * * Funcionalidades:
 * 1. CRUD Completo (Create, Read, Update, Delete).
 * 2. Búsqueda Avanzada y Filtros Multicriterio.
 * 3. Dashboard de Estadísticas de Pacientes integrado.
 * 4. Formulario Wizard (Pasos) para registro detallado.
 * 5. Drawer de Visualización Rápida con Historial.
 * 6. Exportación de Datos a CSV.
 * 7. Acciones por Lote (Bulk Actions).
 * =============================================================================
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Alert } from 'antd';
import {
  Empty,
    Table,
    Button,
    Form,
    Input,
    Select,
    Space,
    Card,
    Row,
    Col,
    Checkbox,
    Progress,
    Typography,
    theme
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { usePermissions } from '../../hooks/usePermissions';
import {
    PlusOutlined,
    DeleteOutlined,
    SearchOutlined,
    ReloadOutlined,
    FilterOutlined,
    ExportOutlined,
    CheckCircleOutlined,
    InfoCircleOutlined,
    FileExcelOutlined,
    HeartOutlined,
    TeamOutlined,
    FilePdfOutlined,
    CalendarOutlined,
    BarChartOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { descargarArchivo } from '../../utils/descargarArchivo';
import 'dayjs/locale/es';

// Importamos el motor API robusto creado anteriormente
import { api } from '../../services/api';
import pdfService from '../../services/pdfService';
import AnimatedStatistic from '../../components/common/AnimatedStatistic';
import { Paciente, AdvancedFilters, ResumenPacientes, RESUMEN_PACIENTES_VACIO } from './pacientesTypes';
import { aQuery, useListadoServidor } from '../../hooks/useListadoServidor';
import apiAxios from '../../services/api';
import { buildPacientesColumns } from './pacientesColumns';
import PacienteWizardModal from './components/PacienteWizardModal';
import PacienteDrawer from './components/PacienteDrawer';
import AnalisisDemograficoModal from './components/AnalisisDemograficoModal';
import ComparacionModal from './components/ComparacionModal';
import ImportarPacientesModal from './components/ImportarPacientesModal';
import AgendaDrawer from './components/AgendaDrawer';
import './Pacientes.css';

// Configuración regional
dayjs.locale('es');
const { Option } = Select;
const { Title, Text } = Typography;

// =============================================================================
// 2. COMPONENTE PRINCIPAL
// =============================================================================

const FILTER_ICON_2 = <FilterOutlined />;
const DELETE_ICON_2 = <DeleteOutlined />;
const BAR_CHART_ICON = <BarChartOutlined />;
const TEAM_ICON_2 = <TeamOutlined />;
const CALENDAR_ICON_5 = <CalendarOutlined />;
const EXPORT_ICON_3 = <ExportOutlined />;
const FILE_EXCEL_ICON_2 = <FileExcelOutlined />;
const FILE_PDF_ICON_4 = <FilePdfOutlined />;
const RELOAD_ICON_2 = <ReloadOutlined />;
const PLUS_ICON_5 = <PlusOutlined />;

const Pacientes: React.FC = () => {
    const navigate = useNavigate();
    const { message, modal } = useAntdApp();
    // Tokens del tema activo — mantienen consistencia en modo claro/oscuro
    const { token } = theme.useToken();
    const { canAdd, canChange, canDelete } = usePermissions();

    // --- ESTADOS DE INTERFAZ ---
    const [searchText, setSearchText] = useState('');
    const [showFilters, setShowFilters] = useState(false);
    const [filters, setFilters] = useState<AdvancedFilters>({});
    const [estadoObstetrico, setEstadoObstetrico] = useState<string | undefined>();

    // Búsqueda (nombres cifrados), filtros y cifras los resuelve el SERVIDOR.
    // Antes se bajaban las ~3.200 pacientes en 17 peticiones y se filtraba en
    // el navegador.
    const filtrosServidor = useMemo(() => ({
        ciudad: filters.ciudad,
        activo: filters.estado ? filters.estado === 'activo' : undefined,
        con_embarazo_activo: filters.tieneEmbarazo ? 'true' : undefined,
        edad_min: filters.edadMin,
        edad_max: filters.edadMax,
        estado_obstetrico: estadoObstetrico,
    }), [filters, estadoObstetrico]);
    const listado = useListadoServidor<Paciente>('/pacientes/', {
        filtros: filtrosServidor, busqueda: searchText, ordenInicial: '-fecha_registro',
    });
    const { parametros, recargar } = listado;
    const loading = listado.cargando;
    const [resumen, setResumen] = useState<ResumenPacientes>(RESUMEN_PACIENTES_VACIO);
    const cargarResumen = useCallback(async () => {
        try {
            const r = await apiAxios.get('/pacientes/resumen/', { params: parametros() });
            setResumen(r.data);
        } catch {
            setResumen(RESUMEN_PACIENTES_VACIO);
        }
    }, [parametros]);
    useEffect(() => { cargarResumen(); }, [cargarResumen]);
    const loadPacientes = useCallback(() => {
        recargar();
        cargarResumen();
        setSelectedRowKeys([]);
    }, [recargar, cargarResumen]);
    const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

    // --- ESTADOS DE MODALES/DRAWERS ---
    const [modalVisible, setModalVisible] = useState(false);
    const [drawerVisible, setDrawerVisible] = useState(false);
    const [editingPaciente, setEditingPaciente] = useState<Paciente | null>(null);
    const [selectedPaciente, setSelectedPaciente] = useState<Paciente | null>(null);

    // ✨ NUEVOS ESTADOS PARA MODALES EXTENDIDOS
    const [modalAnalisisDemograficoVisible, setModalAnalisisDemograficoVisible] = useState(false);
    const [modalComparacionVisible, setModalComparacionVisible] = useState(false);
    const [modalImportarVisible, setModalImportarVisible] = useState(false);
    const [drawerAgendaVisible, setDrawerAgendaVisible] = useState(false);
    const [pacientesComparacion, setPacientesComparacion] = useState<{ a: Paciente | null; b: Paciente | null; c: Paciente | null }>({ a: null, b: null, c: null });

    // --- ESTADOS DE FORMULARIO WIZARD ---
    const [currentStep, setCurrentStep] = useState(0);
    const [formLoading, setFormLoading] = useState(false);
    const [form] = Form.useForm();

    // ✅ Función para mostrar estado civil según género

    // =============================================================================
    // 3. LÓGICA DE CARGA Y DATOS
    // =============================================================================

    // useEffect para cargar datos del paciente al abrir modal de edición
    useEffect(() => {
        if (editingPaciente && modalVisible) {

            // Esperar suficiente tiempo para que el modal y todos los componentes estén listos
            const timer = setTimeout(() => {
                const fechaNacimientoDayjs = editingPaciente.fecha_nacimiento
                    ? dayjs(editingPaciente.fecha_nacimiento)
                    : null;


                // Normalizar estado_civil: quitar sufijo femenino para que coincida con los values del Select
                const normalizarEstadoCivil = (ec: string | undefined): string | undefined => {
                    if (!ec) return ec;
                    const map: Record<string, string> = {
                        'soltera': 'soltero', 'casada': 'casado',
                        'divorciada': 'divorciado', 'viuda': 'viudo',
                    };
                    return map[ec.toLowerCase()] ?? ec;
                };

                // Genero: si viene vacío, inferir 'femenino' (pacientes obstétricas)
                const generoNorm = editingPaciente.genero || 'femenino';

                form.setFieldsValue({
                    nombre: editingPaciente.nombre,
                    apellido_paterno: editingPaciente.apellido_paterno,
                    apellido_materno: editingPaciente.apellido_materno,
                    fecha_nacimiento: fechaNacimientoDayjs,
                    genero: generoNorm,
                    ci: editingPaciente.ci,
                    telefono: editingPaciente.telefono,
                    email: editingPaciente.email,
                    direccion: editingPaciente.direccion,
                    ciudad: editingPaciente.ciudad,
                    pais: editingPaciente.pais,
                    grupo_sanguineo: editingPaciente.grupo_sanguineo || editingPaciente.tipo_sangre,
                    estado_civil: normalizarEstadoCivil(editingPaciente.estado_civil),
                    ocupacion: editingPaciente.ocupacion,
                    peso_kg: editingPaciente.peso_kg,
                    altura_cm: editingPaciente.altura_cm,
                    observaciones: editingPaciente.observaciones,
                });

            }, 600); // Aumentado a 600ms

            return () => clearTimeout(timer);
        }
    }, [editingPaciente, modalVisible, form]);

    // =============================================================================
    // 5. HANDLERS DE ACCIONES (CRUD)
    // =============================================================================

    const handleOpenCreate = useCallback(() => {
        setEditingPaciente(null);
        setCurrentStep(0);
        form.resetFields();
        // Valores por defecto
        form.setFieldsValue({
            pais: 'Bolivia',
            ciudad: 'La Paz',
            genero: 'femenino',
            activo: true
        });
        setModalVisible(true);
    }, [form]);

    const handleOpenEdit = useCallback((paciente: Paciente) => {
        setEditingPaciente(paciente);
        setCurrentStep(0);
        setModalVisible(true);
        // El useEffect se encargará de cargar los datos del formulario
    }, []);

    const handleSubmit = useCallback(async () => {
        try {
            // Validar todos los campos antes de enviar
            const values = await form.validateFields();
            setFormLoading(true);

            // Transformar datos para backend
            const payload = {
                ...values,
                fecha_nacimiento: values.fecha_nacimiento ? values.fecha_nacimiento.format('YYYY-MM-DD') : null,
            };

            if (editingPaciente) {
                await api.put(`/pacientes/${editingPaciente.id}/`, payload);
                message.success({ content: 'Paciente actualizado correctamente', icon: <CheckCircleOutlined style={{ color: token.colorSuccess }} /> });
            } else {
                // `api.post` (envoltorio) ya devuelve la paciente creada, no la respuesta de axios.
                const creada = await api.post<{ id?: number; nombre_completo?: string }>('/pacientes/', payload);
                message.success({ content: 'Paciente registrado exitosamente', icon: <CheckCircleOutlined style={{ color: token.colorSuccess }} /> });
                // Siguiente paso natural del flujo: registrar su embarazo, ya con
                // la paciente elegida.
                if (creada?.id) {
                    modal.confirm({
                        title: '¿Registrar ahora su embarazo?',
                        content: `${creada.nombre_completo || 'La paciente'} quedó registrada. Puede iniciar su embarazo con ella ya elegida.`,
                        okText: 'Registrar embarazo',
                        cancelText: 'Más tarde',
                        onOk: () => navigate(`/dashboard/embarazos/nuevo?paciente=${creada.id}`),
                    });
                }
            }

            setModalVisible(false);
            loadPacientes(); // Recargar tabla
        } catch (error: any) {
            // Si es error de validación de form, no hacemos nada (AntD lo muestra)
            // Si es error de API:
            if (error.response) {
                const datos = error.response.data;
                const detalle = datos && typeof datos === 'object'
                    ? Object.values(datos).flat().filter((v) => typeof v === 'string').join(' ')
                    : '';
                message.error(detalle || 'Error al guardar. Verifique los datos.');
            }
        } finally {
            setFormLoading(false);
        }
    }, [form, editingPaciente, message, loadPacientes, token, modal, navigate]);

    const handleDelete = useCallback(async (id: number) => {
        try {
            await api.delete(`/pacientes/${id}/`);
            message.success('Registro eliminado');
            loadPacientes();
            if (selectedPaciente?.id === id) setDrawerVisible(false);
        } catch (error) {
            message.error("No se pudo eliminar el paciente.");
        }
    }, [loadPacientes, selectedPaciente, message]);

    const handleBulkDelete = useCallback(async () => {
        if (selectedRowKeys.length === 0) return;

        modal.confirm({
            title: `¿Eliminar ${selectedRowKeys.length} pacientes?`,
            content: 'Se darán de baja (baja lógica). Su historia clínica se conserva.',
            okText: 'Sí, Eliminar Todo',
            okType: 'danger',
            cancelText: 'Cancelar',
            onOk: async () => {
                const hide = message.loading('Procesando eliminación...', 0);
                try {
                    // Opción A: Loop de deletes (si backend no soporta bulk)
                    // Opción B: Endpoint bulk (ideal)
                    // Usaremos Loop por compatibilidad básica
                    await Promise.all(selectedRowKeys.map(id => api.delete(`/pacientes/${id}/`)));

                    hide();
                    message.success(`${selectedRowKeys.length} pacientes eliminados.`);
                    setSelectedRowKeys([]);
                    loadPacientes();
                } catch (e) {
                    hide();
                    message.error("Error durante la eliminación masiva.");
                }
            }
        });
    }, [selectedRowKeys, modal, message, loadPacientes]);

    // CSV del listado desde el MISMO endpoint institucional que el Excel/PDF
    // (BOM UTF-8 + cabecera de marca + mismas columnas). Antes era una
    // "simulación" client-side con formato distinto e incompatible.
    const handleExport = useCallback(() => {
        descargarArchivo(`/pacientes/exportar-csv/`, `pacientes_${dayjs().format('YYYYMMDD')}.csv`)
            .then(() => message.success('CSV descargado'))
            .catch(() => message.error('No se pudo generar el CSV'));
    }, [message]);

    // ✨ GENERAR PDF DE LISTADO DE PACIENTES
    const handleExportPDF = useCallback(async () => {
        // El PDF es un listado para imprimir: hasta 200 pacientes con los
        // filtros actuales (para todas, el Excel del servidor).
        try {
            const r = await apiAxios.get('/pacientes/', { params: { ...parametros(), page_size: 200 } });
            pdfService.generarListadoPacientes(r.data?.results ?? []);
            if ((r.data?.count ?? 0) > 200) message.info('El PDF lleva las primeras 200 pacientes; use Excel para el listado completo.');
            else message.success('PDF generado');
        } catch (error) {
            message.error('Error al generar el PDF');
        }
    }, [parametros, message]);

    // ✨ GENERAR PDF DE PACIENTE INDIVIDUAL
    const handleExportPacientePDF = useCallback((paciente: Paciente) => {
        try {
            pdfService.generarReportePaciente(paciente);
            message.success(`PDF del paciente ${paciente.nombre} generado exitosamente`);
        } catch (error) {
            message.error('Error al generar el PDF');
        }
    }, [message]);

    // Excel desde el SERVIDOR con todas las pacientes filtradas (auditado).
    const handleExportExcel = useCallback(() => {
        descargarArchivo(`/pacientes/exportar-excel/${aQuery(parametros())}`, `pacientes_${dayjs().format('YYYYMMDD_HHmm')}.xlsx`)
            .then(() => message.success('Excel descargado'))
            .catch(() => message.error('No se pudo generar el Excel'));
    }, [parametros, message]);

    // =============================================================================
    // 6. DEFINICIÓN DE COLUMNAS DE TABLA
    // =============================================================================

    const columns = useMemo(() => buildPacientesColumns({
        token,
        navigate,
        canChange,
        canDelete,
        modal,
        handleOpenEdit,
        handleExportPacientePDF,
        handleDelete,
        setSelectedPaciente,
        setDrawerVisible,
    }), [canChange, canDelete, handleOpenEdit, navigate, handleExportPacientePDF, handleDelete, modal, token]);

    // =============================================================================
    // 7. RENDERIZADO DE INTERFAZ (JSX)
    // =============================================================================

    return (
        <div className="pacientes-module pacientes-pagina">

            {/* --- ENCABEZADO DE PÁGINA --- */}
            <header className="pacientes-encabezado">
                <div className="pacientes-encabezado__texto">
                    <Title level={2} className="pacientes-encabezado__titulo">Pacientes</Title>
                    <Text className="pacientes-encabezado__descripcion">
                        Registro, búsqueda y seguimiento de las pacientes del establecimiento.
                    </Text>
                </div>
                {canAdd('paciente') && (
                    <Button type="primary" icon={PLUS_ICON_5} onClick={handleOpenCreate} size="large">
                        Nueva Paciente
                    </Button>
                )}
            </header>

            {/* --- ESTADÍSTICAS --- */}
            <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} lg={6}>
                    <Card className="stat-card">
                        <AnimatedStatistic title={<span className="stat-card__etiqueta"><TeamOutlined />Total Pacientes</span>} value={resumen.total} />
                        <Progress percent={100} status="normal" showInfo={false} size="small" />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card className="stat-card">
                        <AnimatedStatistic title={<span className="stat-card__etiqueta"><HeartOutlined />Embarazos Activos</span>} value={resumen.embarazadas} />
                        <Progress percent={resumen.total ? (resumen.embarazadas / resumen.total) * 100 : 0} showInfo={false} size="small" />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card className="stat-card">
                        <AnimatedStatistic title={<span className="stat-card__etiqueta"><PlusOutlined />Nuevos este Mes</span>} value={resumen.nuevos_mes} />
                        <Progress percent={resumen.nuevos_mes > 0 ? 100 : 0} status="normal" showInfo={false} size="small" />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card className="stat-card">
                        <AnimatedStatistic title={<span className="stat-card__etiqueta"><InfoCircleOutlined />Promedio Edad</span>} value={resumen.promedio_edad} suffix="años" />
                    </Card>
                </Col>
            </Row>

            {/* --- BARRA DE HERRAMIENTAS --- */}
            <Card className="pacientes-herramientas">
                <div className="pacientes-herramientas__fila">
                    {/* Izquierda: Búsqueda y Filtros */}
                    <Space size="middle" wrap>
                        <Input
                            placeholder="Buscar por nombre, CI o ID..."
                            prefix={<SearchOutlined className="texto-ayuda" />}
                            onChange={e => setSearchText(e.target.value)}
                            className="pacientes-herramientas__busqueda"
                            size="large"
                            allowClear
                        />
                        <Button
                            icon={FILTER_ICON_2}
                            onClick={() => setShowFilters(!showFilters)}
                            aria-pressed={showFilters}
                            className={showFilters ? 'pacientes-filtro--activo' : undefined}
                        >
                            Filtros Avanzados
                        </Button>
                        {selectedRowKeys.length > 0 && (
                            <Button danger icon={DELETE_ICON_2} onClick={handleBulkDelete}>
                                Eliminar ({selectedRowKeys.length})
                            </Button>
                        )}
                    </Space>

                    {/* Derecha: Acciones */}
                    <Space wrap>
                        <Button icon={BAR_CHART_ICON} onClick={() => setModalAnalisisDemograficoVisible(true)}>
                            Análisis Demográfico
                        </Button>
                        <Button icon={TEAM_ICON_2} onClick={() => setModalComparacionVisible(true)}>
                            Comparar Pacientes
                        </Button>
                        <Button icon={CALENDAR_ICON_5} onClick={() => setDrawerAgendaVisible(true)}>
                            Agenda
                        </Button>
                        <Button icon={FILE_EXCEL_ICON_2} onClick={() => setModalImportarVisible(true)}>Importar Excel</Button>
                        <Button icon={EXPORT_ICON_3} onClick={handleExport}>Exportar CSV</Button>
                        <Button icon={FILE_EXCEL_ICON_2} onClick={handleExportExcel}>
                            Exportar Excel
                        </Button>
                        <Button icon={FILE_PDF_ICON_4} onClick={handleExportPDF}>
                            Exportar PDF
                        </Button>
                        <Button icon={RELOAD_ICON_2} onClick={loadPacientes} loading={loading}>Recargar</Button>
                    </Space>
                </div>

                {/* Panel de Filtros Avanzados (Colapsable) */}
                {showFilters && (
                    <div className="pacientes-herramientas__filtros">
                        {/* Sin filtro de género: todas las pacientes son femeninas
                            (sistema exclusivamente gineco-obstétrico). */}
                        <Row gutter={[16, 16]}>
                            <Col xs={24} sm={12} md={6}>
                                <Input
                                    placeholder="Ciudad"
                                    onChange={(e) => setFilters(prev => ({ ...prev, ciudad: e.target.value }))}
                                />
                            </Col>
                            <Col xs={24} sm={12} md={6}>
                                <Select
                                    placeholder="Estado"
                                    className="pacientes-ancho-completo"
                                    allowClear
                                    onChange={(val) => setFilters(prev => ({ ...prev, estado: val }))}
                                >
                                    <Option value="activo">Activos</Option>
                                    <Option value="inactivo">Inactivos</Option>
                                </Select>
                            </Col>
                            <Col xs={24} sm={12} md={6}>
                                <Checkbox onChange={(e) => setFilters(prev => ({ ...prev, tieneEmbarazo: e.target.checked }))}>
                                    Solo con Embarazo Activo
                                </Checkbox>
                            </Col>
                        </Row>
                    </div>
                )}
            </Card>

            {/* --- TABLA DE DATOS --- */}
            <Card className="pacientes-tabla" styles={{ body: { padding: 0 } }}>
                {listado.error && <Alert type="error" showIcon message={listado.error} className="pacientes-tabla__error" />}
                <Table
                    rowKey="id"
                    dataSource={listado.datos}
                    locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay pacientes registrados" /> }}
                    columns={columns as any}
                    loading={loading}
                    rowSelection={{
                        selectedRowKeys,
                        onChange: (keys) => setSelectedRowKeys(keys)
                    }}
                    pagination={{ ...listado.paginacion, showQuickJumper: true }}
                    onChange={(paginacion, filtrosTabla, sorter) => {
                        // El filtro de «Estado obstétrico» de la columna lo aplica el servidor.
                        const estado = (filtrosTabla as Record<string, unknown[] | null>).estado_obstetrico?.[0];
                        setEstadoObstetrico(typeof estado === 'string' ? estado : undefined);
                        listado.onChange(paginacion, filtrosTabla, sorter as any);
                    }}
                    scroll={{ x: 1000 }}
                />
            </Card>

            {/* MODAL WIZARD (REGISTRO PASO A PASO) */}
            <PacienteWizardModal
                modalVisible={modalVisible}
                editingPaciente={editingPaciente}
                currentStep={currentStep}
                setCurrentStep={setCurrentStep}
                form={form}
                formLoading={formLoading}
                handleSubmit={handleSubmit}
                onCancel={() => setModalVisible(false)}
            />

            {/* DRAWER DE DETALLE (VISTA RÁPIDA) */}
            <PacienteDrawer
                drawerVisible={drawerVisible}
                selectedPaciente={selectedPaciente}
                onClose={() => setDrawerVisible(false)}
                navigate={navigate}
                token={token}
            />

            {/* MÓDULO DE ANÁLISIS DEMOGRÁFICO AVANZADO */}
            <AnalisisDemograficoModal
                visible={modalAnalisisDemograficoVisible}
                onClose={() => setModalAnalisisDemograficoVisible(false)}
                resumen={resumen}
                token={token}
            />

            {/* HERRAMIENTAS DE COMPARACIÓN Y ANÁLISIS */}
            <ImportarPacientesModal
                open={modalImportarVisible}
                onClose={() => setModalImportarVisible(false)}
                onImportado={loadPacientes}
            />
            <ComparacionModal
                visible={modalComparacionVisible}
                onClose={() => {
                    setModalComparacionVisible(false);
                    setPacientesComparacion({ a: null, b: null, c: null });
                }}
                pacientesComparacion={pacientesComparacion}
                setPacientesComparacion={setPacientesComparacion}
            />

            {/* AGENDA Y RECORDATORIOS */}
            <AgendaDrawer
                visible={drawerAgendaVisible}
                onClose={() => setDrawerAgendaVisible(false)}
            />

        </div>
    );
};

export default Pacientes;
