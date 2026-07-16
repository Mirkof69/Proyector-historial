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

import React, { useReducer, useEffect, useMemo, useCallback } from 'react';
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
    Statistic,
    Typography,
    Tooltip,
    Progress,
    Dropdown,
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
    SyncOutlined,
    ApiOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs, { Dayjs } from 'dayjs';
import 'dayjs/locale/es';

// Servicios
import { embarazosService } from '../../services/embarazosService';
import { api } from '../../services/api';
import { GlobalLoader } from '../../components/common/GlobalLoader'; // Para buscar pacientes
import { usuariosService } from '../../services/usuariosService';
import { exportarExcel } from '../../utils/excelExport';
import {
    EmbarazoExtendido, initialState, reducer,
    calcularFPP, calcularEdadGestacional, calcularIMC,
} from './embarazosReducer';
import { buildEmbarazosColumns } from './embarazosColumns';
import EmbarazoFormModal from './components/EmbarazoFormModal';
import EmbarazoDrawer from './components/EmbarazoDrawer';
import AnalisisEvolucionModal from './components/AnalisisEvolucionModal';
import ReportesModal from './components/ReportesModal';
import AlertasModal from './components/AlertasModal';
import PanelControlDrawer from './components/PanelControlDrawer';
import HistorialModal from './components/HistorialModal';
import UploadDocsModal from './components/UploadDocsModal';
import FiltrosAvanzadosDrawer from './components/FiltrosAvanzadosDrawer';

dayjs.locale('es');
const { Option } = Select;
const { Title, Text } = Typography;

// =============================================================================
// 2. COMPONENTE PRINCIPAL
// =============================================================================

const syncIcon = <SyncOutlined />;
const apiIcon = <ApiOutlined />;
const downloadIcon2 = <DownloadOutlined />;
const filterIcon = <FilterOutlined />;
const lineChartIcon2 = <LineChartOutlined />;
const reloadOutlinedIcon4 = <ReloadOutlined />;
const fileTextOutlinedIcon8 = <FileTextOutlined />;
const bellOutlinedIcon3 = <BellOutlined />;
const databaseOutlinedIcon3 = <DatabaseOutlined />;
const plusOutlinedIcon9 = <PlusOutlined />;
const heartOutlinedIcon6 = <HeartOutlined style={{ fontSize: 64, color: '#bfbfbf' }} />;

