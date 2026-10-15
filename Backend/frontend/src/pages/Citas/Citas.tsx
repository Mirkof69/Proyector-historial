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
  Empty,
  Card,
  Table,
  Button,
  Alert,
  MenuProps,
  Typography,
} from 'antd';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
// Cliente axios: `.get()` devuelve la respuesta, los datos están en `.data`.
import api from '../../services/api';
import { citasService, Cita, EstadoCita, TipoCita } from '../../services/citasService';
import { GestionHorariosModal } from './GestionHorariosModal';
import { usePermissions } from '../../hooks/usePermissions';
import { useAntdApp } from '../../hooks/useMessage';
import { useAuth } from '../../hooks/useAuth';
import { aQuery, useListadoServidor } from '../../hooks/useListadoServidor';
import { descargarArchivo } from '../../utils/descargarArchivo';
import CitasStats from './components/CitasStats';
import CitasAlerts from './components/CitasAlerts';
import CitasFilters from './components/CitasFilters';
import CitasQuickActions from './components/CitasQuickActions';
import './Citas.css';
import CitasDrawer from './components/CitasDrawer';
import {
  EstadisticasCitas,
  getEstadoTag, getTipoTexto, esAtrasada, esHoy,
  checkCircleIcon5, closeCircleIcon2, userIcon2, medicineBoxIcon2, bellIcon,
  reloadIcon, exclamationIcon,
} from './citasUtils';
import { buildCitasColumns } from './citasColumns';

const RESUMEN_VACIO: EstadisticasCitas = {
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
};

/** El backend responde con los códigos de estado (`agendada`); la tarjeta usa plurales. */
const desdeResumen = (r: Record<string, number>): EstadisticasCitas => ({
  total: r.total ?? 0,
  agendadas: r.agendada ?? 0,
  confirmadas: r.confirmada ?? 0,
  en_espera: r.en_espera ?? 0,
  en_consulta: r.en_consulta ?? 0,
  completadas: r.completada ?? 0,
  canceladas: r.cancelada ?? 0,
  no_asistio: r.no_asistio ?? 0,
  hoy: r.hoy ?? 0,
  atrasadas: r.atrasadas ?? 0,
  pendientes_confirmacion: r.pendientes_confirmacion ?? 0,
});

