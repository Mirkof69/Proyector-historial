/**
 * =============================================================================
 * MÓDULO MAESTRO: GESTIÓN INTEGRAL DE state.embarazos
 * =============================================================================
 * Autor: Fetal Medical System AI
 * Descripción:
 * Módulo clínico avanzado para la administración del ciclo de embarazo.
 * Integra cálculos obstétricos automáticos (FPP, EG, IMC), gestión de riesgos,
 * vinculación con pacientes, historial de cambios y reportes rápidos.
 * * Funcionalidades Extendidas:
 * 1. Listado Avanzado: Filtros múltiples, búsqueda en tiempo real, ordenamiento.
 * 2. Motor Obstétrico: Cálculo automático de FPP (Naegele) y EG al cambiar FUM.
 * 3. Gestión de Riesgos: Clasificación visual y alertas automáticas.
 * 4. Vinculación Paciente: Buscador asíncrono de pacientes (Select con Search).
 * 5. Dashboard Interno: Estadísticas de state.embarazos activos, riesgos y términos.
 * 6. Drawer de Detalles: Vista rápida con resumen clínico y timeline.
 * 7. Validaciones Estrictas: Reglas de negocio para fechas y datos numéricos.
 * =============================================================================
 */

import React, { useReducer, useEffect, useMemo, useCallback, useState } from 'react';
import {
    Table,
    Button,
    Form,
    Input,
    Select,
    Space,
    Card,
    Row,
    Col,
    Typography,
    Tooltip,
    Progress,
    Dropdown,
    Alert,
    Result as ResultEmpty
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { usePermissions } from '../../hooks/usePermissions';
import {
    PlusOutlined,
    SearchOutlined,
    HeartOutlined,
    WarningOutlined,
    ReloadOutlined,
    CheckCircleOutlined,
    StopOutlined,
    FileTextOutlined,
    LineChartOutlined,
    FileExcelOutlined,
    BellOutlined,
    DatabaseOutlined,
    DownloadOutlined,
    FilterOutlined,
    ExportOutlined,
    SyncOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs, { Dayjs } from 'dayjs';
import 'dayjs/locale/es';

// Servicios
import { embarazosService } from '../../services/embarazosService';
// Envoltorio de services/api: `api.get()` YA devuelve los datos (no la
// respuesta de axios). El listado usa useListadoServidor, que va por axios.
import { api } from '../../services/api';
import AnimatedStatistic from '../../components/common/AnimatedStatistic';
import { usuariosService } from '../../services/usuariosService';
import { descargarArchivo } from '../../utils/descargarArchivo';
import { aQuery, useListadoServidor } from '../../hooks/useListadoServidor';
import {
    EmbarazoExtendido, EmbarazoResumido, initialState, reducer,
    calcularFPP, calcularEdadGestacional, calcularIMC,
} from './embarazosReducer';
import { buildEmbarazosColumns } from './embarazosColumns';
import './paginaClinica.css';
import './Embarazos.css';
import EmbarazoFormModal from './components/EmbarazoFormModal';
import EmbarazoDrawer from './components/EmbarazoDrawer';
import AnalisisEvolucionModal from './components/AnalisisEvolucionModal';
import ReportesModal from './components/ReportesModal';
import AlertasModal from './components/AlertasModal';
import PanelControlDrawer from './components/PanelControlDrawer';
import HistorialModal from './components/HistorialModal';
import FiltrosAvanzadosDrawer from './components/FiltrosAvanzadosDrawer';

dayjs.locale('es');
const { Option } = Select;
const { Title } = Typography;

// =============================================================================
// 2. COMPONENTE PRINCIPAL
// =============================================================================

const syncIcon = <SyncOutlined />;
const downloadIcon2 = <DownloadOutlined />;
const filterIcon = <FilterOutlined />;
const lineChartIcon2 = <LineChartOutlined />;
const reloadOutlinedIcon4 = <ReloadOutlined />;
const fileTextOutlinedIcon8 = <FileTextOutlined />;
const bellOutlinedIcon3 = <BellOutlined />;
const databaseOutlinedIcon3 = <DatabaseOutlined />;
const plusOutlinedIcon9 = <PlusOutlined />;
const heartOutlinedIcon6 = <HeartOutlined className="embarazos-vacio__icono" />;

interface ResumenEmbarazos {
    total: number;
    activos: number;
    alto_riesgo: number;
    a_termino: number;
    primer_trimestre: number;
    segundo_trimestre: number;
    tercer_trimestre: number;
    proximos_partos: EmbarazoResumido[];
    alertas_termino: EmbarazoResumido[];
}

const RESUMEN_VACIO: ResumenEmbarazos = {
    total: 0, activos: 0, alto_riesgo: 0, a_termino: 0,
    primer_trimestre: 0, segundo_trimestre: 0, tercer_trimestre: 0,
    proximos_partos: [], alertas_termino: [],
};

/**
 * Edad gestacional para la barra de progreso de la tabla.
 *
 * Se usa `semanas_gestacion` («S+D») del serializer, que cuenta hasta hoy si
 * el embarazo está activo y hasta el parto si terminó. Antes se recalculaba
 * SIEMPRE hasta hoy desde la FUM y un embarazo de hace un año aparecía con
 * «85 semanas».
 */
const conEdadGestacional = (emb: EmbarazoExtendido): EmbarazoExtendido => {
    let semanas = 0;
    let dias = 0;
    const eg = (emb as { semanas_gestacion?: unknown }).semanas_gestacion;
    if (typeof eg === 'string' && eg.includes('+')) {
        const [s, d] = eg.split('+');
        semanas = parseInt(s, 10) || 0;
        dias = parseInt(d, 10) || 0;
    } else if (emb.estado === 'activo' && emb.fecha_ultima_menstruacion) {
        const diffDias = dayjs().diff(dayjs(emb.fecha_ultima_menstruacion), 'day');
        semanas = Math.floor(diffDias / 7);
        dias = diffDias % 7;
    }
    let trimestre = 1;
    if (semanas >= 14 && semanas < 28) trimestre = 2;
    if (semanas >= 28) trimestre = 3;
    return { ...emb, edad_gestacional_semanas_num: semanas, edad_gestacional_dias_num: dias, trimestre_actual: trimestre };
};

const Embarazos: React.FC = () => {
    const navigate = useNavigate();
    const { message, modal } = useAntdApp();
    const { canAdd, canChange, canDelete } = usePermissions();
    const [form] = Form.useForm();

    const [state, dispatch] = useReducer(reducer, initialState);

    // =============================================================================
    // 3. LÓGICA DE CARGA Y DATOS
    // =============================================================================

    // Listado paginado, filtrado y ordenado EN EL SERVIDOR. Antes se bajaban
    // TODOS los embarazos y TODAS las pacientes (~34 peticiones con 3.200
    // pacientes) para poner un nombre que EmbarazoListSerializer ya trae en
    // `paciente_nombre`, y se filtraba en el navegador.
    const filtrosServidor = useMemo(() => ({
        riesgo_embarazo: state.riskFilter,
        estado: state.statusFilter,
    }), [state.riskFilter, state.statusFilter]);

    const listado = useListadoServidor<EmbarazoExtendido>('/embarazos/', {
        filtros: filtrosServidor, busqueda: state.searchText, tamanoInicial: 10, ordenInicial: '-fecha_registro',
    });
    const { parametros, recargar } = listado;
    const embarazosPagina = useMemo(() => listado.datos.map(conEdadGestacional), [listado.datos]);

    // Cifras de cabecera y paneles con los MISMOS filtros, sobre todos los embarazos.
    const [resumen, setResumen] = useState<ResumenEmbarazos>(RESUMEN_VACIO);
    const cargarResumen = useCallback(async () => {
        try {
            setResumen(await api.get<ResumenEmbarazos>('/embarazos/resumen/', { params: parametros() }));
        } catch {
            // Las cifras no deben impedir usar el listado.
            setResumen(RESUMEN_VACIO);
        }
    }, [parametros]);
    useEffect(() => { cargarResumen(); }, [cargarResumen]);

    const loadEmbarazos = useCallback(() => {
        recargar();
        cargarResumen();
    }, [recargar, cargarResumen]);

    // Carga asíncrona de pacientes para el Select (Buscador)
    const loadPacientesOptions = useCallback(async (search = '') => {
        dispatch({ type: 'SET_LOADING_PACIENTES', payload: true });
        try {
            // Filtramos solo mujeres para el select de state.embarazos
            const response = await api.get('/pacientes/', {
                params: { search: search || undefined, genero: 'femenino', page_size: 20 },
            });
            // `api` (envoltorio de services/api) ya devuelve los datos, no la
            // respuesta de axios: por eso se lee .results directamente.
            const results = Array.isArray(response) ? response : (response as any).results || [];

            const options = results.map((p: any) => ({
                id: p.id,
                nombre_completo: p.nombre_completo || `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`,
                ci: p.ci,
                edad: p.edad,
                peso_kg: p.peso_kg,
                altura_cm: p.altura_cm
            }));
            dispatch({ type: 'SET_PACIENTES_OPTIONS', payload: options });
        } catch (e) {
        } finally {
            dispatch({ type: 'SET_LOADING_PACIENTES', payload: false });
        }
    }, []); // api is a stable axios instance

    // Wrapper de loadPacientesOptions para usar en useEffect sin warning
    const loadPacientesOptionsCallback = useCallback(async (search: string) => {
        await loadPacientesOptions(search);
    }, [loadPacientesOptions]);

    // Carga lista de médicos para el dropdown
    const loadMedicos = useCallback(async () => {
        try {
            dispatch({ type: 'SET_LOADING_MEDICOS', payload: true });
            const response = await usuariosService.getAll({ rol: 'medico' });
            const medicosData = Array.isArray(response) ? response : (response as any).results || [];
            dispatch({ type: 'SET_MEDICOS', payload: medicosData });
        } catch (error) {
            message.error('No se pudieron cargar los médicos');
        } finally {
            dispatch({ type: 'SET_LOADING_MEDICOS', payload: false });
        }
    }, [message]);

    useEffect(() => {
        loadPacientesOptionsCallback('');
        loadMedicos();
    }, [loadPacientesOptionsCallback, loadMedicos]);

    // =============================================================================
    // 4. CÁLCULOS OBSTÉTRICOS AUTOMÁTICOS
    // =============================================================================

    // Cálculos obstétricos puros: ver definiciones en embarazosReducer.

    // Handler para cambio de FUM en el formulario
    const handleFUMChange = useCallback((date: Dayjs | null) => {
        if (date) {
            const fpp = calcularFPP(date);
            const eg = calcularEdadGestacional(date);

            // Actualizar campo FPP automáticamente
            form.setFieldsValue({ fecha_probable_parto: fpp });

            // Mostrar feedback visual inmediato
            dispatch({ type: 'SET_EDAD_GESTACIONAL_CALCULADA', payload: `${eg.semanas} semanas + ${eg.dias} días` });

            if (eg.semanas > 42) {
                message.warning('La fecha seleccionada indica un embarazo mayor a 42 semanas. Verifique la FUM.');
            }
        } else {
            dispatch({ type: 'SET_EDAD_GESTACIONAL_CALCULADA', payload: '' });
            form.setFieldsValue({ fecha_probable_parto: null });
        }
    }, [form, message]);

    // Handler para cambio de peso/talla (Cálculo IMC en tiempo real)
    const handleAntropometriaChange = useCallback(() => {
        const peso = form.getFieldValue('peso_pregestacional');
        const talla = form.getFieldValue('talla_materna');

        if (peso && talla) {
            const imc = calcularIMC(peso, talla);
            if (imc) {
                dispatch({ type: 'SET_IMC_CALCULADO', payload: `${imc.valor} (${imc.clasificacion})` });
            }
        } else {
            dispatch({ type: 'SET_IMC_CALCULADO', payload: '' });
        }
    }, [form]);

    // Handler para auto-poblar peso y talla cuando se selecciona un paciente
    const handlePacienteChange = useCallback((pacienteId: number) => {
        const paciente = state.pacientesOptions.find(p => p.id === pacienteId);
        if (paciente) {
            // Auto-poblar peso y talla si el paciente tiene esos datos
            if (paciente.peso_kg) {
                form.setFieldValue('peso_pregestacional', paciente.peso_kg);
            }
            if (paciente.altura_cm) {
                form.setFieldValue('talla_materna', paciente.altura_cm);
            }
            // Trigger cálculo de IMC si ambos campos están presentes
            if (paciente.peso_kg && paciente.altura_cm) {
                setTimeout(() => handleAntropometriaChange(), 0);
            }
        }
    }, [state.pacientesOptions, form, handleAntropometriaChange]);


    // =============================================================================
    // 5. HANDLERS CRUD (ACCIONES)
    // =============================================================================

    const handleOpenCreate = useCallback(() => {
        dispatch({ type: 'SET_EDITING_EMBARAZO', payload: null });
        form.resetFields();
        dispatch({ type: 'SET_IMC_CALCULADO', payload: '' });
        dispatch({ type: 'SET_EDAD_GESTACIONAL_CALCULADA', payload: '' });

        // Valores por defecto inteligentes
        form.setFieldsValue({
            tipo_embarazo: 'simple',
            riesgo_embarazo: 'bajo',
            estado: 'activo',
            numero_gesta: 1,
            partos_previos: 0,
            cesareas_previas: 0,
            abortos_previos: 0,
            hijos_vivos: 0
        });

        dispatch({ type: 'SET_MODAL_VISIBLE', payload: true });
    }, [form]);

    const handleOpenEdit = useCallback((record: EmbarazoExtendido) => {
        dispatch({ type: 'SET_EDITING_EMBARAZO', payload: record });
        dispatch({ type: 'SET_MODAL_VISIBLE', payload: true });

        const fumDayjs = record.fecha_ultima_menstruacion
            ? dayjs(record.fecha_ultima_menstruacion)
            : null;
        const fppDayjs = record.fecha_probable_parto
            ? dayjs(record.fecha_probable_parto)
            : null;

        const pacienteId = typeof record.paciente === 'object'
            ? (record.paciente as any).id
            : record.paciente;

        form.setFieldsValue({
            paciente: pacienteId,
            numero_gesta: record.numero_gesta,
            fecha_ultima_menstruacion: fumDayjs,
            fecha_probable_parto: fppDayjs,
            tipo_embarazo: record.tipo_embarazo,
            riesgo_embarazo: record.riesgo_embarazo,
            estado: record.estado,
            notas: record.notas,
            medico_responsable: record.medico_responsable,
            partos_previos: record.partos_previos ?? record.numero_para,
            cesareas_previas: record.cesareas_previas ?? record.numero_cesareas,
            abortos_previos: record.abortos_previos ?? record.numero_abortos,
            hijos_vivos: record.hijos_vivos ?? 0,
            peso_pregestacional: record.peso_pregestacional,
            talla_materna: record.talla_materna,
        });

    }, [form]);

    const handleSubmit = useCallback(async () => {
        try {
            // 1. Validar campos
            const values = await form.validateFields();
            dispatch({ type: 'SET_ACTION_LOADING', payload: true });

            // 2. Preparar payload (formatear fechas)
            const payload = {
                ...values,
                fecha_ultima_menstruacion: values.fecha_ultima_menstruacion.format('YYYY-MM-DD'),
                fecha_probable_parto: values.fecha_probable_parto ? values.fecha_probable_parto.format('YYYY-MM-DD') : null,
            };

            // 3. Enviar al backend
            if (state.editingEmbarazo) {
                await embarazosService.update(state.editingEmbarazo.id!, payload);
                message.success({ content: 'Ficha de embarazo actualizada correctamente', icon: <CheckCircleOutlined className="u-c-exito" /> });
            } else {
                await embarazosService.create(payload);
                message.success({ content: 'Nuevo embarazo registrado exitosamente', icon: <CheckCircleOutlined className="u-c-exito" /> });
            }

            // 4. Limpieza y recarga
            dispatch({ type: 'SET_MODAL_VISIBLE', payload: false });
            loadEmbarazos();
        } catch (error: any) {
            if (error.response) {
                message.error(`Error del servidor: ${error.response.data?.detail || 'Datos inválidos'}`);
            } else if (error.errorFields) {
                message.warning("Por favor complete todos los campos obligatorios");
            } else {
                message.error("Error de conexión al guardar");
            }
        } finally {
            dispatch({ type: 'SET_ACTION_LOADING', payload: false });
        }
    }, [form, state.editingEmbarazo, message, loadEmbarazos]);

    const handleDelete = useCallback(async (id: number) => {
        modal.confirm({
            className: 'capa-clinica',
            title: '¿Eliminar embarazo?',
            content: 'Solo se puede borrar un embarazo registrado por error, sin controles, ecografías ni partos. Esta acción no se puede deshacer.',
            okText: 'Sí, eliminar',
            okType: 'danger',
            cancelText: 'Cancelar',
            onOk: async () => {
                try {
                    await embarazosService.delete(id);
                    message.success("Registro eliminado correctamente");
                    loadEmbarazos(); // Recargar lista
                    if (state.selectedEmbarazo?.id === id) dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false }); // Cerrar drawer si estaba abierto
                } catch (e: any) {
                    const datos = e?.response?.data;
                    message.error(datos?.detalle || datos?.error || "No se pudo eliminar el embarazo.");
                }
            }
        });
    }, [modal, message, loadEmbarazos, state.selectedEmbarazo]);

    // =============================================================================
    // =============================================================================


    // Excel armado en el SERVIDOR (auditado). «Con los filtros actuales» manda
    // búsqueda, riesgo y estado de la pantalla; antes ese Excel se generaba en
    // el navegador con lo descargado. «Todos» no manda filtros.
    const handleExportServidor = useCallback(async (conFiltros: boolean) => {
        dispatch({ type: 'SET_EXPORT_LOADING', payload: true });
        try {
            const query = conFiltros ? aQuery(parametros()) : '';
            await descargarArchivo(`/embarazos/exportar-excel/${query}`, `embarazos_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`);
            message.success('Excel descargado');
        } catch (error) {
            message.error('No se pudo exportar el Excel');
        } finally {
            dispatch({ type: 'SET_EXPORT_LOADING', payload: false });
        }
    }, [message, parametros]);

    // Handler para sincronizar datos con servidor
    const handleSyncData = useCallback(async () => {
        dispatch({ type: 'SET_SYNC_LOADING', payload: true });
        try {
            message.loading({ content: 'Sincronizando con el servidor...', key: 'sync' });

            await Promise.all([
                recargar(),
                cargarResumen(),
                loadPacientesOptionsCallback(''),
                loadMedicos()
            ]);

            message.success({
                content: 'Datos sincronizados correctamente',
                key: 'sync',
                icon: <SyncOutlined className="u-c-exito" />
            });
        } catch (error) {
            message.error({ content: 'Error al sincronizar datos', key: 'sync' });
        } finally {
            dispatch({ type: 'SET_SYNC_LOADING', payload: false });
        }
    }, [recargar, cargarResumen, loadPacientesOptionsCallback, loadMedicos, message]);

    // Handler para finalizar embarazo
    const handleFinalizarEmbarazo = useCallback(async (embarazo: EmbarazoExtendido) => {
        modal.confirm({
            className: 'capa-clinica',
            title: '¿Finalizar embarazo?',
            icon: <StopOutlined className="u-c-aviso" />,
            content: `Se marcará como finalizado el embarazo de ${embarazo.paciente_nombre}`,
            okText: 'Finalizar',
            okButtonProps: { icon: <StopOutlined /> },
            cancelText: 'Cancelar',
            onOk: async () => {
                try {
                    await embarazosService.update(embarazo.id!, { estado: 'finalizado' });
                    message.success('Embarazo finalizado correctamente');
                    loadEmbarazos();
                } catch (error) {
                    message.error('Error al finalizar embarazo');
                }
            }
        });
    }, [modal, message, loadEmbarazos]);

    // Handler para ver historial completo
    const handleVerHistorial = useCallback((embarazo: EmbarazoExtendido) => {
        dispatch({ type: 'SET_SELECTED_EMBARAZO', payload: embarazo });
        dispatch({ type: 'SET_HISTORIAL_MODAL_VISIBLE', payload: true });
    }, []);



    // =============================================================================
    // 6. ESTADÍSTICAS Y FILTROS (MEMOIZED)
    // =============================================================================

    const stats = {
        total: resumen.total,
        activos: resumen.activos,
        altoRiesgo: resumen.alto_riesgo,
        termino: resumen.a_termino,
        primerTrimestre: resumen.primer_trimestre,
        segundoTrimestre: resumen.segundo_trimestre,
        tercerTrimestre: resumen.tercer_trimestre,
    };

    // =============================================================================
    // 7. DEFINICIÓN DE COLUMNAS DE TABLA
    // =============================================================================

    const columns = useMemo(() => buildEmbarazosColumns({
        navigate, canChange, canDelete, dispatch,
        handleVerHistorial, handleOpenEdit,
        handleFinalizarEmbarazo, handleDelete,
    }), [navigate, canChange, canDelete, handleVerHistorial, handleOpenEdit, handleFinalizarEmbarazo, handleDelete]);

    // =============================================================================
    // 8. RENDERIZADO DE INTERFAZ (JSX)
    // =============================================================================

    return (
        <div className="pagina-clinica embarazos-page page-container">

            {/* --- ENCABEZADO DE PÁGINA --- */}
            <div className="pc-cabecera">
                <div className="pc-cabecera__texto">
                    <Title level={2} className="pc-cabecera__titulo">Directorio Obstétrico</Title>
                    <p className="pc-cabecera__descripcion">
                        Embarazos registrados, nivel de riesgo y proximidad al término.
                    </p>
                </div>
                <Button type="primary" icon={plusOutlinedIcon9} onClick={handleOpenCreate} aria-label="Registrar nuevo embarazo">
                    Registrar Nuevo Embarazo
                </Button>
            </div>

            {/* --- TARJETAS DE CIFRAS (KPIs) --- */}
            <Row gutter={[16, 16]} className="pc-cifras">
                <Col xs={24} sm={8}>
                    <Card className="pc-cifra">
                        <AnimatedStatistic
                            title="Embarazos Activos"
                            value={stats.activos}
                        />
                        <div className="pc-cifra__nota">
                            Total registrados: {stats.total}
                        </div>
                    </Card>
                </Col>
                <Col xs={24} sm={8}>
                    <Card className="pc-cifra">
                        <AnimatedStatistic
                            title="Alto Riesgo"
                            value={stats.altoRiesgo}
                            prefix={<WarningOutlined />}
                            className="u-cifra-peligro"
                        />
                        <Progress percent={stats.activos > 0 ? (stats.altoRiesgo / stats.activos) * 100 : 0} size="small" showInfo={false} status="exception" />
                    </Card>
                </Col>
                <Col xs={24} sm={8}>
                    <Card className="pc-cifra">
                        <AnimatedStatistic
                            title="Próximos a Término"
                            value={stats.termino}
                        />
                        <div className="pc-cifra__nota">
                            {'>'} 37 semanas de gestación
                        </div>
                    </Card>
                </Col>
            </Row>

            {/* --- FILTROS Y TABLA PRINCIPAL --- */}
            <Card className="embarazos-directorio">

                {/* Toolbar */}
                <div className="pc-barra">
                    <div className="pc-barra__filtros">
                        <Input
                            className="pc-barra__buscar"
                            placeholder="Buscar por nombre, CI o ID..."
                            prefix={<SearchOutlined />}
                            onChange={e => dispatch({ type: 'SET_SEARCH_TEXT', payload: e.target.value })}
                            allowClear
                        />
                        <Select
                            className="pc-barra__filtro"
                            placeholder="Filtrar Riesgo"
                            allowClear
                            onChange={(value) => dispatch({ type: 'SET_RISK_FILTER', payload: value })}
                        >
                            <Option value="bajo">Bajo Riesgo</Option>
                            <Option value="medio">Riesgo Medio</Option>
                            <Option value="alto">Alto Riesgo</Option>
                        </Select>
                        <Select
                            className="pc-barra__filtro"
                            placeholder="Ver Todos"
                            onChange={(value) => dispatch({ type: 'SET_STATUS_FILTER', payload: value })}
                            allowClear
                        >
                            <Option value="activo">En Curso (Activos)</Option>
                            <Option value="finalizado">Finalizados (Parto)</Option>
                            <Option value="perdida">Interrumpidos</Option>
                        </Select>
                    </div>
                    <Space wrap className="pc-barra__acciones">
                            <Tooltip title="Filtros Avanzados">
                                <Button
                                    icon={filterIcon}
                                    onClick={() => dispatch({ type: 'SET_FILTROS_AVANZADOS_VISIBLE', payload: true })}
                                >
                                    Filtros
                                </Button>
                            </Tooltip>
                            <Dropdown
                                menu={{
                                    items: [
                                        {
                                            key: 'excel-vista',
                                            label: 'Excel con los filtros actuales',
                                            icon: <FileExcelOutlined />,
                                            onClick: () => handleExportServidor(true)
                                        },
                                        {
                                            key: 'excel-todos',
                                            label: 'Excel de todos los embarazos',
                                            icon: <ExportOutlined />,
                                            onClick: () => handleExportServidor(false)
                                        }
                                    ]
                                }}
                            >
                                <Button icon={downloadIcon2} loading={state.exportLoading}>
                                    Exportar
                                </Button>
                            </Dropdown>
                            <Button
                                icon={syncIcon}
                                onClick={handleSyncData}
                                loading={state.syncLoading}
                                aria-label="Sincronizar datos"
                                title="Sincronizar datos"
                            />
                            <Tooltip title="Análisis de Evolución">
                                <Button
                                    icon={lineChartIcon2}
                                    onClick={() => dispatch({ type: 'SET_MODAL_ANALISIS_EVOLUCION_VISIBLE', payload: true })}
                                >
                                    Análisis
                                </Button>
                            </Tooltip>
                            <Tooltip title="Generador de Reportes">
                                <Button
                                    icon={fileTextOutlinedIcon8}
                                    onClick={() => dispatch({ type: 'SET_MODAL_REPORTES_VISIBLE', payload: true })}
                                >
                                    Reportes
                                </Button>
                            </Tooltip>
                            <Tooltip title="Sistema de Alertas">
                                <Button
                                    icon={bellOutlinedIcon3}
                                    onClick={() => dispatch({ type: 'SET_MODAL_ALERTAS_VISIBLE', payload: true })}
                                >
                                    Alertas
                                </Button>
                            </Tooltip>
                            <Tooltip title="Panel de Control Obstétrico">
                                <Button
                                    icon={databaseOutlinedIcon3}
                                    onClick={() => dispatch({ type: 'SET_DRAWER_PANEL_CONTROL_VISIBLE', payload: true })}
                                >
                                    Panel Control
                                </Button>
                            </Tooltip>
                            <Button icon={reloadOutlinedIcon4} onClick={loadEmbarazos} loading={listado.cargando}>
                                Recargar
                            </Button>
                    </Space>
                </div>

                {listado.error && <Alert type="error" showIcon message={listado.error} className="embarazos-error" />}

                {/* Tabla */}
                <Table
                    className="embarazos-tabla"
                    dataSource={embarazosPagina}
                    columns={columns as any}
                    rowKey="id"
                    loading={listado.cargando}
                    pagination={listado.paginacion}
                    onChange={listado.onChange as any}
                    scroll={{ x: 1200 }}
                    locale={{
                        emptyText: (
                            <ResultEmpty
                                icon={heartOutlinedIcon6}
                                title="No hay embarazos registrados"
                                subTitle="Comience registrando un nuevo embarazo utilizando el botón superior"
                                extra={
                                    canAdd('embarazo') ? (
                                        <Button icon={plusOutlinedIcon9} onClick={handleOpenCreate}>
                                            Registrar Nuevo Embarazo
                                        </Button>
                                    ) : null
                                }
                            />
                        )
                    }}
                />
            </Card>

            {/* MODAL DE REGISTRO / EDICIÓN */}
            <EmbarazoFormModal
                modalVisible={state.modalVisible}
                editingEmbarazo={state.editingEmbarazo}
                edadGestacionalCalculada={state.edadGestacionalCalculada}
                imcCalculado={state.imcCalculado}
                pacientesOptions={state.pacientesOptions}
                loadingPacientes={state.loadingPacientes}
                medicos={state.medicos}
                loadingMedicos={state.loadingMedicos}
                actionLoading={state.actionLoading}
                form={form}
                dispatch={dispatch}
                handleSubmit={handleSubmit}
                handleFUMChange={handleFUMChange}
                handleAntropometriaChange={handleAntropometriaChange}
                handlePacienteChange={handlePacienteChange}
                loadPacientesOptions={loadPacientesOptions}
            />

            {/* DRAWER DE DETALLE RÁPIDO */}
            <EmbarazoDrawer
                drawerVisible={state.drawerVisible}
                selectedEmbarazo={state.selectedEmbarazo}
                dispatch={dispatch}
                navigate={navigate}
            />

            {/* MÓDULO DE ANÁLISIS Y GRÁFICAS DE EVOLUCIÓN */}
            <AnalisisEvolucionModal
                visible={state.modalAnalisisEvolucionVisible}
                onClose={() => dispatch({ type: 'SET_MODAL_ANALISIS_EVOLUCION_VISIBLE', payload: false })}
                total={stats.total}
                stats={stats}
            />

            {/* GENERADOR DE REPORTES AVANZADOS */}
            <ReportesModal
                visible={state.modalReportesVisible}
                onClose={() => dispatch({ type: 'SET_MODAL_REPORTES_VISIBLE', payload: false })}
            />

            {/* SISTEMA DE ALERTAS Y RECORDATORIOS */}
            <AlertasModal
                visible={state.modalAlertasVisible}
                onClose={() => dispatch({ type: 'SET_MODAL_ALERTAS_VISIBLE', payload: false })}
                alertas={resumen.alertas_termino}
                totalATermino={resumen.a_termino}
            />

            {/* PANEL DE CONTROL MÉDICO AVANZADO */}
            <PanelControlDrawer
                visible={state.drawerPanelControlVisible}
                onClose={() => dispatch({ type: 'SET_DRAWER_PANEL_CONTROL_VISIBLE', payload: false })}
                proximosPartos={resumen.proximos_partos}
                stats={stats}
                canAdd={canAdd}
                handleOpenCreate={handleOpenCreate}
            />

            {/* MODAL DE HISTORIAL COMPLETO */}
            <HistorialModal
                visible={state.historialModalVisible}
                onClose={() => dispatch({ type: 'SET_HISTORIAL_MODAL_VISIBLE', payload: false })}
                selectedEmbarazo={state.selectedEmbarazo}
            />


            {/* DRAWER DE FILTROS AVANZADOS */}
            <FiltrosAvanzadosDrawer
                visible={state.filtrosAvanzadosVisible}
                onClose={() => dispatch({ type: 'SET_FILTROS_AVANZADOS_VISIBLE', payload: false })}
                vistaComparacion={state.vistaComparacion}
                mostrarFinalizados={state.mostrarFinalizados}
                dispatch={dispatch}
                message={message}
            />

        </div>
    );
};

export default Embarazos;
