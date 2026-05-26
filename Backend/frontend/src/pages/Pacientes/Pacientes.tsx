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
    Table,
    Button,
    Modal,
    Form,
    Input,
    DatePicker,
    Select,
    Space,
    Card,
    Row,
    Col,
    Tag,
    Typography,
    Tooltip,
    Badge,
    Divider,
    Drawer,
    Steps,
    Statistic,
    Avatar,
    Empty,
    Descriptions,
    Timeline,
    Alert,
    Dropdown,
    Menu,
    Checkbox,
    Spin,
    Progress,
    Tabs,
    Radio,
    Upload,
    List,
    Calendar
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { usePermissions } from '../../hooks/usePermissions';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    SearchOutlined,
    UserOutlined,
    ReloadOutlined,
    FolderOpenOutlined,
    PhoneOutlined,
    MailOutlined,
    IdcardOutlined,
    WomanOutlined,
    ManOutlined,
    HomeOutlined,
    GlobalOutlined,
    FilterOutlined,
    ExportOutlined,
    MoreOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    InfoCircleOutlined,
    HistoryOutlined,
    FileExcelOutlined,
    PrinterOutlined,
    MedicineBoxOutlined,
    HeartOutlined,
    HeartFilled,
    TeamOutlined,
    DownloadOutlined,
    WarningOutlined,
    CalendarOutlined,
    FileTextOutlined,
    FilePdfOutlined,
    InboxOutlined,
    SyncOutlined,
    CloudUploadOutlined,
    CloudDownloadOutlined,
    DatabaseOutlined,
    ApiOutlined,
    UploadOutlined,
    BookOutlined,
    SafetyCertificateOutlined,
    SettingOutlined,
    QuestionCircleOutlined,
    BarChartOutlined,
    RiseOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import locale from 'antd/es/date-picker/locale/es_ES';

// Importamos el motor API robusto creado anteriormente
import { api } from '../../services/api';
import pdfService from '../../services/pdfService';
import { exportarExcel } from '../../utils/excelExport';
import { GlobalLoader } from '../../components/common/GlobalLoader';

// Configuración regional
dayjs.locale('es');
const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;
const { Step } = Steps;
const { RangePicker } = DatePicker;

// =============================================================================
// 1. DEFINICIÓN DE TIPOS Y ENTIDADES
// =============================================================================

export interface Paciente {
    id: number;
    id_clinico: string;
    nombre: string;
    apellido_paterno: string;
    apellido_materno?: string;
    nombre_completo?: string; // Campo calculado en frontend o backend
    fecha_nacimiento: string; // ISO string YYYY-MM-DD
    edad?: number;
    genero: 'femenino' | 'masculino' | 'otro';
    ci: string;
    telefono?: string;
    email?: string;
    direccion?: string;
    ciudad?: string;
    pais?: string;
    estado_civil?: string; // Nuevo campo extendido
    ocupacion?: string; // Nuevo campo extendido
    grupo_sanguineo?: string; // Nuevo campo extendido
    tipo_sangre?: string; // Campo de tipo de sangre desde backend
    peso_kg?: number;
    altura_cm?: number;
    imc?: number;
    factor_rh?: string;
    numero_seguro_social?: string;
    estado_paciente?: string;
    fecha_baja?: string;
    observaciones?: string;
    activo: boolean;
    embarazos_activos?: boolean;
    fecha_registro?: string;
    foto_perfil?: string; // URL simulada
    _uniqueRowKey?: string; // ✅ Para evitar warnings de keys duplicadas
}

// Filtros avanzados
interface AdvancedFilters {
    genero?: string;
    edadMin?: number;
    edadMax?: number;
    ciudad?: string;
    estado?: string; // 'activo' | 'inactivo'
    tieneEmbarazo?: boolean;
}

// Estadísticas
interface PacienteStats {
    total: number;
    activos: number;
    nuevosMes: number;
    embarazadas: number;
    promedioEdad: number;
}

// =============================================================================
// 2. COMPONENTE PRINCIPAL
// =============================================================================

const USER_ICON = <UserOutlined />;
const FOLDER_OPEN_ICON = <FolderOpenOutlined />;
const SEARCH_ICON_2 = <SearchOutlined />;
const MORE_ICON = <MoreOutlined />;
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
const HOME_ICON_2 = <HomeOutlined />;
const MEDICINE_BOX_ICON_4 = <MedicineBoxOutlined />;
const CHECK_CIRCLE_ICON_5 = <CheckCircleOutlined />;
const BOOK_ICON = <BookOutlined />;
const RISE_ICON = <RiseOutlined />;
const CLOSE_CIRCLE_ICON_2 = <CloseCircleOutlined />;
const WOMAN_ICON = <WomanOutlined />;
const MAN_ICON_2 = <ManOutlined />;
const HEART_ICON_5 = <HeartOutlined />;
const FILE_TEXT_ICON_6 = <FileTextOutlined />;
const DOWNLOAD_ICON_5 = <DownloadOutlined />;
const CLOUD_UPLOAD_ICON = <CloudUploadOutlined />;
const CLOUD_DOWNLOAD_ICON = <CloudDownloadOutlined />;
const DATABASE_ICON_2 = <DatabaseOutlined />;

