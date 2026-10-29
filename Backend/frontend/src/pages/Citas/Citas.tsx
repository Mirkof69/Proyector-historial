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
import { conMotivo } from '../../utils/erroresApi';
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
          message.error(conMotivo('No se pudo eliminar la cita', error));
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
      message.error(conMotivo('No se pudo confirmar la cita', error));
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
          message.error(conMotivo('No se pudo cancelar la cita', error));
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
      message.error(conMotivo('No se pudo registrar la llegada', error));
    }
  }, [message, cargarCitas]);

  const handlePasarConsulta = useCallback(async (id: number) => {
    try {
      await citasService.pasarConsulta(id);
      message.success('Paciente pasado a consulta');
      cargarCitas();
    } catch (error) {
      message.error(conMotivo('No se pudo pasar a consulta', error));
    }
  }, [message, cargarCitas]);

  const handleCompletar = useCallback(async (id: number) => {
    try {
      await citasService.completar(id);
      message.success('Cita completada correctamente');
      cargarCitas();
    } catch (error) {
      message.error(conMotivo('No se pudo completar la cita', error));
    }
  }, [message, cargarCitas]);

  const handleNoAsistio = useCallback((id: number) => {
    modal.confirm({
      title: '¿La paciente no vino?',
      icon: exclamationIcon,
      content: 'La cita queda como «No asistió» y libera el turno.',
      okText: 'Marcar No asistió',
      cancelText: 'Volver',
      onOk: async () => {
        try {
          await citasService.noAsistio(id);
          message.success('Cita marcada como «No asistió»');
          cargarCitas();
        } catch (error) {
          message.error(conMotivo('No se pudo marcar «No asistió»', error));
        }
      },
    });
  }, [message, modal, cargarCitas]);

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
      message.error(conMotivo('No se pudo enviar el recordatorio', error));
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

  // Cada acción solo cuando corresponde a la fecha de la cita (el servidor
  // aplica la misma regla): la llegada y la consulta, el mismo día; «No asistió»
  // y completar, ese día o después; confirmar y recordar, antes.
  const getMenuAcciones = useCallback((record: Cita) => {
    const dia = dayjs(record.fecha_cita);
    const hoy = dia.isSame(dayjs(), 'day');
    const yaLlego = !dia.isAfter(dayjs(), 'day');
    const porVenir = !dia.isBefore(dayjs(), 'day');
    const pendiente = ['agendada', 'confirmada'].includes(record.estado);
    const item = (key: string, label: string, icon: React.ReactNode, onClick: () => void, danger = false) =>
      ({ key, label, icon, onClick, danger });
    const items = [
      record.estado === 'agendada' && porVenir && item('confirmar', 'Confirmar', checkCircleIcon5, () => handleConfirmar(record.id!)),
      pendiente && hoy && item('presente', 'Marcar Presente', userIcon2, () => handleMarcarPresente(record.id!)),
      pendiente && porVenir && !hoy && item('recordatorio', 'Enviar Recordatorio', bellIcon, () => handleEnviarRecordatorio(record.id!)),
      record.estado === 'en_espera' && hoy && item('consulta', 'Pasar a Consulta', medicineBoxIcon2, () => handlePasarConsulta(record.id!)),
      ['en_espera', 'en_consulta'].includes(record.estado) && yaLlego && item('completar', 'Completar', checkCircleIcon5, () => handleCompletar(record.id!)),
      ['agendada', 'confirmada', 'en_espera'].includes(record.estado) && yaLlego && item('no_asistio', 'No asistió', closeCircleIcon2, () => handleNoAsistio(record.id!), true),
      ['agendada', 'confirmada', 'en_espera'].includes(record.estado) && item('cancelar', 'Cancelar Cita', closeCircleIcon2, () => handleCancelar(record.id!), true),
    ].filter(Boolean) as NonNullable<MenuProps['items']>;
    return { items: items.length ? items : [{ key: 'sin', label: 'Sin acciones para esta cita', disabled: true }] } as MenuProps;
  }, [handleConfirmar, handleMarcarPresente, handleEnviarRecordatorio, handlePasarConsulta, handleCompletar, handleNoAsistio, handleCancelar]);

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
