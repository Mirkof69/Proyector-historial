/**
 * ==================================================================================
 * CITAS - LISTA COMPLETA Y CALENDARIO
 * ==================================================================================
 * Vista principal del módulo de citas médicas
 * - Lista con todos los filtros y búsqueda
 * - Estadísticas en tiempo real
 * - Acciones rápidas (confirmar, cancelar, etc)
 * - Alertas de citas atrasadas y pendientes
 * ==================================================================================
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Alert,
  MenuProps,
} from 'antd';
import {
  CalendarOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import api from '../../services/api';
import { citasService, Cita, EstadoCita, TipoCita } from '../../services/citasService';
import { GestionHorariosModal } from './GestionHorariosModal';
import { usePermissions } from '../../hooks/usePermissions';
import { exportarExcel } from '../../utils/excelExport';
import { useAntdApp } from '../../hooks/useMessage';
import { GlobalLoader } from '../../components/common/GlobalLoader';
import { useAuth } from '../../hooks/useAuth';
import CitasStats from './components/CitasStats';
import CitasAlerts from './components/CitasAlerts';
import CitasFilters from './components/CitasFilters';
import CitasQuickActions from './components/CitasQuickActions';
import CitasDrawer from './components/CitasDrawer';
import {
  EstadisticasCitas,
  getEstadoTag, getTipoTexto, esAtrasada, esHoy,
  checkCircleIcon5, closeCircleIcon2, userIcon2, medicineBoxIcon2, bellIcon,
  reloadIcon, exclamationIcon,
} from './citasUtils';
import { buildCitasColumns } from './citasColumns';

const CitasPage: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();
  const { canAdd, canChange, canDelete } = usePermissions();
  const { user: currentUser } = useAuth();
  interface CitasState {
    loading: boolean;
    citas: Cita[];
    busqueda: string;
    filtroEstado: EstadoCita | '';
    filtroTipo: TipoCita | '';
    filtroFecha: [dayjs.Dayjs, dayjs.Dayjs] | null;
    estadisticas: EstadisticasCitas;
    modalHorariosVisible: boolean;
    drawerVistaRapidaVisible: boolean;
    citaSeleccionada: Cita | null;
  }

  const [state, setState] = useState<CitasState>({
    loading: false,
    citas: [],
    busqueda: '',
    filtroEstado: '',
    filtroTipo: '',
    filtroFecha: null,
    estadisticas: {
      total: 0,
      agendadas: 0,
      confirmadas: 0,
      en_espera: 0,
      en_consulta: 0,
      completadas: 0,
      canceladas: 0,
      no_asistio: 0,
      hoy: 0,
      atrasadas: 0,
      pendientes_confirmacion: 0,
    },
    modalHorariosVisible: false,
    drawerVistaRapidaVisible: false,
    citaSeleccionada: null,
  });

  const loading = state.loading;
  const setLoading = (val: boolean) => setState((prev) => ({ ...prev, loading: val }));
  const [loadError, setLoadError] = useState<string | null>(null);

  const citas = state.citas;
  const setCitas = (val: Cita[]) => setState((prev) => ({ ...prev, citas: val }));

  const busqueda = state.busqueda;
  const setBusqueda = (val: string) => setState((prev) => ({ ...prev, busqueda: val }));

  const filtroEstado = state.filtroEstado;
  const setFiltroEstado = (val: EstadoCita | '') => setState((prev) => ({ ...prev, filtroEstado: val }));

  const filtroTipo = state.filtroTipo;
  const setFiltroTipo = (val: TipoCita | '') => setState((prev) => ({ ...prev, filtroTipo: val }));

  const filtroFecha = state.filtroFecha;
  const setFiltroFecha = (val: [dayjs.Dayjs, dayjs.Dayjs] | null) => setState((prev) => ({ ...prev, filtroFecha: val }));

  const estadisticas = state.estadisticas;
  const setEstadisticas = (val: EstadisticasCitas) => setState((prev) => ({ ...prev, estadisticas: val }));

  const modalHorariosVisible = state.modalHorariosVisible;
  const setModalHorariosVisible = (val: boolean) => setState((prev) => ({ ...prev, modalHorariosVisible: val }));

  const drawerVistaRapidaVisible = state.drawerVistaRapidaVisible;
  const setDrawerVistaRapidaVisible = (val: boolean) => setState((prev) => ({ ...prev, drawerVistaRapidaVisible: val }));

  const citaSeleccionada = state.citaSeleccionada;
  const setCitaSeleccionada = (val: Cita | null) => setState((prev) => ({ ...prev, citaSeleccionada: val }));

  const citasFiltradas = useMemo(() => {
    let resultado = [...citas];

    if (busqueda) {
      const busquedaLower = busqueda.toLowerCase();
      resultado = resultado.filter(
        (cita) =>
          cita.motivo?.toLowerCase().includes(busquedaLower) ||
          cita.observaciones?.toLowerCase().includes(busquedaLower) ||
          cita.paciente_info?.nombre_completo?.toLowerCase().includes(busquedaLower) ||
          cita.medico_info?.nombre?.toLowerCase().includes(busquedaLower) ||
          cita.paciente_info?.id_clinico?.toLowerCase().includes(busquedaLower)
      );
    }

    if (filtroEstado) {
      resultado = resultado.filter((cita) => cita.estado === filtroEstado);
    }

    if (filtroTipo) {
      resultado = resultado.filter((cita) => cita.tipo_cita === filtroTipo);
    }

    if (filtroFecha) {
      resultado = resultado.filter((cita) => {
        const fecha = dayjs(cita.fecha_cita);
        return fecha.isAfter(filtroFecha[0].startOf('day').subtract(1, 'day')) &&
          fecha.isBefore(filtroFecha[1].endOf('day').add(1, 'day'));
      });
    }

    return resultado;
  }, [citas, busqueda, filtroEstado, filtroTipo, filtroFecha]);

  const calcularEstadisticas = useCallback((data: Cita[]) => {
    const hoy = dayjs().startOf('day');
    const stats: EstadisticasCitas = {
      total: data.length,
      agendadas: data.filter((c) => c.estado === 'agendada').length,
      confirmadas: data.filter((c) => c.estado === 'confirmada').length,
      en_espera: data.filter((c) => c.estado === 'en_espera').length,
      en_consulta: data.filter((c) => c.estado === 'en_consulta').length,
      completadas: data.filter((c) => c.estado === 'completada').length,
      canceladas: data.filter((c) => c.estado === 'cancelada').length,
      no_asistio: data.filter((c) => c.estado === 'no_asistio').length,
      hoy: data.filter(
        (c) =>
          dayjs(c.fecha_cita).isSame(hoy, 'day') &&
          ['agendada', 'confirmada', 'en_espera', 'en_consulta'].includes(c.estado)
      ).length,
      atrasadas: data.filter(
        (c) =>
          dayjs(c.fecha_cita).isBefore(dayjs(), 'day') &&
          ['agendada', 'confirmada'].includes(c.estado)
      ).length,
      pendientes_confirmacion: data.filter((c) => c.estado === 'agendada').length,
    };
    setEstadisticas(stats);
  }, []);

  const cargarCitas = useCallback(async () => {
    setLoading(true);
    try {

      // 🚀 PASO 1: Obtener primera página de cada endpoint para saber cuántas páginas hay
      const [citasPage1, pacientesPage1] = await Promise.all([
        api.get('/citas/citas/?page=1&limit=200'),
        api.get('/pacientes/?page=1&limit=200')
      ]);

      // Calcular total de páginas
      const citasTotales = citasPage1.data.count || 0;
      const pacientesTotales = pacientesPage1.data.count || 0;

      const citasPages = Math.ceil(citasTotales / 200);
      const pacientesPages = Math.ceil(pacientesTotales / 200);


      // 🚀 PASO 2: Crear arrays de promesas para TODAS las páginas (en paralelo)
      const citasPromises = Array.from({ length: citasPages }, (_, i) =>
        api.get(`/citas/citas/?page=${i + 1}&limit=200`)
      );

      const pacientesPromises = Array.from({ length: pacientesPages }, (_, i) =>
        api.get(`/pacientes/?page=${i + 1}&limit=200`)
      );

      // 🚀 PASO 3: Ejecutar TODAS las requests en PARALELO
      const [citasResponses, pacientesResponses] = await Promise.all([
        Promise.all(citasPromises),
        Promise.all(pacientesPromises)
      ]);

      // 🚀 PASO 4: Combinar todos los resultados
      const allCitas = citasResponses.flatMap(res => res.data.results || []);
      const allPacientes = pacientesResponses.flatMap(res => res.data.results || []);

      const pacientesMap = new Map(allPacientes.map((p: any) => [p.id, p]));

      // Enriquecer citas con nombres de pacientes si es necesario y agregar _uniqueRowKey
      const citasEnriquecidas = allCitas.map((cita: any, index: number) => {
        if (!cita.paciente_info && cita.paciente) {
          const p = pacientesMap.get(cita.paciente);
          if (p) {
            cita.paciente_info = {
              id: p.id,
              nombre_completo: `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`.trim(),
              id_clinico: p.id_clinico || '',
              telefono: p.telefono || '',
              email: p.email || '',
              edad: p.edad || 0,
            };
          }
        }
        return { ...cita, _uniqueRowKey: `cita-${cita.id}-${index}-${Date.now()}` };
      });

      setCitas(citasEnriquecidas);
      calcularEstadisticas(citasEnriquecidas);
      setLoadError(null);
    } catch (error) {
      setLoadError('No se pudieron cargar las citas. Verifique su conexión e intente nuevamente.');
    } finally {
      setLoading(false);
    }
  }, [calcularEstadisticas]);

  useEffect(() => {
    cargarCitas();
  }, [cargarCitas]);

  const limpiarFiltros = () => {
    setBusqueda('');
    setFiltroEstado('');
    setFiltroTipo('');
    setFiltroFecha(null);
  };

  const handleNuevo = useCallback(() => {
    navigate('/dashboard/citas/nuevo');
  }, [navigate]);

  const handleVer = useCallback((id: number) => {
    navigate(`/dashboard/citas/${id}`);
  }, [navigate]);

  // ✨ NUEVA FUNCIÓN PARA VISTA RÁPIDA CON DRAWER
  const handleVerVistaRapida = useCallback((cita: Cita) => {
    setCitaSeleccionada(cita);
    setDrawerVistaRapidaVisible(true);
  }, []);

  const handleEditar = useCallback((id: number) => {
    navigate(`/dashboard/citas/${id}/editar`);
  }, [navigate]);

  const handleEliminar = useCallback((cita: any) => {
    modal.confirm({
      title: '⚠️ ¿Confirmar eliminación permanente?',
      icon: exclamationIcon,
      content: (
        <div>
          <p><strong>Se eliminará la cita médica:</strong></p>
          <ul style={{ marginLeft: 20 }}>
            <li>Paciente: {cita.paciente_info?.nombre_completo || 'No especificado'}</li>
            <li>Fecha: {dayjs(cita.fecha_cita).format('DD/MM/YYYY')} - {cita.hora_cita?.substring(0, 5)}</li>
            <li>Tipo: {getTipoTexto(cita.tipo_cita)}</li>
            <li>Motivo: {cita.motivo || 'No especificado'}</li>
          </ul>
          <p style={{ color: '#ff4d4f', fontWeight: 'bold', marginTop: 16 }}>
            ⚠️ ADVERTENCIA: Esta acción es permanente y NO se puede deshacer.
          </p>
          <p style={{ marginTop: 16 }}>
            Se perderán todos los datos de esta cita, incluyendo observaciones y recordatorios asociados.
          </p>
        </div>
      ),
      okText: 'Sí, eliminar permanentemente',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await citasService.delete(cita.id);
          message.success('Cita eliminada correctamente');
          cargarCitas();
        } catch (error) {
          message.error('Error al eliminar la cita');
        }
      },
    });
  }, [modal, message, cargarCitas]);

  const handleConfirmar = useCallback(async (id: number) => {
    try {
      await citasService.confirmar(id);
      message.success('Cita confirmada correctamente');
      cargarCitas();
    } catch (error) {
      message.error('Error al confirmar la cita');
    }
  }, [message, cargarCitas]);

  const handleCancelar = useCallback(async (id: number) => {
    modal.confirm({
      title: '¿Cancelar cita?',
      icon: exclamationIcon,
      content: '¿Está seguro de querer cancelar esta cita?',
      okText: 'Cancelar Cita',
      okType: 'danger',
      cancelText: 'No',
      onOk: async () => {
        try {
          await citasService.cancelar(id);
          message.success('Cita cancelada correctamente');
          cargarCitas();
        } catch (error) {
          message.error('Error al cancelar la cita');
        }
      },
    });
  }, [message, modal, cargarCitas]);

  const handleMarcarPresente = useCallback(async (id: number) => {
    try {
      await citasService.marcarPresente(id);
      message.success('Paciente marcado como presente');
      cargarCitas();
    } catch (error) {
      message.error('Error al marcar paciente presente');
    }
  }, [message, cargarCitas]);

  const handlePasarConsulta = useCallback(async (id: number) => {
    try {
      await citasService.pasarConsulta(id);
      message.success('Paciente pasado a consulta');
      cargarCitas();
    } catch (error) {
      message.error('Error al pasar paciente a consulta');
    }
  }, [message, cargarCitas]);

  const handleCompletar = useCallback(async (id: number) => {
    try {
      await citasService.completar(id);
      message.success('Cita completada correctamente');
      cargarCitas();
    } catch (error) {
      message.error('Error al completar la cita');
    }
  }, [message, cargarCitas]);

  const handleEnviarRecordatorio = useCallback(async (id: number) => {
    try {
      const result = await citasService.enviarRecordatorio(id);
      if (result.success) {
        message.success(result.message || 'Recordatorio enviado correctamente');
        cargarCitas();
      } else {
        message.warning(result.message || 'No se pudo enviar el recordatorio');
      }
    } catch (error) {
      message.error('Error al enviar recordatorio');
    }
  }, [message, cargarCitas]);

  const handleVerCalendario = useCallback(() => {
    navigate('/dashboard/citas/calendario');
  }, [navigate]);

  const handleExportExcel = useCallback(() => {
    try {
      const columnas = {
        'id': 'ID',
        'paciente_info.nombre_completo': 'Paciente',
        'fecha_cita': 'Fecha',
        'hora_cita': 'Hora',
        'tipo_cita': 'Tipo',
        'motivo': 'Motivo',
        'medico_info.nombre': 'Médico',
        'estado': 'Estado',
        'observaciones': 'Observaciones'
      };

      exportarExcel(
        citasFiltradas,
        columnas,
        {
          filename: `citas_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
          sheetName: 'Citas',
          title: `Agenda de Citas Médicas - ${dayjs().format('DD/MM/YYYY')}`
        }
      );
      message.success('Archivo Excel generado exitosamente');
    } catch (error) {
      message.error('Error al generar el archivo Excel');
    }
  }, [citasFiltradas, message]);

  const getMenuAcciones = useCallback((record: Cita) => ({
    items: [
      ...(record.estado === 'agendada' ? [
        {
          key: 'confirmar',
          label: 'Confirmar',
          icon: checkCircleIcon5,
          onClick: () => handleConfirmar(record.id!)
        }
      ] : []),
      ...(['agendada', 'confirmada'].includes(record.estado) ? [
        {
          key: 'presente',
          label: 'Marcar Presente',
          icon: userIcon2,
          onClick: () => handleMarcarPresente(record.id!)
        },
        {
          key: 'recordatorio',
          label: 'Enviar Recordatorio',
          icon: bellIcon,
          onClick: () => handleEnviarRecordatorio(record.id!)
        }
      ] : []),
      ...(record.estado === 'en_espera' ? [
        {
          key: 'consulta',
          label: 'Pasar a Consulta',
          icon: medicineBoxIcon2,
          onClick: () => handlePasarConsulta(record.id!)
        }
      ] : []),
      ...(record.estado === 'en_consulta' ? [
        {
          key: 'completar',
          label: 'Completar',
          icon: checkCircleIcon5,
          onClick: () => handleCompletar(record.id!)
        }
      ] : []),
      ...(!['completada', 'cancelada', 'no_asistio'].includes(record.estado) ? [
        {
          key: 'cancelar',
          label: 'Cancelar Cita',
          icon: closeCircleIcon2,
          danger: true,
          onClick: () => handleCancelar(record.id!)
        }
      ] : [])
    ]
  }) as MenuProps, [handleConfirmar, handleMarcarPresente, handleEnviarRecordatorio, handlePasarConsulta, handleCompletar, handleCancelar]);

  const columns = useMemo(
    () => buildCitasColumns({ canChange, canDelete, handleVerVistaRapida, handleEditar, handleEliminar, getMenuAcciones }),
    [canChange, canDelete, handleVerVistaRapida, handleEditar, handleEliminar, getMenuAcciones]
  );

  if (loading && citas.length === 0) {
    return <GlobalLoader tip="Cargando agenda de citas…" />;
  }

  return (
    <div className="citas-container animate-fade-in">
      <CitasStats estadisticas={estadisticas} />
      <CitasAlerts atrasadas={estadisticas.atrasadas} hoy={estadisticas.hoy} />

      {/* Tabla principal */}
      <Card
        title={
          <Space>
            <CalendarOutlined style={{ fontSize: 24, color: '#1890ff' }} />
            <span style={{ fontSize: 18, fontWeight: 600 }}>Gestión de Citas Médicas</span>
          </Space>
        }
        extra={
          <CitasQuickActions
            loading={loading}
            canAdd={canAdd('cita')}
            onVerCalendario={handleVerCalendario}
            onGestionarHorarios={() => setModalHorariosVisible(true)}
            onExportExcel={handleExportExcel}
            onActualizar={cargarCitas}
            onNuevaCita={handleNuevo}
          />
        }
      >
        <CitasFilters
          busqueda={busqueda}
          filtroEstado={filtroEstado}
          filtroTipo={filtroTipo}
          filtroFecha={filtroFecha}
          onBusquedaChange={setBusqueda}
          onFiltroEstadoChange={setFiltroEstado}
          onFiltroTipoChange={setFiltroTipo}
          onFiltroFechaChange={setFiltroFecha}
          onLimpiar={limpiarFiltros}
        />

        {loadError && (
          <Alert
            type="error"
            showIcon
            message="Error al cargar las citas"
            description={loadError}
            action={
              <Button size="small" icon={reloadIcon} onClick={cargarCitas}>
                Reintentar
              </Button>
            }
            style={{ marginBottom: 16 }}
          />
        )}

        {/* Tabla */}
        <Table
          columns={columns}
          dataSource={citasFiltradas}
          rowKey={(record: any) => record._uniqueRowKey || `cita-fallback-${record.id}`}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50', '100'],
            showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} citas`,
          }}
          scroll={{ x: 1400 }}
          rowClassName={(record) => {
            if (esAtrasada(record.fecha_cita, record.estado)) {
              return 'row-atrasada';
            }
            if (esHoy(record.fecha_cita) && !['completada', 'cancelada', 'no_asistio'].includes(record.estado)) {
              return 'row-hoy';
            }
            return '';
          }}
        />
      </Card>

      {modalHorariosVisible && (
        <GestionHorariosModal
          open={modalHorariosVisible}
          onCancel={() => setModalHorariosVisible(false)}
          currentUser={(currentUser as any) ?? undefined}
        />
      )}

      <CitasDrawer
        visible={drawerVistaRapidaVisible}
        cita={citaSeleccionada}
        canChange={canChange('cita')}
        onClose={() => setDrawerVistaRapidaVisible(false)}
        getEstadoTag={getEstadoTag}
      />
    </div>
  );
};

export default CitasPage;