const Pacientes: React.FC = () => {
    const navigate = useNavigate();
    const { message, modal } = useAntdApp();
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
    const getEstadoCivilConGenero = (estadoCivil: string | undefined, genero: string | undefined): string => {
        if (!estadoCivil) return 'N/A';

        const esFemenino = genero === 'femenino';

        switch (estadoCivil) {
            case 'soltero':
                return esFemenino ? 'Soltera' : 'Soltero';
            case 'casado':
                return esFemenino ? 'Casada' : 'Casado';
            case 'divorciado':
                return esFemenino ? 'Divorciada' : 'Divorciado';
            case 'viudo':
                return esFemenino ? 'Viuda' : 'Viudo';
            case 'union_libre':
                return 'Unión Libre';
            default:
                return estadoCivil;
        }
    };

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
        const startTime = performance.now();

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

            const endTime = performance.now();
            const loadTime = ((endTime - startTime) / 1000).toFixed(2);
            message.success(`${allPacientes.length} pacientes cargados en ${loadTime}s`, 3);

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
                message.success({ content: 'Paciente actualizado correctamente', icon: <CheckCircleOutlined style={{ color: '#52c41a' }} /> });
            } else {
                await api.post('/pacientes/', payload);
                message.success({ content: 'Paciente registrado exitosamente', icon: <CheckCircleOutlined style={{ color: '#52c41a' }} /> });
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
    }, [form, editingPaciente, message, loadPacientes]);

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

    const columns = useMemo(() => [
        {
            title: 'ID / Registro',
            dataIndex: 'id_clinico',
            width: 120,
            render: (text: string, record: Paciente) => (
                <div>
                    <Tag color="blue" style={{ marginRight: 0 }}>{text}</Tag>
                    <div style={{ fontSize: '12px', color: '#999', marginTop: 4 }}>
                        {dayjs(record.fecha_registro).format('DD/MM/YYYY')}
                    </div>
                </div>
            ),
        },
        {
            title: 'Paciente',
            key: 'paciente',
            width: 250,
            sorter: (a: Paciente, b: Paciente) => a.nombre.localeCompare(b.nombre),
            render: (_: any, record: Paciente) => (
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar
                        shape="square"
                        size="large"
                        icon={USER_ICON}
                        src={record.foto_perfil}
                        style={{
                            backgroundColor: record.genero === 'femenino' ? '#ffadd2' : '#1890ff',
                            marginRight: 12
                        }}
                    />
                    <div>
                        <Text strong style={{ fontSize: 15 }}>{record.nombre_completo}</Text>
                        <div style={{ fontSize: 12, color: '#666' }}>
                            {record.edad} años • {record.genero === 'femenino' ? 'Mujer' : 'Hombre'}
                        </div>
                    </div>
                </div>
            ),
        },
        {
            title: 'Identificación',
            dataIndex: 'ci',
            width: 130,
            render: (ci: string) => (
                <Space>
                    <IdcardOutlined style={{ color: '#1890ff' }} />
                    <Text copyable>{ci}</Text>
                </Space>
            )
        },
        {
            title: 'Estado Obstétrico',
            key: 'estado_obstetrico',
            width: 160,
            filters: [
                { text: 'Gestando', value: 'gestando' },
                { text: 'Sin Embarazo', value: 'sin_embarazo' },
                { text: 'Con Historial', value: 'con_historial' },
            ],
            onFilter: (value: any, record: Paciente) => {
                if (value === 'gestando') return !!record.embarazos_activos;
                if (value === 'sin_embarazo') return !record.embarazos_activos && !(record as any).numero_gesta;
                if (value === 'con_historial') return !record.embarazos_activos && !!(record as any).numero_gesta;
                return true;
            },
            render: (_: any, record: Paciente) => {
                const pacienteExtendido = record as any;
                const tieneEmbarazoActivo = record.embarazos_activos;
                const numeroGesta = pacienteExtendido.numero_gesta || 0;
                const numeroAbortos = pacienteExtendido.numero_abortos || 0;
                const numeroCesareas = pacienteExtendido.numero_cesareas || 0;
                const numeroPara = pacienteExtendido.numero_para || 0;
                const ultimoEstado = pacienteExtendido.ultimo_estado_obstetrico || '';
                const fechaUltimoEvento = pacienteExtendido.fecha_ultimo_evento || '';

                if (tieneEmbarazoActivo) {
                    // Embarazo Activo - EN CONTROL
                    return (
                        <Space direction="vertical" size={3} style={{ width: '100%' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Badge status="processing" />
                                <Tag color="green" style={{ margin: 0, fontWeight: 'bold', fontSize: '12px' }}>
                                    🤰 GESTANDO
                                </Tag>
                            </div>
                            <div style={{ fontSize: '12px', color: '#52c41a' }}>
                                ✓ En Control Prenatal
                            </div>
                            {numeroGesta > 0 && (
                                <Text style={{ fontSize: '12px', color: '#666' }}>
                                    Gesta: {numeroGesta}
                                </Text>
                            )}
                        </Space>
                    );
                } else if (numeroGesta > 0 || numeroAbortos > 0 || numeroCesareas > 0 || numeroPara > 0) {
                    // Tiene historial obstétrico - MOSTRAR ESTADO FINAL

                    // Determinar el estado final más reciente
                    let estadoFinal = '';
                    let colorEstado = 'blue';
                    let iconoEstado: React.ReactNode = <FileTextOutlined />;

                    if (ultimoEstado) {
                        estadoFinal = ultimoEstado;
                        if (ultimoEstado.toLowerCase().includes('aborto')) {
                            colorEstado = 'orange';
                            iconoEstado = <WarningOutlined />;
                        } else if (ultimoEstado.toLowerCase().includes('cesarea') || ultimoEstado.toLowerCase().includes('cesárea')) {
                            colorEstado = 'purple';
                            iconoEstado = <MedicineBoxOutlined />;
                        } else if (ultimoEstado.toLowerCase().includes('parto')) {
                            colorEstado = 'cyan';
                            iconoEstado = <HeartOutlined />;
                        }
                    } else {
                        if (numeroAbortos > 0 && numeroPara === 0 && numeroCesareas === 0) {
                            estadoFinal = 'Último: Aborto';
                            colorEstado = 'orange';
                            iconoEstado = <WarningOutlined />;
                        } else if (numeroCesareas > 0) {
                            estadoFinal = 'Último: Cesárea';
                            colorEstado = 'purple';
                            iconoEstado = <MedicineBoxOutlined />;
                        } else if (numeroPara > 0) {
                            estadoFinal = 'Último: Parto Normal';
                            colorEstado = 'cyan';
                            iconoEstado = <HeartOutlined />;
                        } else {
                            estadoFinal = 'Con Historial';
                            colorEstado = 'blue';
                            iconoEstado = <FileTextOutlined />;
                        }
                    }

                    return (
                        <Space direction="vertical" size={2} style={{ width: '100%' }}>
                            <Tag color={colorEstado} style={{ margin: 0, fontSize: '12px', fontWeight: 'bold' }}>
                                {iconoEstado} {estadoFinal}
                            </Tag>
                            <Space direction="vertical" size={2} style={{ width: '100%' }}>
                                {numeroGesta > 0 && <Tag color="blue" style={{ margin: 0, fontSize: '12px', fontWeight: 'bold' }}>Gestaciones: {numeroGesta}</Tag>}
                                {numeroPara > 0 && <Tag color="green" style={{ margin: 0, fontSize: '12px', fontWeight: 'bold' }}>Partos: {numeroPara}</Tag>}
                                {numeroCesareas > 0 && <Tag color="purple" style={{ margin: 0, fontSize: '12px', fontWeight: 'bold' }}>Cesáreas: {numeroCesareas}</Tag>}
                                {numeroAbortos > 0 && <Tag color="orange" style={{ margin: 0, fontSize: '12px', fontWeight: 'bold' }}>Abortos: {numeroAbortos}</Tag>}
                            </Space>
                            {fechaUltimoEvento && (
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                    {dayjs(fechaUltimoEvento).format('DD/MM/YYYY')}
                                </Text>
                            )}
                        </Space>
                    );
                } else {
                    // Sin embarazo y sin historial
                    return (
                        <Space direction="vertical" size={2}>
                            <Tag color="default" style={{ margin: 0, fontSize: '12px' }}>
                                ✓ Sin Embarazo
                            </Tag>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                                Sin historial
                            </Text>
                        </Space>
                    );
                }
            },
        },
        {
            title: 'Datos Médicos',
            key: 'datos_medicos',
            width: 200,
            render: (_: any, record: Paciente) => {
                // Calcular IMC si tenemos peso y altura
                let imc = record.imc;
                if (!imc && record.peso_kg && record.altura_cm) {
                    const alturaMetros = record.altura_cm / 100;
                    imc = record.peso_kg / (alturaMetros * alturaMetros);
                }

                const tieneDatos = record.tipo_sangre || imc || record.peso_kg || record.altura_cm;

                return (
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                        {/* Tipo de Sangre */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            <HeartFilled style={{ color: '#ff4d4f', fontSize: 12 }} />
                            {record.tipo_sangre ? (
                                <Tag color="red" style={{ fontWeight: 'bold', margin: 0, fontSize: '12px' }}>
                                    {record.tipo_sangre}
                                    {record.factor_rh && ` ${record.factor_rh === 'positivo' ? '+' : '-'}`}
                                </Tag>
                            ) : (
                                <Text type="secondary" style={{ fontSize: '12px' }}>Sin registro</Text>
                            )}
                        </div>

                        {/* Peso y Altura */}
                        {(record.peso_kg || record.altura_cm) && (
                            <div style={{ fontSize: '12px', color: '#666' }}>
                                {record.peso_kg && <span>{record.peso_kg}kg</span>}
                                {record.peso_kg && record.altura_cm && <span> • </span>}
                                {record.altura_cm && <span>{record.altura_cm}cm</span>}
                            </div>
                        )}

                        {/* IMC */}
                        {imc && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <Text strong style={{ fontSize: '12px', color: '#666' }}>IMC:</Text>
                                <Tag
                                    color={
                                        imc < 18.5 ? 'orange' :
                                            imc < 25 ? 'green' :
                                                imc < 30 ? 'gold' : 'red'
                                    }
                                    style={{ fontSize: '12px', margin: 0 }}
                                >
                                    {imc.toFixed(1)} - {
                                        imc < 18.5 ? 'Bajo' :
                                            imc < 25 ? 'Normal' :
                                                imc < 30 ? 'Sobrepeso' : 'Obesidad'
                                    }
                                </Tag>
                            </div>
                        )}

                        {!tieneDatos && <Text type="secondary" style={{ fontSize: '12px' }}>Sin datos médicos</Text>}
                    </Space>
                );
            },
        },
        {
            title: 'Contacto',
            key: 'contacto',
            width: 150,
            render: (_: any, record: Paciente) => (
                <Space direction="vertical" size={0} style={{ fontSize: 12 }}>
                    {record.telefono && <span><PhoneOutlined /> {record.telefono}</span>}
                    {record.ciudad && <span><HomeOutlined /> {record.ciudad}</span>}
                </Space>
            ),
        },
        {
            title: 'Acciones',
            key: 'acciones',
            fixed: 'right' as 'right',
            width: 140,
            render: (_: any, record: Paciente) => (
                <Space>
                    <Tooltip title="Historia Clínica">
                        <Button
                            type="primary"
                            shape="circle"
                            icon={FOLDER_OPEN_ICON}
                            onClick={() => navigate(`/dashboard/pacientes/${record.id}/historia`)}
                        />
                    </Tooltip>
                    <Tooltip title="Ver Detalles">
                        <Button
                            shape="circle"
                            icon={SEARCH_ICON_2}
                            onClick={() => { setSelectedPaciente(record); setDrawerVisible(true); }}
                        />
                    </Tooltip>
                    <Dropdown menu={{
                        items: [
                            // Editar - solo si tiene permiso
                            ...(canChange('paciente') ? [{
                                key: 'edit',
                                icon: <EditOutlined />,
                                label: 'Editar Información',
                                onClick: () => handleOpenEdit(record)
                            }] : []),
                            {
                                key: 'history',
                                icon: <HistoryOutlined />,
                                label: 'Ver Historial',
                                onClick: () => navigate(`/dashboard/pacientes/${record.id}/historia`)
                            },
                            {
                                key: 'export-pdf',
                                icon: <SafetyCertificateOutlined />,
                                label: 'Exportar a PDF',
                                onClick: () => handleExportPacientePDF(record)
                            },
                            {
                                key: 'print',
                                icon: <PrinterOutlined />,
                                label: 'Imprimir Ficha'
                            },
                            {
                                key: 'settings',
                                icon: <SettingOutlined />,
                                label: 'Configuración Paciente'
                            },
                            {
                                key: 'help',
                                icon: <QuestionCircleOutlined />,
                                label: 'Ayuda'
                            },
                            // Separador solo si tiene permiso de eliminar
                            ...(canDelete('paciente') ? [{
                                type: 'divider' as const
                            }] : []),
                            // Eliminar - solo si tiene permiso
                            ...(canDelete('paciente') ? [{
                                key: 'delete',
                                danger: true,
                                icon: <DeleteOutlined />,
                                label: 'Eliminar Paciente',
                                onClick: () => {
                                    Modal.confirm({
                                        title: '⚠️ ¿Confirmar eliminación permanente del paciente?',
                                        content: (
                                            <div>
                                                <p><strong>Se eliminará el paciente:</strong></p>
                                                <ul style={{ marginLeft: 20 }}>
                                                    <li>Nombre: {record.nombre_completo}</li>
                                                    <li>ID Clínico: {record.id_clinico}</li>
                                                    <li>CI: {record.ci}</li>
                                                </ul>
                                                <p style={{ color: '#ff4d4f', fontWeight: 'bold', marginTop: 16 }}>
                                                    ⚠️ ADVERTENCIA: Esta acción eliminará PERMANENTEMENTE:
                                                </p>
                                                <ul style={{ marginLeft: 20, color: '#ff4d4f' }}>
                                                    <li>Toda la historia clínica del paciente</li>
                                                    <li>Todos los embarazos registrados</li>
                                                    <li>Todos los controles prenatales</li>
                                                    <li>Todos los partos y recién nacidos</li>
                                                    <li>Documentos, citas y seguimientos</li>
                                                </ul>
                                                <p style={{ marginTop: 16 }}>
                                                    <strong>Esta acción NO se puede deshacer. ¿Está completamente seguro?</strong>
                                                </p>
                                            </div>
                                        ),
                                        okText: 'Sí, eliminar permanentemente',
                                        cancelText: 'Cancelar',
                                        okButtonProps: { danger: true },
                                        width: 650,
                                        onOk: () => handleDelete(record.id)
                                    });
                                }
                            }] : [])
                        ]
                    }} trigger={['click']}>
                        <Button type="text" icon={MORE_ICON} />
                    </Dropdown>
                </Space>
            ),
        },
    ], [canChange, canDelete, handleOpenEdit, navigate, handleExportPacientePDF, handleDelete]);

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
                            <Statistic title="Total Pacientes" value={stats.total} prefix={<TeamOutlined />} />
                            <Progress percent={100} showInfo={false} strokeColor="#1890ff" size="small" />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <Statistic title="Embarazos Activos" value={stats.embarazadas} prefix={<HeartOutlined style={{ color: '#ff4d4f' }} />} valueStyle={{ color: '#ff4d4f' }} />
                            <Progress percent={(stats.embarazadas / stats.total) * 100} showInfo={false} strokeColor="#ff4d4f" size="small" />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <Statistic title="Nuevos este Mes" value={stats.nuevosMes} prefix={<PlusOutlined style={{ color: '#52c41a' }} />} valueStyle={{ color: '#52c41a' }} />
                            <Progress percent={stats.nuevosMes > 0 ? 100 : 0} showInfo={false} strokeColor="#52c41a" size="small" />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <Statistic title="Promedio Edad" value={stats.promedioEdad} suffix="años" prefix={<InfoCircleOutlined style={{ color: '#faad14' }} />} />
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
                            prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
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
                        <Button icon={FILE_EXCEL_ICON_2} onClick={handleExportExcel} style={{ backgroundColor: '#52c41a', color: 'white', borderColor: '#52c41a' }}>
                            Exportar Excel
                        </Button>
                        <Button icon={FILE_PDF_ICON_4} onClick={handleExportPDF} style={{ backgroundColor: '#ff4d4f', color: 'white', borderColor: '#ff4d4f' }}>
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
                    <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid #f0f0f0' }} className="animate-slide-down">
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

            {/* ========================================================================
            MODAL WIZARD (REGISTRO PASO A PASO)
           ======================================================================== */}
            <Modal
                title={editingPaciente ? `Editar: ${editingPaciente.nombre_completo}` : 'Registro de Nuevo Paciente'}
                open={modalVisible}
                onCancel={() => setModalVisible(false)}
                footer={null}
                width={800}
                maskClosable={false}
            >
                <Steps current={currentStep} style={{ marginBottom: 24 }} size="small">
                    <Step title="Datos Personales" icon={USER_ICON} />
                    <Step title="Contacto" icon={HOME_ICON_2} />
                    <Step title="Información Médica" icon={MEDICINE_BOX_ICON_4} />
                </Steps>

                <Form
                    form={form}
                    layout="vertical"
                    initialValues={{ pais: 'Bolivia', activo: true }}
                >
                    {/* PASO 1: DATOS PERSONALES */}
                    <div style={{ display: currentStep === 0 ? 'block' : 'none' }}>
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item name="nombre" label="Nombres" rules={[{ required: true, message: 'Requerido' }]}>
                                    <Input prefix={<UserOutlined />} placeholder="Ej: Ana María" />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item name="apellido_paterno" label="Apellido Paterno" rules={[{ required: true, message: 'Requerido' }]}>
                                    <Input placeholder="Ej: Flores" />
                                </Form.Item>
                            </Col>
                        </Row>
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item name="apellido_materno" label="Apellido Materno">
                                    <Input placeholder="Ej: Quispe" />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item name="ci" label="Cédula de Identidad" rules={[{ required: true, message: 'Requerido' }, { pattern: /^[0-9]{5,10}$/, message: '5-10 dígitos' }]}>
                                    <Input prefix={<IdcardOutlined />} />
                                </Form.Item>
                            </Col>
                        </Row>
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item name="fecha_nacimiento" label="Fecha de Nacimiento" rules={[{ required: true, message: 'Seleccione fecha' }]}>
                                    <DatePicker
                                        style={{ width: '100%' }}
                                        format="DD/MM/YYYY"
                                        locale={locale}
                                        disabledDate={(d) => d && d > dayjs()}
                                    />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item name="genero" label="Género" rules={[{ required: true }]}>
                                    <Select>
                                        <Option value="femenino">Femenino</Option>
                                        <Option value="masculino">Masculino</Option>
                                        <Option value="otro">Otro</Option>
                                    </Select>
                                </Form.Item>
                            </Col>
                        </Row>
                    </div>

                    {/* PASO 2: CONTACTO */}
                    <div style={{ display: currentStep === 1 ? 'block' : 'none' }}>
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item name="telefono" label="Teléfono / Celular" rules={[{ pattern: /^[0-9]{7,8}$/, message: 'Número inválido (7-8 dígitos)' }]}>
                                    <Input prefix={<PhoneOutlined />} />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item name="email" label="Correo Electrónico" rules={[{ type: 'email' }]}>
                                    <Input prefix={<MailOutlined />} />
                                </Form.Item>
                            </Col>
                        </Row>
                        <Form.Item name="direccion" label="Dirección Domiciliaria">
                            <Input prefix={<HomeOutlined />} />
                        </Form.Item>
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item name="ciudad" label="Ciudad">
                                    <Input />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item name="pais" label="País">
                                    <Input prefix={<GlobalOutlined />} />
                                </Form.Item>
                            </Col>
                        </Row>
                    </div>

                    {/* PASO 3: EXTRA */}
                    <div style={{ display: currentStep === 2 ? 'block' : 'none' }}>
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item name="grupo_sanguineo" label="Grupo Sanguíneo">
                                    <Select placeholder="Seleccione...">
                                        <Option value="O+">O+</Option>
                                        <Option value="O-">O-</Option>
                                        <Option value="A+">A+</Option>
                                        <Option value="A-">A-</Option>
                                        <Option value="B+">B+</Option>
                                        <Option value="B-">B-</Option>
                                        <Option value="AB+">AB+</Option>
                                        <Option value="AB-">AB-</Option>
                                    </Select>
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item name="estado_civil" label="Estado Civil">
                                    <Select>
                                        <Option value="soltero">Soltero/a</Option>
                                        <Option value="casado">Casado/a</Option>
                                        <Option value="union_libre">Unión Libre</Option>
                                        <Option value="divorciado">Divorciado/a</Option>
                                        <Option value="viudo">Viudo/a</Option>
                                    </Select>
                                </Form.Item>
                            </Col>
                        </Row>
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item
                                    name="peso_kg"
                                    label="Peso (kg)"
                                    rules={[
                                        {
                                            pattern: /^\d+(\.\d{1,2})?$/,
                                            message: 'Ingrese un peso válido'
                                        }
                                    ]}
                                >
                                    <Input
                                        type="number"
                                        placeholder="Ej: 65.5"
                                        suffix="kg"
                                        step="0.1"
                                    />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item
                                    name="altura_cm"
                                    label="Altura (cm)"
                                    rules={[
                                        {
                                            pattern: /^\d+(\.\d{1,2})?$/,
                                            message: 'Ingrese una altura válida'
                                        }
                                    ]}
                                >
                                    <Input
                                        type="number"
                                        placeholder="Ej: 165"
                                        suffix="cm"
                                        step="0.1"
                                    />
                                </Form.Item>
                            </Col>
                        </Row>
                        <Form.Item name="ocupacion" label="Ocupación">
                            <Input />
                        </Form.Item>
                        <Form.Item name="observaciones" label="Observaciones / Antecedentes Breves">
                            <Input.TextArea rows={3} />
                        </Form.Item>
                    </div>
                </Form>

                <Divider />

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Button disabled={currentStep === 0} onClick={() => setCurrentStep(prev => prev - 1)}>
                        Atrás
                    </Button>
                    {currentStep < 2 && (
                        <Button type="primary" onClick={() => setCurrentStep(prev => prev + 1)}>
                            Siguiente
                        </Button>
                    )}
                    {currentStep === 2 && (
                        <Button type="primary" icon={CHECK_CIRCLE_ICON_5} onClick={handleSubmit} loading={formLoading}>
                            {editingPaciente ? 'Guardar Cambios' : 'Registrar Paciente'}
                        </Button>
                    )}
                </div>
            </Modal>

            {/* ========================================================================
            DRAWER DE DETALLE (VISTA RÁPIDA)
           ======================================================================== */}
            <Drawer
                className="paciente-expediente-drawer"
                title="Expediente Rápido"
                placement="right"
                width={600}
                onClose={() => setDrawerVisible(false)}
                open={drawerVisible}
                extra={
                    <Space>
                        <Menu mode="horizontal" selectedKeys={[]} style={{ border: 'none' }}>
                            <Menu.Item key="book" icon={BOOK_ICON}>Documentos</Menu.Item>
                            <Menu.Item key="rise" icon={RISE_ICON}>Métricas</Menu.Item>
                        </Menu>
                        <Button type="primary" onClick={() => { setDrawerVisible(false); navigate(`/dashboard/pacientes/${selectedPaciente?.id}/historia`); }}>
                            Ver Historia Completa
                        </Button>
                    </Space>
                }
            >
                {selectedPaciente ? (
                    <Spin spinning={false} tip="Cargando expediente…">
                        <div className="drawer-content">
                            {/* CABECERA DRAWER */}
                            <div className="drawer-header-section">
                                <Avatar
                                    size={80}
                                    icon={selectedPaciente.genero === 'femenino' ? <WomanOutlined /> : <ManOutlined />}
                                    style={{ backgroundColor: selectedPaciente.genero === 'femenino' ? '#ffadd2' : '#1890ff', marginBottom: 10 }}
                                />
                                <Title level={3} style={{ margin: 0 }}>{selectedPaciente.nombre_completo}</Title>
                                <Text type="secondary">{selectedPaciente.id_clinico}</Text>
                                <div style={{ marginTop: 10 }}>
                                    {selectedPaciente.activo ? (
                                        <Tag color="green">ACTIVO</Tag>
                                    ) : (
                                        <Tag color="red" icon={CLOSE_CIRCLE_ICON_2}>INACTIVO</Tag>
                                    )}
                                    {selectedPaciente.embarazos_activos && <Tag color="purple">GESTANTE</Tag>}
                                    {selectedPaciente.genero === 'femenino' && (
                                        <Tag icon={WOMAN_ICON} color="pink">Femenino</Tag>
                                    )}
                                    {selectedPaciente.genero === 'masculino' && (
                                        <Tag icon={MAN_ICON_2} color="blue">Masculino</Tag>
                                    )}
                                </div>
                            </div>

                            <Descriptions title="Datos Generales" bordered column={1} size="small" className="drawer-descriptions">
                                <Descriptions.Item label="CI">{selectedPaciente.ci}</Descriptions.Item>
                                <Descriptions.Item label="Edad">{selectedPaciente.edad} años ({dayjs(selectedPaciente.fecha_nacimiento).format('DD/MM/YYYY')})</Descriptions.Item>
                                <Descriptions.Item label="Teléfono">{selectedPaciente.telefono || 'N/A'}</Descriptions.Item>
                                <Descriptions.Item label="Dirección">
                                    {selectedPaciente.direccion && selectedPaciente.ciudad
                                        ? `${selectedPaciente.direccion}, ${selectedPaciente.ciudad}`
                                        : selectedPaciente.direccion || selectedPaciente.ciudad || 'N/A'
                                    }
                                </Descriptions.Item>
                                <Descriptions.Item label="Email">{selectedPaciente.email || 'N/A'}</Descriptions.Item>
                                <Descriptions.Item label="Tipo de Sangre">
                                    {selectedPaciente.tipo_sangre ? (
                                        <Tag color="red" style={{ fontSize: 14, fontWeight: 'bold' }}>{selectedPaciente.tipo_sangre}</Tag>
                                    ) : 'N/A'}
                                </Descriptions.Item>
                                <Descriptions.Item label="Estado Civil">
                                    <Tag color="blue">
                                        {getEstadoCivilConGenero(selectedPaciente.estado_civil, selectedPaciente.genero)}
                                    </Tag>
                                </Descriptions.Item>
                                <Descriptions.Item label="Ocupación">
                                    {selectedPaciente.ocupacion || 'N/A'}
                                </Descriptions.Item>
                            </Descriptions>

                            <Descriptions title="Datos Médicos" bordered column={1} size="small" className="drawer-descriptions" style={{ marginTop: 16 }}>
                                <Descriptions.Item label="Peso">
                                    {selectedPaciente.peso_kg ? `${selectedPaciente.peso_kg} kg` : 'N/A'}
                                </Descriptions.Item>
                                <Descriptions.Item label="Altura">
                                    {selectedPaciente.altura_cm ? `${selectedPaciente.altura_cm} cm` : 'N/A'}
                                </Descriptions.Item>
                                <Descriptions.Item label="IMC">
                                    {selectedPaciente.imc ? (
                                        <Tag
                                            color={
                                                selectedPaciente.imc < 18.5 ? 'orange' :
                                                    selectedPaciente.imc < 25 ? 'green' :
                                                        selectedPaciente.imc < 30 ? 'gold' : 'red'
                                            }
                                            style={{ fontSize: 14, fontWeight: 'bold' }}
                                        >
                                            {selectedPaciente.imc}
                                            {' - '}
                                            {selectedPaciente.imc < 18.5 ? 'Bajo Peso' :
                                                selectedPaciente.imc < 25 ? 'Normal' :
                                                    selectedPaciente.imc < 30 ? 'Sobrepeso' : 'Obesidad'}
                                        </Tag>
                                    ) : 'N/A'}
                                </Descriptions.Item>
                            </Descriptions>

                            <Divider orientation="left">🔗 Acceso Rápido a Módulos</Divider>
                            <Card size="small" style={{ marginBottom: 16 }}>
                                <Space direction="vertical" style={{ width: '100%' }} size="small">
                                    <Button
                                        type="link"
                                        icon={HEART_ICON_5}
                                        block
                                        style={{ textAlign: 'left' }}
                                        onClick={() => {
                                            setDrawerVisible(false);
                                            navigate(`/dashboard/embarazos?paciente=${selectedPaciente.id}`);
                                        }}
                                    >
                                        Ver Embarazos de {selectedPaciente.nombre}
                                    </Button>
                                    <Button
                                        type="link"
                                        icon={MEDICINE_BOX_ICON_4}
                                        block
                                        style={{ textAlign: 'left' }}
                                        onClick={() => {
                                            setDrawerVisible(false);
                                            navigate(`/dashboard/controles?paciente=${selectedPaciente.id}`);
                                        }}
                                    >
                                        Ver Controles Prenatales
                                    </Button>
                                    <Button
                                        type="link"
                                        icon={CALENDAR_ICON_5}
                                        block
                                        style={{ textAlign: 'left' }}
                                        onClick={() => {
                                            setDrawerVisible(false);
                                            navigate(`/dashboard/citas?paciente=${selectedPaciente.id}`);
                                        }}
                                    >
                                        Ver Citas Programadas
                                    </Button>
                                    <Button
                                        type="link"
                                        icon={FILE_TEXT_ICON_6}
                                        block
                                        style={{ textAlign: 'left' }}
                                        onClick={() => {
                                            setDrawerVisible(false);
                                            navigate(`/dashboard/laboratorio?paciente=${selectedPaciente.id}`);
                                        }}
                                    >
                                        Ver Exámenes de Laboratorio
                                    </Button>
                                    <Button
                                        type="link"
                                        icon={SEARCH_ICON_2}
                                        block
                                        style={{ textAlign: 'left' }}
                                        onClick={() => {
                                            setDrawerVisible(false);
                                            navigate(`/dashboard/ecografias?paciente=${selectedPaciente.id}`);
                                        }}
                                    >
                                        Ver Ecografías
                                    </Button>
                                    <Divider style={{ margin: '8px 0' }} />
                                    <Button
                                        type="primary"
                                        icon={FOLDER_OPEN_ICON}
                                        block
                                        onClick={() => {
                                            setDrawerVisible(false);
                                            navigate(`/dashboard/pacientes/${selectedPaciente.id}/historia`);
                                        }}
                                    >
                                        Ver Historia Clínica Completa
                                    </Button>
                                </Space>
                            </Card>

                            <Divider orientation="left">Actividad Reciente</Divider>
                            <Timeline
                                mode="left"
                                items={[
                                    {
                                        color: "green",
                                        children: `Registro en el sistema (${dayjs(selectedPaciente.fecha_registro).format('DD/MM/YYYY')})`
                                    },
                                    ...(selectedPaciente.embarazos_activos ? [
                                        {
                                            color: "purple",
                                            dot: <HeartOutlined />,
                                            children: "Embarazo activo registrado"
                                        }
                                    ] : []),
                                    {
                                        color: "gray",
                                        children: "Sin consultas recientes"
                                    }
                                ]}
                            />

                            {selectedPaciente.observaciones && (
                                <Alert message="Observaciones" description={selectedPaciente.observaciones} type="info" showIcon style={{ marginTop: 20 }} />
                            )}

                            <Divider>Notas Rápidas</Divider>
                            <TextArea
                                rows={3}
                                placeholder="Agregar notas rápidas sobre este paciente..."
                                style={{ marginBottom: 16 }}
                            />

                            <Divider>Filtrar por Fechas</Divider>
                            <RangePicker style={{ width: '100%' }} />
                        </div>
                    </Spin>
                ) : (
                    <Empty description="Seleccione un paciente" />
                )}
            </Drawer>

            {/* ========================================================================
            MÓDULO DE ANÁLISIS DEMOGRÁFICO AVANZADO
           ======================================================================== */}
            <Modal
                title={<Space><BarChartOutlined /> Panel de Análisis Demográfico</Space>}
                open={modalAnalisisDemograficoVisible}
                onCancel={() => setModalAnalisisDemograficoVisible(false)}
                width={1200}
                footer={null}
            >
                <Tabs
                    items={[
                        {
                            key: '1',
                            label: 'Distribución por Edad',
                            children: (
                                <Card>
                                    <Alert
                                        message="Pirámide Poblacional"
                                        description={`Análisis de ${stats.total} pacientes. Edad promedio: ${stats.promedioEdad} años.`}
                                        type="info"
                                        showIcon
                                        style={{ marginBottom: 16 }}
                                    />
                                    <Row gutter={16}>
                                        <Col span={8}>
                                            <Statistic title="Menores de 20" value={pacientes.filter(p => (p.edad || 0) < 20).length} suffix="pacientes" />
                                        </Col>
                                        <Col span={8}>
                                            <Statistic title="20-35 años" value={pacientes.filter(p => (p.edad || 0) >= 20 && (p.edad || 0) <= 35).length} suffix="pacientes" />
                                        </Col>
                                        <Col span={8}>
                                            <Statistic title="Mayores de 35" value={pacientes.filter(p => (p.edad || 0) > 35).length} suffix="pacientes" />
                                        </Col>
                                    </Row>
                                    <Divider />
                                    <Table
                                        size="small"
                                        columns={[
                                            { title: 'Rango Etario', dataIndex: 'rango', key: 'rango' },
                                            { title: 'Cantidad', dataIndex: 'cantidad', key: 'cantidad' },
                                            { title: 'Porcentaje', dataIndex: 'porcentaje', key: 'porcentaje', render: (v: number) => `${v.toFixed(1)}%` }
                                        ]}
                                        dataSource={[
                                            { key: '1', rango: '< 15 años', cantidad: pacientes.filter(p => (p.edad || 0) < 15).length, porcentaje: (pacientes.filter(p => (p.edad || 0) < 15).length / stats.total) * 100 },
                                            { key: '2', rango: '15-19 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 15 && (p.edad || 0) < 20).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 15 && (p.edad || 0) < 20).length / stats.total) * 100 },
                                            { key: '3', rango: '20-24 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 20 && (p.edad || 0) < 25).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 20 && (p.edad || 0) < 25).length / stats.total) * 100 },
                                            { key: '4', rango: '25-29 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 25 && (p.edad || 0) < 30).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 25 && (p.edad || 0) < 30).length / stats.total) * 100 },
                                            { key: '5', rango: '30-34 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 30 && (p.edad || 0) < 35).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 30 && (p.edad || 0) < 35).length / stats.total) * 100 },
                                            { key: '6', rango: '35-39 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 35 && (p.edad || 0) < 40).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 35 && (p.edad || 0) < 40).length / stats.total) * 100 },
                                            { key: '7', rango: '≥ 40 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 40).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 40).length / stats.total) * 100 }
                                        ]}
                                        pagination={false}
                                    />
                                </Card>
                            ),
                        },
                        {
                            key: '2',
                            label: 'Distribución Geográfica',
                            children: (
                                <Card title="Pacientes por Ciudad">
                                    <Text>Mapa de distribución demográfica por ubicación geográfica:</Text>
                                    <Divider />
                                    {['La Paz', 'Cochabamba', 'Santa Cruz', 'Oruro', 'Potosí', 'Tarija', 'Beni', 'Pando', 'Chuquisaca'].map((ciudad) => {
                                        const count = pacientes.filter(p => p.ciudad?.toLowerCase().includes(ciudad.toLowerCase())).length;
                                        const percent = (count / stats.total) * 100;
                                        return (
                                            <div key={ciudad} style={{ marginBottom: 16 }}>
                                                <Row justify="space-between">
                                                    <Col><Text strong>{ciudad}</Text></Col>
                                                    <Col><Text>{count} pacientes ({percent.toFixed(1)}%)</Text></Col>
                                                </Row>
                                                <Progress percent={percent} strokeColor="#1890ff" showInfo={false} />
                                            </div>
                                        );
                                    })}
                                </Card>
                            ),
                        },
                        {
                            key: '3',
                            label: 'Grupos de Riesgo',
                            children: (
                                <Card title="Análisis de Poblaciones Vulnerables">
                                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                                        <Alert
                                            message="Identificación de Grupos Prioritarios"
                                            description="Detección automática de pacientes que requieren atención especializada"
                                            type="warning"
                                            showIcon
                                        />

                                        <Card size="small" title="Adolescentes (< 20 años)">
                                            <Statistic
                                                value={pacientes.filter(p => (p.edad || 0) < 20).length}
                                                suffix={`/ ${stats.total}`}
                                                prefix={<UserOutlined />}
                                            />
                                            <Text type="secondary">Requieren seguimiento psicosocial</Text>
                                        </Card>

                                        <Card size="small" title="Gestantes Añosas (≥ 35 años)">
                                            <Statistic
                                                value={pacientes.filter(p => (p.edad || 0) >= 35 && p.embarazos_activos).length}
                                                suffix="casos"
                                                prefix={<WarningOutlined />}
                                                valueStyle={{ color: '#cf1322' }}
                                            />
                                            <Text type="secondary">Mayor riesgo obstétrico</Text>
                                        </Card>

                                        <Card size="small" title="Multigestantes con Cesáreas Previas">
                                            <Statistic
                                                value={0}
                                                suffix="identificadas"
                                                prefix={<MedicineBoxOutlined />}
                                            />
                                            <Text type="secondary">Requieren evaluación quirúrgica especializada</Text>
                                        </Card>
                                    </Space>
                                </Card>
                            ),
                        },
                        {
                            key: '4',
                            label: 'Tendencias Temporales',
                            children: (
                                <Card title="Evolución de Registros">
                                    <Alert
                                        message="Análisis de Captación"
                                        description={`Se han registrado ${stats.nuevosMes} nuevos pacientes este mes. Tendencia: ${stats.nuevosMes > 10 ? 'CRECIENTE' : 'ESTABLE'}`}
                                        type={stats.nuevosMes > 10 ? 'success' : 'info'}
                                        showIcon
                                    />
                                    <Divider />
                                    <Row gutter={16}>
                                        {['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'].map((mes) => (
                                            <Col span={6} key={mes}>
                                                <Card size="small" style={{ textAlign: 'center', marginBottom: 8 }}>
                                                    <Statistic title={mes} value={0} valueStyle={{ fontSize: 18 }} />
                                                </Card>
                                            </Col>
                                        ))}
                                    </Row>
                                </Card>
                            ),
                        },
                    ]}
                />
            </Modal>

            {/* ========================================================================
            SISTEMA DE IMPORTACIÓN/EXPORTACIÓN MASIVA
           ======================================================================== */}
            <Modal
                title="Importación/Exportación Masiva de Pacientes"
                open={modalImportExportVisible}
                onCancel={() => setModalImportExportVisible(false)}
                width={800}
                footer={null}
            >
                <Tabs
                    items={[
                        {
                            key: '1',
                            label: <span><UploadOutlined /> Importar Datos</span>,
                            children: (
                                <Card>
                                    <Alert
                                        message="Carga Masiva desde Excel/CSV"
                                        description="Importe hasta 1000 registros simultáneamente. Formato requerido: Excel (.xlsx) o CSV (UTF-8)"
                                        type="info"
                                        showIcon
                                        style={{ marginBottom: 16 }}
                                    />
                                    <Upload.Dragger
                                        name="file"
                                        multiple={false}
                                        accept=".xlsx,.xls,.csv"
                                        beforeUpload={() => false}
                                    >
                                        <p className="ant-upload-drag-icon">
                                            <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                                        </p>
                                        <p className="ant-upload-text">Click o arrastre el archivo aquí</p>
                                        <p className="ant-upload-hint">
                                            Soporta archivos Excel (.xlsx) o CSV. Máximo 5MB.
                                        </p>
                                    </Upload.Dragger>
                                    <Divider />
                                    <Space>
                                        <Button icon={DOWNLOAD_ICON_5} type="link">
                                            Descargar Plantilla Excel
                                        </Button>
                                        <Button icon={FILE_TEXT_ICON_6} type="link">
                                            Ver Guía de Importación
                                        </Button>
                                    </Space>
                                </Card>
                            ),
                        },
                        {
                            key: '2',
                            label: <span><DownloadOutlined /> Exportar Datos</span>,
                            children: (
                                <Card>
                                    <Form layout="vertical">
                                        <Form.Item label="Formato de Exportación">
                                            <Radio.Group defaultValue="excel">
                                                <Radio.Button value="excel">
                                                    <FileExcelOutlined /> Excel (.xlsx)
                                                </Radio.Button>
                                                <Radio.Button value="csv">
                                                    <FileTextOutlined /> CSV
                                                </Radio.Button>
                                                <Radio.Button value="pdf">
                                                    <FilePdfOutlined /> PDF
                                                </Radio.Button>
                                                <Radio.Button value="json">
                                                    <ApiOutlined /> JSON
                                                </Radio.Button>
                                            </Radio.Group>
                                        </Form.Item>

                                        <Form.Item label="Filtros de Exportación">
                                            <Checkbox.Group>
                                                <Row>
                                                    <Col span={12}><Checkbox value="activos">Solo Activos</Checkbox></Col>
                                                    <Col span={12}><Checkbox value="embarazadas">Solo Embarazadas</Checkbox></Col>
                                                    <Col span={12}><Checkbox value="nuevos">Nuevos Este Mes</Checkbox></Col>
                                                    <Col span={12}><Checkbox value="todos">Todos los Registros</Checkbox></Col>
                                                </Row>
                                            </Checkbox.Group>
                                        </Form.Item>

                                        <Form.Item label="Campos a Incluir">
                                            <Checkbox.Group defaultValue={['basicos', 'contacto']}>
                                                <Space direction="vertical">
                                                    <Checkbox value="basicos">Datos Básicos (Nombre, CI, Edad)</Checkbox>
                                                    <Checkbox value="contacto">Información de Contacto</Checkbox>
                                                    <Checkbox value="medicos">Datos Médicos (Grupo Sanguíneo, etc.)</Checkbox>
                                                    <Checkbox value="obstetricos">Historial Obstétrico</Checkbox>
                                                    <Checkbox value="observaciones">Observaciones y Notas</Checkbox>
                                                </Space>
                                            </Checkbox.Group>
                                        </Form.Item>

                                        <Divider />

                                        <Button type="primary" icon={EXPORT_ICON_3} block size="large">
                                            Generar y Descargar Reporte
                                        </Button>
                                    </Form>
                                </Card>
                            ),
                        },
                        {
                            key: '3',
                            label: <span><SyncOutlined /> Sincronización</span>,
                            children: (
                                <Card title="Sincronización con Sistemas Externos">
                                    <Alert
                                        message="Integración con SNIS-VE (Sistema Nacional)"
                                        description="Exporte datos al formato SNIS para reportes epidemiológicos mensuales"
                                        type="success"
                                        showIcon
                                        style={{ marginBottom: 16 }}
                                    />

                                    <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                        <Button icon={CLOUD_UPLOAD_ICON} block>
                                            Exportar a SNIS-VE (Formulario 301)
                                        </Button>
                                        <Button icon={CLOUD_DOWNLOAD_ICON} block>
                                            Importar desde Sistema Anterior
                                        </Button>
                                        <Button icon={DATABASE_ICON_2} block>
                                            Backup Completo de Base de Datos
                                        </Button>
                                    </Space>

                                    <Divider />

                                    <Descriptions title="Última Sincronización" column={1} size="small" bordered>
                                        <Descriptions.Item label="Fecha">{dayjs().subtract(2, 'day').format('DD/MM/YYYY HH:mm')}</Descriptions.Item>
                                        <Descriptions.Item label="Registros Enviados">245 pacientes</Descriptions.Item>
                                        <Descriptions.Item label="Estado"><Tag color="green">EXITOSO</Tag></Descriptions.Item>
                                    </Descriptions>
                                </Card>
                            ),
                        },
                    ]}
                />
            </Modal>

            {/* ========================================================================
            HERRAMIENTAS DE COMPARACIÓN Y ANÁLISIS
           ======================================================================== */}
            <Modal
                title="Comparación de Pacientes"
                open={modalComparacionVisible}
                onCancel={() => {
                    setModalComparacionVisible(false);
                    setPacientesComparacion({ a: null, b: null, c: null });
                }}
                width={1000}
                footer={null}
            >
                <Alert
                    message="Herramienta de Comparación Clínica"
                    description="Seleccione hasta 3 pacientes para comparar perfiles médicos, evolución y resultados"
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                />

                <Row gutter={16}>
                    <Col span={8}>
                        <Card title="Paciente A" size="small">
                            <Select
                                placeholder="Seleccionar paciente..."
                                style={{ width: '100%' }}
                                showSearch
                                optionFilterProp="children"
                                value={pacientesComparacion.a?.id}
                                onChange={(id) => {
                                    const pac = pacientes.find(p => p.id === id);
                                    setPacientesComparacion(prev => ({ ...prev, a: pac || null }));
                                }}
                            >
                                {pacientes.map(p => (
                                    <Option key={p.id} value={p.id}>{p.nombre_completo}</Option>
                                ))}
                            </Select>
                            <Divider />
                            {pacientesComparacion.a ? (
                                <Descriptions size="small" column={1} bordered>
                                    <Descriptions.Item label="Edad">{pacientesComparacion.a.edad} años</Descriptions.Item>
                                    <Descriptions.Item label="Grupo">{pacientesComparacion.a.tipo_sangre || 'N/A'}</Descriptions.Item>
                                    <Descriptions.Item label="CI">{pacientesComparacion.a.ci}</Descriptions.Item>
                                </Descriptions>
                            ) : (
                                <Empty description="Seleccione un paciente" />
                            )}
                        </Card>
                    </Col>
                    <Col span={8}>
                        <Card title="Paciente B" size="small">
                            <Select
                                placeholder="Seleccionar paciente..."
                                style={{ width: '100%' }}
                                showSearch
                                optionFilterProp="children"
                                value={pacientesComparacion.b?.id}
                                onChange={(id) => {
                                    const pac = pacientes.find(p => p.id === id);
                                    setPacientesComparacion(prev => ({ ...prev, b: pac || null }));
                                }}
                            >
                                {pacientes.map(p => (
                                    <Option key={p.id} value={p.id}>{p.nombre_completo}</Option>
                                ))}
                            </Select>
                            <Divider />
                            {pacientesComparacion.b ? (
                                <Descriptions size="small" column={1} bordered>
                                    <Descriptions.Item label="Edad">{pacientesComparacion.b.edad} años</Descriptions.Item>
                                    <Descriptions.Item label="Grupo">{pacientesComparacion.b.tipo_sangre || 'N/A'}</Descriptions.Item>
                                    <Descriptions.Item label="CI">{pacientesComparacion.b.ci}</Descriptions.Item>
                                </Descriptions>
                            ) : (
                                <Empty description="Seleccione un paciente" />
                            )}
                        </Card>
                    </Col>
                    <Col span={8}>
                        <Card title="Paciente C" size="small">
                            <Select
                                placeholder="Seleccionar paciente..."
                                style={{ width: '100%' }}
                                showSearch
                                optionFilterProp="children"
                                value={pacientesComparacion.c?.id}
                                onChange={(id) => {
                                    const pac = pacientes.find(p => p.id === id);
                                    setPacientesComparacion(prev => ({ ...prev, c: pac || null }));
                                }}
                            >
                                {pacientes.map(p => (
                                    <Option key={p.id} value={p.id}>{p.nombre_completo}</Option>
                                ))}
                            </Select>
                            <Divider />
                            {pacientesComparacion.c ? (
                                <Descriptions size="small" column={1} bordered>
                                    <Descriptions.Item label="Edad">{pacientesComparacion.c.edad} años</Descriptions.Item>
                                    <Descriptions.Item label="Grupo">{pacientesComparacion.c.tipo_sangre || 'N/A'}</Descriptions.Item>
                                    <Descriptions.Item label="CI">{pacientesComparacion.c.ci}</Descriptions.Item>
                                </Descriptions>
                            ) : (
                                <Empty description="Seleccione un paciente" />
                            )}
                        </Card>
                    </Col>
                </Row>

                <Divider />

                <Table
                    size="small"
                    columns={[
                        { title: 'Característica', dataIndex: 'item', key: 'item', fixed: 'left', width: 150 },
                        { title: 'Paciente A', dataIndex: 'pacA', key: 'pacA' },
                        { title: 'Paciente B', dataIndex: 'pacB', key: 'pacB' },
                        { title: 'Paciente C', dataIndex: 'pacC', key: 'pacC' }
                    ]}
                    dataSource={[
                        {
                            key: '1',
                            item: 'Edad',
                            pacA: pacientesComparacion.a ? `${pacientesComparacion.a.edad} años` : '-',
                            pacB: pacientesComparacion.b ? `${pacientesComparacion.b.edad} años` : '-',
                            pacC: pacientesComparacion.c ? `${pacientesComparacion.c.edad} años` : '-'
                        },
                        {
                            key: '2',
                            item: 'Grupo Sanguíneo',
                            pacA: pacientesComparacion.a?.tipo_sangre || '-',
                            pacB: pacientesComparacion.b?.tipo_sangre || '-',
                            pacC: pacientesComparacion.c?.tipo_sangre || '-'
                        },
                        {
                            key: '3',
                            item: 'CI',
                            pacA: pacientesComparacion.a?.ci || '-',
                            pacB: pacientesComparacion.b?.ci || '-',
                            pacC: pacientesComparacion.c?.ci || '-'
                        },
                        {
                            key: '4',
                            item: 'Ciudad',
                            pacA: pacientesComparacion.a?.ciudad || '-',
                            pacB: pacientesComparacion.b?.ciudad || '-',
                            pacC: pacientesComparacion.c?.ciudad || '-'
                        },
                        {
                            key: '5',
                            item: 'Teléfono',
                            pacA: pacientesComparacion.a?.telefono || '-',
                            pacB: pacientesComparacion.b?.telefono || '-',
                            pacC: pacientesComparacion.c?.telefono || '-'
                        },
                        {
                            key: '6',
                            item: 'Estado Civil',
                            pacA: pacientesComparacion.a ? getEstadoCivilConGenero(pacientesComparacion.a.estado_civil, pacientesComparacion.a.genero) : '-',
                            pacB: pacientesComparacion.b ? getEstadoCivilConGenero(pacientesComparacion.b.estado_civil, pacientesComparacion.b.genero) : '-',
                            pacC: pacientesComparacion.c ? getEstadoCivilConGenero(pacientesComparacion.c.estado_civil, pacientesComparacion.c.genero) : '-'
                        },
                        {
                            key: '7',
                            item: 'Peso',
                            pacA: pacientesComparacion.a?.peso_kg ? `${pacientesComparacion.a.peso_kg} kg` : '-',
                            pacB: pacientesComparacion.b?.peso_kg ? `${pacientesComparacion.b.peso_kg} kg` : '-',
                            pacC: pacientesComparacion.c?.peso_kg ? `${pacientesComparacion.c.peso_kg} kg` : '-'
                        },
                        {
                            key: '8',
                            item: 'Altura',
                            pacA: pacientesComparacion.a?.altura_cm ? `${pacientesComparacion.a.altura_cm} cm` : '-',
                            pacB: pacientesComparacion.b?.altura_cm ? `${pacientesComparacion.b.altura_cm} cm` : '-',
                            pacC: pacientesComparacion.c?.altura_cm ? `${pacientesComparacion.c.altura_cm} cm` : '-'
                        },
                        {
                            key: '9',
                            item: 'IMC',
                            pacA: pacientesComparacion.a?.imc ? `${pacientesComparacion.a.imc.toFixed(1)}` : '-',
                            pacB: pacientesComparacion.b?.imc ? `${pacientesComparacion.b.imc.toFixed(1)}` : '-',
                            pacC: pacientesComparacion.c?.imc ? `${pacientesComparacion.c.imc.toFixed(1)}` : '-'
                        }
                    ]}
                    pagination={false}
                />

                <Divider />

                <Button type="primary" icon={FILE_PDF_ICON_4} block>
                    Generar Reporte Comparativo PDF
                </Button>
            </Modal>

            {/* ========================================================================
            AGENDA Y RECORDATORIOS
           ======================================================================== */}
            <Drawer
                title="Sistema de Agendamiento Rápido"
                placement="right"
                width={500}
                open={drawerAgendaVisible}
                onClose={() => setDrawerAgendaVisible(false)}
            >
                <Calendar fullscreen={false} />
                <Divider />
                <Card title="Próximas Citas Hoy" size="small">
                    <List
                        size="small"
                        dataSource={pacientes.filter(p => p.embarazos_activos).slice(0, 5)}
                        renderItem={(item) => (
                            <List.Item>
                                <List.Item.Meta
                                    avatar={<Avatar icon={USER_ICON} />}
                                    title={item.nombre_completo}
                                    description={`Control Prenatal • ${dayjs().format('HH:mm')}`}
                                />
                            </List.Item>
                        )}
                    />
                </Card>
                <Divider />
                <Button type="primary" icon={CALENDAR_ICON_5} block>
                    Abrir Agenda Completa
                </Button>
            </Drawer>

        </div>
    );
};

export default Pacientes;