const CitasPage: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();
  const { canAdd, canChange, canDelete } = usePermissions();
  const { user: currentUser } = useAuth();

  const [busqueda, setBusqueda] = useState('');
  const [filtroEstado, setFiltroEstado] = useState<EstadoCita | ''>('');
  const [filtroTipo, setFiltroTipo] = useState<TipoCita | ''>('');
  const [filtroFecha, setFiltroFecha] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [estadisticas, setEstadisticas] = useState<EstadisticasCitas>(RESUMEN_VACIO);
  const [modalHorariosVisible, setModalHorariosVisible] = useState(false);
  const [drawerVistaRapidaVisible, setDrawerVistaRapidaVisible] = useState(false);
  const [citaSeleccionada, setCitaSeleccionada] = useState<Cita | null>(null);

  // Búsqueda, filtros, orden y paginación los resuelve el SERVIDOR. Antes se
  // descargaban TODAS las citas y TODAS las pacientes en bucle (~34
  // peticiones con 3.200 pacientes) para poner nombres que CitaListSerializer
  // ya trae en `paciente_info`, y se filtraba en el navegador.
  const filtrosServidor = useMemo(() => ({
    estado: filtroEstado || undefined,
    tipo_cita: filtroTipo || undefined,
    // `fecha_cita` es DateField: se manda la fecha LOCAL. Con toISOString()
    // el «hasta» de La Paz (UTC-4) caería en el día siguiente.
    fecha_desde: filtroFecha?.[0]?.format('YYYY-MM-DD'),
    fecha_hasta: filtroFecha?.[1]?.format('YYYY-MM-DD'),
  }), [filtroEstado, filtroTipo, filtroFecha]);

  const listado = useListadoServidor<Cita>('/citas/citas/', {
    filtros: filtrosServidor, busqueda, tamanoInicial: 10, ordenInicial: '-fecha_cita',
  });
  const { parametros, recargar } = listado;

  // Cifras con los MISMOS filtros que la tabla, contadas sobre todas las citas.
  const cargarResumen = useCallback(async () => {
    try {
      const r = await api.get('/citas/citas/resumen/', { params: parametros() });
      setEstadisticas(desdeResumen(r.data));
    } catch {
      // Las cifras de cabecera no deben impedir usar la agenda.
      setEstadisticas(RESUMEN_VACIO);
    }
  }, [parametros]);
  useEffect(() => { cargarResumen(); }, [cargarResumen]);

  const cargarCitas = useCallback(() => {
    recargar();
    cargarResumen();
  }, [recargar, cargarResumen]);

  const limpiarFiltros = () => {
    setBusqueda('');
    setFiltroEstado('');
    setFiltroTipo('');
    setFiltroFecha(null);
  };

  const handleNuevo = useCallback(() => {
    navigate('/dashboard/citas/nuevo');
  }, [navigate]);

  // NUEVA FUNCIÓN PARA VISTA RÁPIDA CON DRAWER
  const handleVerVistaRapida = useCallback((cita: Cita) => {
    setCitaSeleccionada(cita);
    setDrawerVistaRapidaVisible(true);
  }, []);

  const handleEditar = useCallback((id: number) => {
    navigate(`/dashboard/citas/${id}/editar`);
  }, [navigate]);

  const handleEliminar = useCallback((cita: any) => {
    modal.confirm({
      title: '¿Confirmar eliminación permanente?',
      icon: exclamationIcon,
      content: (
        <div>
          <p><strong>Se eliminará la cita médica:</strong></p>
          <ul className="citas-borrado__lista">
            <li>Paciente: {cita.paciente_info?.nombre_completo || 'No especificado'}</li>
            <li>Fecha: {dayjs(cita.fecha_cita).format('DD/MM/YYYY')} - {cita.hora_cita?.substring(0, 5)}</li>
            <li>Tipo: {getTipoTexto(cita.tipo_cita)}</li>
            <li>Motivo: {cita.motivo || 'No especificado'}</li>
          </ul>
          <p className="citas-borrado__advertencia">
            ADVERTENCIA: Esta acción es permanente y NO se puede deshacer.
          </p>
          <p className="citas-arriba">
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

  const handleExportExcel = useCallback(async () => {
    // El Excel lo arma el servidor con TODAS las citas que cumplen los filtros
    // (no solo la página visible) y la exportación queda auditada.
    try {
      await descargarArchivo(`/citas/citas/exportar-excel/${aQuery(parametros())}`, `citas_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`);
      message.success('Archivo Excel generado exitosamente');
    } catch {
      message.error('Error al generar el archivo Excel');
    }
  }, [parametros, message]);

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

  return (
    <div className="citas-page page-container">
      <header className="citas-page__cabecera">
        <div>
          <Typography.Title level={2}>Gestión de Citas Médicas</Typography.Title>
          <Typography.Text type="secondary">Agenda de consultas: confirmación, llegada y atención de cada cita.</Typography.Text>
        </div>
        <CitasQuickActions
          loading={listado.cargando}
          canAdd={canAdd('cita')}
          onVerCalendario={handleVerCalendario}
          onGestionarHorarios={() => setModalHorariosVisible(true)}
          onExportExcel={handleExportExcel}
          onActualizar={cargarCitas}
          onNuevaCita={handleNuevo}
        />
      </header>

      <CitasStats estadisticas={estadisticas} />
      <CitasAlerts atrasadas={estadisticas.atrasadas} hoy={estadisticas.hoy} />

      {/* Tabla principal */}
      <Card>
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

        {listado.error && (
          <Alert
            type="error"
            showIcon
            message="Error al cargar las citas"
            description={listado.error}
            action={
              <Button size="small" icon={reloadIcon} onClick={cargarCitas}>
                Reintentar
              </Button>
            }
            className="citas-separado"
          />
        )}

        {/* Tabla */}
        <Table
          columns={columns}
          dataSource={listado.datos}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay citas registradas" /> }}
          rowKey="id"
          loading={listado.cargando}
          pagination={listado.paginacion}
          onChange={listado.onChange}
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
