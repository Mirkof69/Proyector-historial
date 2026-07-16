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
    SyncOutlined,
    BarChartOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import 'dayjs/locale/es';

// Importamos el motor API robusto creado anteriormente
import { api } from '../../services/api';
import pdfService from '../../services/pdfService';
import { exportarExcel } from '../../utils/excelExport';
import { GlobalLoader } from '../../components/common/GlobalLoader';
import AnimatedStatistic from '../../components/common/AnimatedStatistic';
import { Paciente, AdvancedFilters, PacienteStats } from './pacientesTypes';
import { buildPacientesColumns } from './pacientesColumns';
import PacienteWizardModal from './components/PacienteWizardModal';
import PacienteDrawer from './components/PacienteDrawer';
import AnalisisDemograficoModal from './components/AnalisisDemograficoModal';
import ImportExportModal from './components/ImportExportModal';
import ComparacionModal from './components/ComparacionModal';
import AgendaDrawer from './components/AgendaDrawer';

// Configuración regional
dayjs.locale('es');
const { Option } = Select;

// =============================================================================
// 2. COMPONENTE PRINCIPAL
// =============================================================================

const FILTER_ICON_2 = <FilterOutlined />;
const DELETE_ICON_2 = <DeleteOutlined />;
const BAR_CHART_ICON = <BarChartOutlined />;
const SYNC_ICON_2 = <SyncOutlined />;
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

    // --- ESTADOS GLOBALES ---
    const [pacientes, setPacientes] = useState<Paciente[]>([]);
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState<PacienteStats>({ total: 0, activos: 0, nuevosMes: 0, embarazadas: 0, promedioEdad: 0 });
    // --- ESTADOS DE PAGINACIÓN ---
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(100);
    const [totalPacientes, setTotalPacientes] = useState(0);

    // --- ESTADOS DE INTERFAZ ---
    const [searchText, setSearchText] = useState('');
    const [showFilters, setShowFilters] = useState(false);
    const [filters, setFilters] = useState<AdvancedFilters>({});
    const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

    // --- ESTADOS DE MODALES/DRAWERS ---
    const [modalVisible, setModalVisible] = useState(false);
    const [drawerVisible, setDrawerVisible] = useState(false);
    const [editingPaciente, setEditingPaciente] = useState<Paciente | null>(null);
    const [selectedPaciente, setSelectedPaciente] = useState<Paciente | null>(null);

    // ✨ NUEVOS ESTADOS PARA MODALES EXTENDIDOS
    const [modalAnalisisDemograficoVisible, setModalAnalisisDemograficoVisible] = useState(false);
    const [modalImportExportVisible, setModalImportExportVisible] = useState(false);
    const [modalComparacionVisible, setModalComparacionVisible] = useState(false);
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


                // Verificar los valores después de un momento
                setTimeout(() => {
                    const valores = form.getFieldsValue();
                }, 200);
            }, 600); // Aumentado a 600ms

            return () => clearTimeout(timer);
        }
    }, [editingPaciente, modalVisible, form]);

    /**
     * ✅ OPTIMIZACIÓN: Carga inicial de datos PARALELA desde el Backend
     * Obtiene TODOS los pacientes cargando TODAS las páginas en paralelo (Promise.all)
     */
    const loadPacientes = useCallback(async () => {
        setLoading(true);

        try {

            // 🚀 PASO 1: Obtener primera página para saber cuántas páginas hay
            const firstPageResponse = await api.get<any>('/pacientes/?page=1&limit=200');
            const totalCount = firstPageResponse.count || 0;
            const totalPages = Math.ceil(totalCount / 200);


            // 🚀 PASO 2: Crear arrays de promesas para TODAS las páginas
            const promises = Array.from({ length: totalPages }, (_, i) =>
                api.get<any>(`/pacientes/?page=${i + 1}&limit=200`)
            );

            // 🚀 PASO 3: Ejecutar TODAS las requests en PARALELO
            const responses = await Promise.all(promises);

            // 🚀 PASO 4: Combinar todos los resultados y agregar rowKey único
            const allPacientes: Paciente[] = [];
            for (const res of responses) {
                const results = Array.isArray(res) ? res : res.results || [];
                for (const paciente of results) {
                    allPacientes.push({
                        ...paciente,
                        _uniqueRowKey: `paciente-${paciente.id}-${allPacientes.length}-${Date.now()}`
                    });
                }
            }

            setPacientes(allPacientes);
            setTotalPacientes(allPacientes.length);
            calcularEstadisticas(allPacientes);

            // Limpiar selecciones
            setSelectedRowKeys([]);
        } catch (error) {
            message.error("Error al sincronizar datos con el servidor");
        } finally {
            setLoading(false);
        }
    }, [message]);

    // ✅ OPTIMIZACIÓN: useEffect con dependencia explícita en loadPacientes
    useEffect(() => {
        loadPacientes();
    }, [loadPacientes]);

    /**
     * Calcula estadísticas en tiempo real basadas en la lista cargada
     */
    const calcularEstadisticas = (lista: Paciente[]) => {
        const total = lista.length;
        const activos = lista.filter(p => p.activo).length;
        const embarazadas = lista.filter(p => p.embarazos_activos).length;

        // Nuevos este mes
        const currentMonth = dayjs().month();
        const currentYear = dayjs().year();
        const nuevosMes = lista.filter(p => {
            if (!p.fecha_registro) return false;
            const date = dayjs(p.fecha_registro);
            return date.month() === currentMonth && date.year() === currentYear;
        }).length;

        // Promedio edad
        const sumaEdades = lista.reduce((acc, curr) => acc + (curr.edad || 0), 0);
        const promedioEdad = total > 0 ? Math.round(sumaEdades / total) : 0;

        setStats({ total, activos, nuevosMes, embarazadas, promedioEdad });
    };

    // =============================================================================
    // 4. LÓGICA DE FILTRADO AVANZADO (MEMOIZED)
    // =============================================================================

    const filteredData = useMemo(() => {
        let data = [...pacientes];

        // 1. Búsqueda de Texto
        if (searchText) {
            const lower = searchText.toLowerCase();
            data = data.filter(p =>
                (p.nombre_completo?.toLowerCase().includes(lower)) ||
                (p.nombre?.toLowerCase().includes(lower)) ||
                (p.apellido_paterno?.toLowerCase().includes(lower)) ||
                (p.ci?.toLowerCase().includes(lower)) ||
                (p.id_clinico?.toLowerCase().includes(lower))
            );
        }

        // 2. Filtros Avanzados
        if (filters.genero) {
            data = data.filter(p => p.genero === filters.genero);
        }
        if (filters.ciudad) {
            data = data.filter(p => p.ciudad?.toLowerCase().includes(filters.ciudad!.toLowerCase()));
        }
        if (filters.estado) {
            const isActive = filters.estado === 'activo';
            data = data.filter(p => p.activo === isActive);
        }
        if (filters.tieneEmbarazo) {
            data = data.filter(p => p.embarazos_activos);
        }
        if (filters.edadMin !== undefined) {
            data = data.filter(p => (p.edad || 0) >= filters.edadMin!);
        }
        if (filters.edadMax !== undefined) {
            data = data.filter(p => (p.edad || 0) <= filters.edadMax!);
        }

        return data;
    }, [pacientes, searchText, filters]);

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
                await api.post('/pacientes/', payload);
                message.success({ content: 'Paciente registrado exitosamente', icon: <CheckCircleOutlined style={{ color: token.colorSuccess }} /> });
            }

            setModalVisible(false);
            loadPacientes(); // Recargar tabla
        } catch (error: any) {
            // Si es error de validación de form, no hacemos nada (AntD lo muestra)
            // Si es error de API:
            if (error.response) {
                message.error("Error al guardar. Verifique los datos.");
            }
        } finally {
            setFormLoading(false);
        }
    }, [form, editingPaciente, message, loadPacientes, token]);

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
            content: 'Esta acción no se puede deshacer. Se perderán historias clínicas asociadas.',
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

    const handleExport = useCallback(() => {
        // Simulación de exportación a CSV
        const header = ["ID Clinico", "Nombre", "CI", "Telefono", "Edad", "Genero", "Ciudad"];
        const rows = filteredData.map(p => [
            p.id_clinico,
            `"${p.nombre} ${p.apellido_paterno}"`,
            p.ci,
            p.telefono || '',
            p.edad,
            p.genero,
            p.ciudad || ''
        ]);

        const csvContent = "data:text/csv;charset=utf-8,"
            + header.join(",") + "\n"
            + rows.map(e => e.join(",")).join("\n");

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "reporte_pacientes_" + dayjs().format('YYYYMMDD') + ".csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        message.success("Archivo CSV generado");
    }, [filteredData, message]);

    // ✨ GENERAR PDF DE LISTADO DE PACIENTES
    const handleExportPDF = useCallback(() => {
        try {
            pdfService.generarListadoPacientes(filteredData);
            message.success('PDF generado exitosamente');
        } catch (error) {
            message.error('Error al generar el PDF');
        }
    }, [filteredData, message]);

    // ✨ GENERAR PDF DE PACIENTE INDIVIDUAL
    const handleExportPacientePDF = useCallback((paciente: Paciente) => {
        try {
            pdfService.generarReportePaciente(paciente);
            message.success(`PDF del paciente ${paciente.nombre} generado exitosamente`);
        } catch (error) {
            message.error('Error al generar el PDF');
        }
    }, [message]);

    // ✨ EXPORTAR A EXCEL
    const handleExportExcel = useCallback(() => {
        try {
            const columnas = {
                'id_clinico': 'ID Clínico',
                'nombre': 'Nombre',
                'apellido_paterno': 'Apellido Paterno',
                'apellido_materno': 'Apellido Materno',
                'ci': 'CI',
                'fecha_nacimiento': 'Fecha Nacimiento',
                'edad': 'Edad',
                'genero': 'Género',
                'telefono': 'Teléfono',
                'email': 'Email',
                'direccion': 'Dirección',
                'ciudad': 'Ciudad',
                'estado_civil': 'Estado Civil',
                'ocupacion': 'Ocupación',
                'grupo_sanguineo': 'Grupo Sanguíneo',
                'rh': 'RH'
            };

            exportarExcel(
                filteredData,
                columnas,
                {
                    filename: `pacientes_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
                    sheetName: 'Pacientes',
                    title: `Listado de Pacientes - ${dayjs().format('DD/MM/YYYY')}`
                }
            );
            message.success('Archivo Excel generado exitosamente');
        } catch (error) {
            message.error('Error al generar el archivo Excel');
        }
    }, [filteredData, message]);

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

    if (loading && pacientes.length === 0) {
        return <GlobalLoader tip="Cargando directorio de pacientes…" />;
    }

    return (
        <div className="pacientes-module animate-fade-in">

            {/* --- HEADER Y ESTADÍSTICAS --- */}
            <div style={{ marginBottom: 24 }}>
                <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <AnimatedStatistic title="Total Pacientes" value={stats.total} prefix={<TeamOutlined />} />
                            <Progress percent={100} showInfo={false} strokeColor={token.colorPrimary} size="small" />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <AnimatedStatistic title="Embarazos Activos" value={stats.embarazadas} prefix={<HeartOutlined style={{ color: token.colorError }} />} valueStyle={{ color: token.colorError }} />
                            <Progress percent={(stats.embarazadas / stats.total) * 100} showInfo={false} strokeColor={token.colorError} size="small" />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <AnimatedStatistic title="Nuevos este Mes" value={stats.nuevosMes} prefix={<PlusOutlined style={{ color: token.colorSuccess }} />} valueStyle={{ color: token.colorSuccess }} />
                            <Progress percent={stats.nuevosMes > 0 ? 100 : 0} showInfo={false} strokeColor={token.colorSuccess} size="small" />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <AnimatedStatistic title="Promedio Edad" value={stats.promedioEdad} suffix="años" prefix={<InfoCircleOutlined style={{ color: token.colorWarning }} />} />
                        </Card>
                    </Col>
                </Row>
            </div>

            {/* --- BARRA DE HERRAMIENTAS --- */}
            <Card variant="borderless" className="shadow-card" style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
                    {/* Izquierda: Búsqueda y Filtros */}
                    <Space size="middle" wrap>
                        <Input
                            placeholder="Buscar por nombre, CI o ID..."
                            prefix={<SearchOutlined style={{ color: token.colorTextQuaternary }} />}
                            onChange={e => setSearchText(e.target.value)}
                            style={{ width: 300 }}
                            size="large"
                            allowClear
                        />
                            <Button
                                icon={FILTER_ICON_2}
                                onClick={() => setShowFilters(!showFilters)}
                            type={showFilters ? 'primary' : 'default'}
                        >
                            Filtros Avanzados
                        </Button>
                        {selectedRowKeys.length > 0 && (
                            <Button danger icon={DELETE_ICON_2} onClick={handleBulkDelete}>
                                Eliminar ({selectedRowKeys.length})
                            </Button>
                        )}
                    </Space>

                    {/* Derecha: Acciones Principales */}
                    <Space wrap>
                        <Button icon={BAR_CHART_ICON} onClick={() => setModalAnalisisDemograficoVisible(true)}>
                            Análisis Demográfico
                        </Button>
                        <Button icon={SYNC_ICON_2} onClick={() => setModalImportExportVisible(true)}>
                            Importar/Exportar
                        </Button>
                        <Button icon={TEAM_ICON_2} onClick={() => setModalComparacionVisible(true)}>
                            Comparar Pacientes
                        </Button>
                        <Button icon={CALENDAR_ICON_5} onClick={() => setDrawerAgendaVisible(true)}>
                            Agenda
                        </Button>
                        <Button icon={EXPORT_ICON_3} onClick={handleExport}>Exportar CSV</Button>
                        <Button icon={FILE_EXCEL_ICON_2} onClick={handleExportExcel} style={{ backgroundColor: token.colorSuccess, color: 'white', borderColor: token.colorSuccess }}>
                            Exportar Excel
                        </Button>
                        <Button icon={FILE_PDF_ICON_4} onClick={handleExportPDF} style={{ backgroundColor: token.colorError, color: 'white', borderColor: token.colorError }}>
                            Exportar PDF
                        </Button>
                        <Button icon={RELOAD_ICON_2} onClick={loadPacientes} loading={loading}>Recargar</Button>
                        {canAdd('paciente') && (
                            <Button type="primary" icon={PLUS_ICON_5} onClick={handleOpenCreate} size="large">
                                Nueva Paciente
                            </Button>
                        )}
                    </Space>
                </div>

                {/* Panel de Filtros Avanzados (Colapsable) */}
                {showFilters && (
                    <div style={{ marginTop: 20, paddingTop: 20, borderTop: `1px solid ${token.colorBorderSecondary}` }} className="animate-slide-down">
                        <Row gutter={[16, 16]}>
                            <Col span={6}>
                                <Select
                                    placeholder="Género"
                                    style={{ width: '100%' }}
                                    allowClear
                                    onChange={(val) => setFilters(prev => ({ ...prev, genero: val }))}
                                >
                                    <Option value="femenino">Femenino</Option>
                                    <Option value="masculino">Masculino</Option>
                                </Select>
                            </Col>
                            <Col span={6}>
                                <Input
                                    placeholder="Ciudad"
                                    onChange={(e) => setFilters(prev => ({ ...prev, ciudad: e.target.value }))}
                                />
                            </Col>
                            <Col span={6}>
                                <Select
                                    placeholder="Estado"
                                    style={{ width: '100%' }}
                                    allowClear
                                    onChange={(val) => setFilters(prev => ({ ...prev, estado: val }))}
                                >
                                    <Option value="activo">Activos</Option>
                                    <Option value="inactivo">Inactivos</Option>
                                </Select>
                            </Col>
                            <Col span={6}>
                                <Checkbox onChange={(e) => setFilters(prev => ({ ...prev, tieneEmbarazo: e.target.checked }))}>
                                    Solo con Embarazo Activo
                                </Checkbox>
                            </Col>
                        </Row>
                    </div>
                )}
            </Card>

            {/* --- TABLA DE DATOS --- */}
            <Card variant="borderless" className="shadow-card" styles={{ body: { padding: 0 } }}>
                <Table
                    rowKey={(record: any) => record._uniqueRowKey || `paciente-fallback-${record.id}`}
                    dataSource={filteredData}
                    locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay pacientes registrados" /> }}
                    columns={columns as any}
                    loading={loading}
                    rowSelection={{
                        selectedRowKeys,
                        onChange: (keys) => setSelectedRowKeys(keys)
                    }}
                    pagination={{
                        current: currentPage,
                        pageSize: pageSize,
                        total: totalPacientes,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} pacientes (Total en base de datos: ${totalPacientes})`,
                        pageSizeOptions: ['10', '20', '50', '100', '200'],
                    }}
                    onChange={(pagination) => {
                        if (pagination.current !== currentPage) setCurrentPage(pagination.current!);
                        if (pagination.pageSize !== pageSize) {
                            setPageSize(pagination.pageSize!);
                            setCurrentPage(1);
                        }
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
                pacientes={pacientes}
                stats={stats}
                token={token}
            />

            {/* SISTEMA DE IMPORTACIÓN/EXPORTACIÓN MASIVA */}
            <ImportExportModal
                visible={modalImportExportVisible}
                onClose={() => setModalImportExportVisible(false)}
                token={token}
            />

            {/* HERRAMIENTAS DE COMPARACIÓN Y ANÁLISIS */}
            <ComparacionModal
                visible={modalComparacionVisible}
                onClose={() => {
                    setModalComparacionVisible(false);
                    setPacientesComparacion({ a: null, b: null, c: null });
                }}
                pacientes={pacientes}
                pacientesComparacion={pacientesComparacion}
                setPacientesComparacion={setPacientesComparacion}
            />

            {/* AGENDA Y RECORDATORIOS */}
            <AgendaDrawer
                visible={drawerAgendaVisible}
                onClose={() => setDrawerAgendaVisible(false)}
                pacientes={pacientes}
            />

        </div>
    );
};

export default Pacientes;