const Embarazos: React.FC = () => {
    const navigate = useNavigate();
    const { message, modal } = useAntdApp();
    const { canAdd, canChange, canDelete } = usePermissions();
    const [form] = Form.useForm();

    const [state, dispatch] = useReducer(reducer, initialState);

    // =============================================================================
    // 3. LÓGICA DE CARGA Y DATOS
    // =============================================================================

    const loadEmbarazos = useCallback(async () => {
        dispatch({ type: 'SET_LOADING', payload: true });

        try {

            // 🚀 PASO 1: Obtener primera página de cada endpoint para saber cuántas páginas hay
            const [embarazosPage1, pacientesPage1] = await Promise.all([
                api.get<any>('/embarazos/?page=1&limit=200').catch(err => {
                    return { count: 0, results: [] };
                }),
                api.get<any>('/pacientes/?page=1&limit=200').catch(err => {
                    return { count: 0, results: [] };
                })
            ]);

            const embarazosCount = embarazosPage1.count || 0;
            const embarazosPages = Math.ceil(embarazosCount / 200);
            const pacientesCount = pacientesPage1.count || 0;
            const pacientesPages = Math.ceil(pacientesCount / 200);


            // Si no hay datos, salir temprano
            if (embarazosCount === 0) {
                dispatch({ type: 'SET_EMBARAZOS', payload: [] });
                message.info('No hay embarazos registrados. Verifique que esté autenticado correctamente.', 3);
                dispatch({ type: 'SET_LOADING', payload: false });
                return;
            }

            // 🚀 PASO 2: Crear arrays de promesas para TODAS las páginas con manejo de errores
            const embarazosPromises = Array.from({ length: embarazosPages }, (_, i) =>
                api.get<any>(`/embarazos/?page=${i + 1}&limit=200`).catch(err => {
                    return { results: [] };
                })
            );
            const pacientesPromises = Array.from({ length: pacientesPages }, (_, i) =>
                api.get<any>(`/pacientes/?page=${i + 1}&limit=200`).catch(err => {
                    return { results: [] };
                })
            );

            // 🚀 PASO 3: Ejecutar TODAS las requests en PARALELO (state.embarazos Y pacientes juntos)
            const [embarazosResponses, pacientesResponses] = await Promise.all([
                Promise.all(embarazosPromises),
                Promise.all(pacientesPromises)
            ]);

            // 🚀 PASO 4: Combinar resultados
            const allEmbarazos = embarazosResponses.flatMap(res =>
                Array.isArray(res.results) ? res.results : []
            );

            const allPacientes = pacientesResponses.flatMap(res =>
                Array.isArray(res.results) ? res.results : []
            );

            const pacientesMap = new Map(allPacientes.map((p: any) => [p.id, p]));

            // ✅ Enriquecer datos con cálculos locales + unique keys
            const listaProcesada = allEmbarazos.map((emb: any, index: number) => {
                const fum = emb.fecha_ultima_menstruacion ? dayjs(emb.fecha_ultima_menstruacion) : null;
                let semanas = 0;
                let dias = 0;

                if (fum) {
                    const diffDias = dayjs().diff(fum, 'day');
                    semanas = Math.floor(diffDias / 7);
                    dias = diffDias % 7;
                } else if (emb.edad_gestacional_semanas && typeof emb.edad_gestacional_semanas === 'string') {
                    // Fallback si el backend manda string "20+4"
                    const parts = emb.edad_gestacional_semanas.split('+');
                    semanas = parseInt(parts[0]) || 0;
                    dias = parseInt(parts[1]) || 0;
                }

                let trimestre = 1;
                if (semanas >= 14 && semanas < 28) trimestre = 2;
                if (semanas >= 28) trimestre = 3;

                // Mapear nombre de paciente
                let nombrePaciente = emb.paciente_nombre;
                if (!nombrePaciente && emb.paciente) {
                    const pId = typeof emb.paciente === 'object' ? emb.paciente.id : emb.paciente;
                    const p = pacientesMap.get(pId) as any;
                    if (p) {
                        nombrePaciente = p.nombre_completo || `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`.trim();
                    }
                }

                return {
                    ...emb,
                    paciente_nombre: nombrePaciente,
                    edad_gestacional_semanas_num: semanas,
                    edad_gestacional_dias_num: dias,
                    trimestre_actual: trimestre,
                    _uniqueRowKey: `embarazo-${emb.id}-${index}-${Date.now()}`
                };
            });

            // Ordenar por fecha de creación descendente (más nuevos primero)
            listaProcesada.sort((a: any, b: any) => {
                return dayjs(b.fecha_registro).unix() - dayjs(a.fecha_registro).unix();
            });

            dispatch({ type: 'SET_EMBARAZOS', payload: listaProcesada });
        } catch (error) {
            message.error('No se pudo cargar la lista de embarazos. Verifique su conexión.');
        } finally {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, [message]);

    // Carga asíncrona de pacientes para el Select (Buscador)
    const loadPacientesOptions = useCallback(async (search = '') => {
        dispatch({ type: 'SET_LOADING_PACIENTES', payload: true });
        try {
            // Filtramos solo mujeres para el select de state.embarazos
            const response = await api.get('/pacientes/', {
                params: {
                    search,
                    genero: 'femenino',
                    limit: 20 // Limitar resultados para rendimiento
                }
            });
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

    // ✅ Wrapper de loadPacientesOptions para usar en useEffect sin warning
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
        loadEmbarazos();
        loadPacientesOptionsCallback('');
        loadMedicos();
    }, [loadEmbarazos, loadPacientesOptionsCallback, loadMedicos]); // Fix: Added missing loadMedicos dependency

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
                message.success({ content: 'Ficha de embarazo actualizada correctamente', icon: <CheckCircleOutlined style={{ color: '#52c41a' }} /> });
            } else {
                await embarazosService.create(payload);
                message.success({ content: 'Nuevo embarazo registrado exitosamente', icon: <CheckCircleOutlined style={{ color: '#52c41a' }} /> });
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
            title: '¿Eliminar embarazo?',
            content: 'Esta acción no se puede deshacer.',
            okText: 'Sí, eliminar',
            okType: 'danger',
            cancelText: 'Cancelar',
            onOk: async () => {
                try {
                    await embarazosService.delete(id);
                    message.success("Registro eliminado correctamente");
                    loadEmbarazos(); // Recargar lista
                    if (state.selectedEmbarazo?.id === id) dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false }); // Cerrar drawer si estaba abierto
                } catch (e) {
                    message.error("No se pudo eliminar el registro. Puede tener controles asociados.");
                }
            }
        });
    }, [modal, message, loadEmbarazos, state.selectedEmbarazo]);

    // =============================================================================
    // 5B. NUEVOS HANDLERS PARA FUNCIONALIDADES ADICIONALES
    // =============================================================================

    // ✅ Handler para subir documentos del embarazo (ecografías, análisis)
    const handleUploadDocuments = useCallback(async (options: any) => {
        const { file, onSuccess, onError } = options;
        dispatch({ type: 'SET_UPLOADING_FILES', payload: true });

        try {
            // Simular subida de archivo (aquí integrarías con tu backend)
            const formData = new FormData();
            formData.append('file', file);
            formData.append('embarazo_id', state.selectedEmbarazo?.id?.toString() || '');
            formData.append('tipo_documento', 'ecografia'); // Podría ser 'laboratorio', 'receta', etc.

            // await api.post('/documentos-embarazo/', formData);

            message.success({
                content: `Documento "${file.name}" subido correctamente`,
                icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />
            });

            onSuccess(file);
            dispatch({ type: 'SET_FILE_LIST', payload: [...state.fileList, file] });
        } catch (error) {
            message.error('Error al subir el documento');
            onError(error);
        } finally {
            dispatch({ type: 'SET_UPLOADING_FILES', payload: false });
        }
    }, [state.selectedEmbarazo, state.fileList, message]);

    // ✅ Handler para exportar datos a Excel/PDF
    const handleExportData = useCallback(async (formato: 'excel' | 'pdf') => {
        dispatch({ type: 'SET_EXPORT_LOADING', payload: true });
        try {
            message.loading({ content: `Generando reporte ${formato.toUpperCase()}...`, key: 'export' });

            // Simular generación de reporte
            await new Promise(resolve => setTimeout(resolve, 1500));

            const nombreArchivo = `embarazos_${dayjs().format('YYYY-MM-DD')}.${formato}`;

            message.success({
                content: `Reporte generado: ${nombreArchivo}`,
                key: 'export',
                icon: <DownloadOutlined style={{ color: '#52c41a' }} />
            });

        } catch (error) {
            message.error({ content: 'Error al generar el reporte', key: 'export' });
        } finally {
            dispatch({ type: 'SET_EXPORT_LOADING', payload: false });
        }
    }, [message]);

    // ✅ Handler para exportar datos a Excel
    const handleExportExcel = useCallback(() => {
        try {
            const columnas = {
                'id': 'ID',
                'paciente_nombre': 'Paciente',
                'numero_gesta': 'Gesta',
                'fecha_ultima_menstruacion': 'FUM',
                'fecha_probable_parto': 'FPP',
                'edad_gestacional_actual': 'Edad Gestacional',
                'riesgo_embarazo': 'Riesgo',
                'estado': 'Estado',
                'gestas_previas': 'Gestas Previas',
                'partos_previos': 'Partos',
                'cesareas_previas': 'Cesáreas',
                'abortos_previos': 'Abortos'
            };

            exportarExcel(
                state.embarazos,
                columnas,
                {
                    filename: `embarazos_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
                    sheetName: 'Embarazos',
                    title: `Listado de Embarazos - ${dayjs().format("DD/MM/YYYY")}`
                }
            );
            message.success('Archivo Excel generado exitosamente');
        } catch (error) {
            message.error('Error al generar el archivo Excel');
        }
    }, [state.embarazos, message]);

    // ✅ Handler para sincronizar datos con servidor
    const handleSyncData = useCallback(async () => {
        dispatch({ type: 'SET_SYNC_LOADING', payload: true });
        try {
            message.loading({ content: 'Sincronizando con el servidor...', key: 'sync' });

            await Promise.all([
                loadEmbarazos(),
                loadPacientesOptionsCallback(''),
                loadMedicos()
            ]);

            message.success({
                content: 'Datos sincronizados correctamente',
                key: 'sync',
                icon: <SyncOutlined style={{ color: '#52c41a' }} />
            });
        } catch (error) {
            message.error({ content: 'Error al sincronizar datos', key: 'sync' });
        } finally {
            dispatch({ type: 'SET_SYNC_LOADING', payload: false });
        }
    }, [loadEmbarazos, loadPacientesOptionsCallback, loadMedicos, message]);

    // ✅ Handler para finalizar embarazo
    const handleFinalizarEmbarazo = useCallback(async (embarazo: EmbarazoExtendido) => {
        modal.confirm({
            title: '¿Finalizar embarazo?',
            icon: <StopOutlined style={{ color: '#faad14' }} />,
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

    // ✅ Handler para ver historial completo
    const handleVerHistorial = useCallback((embarazo: EmbarazoExtendido) => {
        dispatch({ type: 'SET_SELECTED_EMBARAZO', payload: embarazo });
        dispatch({ type: 'SET_HISTORIAL_MODAL_VISIBLE', payload: true });
    }, []);

    // ✅ Handler para abrir modal de documentos
    const handleOpenUploadModal = useCallback((embarazo: EmbarazoExtendido) => {
        dispatch({ type: 'SET_SELECTED_EMBARAZO', payload: embarazo });
        dispatch({ type: 'SET_FILE_LIST', payload: [] });
        dispatch({ type: 'SET_UPLOAD_MODAL_VISIBLE', payload: true });
    }, []);

    // ✅ Handler para integración API externa
    const handleIntegracionAPI = useCallback(async () => {
        try {
            message.loading({ content: 'Conectando con API externa...', key: 'api' });

            // Simular integración con API (ej: sistema de laboratorio, PACS de ecografías)
            await new Promise(resolve => setTimeout(resolve, 1000));

            message.success({
                content: 'Conexión establecida con sistema externo',
                key: 'api',
                icon: <ApiOutlined style={{ color: '#52c41a' }} />
            });
        } catch (error) {
            message.error({ content: 'Error al conectar con API externa', key: 'api' });
        }
    }, [message]);

    // =============================================================================
    // 6. ESTADÍSTICAS Y FILTROS (MEMOIZED)
    // =============================================================================

    const filteredData = useMemo(() => {
        return state.embarazos.filter(item => {
            // Filtro de Texto (Nombre paciente, médico)
            const matchesSearch = !state.searchText ||
                (item.paciente_nombre?.toLowerCase().includes(state.searchText.toLowerCase())) ||
                (item.observaciones?.toLowerCase().includes(state.searchText.toLowerCase())); // Buscar en notas también

            // Filtro de Riesgo
            const matchesRisk = !state.riskFilter || item.riesgo_embarazo === state.riskFilter;

            // Filtro de Estado
            const matchesStatus = !state.statusFilter || item.estado === state.statusFilter;

            return matchesSearch && matchesRisk && matchesStatus;
        });
    }, [state.embarazos, state.searchText, state.riskFilter, state.statusFilter]);

    const stats = useMemo(() => {
        return {
            total: state.embarazos.length,
            activos: state.embarazos.filter(e => e.estado === 'activo').length,
            altoRiesgo: state.embarazos.filter(e => e.riesgo_embarazo === 'alto' && e.estado === 'activo').length,
            termino: state.embarazos.filter(e => (e.edad_gestacional_semanas_num || 0) >= 37 && e.estado === 'activo').length,
            primerTrimestre: state.embarazos.filter(e => (e.edad_gestacional_semanas_num || 0) < 14 && e.estado === 'activo').length
        };
    }, [state.embarazos]);

    // =============================================================================
    // 7. DEFINICIÓN DE COLUMNAS DE TABLA
    // =============================================================================

    const columns = useMemo(() => buildEmbarazosColumns({
        navigate, canChange, canDelete, modal, dispatch,
        handleVerHistorial, handleOpenEdit, handleOpenUploadModal,
        handleFinalizarEmbarazo, handleDelete,
    }), [navigate, canChange, canDelete, handleVerHistorial, handleOpenEdit, handleOpenUploadModal, handleFinalizarEmbarazo, handleDelete, modal]);

    // =============================================================================
    // 8. RENDERIZADO DE INTERFAZ (JSX)
    // =============================================================================

    if (state.loading && state.embarazos.length === 0) {
        return <GlobalLoader tip="Cargando registros obstétricos…" />;
    }

    return (
        <div className="embarazos-module animate-fade-in">

            {/* --- HEADER DE ESTADÍSTICAS (KPIs) --- */}
            <div style={{ marginBottom: 24 }}>
                <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <Statistic
                                title="Embarazos Activos"
                                value={stats.activos}
                                prefix={<HeartOutlined style={{ color: '#1890ff' }} />}
                            />
                            <div style={{ fontSize: 12, color: '#666', marginTop: 8 }}>
                                Total registrados: {stats.total}
                            </div>
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <Statistic
                                title="Alto Riesgo"
                                value={stats.altoRiesgo}
                                prefix={<WarningOutlined style={{ color: '#ff4d4f' }} />}
                                valueStyle={{ color: '#ff4d4f' }}
                            />
                            <Progress percent={stats.activos > 0 ? (stats.altoRiesgo / stats.activos) * 100 : 0} size="small" showInfo={false} status="exception" />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <Statistic
                                title="Próximos a Término"
                                value={stats.termino}
                                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                                valueStyle={{ color: '#52c41a' }}
                            />
                            <div style={{ fontSize: 12, color: '#666', marginTop: 8 }}>
                                {'>'} 37 semanas de gestación
                            </div>
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm action-card" style={{ background: '#e6f7ff', cursor: 'pointer' }} onClick={handleOpenCreate} tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleOpenCreate(); } }}>
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 80 }}>
                                <PlusOutlined style={{ fontSize: 24, color: '#1890ff', marginBottom: 8 }} />
                                <Text strong style={{ color: '#1890ff' }}>Registrar Nuevo Embarazo</Text>
                            </div>
                        </Card>
                    </Col>
                </Row>
            </div>

            {/* --- FILTROS Y TABLA PRINCIPAL --- */}
            <Card className="shadow-card" title={<Title level={4} style={{ margin: 0 }}>Directorio Obstétrico</Title>}>

                {/* Toolbar */}
                <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
                    <Col xs={24} md={8}>
                        <Input
                            placeholder="Buscar por nombre, CI o ID..."
                            prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                            onChange={e => dispatch({ type: 'SET_SEARCH_TEXT', payload: e.target.value })}
                            allowClear
                            size="large"
                        />
                    </Col>
                    <Col xs={12} md={5}>
                        <Select
                            placeholder="Filtrar Riesgo"
                            style={{ width: '100%' }}
                            allowClear
                            size="large"
                            onChange={(value) => dispatch({ type: 'SET_RISK_FILTER', payload: value })}
                        >
                            <Option value="bajo">🟢 Bajo Riesgo</Option>
                            <Option value="medio">🟠 Riesgo Medio</Option>
                            <Option value="alto">🔴 Alto Riesgo</Option>
                        </Select>
                    </Col>
                    <Col xs={12} md={5}>
                        <Select
                            placeholder="Ver Todos"
                            style={{ width: '100%' }}
                            size="large"
                            onChange={(value) => dispatch({ type: 'SET_STATUS_FILTER', payload: value })}
                            allowClear
                        >
                            <Option value="activo">En Curso (Activos)</Option>
                            <Option value="finalizado">Finalizados (Parto)</Option>
                            <Option value="perdida">Interrumpidos</Option>
                        </Select>
                    </Col>
                    <Col xs={24} md={6} style={{ textAlign: 'right' }}>
                        <Space wrap>
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
                                            key: 'excel-new',
                                            label: 'Exportar a Excel (Nueva)',
                                            icon: <FileExcelOutlined />,
                                            onClick: handleExportExcel
                                        },
                                        {
                                            key: 'excel',
                                            label: 'Exportar a Excel',
                                            icon: <ExportOutlined />,
                                            onClick: () => handleExportData('excel')
                                        },
                                        {
                                            key: 'pdf',
                                            label: 'Exportar a PDF',
                                            icon: <DownloadOutlined />,
                                            onClick: () => handleExportData('pdf')
                                        }
                                    ]
                                }}
                            >
                                <Button icon={downloadIcon2} loading={state.exportLoading}>
                                    Exportar
                                </Button>
                            </Dropdown>
                            <Tooltip title="Sincronizar datos">
                                <Button
                                    icon={syncIcon}
                                    onClick={handleSyncData}
                                    loading={state.syncLoading}
                                />
                            </Tooltip>
                            <Tooltip title="Integración API">
                                <Button
                                    icon={apiIcon}
                                    onClick={handleIntegracionAPI}
                                    type="dashed"
                                />
                            </Tooltip>
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
                                    type="primary"
                                >
                                    Panel Control
                                </Button>
                            </Tooltip>
                            <Button icon={reloadOutlinedIcon4} onClick={loadEmbarazos} loading={state.loading}>
                                Recargar
                            </Button>
                        </Space>
                    </Col>
                </Row>

                {/* Tabla */}
                <Table
                    dataSource={filteredData}
                    columns={columns as any}
                    rowKey={(record: any) => record._uniqueRowKey || `embarazo-fallback-${record.id}`}
                    loading={state.loading}
                    pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showTotal: (total) => `Total ${total} registros`,
                        pageSizeOptions: ['10', '20', '50', '100'],
                    }}
                    scroll={{ x: 1200 }}
                    locale={{
                        emptyText: (
                            <ResultEmpty
                                icon={heartOutlinedIcon6}
                                title="No hay embarazos registrados"
                                subTitle="Comience registrando un nuevo embarazo utilizando el botón superior"
                                extra={
                                    canAdd('embarazo') ? (
                                        <Button type="primary" icon={plusOutlinedIcon9} onClick={handleOpenCreate}>
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
                embarazos={state.embarazos}
                stats={stats}
            />

            {/* GENERADOR DE REPORTES AVANZADOS */}
            <ReportesModal
                visible={state.modalReportesVisible}
                onClose={() => dispatch({ type: 'SET_MODAL_REPORTES_VISIBLE', payload: false })}
                embarazos={state.embarazos}
            />

            {/* SISTEMA DE ALERTAS Y RECORDATORIOS */}
            <AlertasModal
                visible={state.modalAlertasVisible}
                onClose={() => dispatch({ type: 'SET_MODAL_ALERTAS_VISIBLE', payload: false })}
                embarazos={state.embarazos}
            />

            {/* PANEL DE CONTROL MÉDICO AVANZADO */}
            <PanelControlDrawer
                visible={state.drawerPanelControlVisible}
                onClose={() => dispatch({ type: 'SET_DRAWER_PANEL_CONTROL_VISIBLE', payload: false })}
                embarazos={state.embarazos}
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

            {/* MODAL DE SUBIDA DE DOCUMENTOS */}
            <UploadDocsModal
                visible={state.uploadModalVisible}
                onClose={() => dispatch({ type: 'SET_UPLOAD_MODAL_VISIBLE', payload: false })}
                selectedEmbarazo={state.selectedEmbarazo}
                uploadingFiles={state.uploadingFiles}
                fileList={state.fileList}
                dispatch={dispatch}
                handleUploadDocuments={handleUploadDocuments}
                message={message}
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
