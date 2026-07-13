import React, { Suspense } from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuth } from '../hooks/useAuth';
import { logger } from '../utils/logger';
import ProtectedRoute from './ProtectedRoute';

// --- PUBLIC PAGES (eager - needed before auth) ---
import Login from '../pages/Login/Login';
import LandingPage from '../pages/Dashboard/LandingPage';
import SetupMfa from '../pages/SetupMfa/SetupMfa';
import DashboardLayout from '../pages/Dashboard/Dashboard';
import NotFound from '../pages/NotFound';
import Unauthorized from '../pages/Unauthorized';
import PageTransition from '../components/common/PageTransition';

import {
  DashboardHome, DashboardGraficasReales, Pacientes, DetallePaciente, FormularioPaciente,
  BusquedaAvanzada, GlobalSearch, HistoriaClinica, ListaHistoriasClinicas, Embarazos,
  DetalleEmbarazo, FormularioEmbarazo, Controles, DetalleControl, FormularioControl,
  Ecografias, DetalleEcografia, FormularioEcografia, VisorDICOM, ArchivosEcografia,
  Laboratorio, DetalleLaboratorio, FormularioLaboratorio, TiposExamen, ResultadosLaboratorio,
  ValoresReferencia, Citas, FormularioCita, DetalleCita, CalendarioCitas, IAAsistenteMedico,
  IaMedica, Partos, DetalleParto, FormularioParto, Partograma, ApgarScore, ComplicacionesParto,
  RecienNacidos, Reportes, GenerarReporte, DetalleReporte, KPIs, Indicadores, AuditoriaReportes,
  Calculadoras, CalculadorasAvanzadas, IndiceCalculadoras, ScoreBishop, IMCGananciaPonderal,
  RiesgoPreeclampsia, CrecimientoFetal, RiesgoCromosomico, DosisMedicamentos, HemorragiaObstetrica,
  SufrimientoFetal, Usuarios, Roles, FormularioRol, DetalleRol, Auditoria, AccessLogs, Statistics,
  Perfil, Configuracion, Ayuda, Evoluciones, DetalleEvolucion, FormularioEvolucion, Antecedentes,
  AntecedentesGinecoObstetricos, AntecedentesPatologicos, FormularioAntecedenteGineco,
  FormularioAntecedentePatologico, Consultorios, FormularioConsultorio, DetalleConsultorio,
  Triaje, FormularioTriaje, DetalleTriaje, Vacunas, FormularioVacuna, DetalleVacuna, TiposVacuna,
  AlertasMedicas, DetalleAlerta, ConfiguracionAlertas, SistemaAlertas, NotasEvolucion,
  FormularioNotaEvolucion, DetalleNotaEvolucion, Notificaciones, DatabaseBackup,
} from './lazyPages';

const AppRoutes: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();

  const handleLogout = () => {
    logout();
    logger.log('👋 Sesión cerrada');
  };

  const handleLoginSuccess = () => {
    logger.log('✅ Login exitoso');
  };

  return (
    <Suspense fallback={<div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Spin size="large" tip="Cargando módulo clínico…"><div /></Spin></div>}>
      <Routes>
        {/* ==================== RUTAS PÚBLICAS ==================== */}

        {/* LANDING PAGE / HOME PÚBLICA */}
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <LandingPage />
            )
          }
        />

        {/* LOGIN */}
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Login onLoginSuccess={handleLoginSuccess} />
            )
          }
        />

        {/* SETUP MFA — público, accesible sin autenticación completa */}
        <Route path="/setup-mfa" element={<SetupMfa />} />

        {/* ==================== RUTAS PROTEGIDAS (DASHBOARD PRINCIPAL) ==================== */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout onLogout={handleLogout}>
                <PageTransition>
                  <Outlet />
                </PageTransition>
              </DashboardLayout>
            </ProtectedRoute>
          }
        >
          {/* DASHBOARD HOME */}
          <Route index element={<DashboardHome />} />
          <Route path="home" element={<DashboardHome />} />
          <Route path="graficas" element={<DashboardGraficasReales />} />
          <Route path="graficas-reales" element={<DashboardGraficasReales />} />

          {/* MÓDULO: PACIENTES */}
          <Route path="pacientes" element={<ProtectedRoute requiredPermission="view_paciente"><Pacientes /></ProtectedRoute>} />
          <Route path="pacientes/nuevo" element={<ProtectedRoute requiredPermission="add_paciente"><FormularioPaciente /></ProtectedRoute>} />
          <Route path="pacientes/buscar" element={<ProtectedRoute requiredPermission="view_paciente"><BusquedaAvanzada /></ProtectedRoute>} />
          <Route path="busqueda/global" element={<GlobalSearch />} />
          <Route path="busqueda" element={<GlobalSearch />} />
          <Route path="pacientes/:id" element={<ProtectedRoute requiredPermission="view_paciente"><DetallePaciente /></ProtectedRoute>} />
          <Route path="pacientes/:id/editar" element={<ProtectedRoute requiredPermission="change_paciente"><FormularioPaciente /></ProtectedRoute>} />
          <Route path="pacientes/:id/historia" element={<ProtectedRoute requiredPermission="view_paciente"><HistoriaClinica /></ProtectedRoute>} />

          {/* ESTADÍSTICAS */}
          <Route path="estadisticas" element={<Statistics />} />

          {/* LOGS DE ACCESO (SOLO ADMIN O CON PERMISO) */}
          <Route path="access-logs" element={<AccessLogs />} />

          {/* MÓDULO: HISTORIA CLÍNICA */}
          <Route path="historia-clinica" element={<ProtectedRoute requiredPermission="view_paciente"><ListaHistoriasClinicas /></ProtectedRoute>} />
          <Route path="historia-clinica/:id" element={<ProtectedRoute requiredPermission="view_paciente"><HistoriaClinica /></ProtectedRoute>} />

          {/* MÓDULO: EMBARAZOS */}
          <Route path="embarazos" element={<ProtectedRoute requiredPermission="view_embarazo"><Embarazos /></ProtectedRoute>} />
          <Route path="embarazos/nuevo" element={<ProtectedRoute requiredPermission="add_embarazo"><FormularioEmbarazo /></ProtectedRoute>} />
          <Route path="embarazos/:id" element={<ProtectedRoute requiredPermission="view_embarazo"><DetalleEmbarazo /></ProtectedRoute>} />
          <Route path="embarazos/:id/editar" element={<ProtectedRoute requiredPermission="change_embarazo"><FormularioEmbarazo /></ProtectedRoute>} />
          <Route path="embarazos/:id/timeline" element={<ProtectedRoute requiredPermission="view_embarazo"><DetalleEmbarazo /></ProtectedRoute>} />

          {/* MÓDULO: CONTROLES PRENATALES */}
          <Route path="controles" element={<ProtectedRoute requiredPermission="view_controlprenatal"><Controles /></ProtectedRoute>} />
          <Route path="controles/nuevo" element={<ProtectedRoute requiredPermission="add_controlprenatal"><FormularioControl /></ProtectedRoute>} />
          <Route path="controles/:id" element={<ProtectedRoute requiredPermission="view_controlprenatal"><DetalleControl /></ProtectedRoute>} />
          <Route path="controles/:id/editar" element={<ProtectedRoute requiredPermission="change_controlprenatal"><FormularioControl /></ProtectedRoute>} />

          {/* MÓDULO: ECOGRAFÍAS */}
          <Route path="ecografias" element={<ProtectedRoute requiredPermission="view_ecografia"><Ecografias /></ProtectedRoute>} />
          <Route path="ecografias/nuevo" element={<ProtectedRoute requiredPermission="add_ecografia"><FormularioEcografia /></ProtectedRoute>} />
          <Route path="ecografias/:id" element={<ProtectedRoute requiredPermission="view_ecografia"><DetalleEcografia /></ProtectedRoute>} />
          <Route path="ecografias/:id/editar" element={<ProtectedRoute requiredPermission="change_ecografia"><FormularioEcografia /></ProtectedRoute>} />
          <Route path="ecografias/:id/dicom" element={<ProtectedRoute requiredPermission="view_ecografia"><VisorDICOM /></ProtectedRoute>} />
          <Route path="ecografias/:id/viewer" element={<ProtectedRoute requiredPermission="view_ecografia"><VisorDICOM /></ProtectedRoute>} />

          {/* MÓDULO: LABORATORIO */}
          <Route path="laboratorio" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><Laboratorio /></ProtectedRoute>} />
          <Route path="laboratorios" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><Laboratorio /></ProtectedRoute>} />
          <Route path="laboratorios/hemogramas" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><Laboratorio /></ProtectedRoute>} />
          <Route path="laboratorios/bioquimicas" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><Laboratorio /></ProtectedRoute>} />
          <Route path="laboratorios/marcadores" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><Laboratorio /></ProtectedRoute>} />
          <Route path="laboratorio/nuevo" element={<ProtectedRoute requiredPermission="add_examenlaboratorio"><FormularioLaboratorio /></ProtectedRoute>} />
          <Route path="laboratorio/:id" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><DetalleLaboratorio /></ProtectedRoute>} />
          <Route path="laboratorio/:id/editar" element={<ProtectedRoute requiredPermission="change_examenlaboratorio"><FormularioLaboratorio /></ProtectedRoute>} />

          {/* MÓDULO: CALCULADORAS */}
          <Route path="calculadoras" element={<ProtectedRoute requiredPermission="view_calculoclinico"><Calculadoras /></ProtectedRoute>} />
          <Route path="calculadoras/:tipo" element={<ProtectedRoute requiredPermission="view_calculoclinico"><Calculadoras /></ProtectedRoute>} />
          <Route path="calculadoras-avanzadas" element={<ProtectedRoute requiredPermission="view_calculoclinico"><CalculadorasAvanzadas /></ProtectedRoute>} />
          <Route path="calculadoras-avanzadas/:tipo" element={<ProtectedRoute requiredPermission="view_calculoclinico"><CalculadorasAvanzadas /></ProtectedRoute>} />
          <Route path="panel-calculadoras" element={<ProtectedRoute requiredPermission="view_calculoclinico"><IndiceCalculadoras /></ProtectedRoute>} />

          {/* MÓDULO: CITAS Y AGENDA */}
          <Route path="citas" element={<ProtectedRoute requiredPermission="view_cita"><Citas /></ProtectedRoute>} />
          <Route path="citas/nuevo" element={<ProtectedRoute requiredPermission="add_cita"><FormularioCita /></ProtectedRoute>} />
          <Route path="citas/:id" element={<ProtectedRoute requiredPermission="view_cita"><DetalleCita /></ProtectedRoute>} />
          <Route path="citas/:id/editar" element={<ProtectedRoute requiredPermission="change_cita"><FormularioCita /></ProtectedRoute>} />
          <Route path="citas/calendario" element={<ProtectedRoute requiredPermission="view_cita"><CalendarioCitas /></ProtectedRoute>} />
          <Route path="citas/hoy" element={<ProtectedRoute requiredPermission="view_cita"><Citas /></ProtectedRoute>} />

          {/* MÓDULO: PARTOS */}
          <Route path="partos" element={<ProtectedRoute requiredPermission="view_parto"><Partos /></ProtectedRoute>} />
          <Route path="partos/nuevo" element={<ProtectedRoute requiredPermission="add_parto"><FormularioParto /></ProtectedRoute>} />
          <Route path="partos/:id" element={<ProtectedRoute requiredPermission="view_parto"><DetalleParto /></ProtectedRoute>} />
          <Route path="partos/:id/editar" element={<ProtectedRoute requiredPermission="change_parto"><FormularioParto /></ProtectedRoute>} />

          {/* MÓDULO: REPORTES Y ESTADÍSTICAS */}
          <Route path="reportes" element={<ProtectedRoute requiredPermission="view_reportegenerado"><Reportes /></ProtectedRoute>} />
          <Route path="reportes/generar" element={<ProtectedRoute requiredPermission="add_reportegenerado"><GenerarReporte /></ProtectedRoute>} />
          <Route path="reportes/pdf" element={<Navigate to="/dashboard/reportes/generar" replace />} />
          <Route path="reportes/pdf-automatico" element={<Navigate to="/dashboard/reportes/generar" replace />} />
          <Route path="reportes/:id" element={<ProtectedRoute requiredPermission="view_reportegenerado"><DetalleReporte /></ProtectedRoute>} />
          <Route path="reportes/historial" element={<ProtectedRoute requiredPermission="view_reportegenerado"><Reportes /></ProtectedRoute>} />

          {/* MÓDULO: IA MEDICA Y CNN */}
          <Route path="ia-medica/imagenes" element={<IaMedica />} />

          {/* MÓDULO: ADMINISTRACIÓN Y SISTEMA */}
          <Route path="usuarios" element={<ProtectedRoute requiredPermission="view_usuario"><Usuarios /></ProtectedRoute>} />
          <Route path="auditoria" element={<ProtectedRoute requiredPermission="view_usuario"><Auditoria /></ProtectedRoute>} />
          <Route path="perfil" element={<Perfil />} />
          <Route path="configuracion" element={<ProtectedRoute requiredPermission="view_sistemaconfiguracion"><Configuracion /></ProtectedRoute>} />
          <Route path="ayuda" element={<Ayuda />} />

          {/* MÓDULO: NOTIFICACIONES */}
          <Route path="notificaciones" element={<Notificaciones />} />

          {/* MÓDULO: BACKUP */}
          <Route path="backup" element={<ProtectedRoute requiredPermission="view_sistemaconfiguracion"><DatabaseBackup /></ProtectedRoute>} />

          {/* MÓDULO: EVOLUCIONES */}
          <Route path="evoluciones" element={<Evoluciones />} />
          <Route path="evoluciones/nuevo" element={<FormularioEvolucion />} />
          <Route path="evoluciones/:id" element={<DetalleEvolucion />} />
          <Route path="evoluciones/:id/editar" element={<FormularioEvolucion />} />

          {/* MÓDULO: ANTECEDENTES */}
          <Route path="antecedentes" element={<Antecedentes />} />

          {/* MÓDULO: CONSULTORIOS */}
          <Route path="consultorios" element={<Consultorios />} />
          <Route path="consultorios/nuevo" element={<FormularioConsultorio />} />
          <Route path="consultorios/:id" element={<DetalleConsultorio />} />
          <Route path="consultorios/editar/:id" element={<FormularioConsultorio />} />

          {/* MÓDULO: TRIAJE DE ENFERMERÍA */}
          <Route path="triaje" element={<ProtectedRoute requiredPermission="view_triajeenfermeria"><Triaje /></ProtectedRoute>} />
          <Route path="triaje/nuevo" element={<ProtectedRoute requiredPermission="add_triajeenfermeria"><FormularioTriaje /></ProtectedRoute>} />
          <Route path="triaje/:id" element={<ProtectedRoute requiredPermission="view_triajeenfermeria"><DetalleTriaje /></ProtectedRoute>} />
          <Route path="triaje/:id/editar" element={<ProtectedRoute requiredPermission="change_triajeenfermeria"><FormularioTriaje /></ProtectedRoute>} />

          {/* MÓDULO: VACUNAS */}
          <Route path="vacunas" element={<ProtectedRoute requiredPermission="view_registrovacuna"><Vacunas /></ProtectedRoute>} />
          <Route path="vacunas/nuevo" element={<ProtectedRoute requiredPermission="add_registrovacuna"><FormularioVacuna /></ProtectedRoute>} />
          <Route path="vacunas/:id" element={<ProtectedRoute requiredPermission="view_registrovacuna"><DetalleVacuna /></ProtectedRoute>} />
          <Route path="vacunas/:id/editar" element={<ProtectedRoute requiredPermission="change_registrovacuna"><FormularioVacuna /></ProtectedRoute>} />
          <Route path="vacunas/tipos" element={<ProtectedRoute requiredPermission="view_tipovacuna"><TiposVacuna /></ProtectedRoute>} />

          {/* MÓDULO: ALERTAS MÉDICAS */}
          <Route path="alertas" element={<ProtectedRoute requiredPermission="view_alertamedica"><AlertasMedicas /></ProtectedRoute>} />
          <Route path="alertas/:id" element={<ProtectedRoute requiredPermission="view_alertamedica"><DetalleAlerta /></ProtectedRoute>} />
          <Route path="alertas/configuracion" element={<ProtectedRoute requiredPermission="change_alertamedica"><ConfiguracionAlertas /></ProtectedRoute>} />
          <Route path="alertas/sistema" element={<ProtectedRoute requiredPermission="view_alertamedica"><SistemaAlertas /></ProtectedRoute>} />

          {/* MÓDULO: NOTAS DE EVOLUCIÓN */}
          <Route path="notas-evolucion" element={<ProtectedRoute requiredPermission="view_notaevolucion"><NotasEvolucion /></ProtectedRoute>} />
          <Route path="notas-evolucion/nuevo" element={<ProtectedRoute requiredPermission="add_notaevolucion"><FormularioNotaEvolucion /></ProtectedRoute>} />
          <Route path="notas-evolucion/:id" element={<ProtectedRoute requiredPermission="view_notaevolucion"><DetalleNotaEvolucion /></ProtectedRoute>} />
          <Route path="notas-evolucion/:id/editar" element={<ProtectedRoute requiredPermission="change_notaevolucion"><FormularioNotaEvolucion /></ProtectedRoute>} />

          {/* CALCULADORAS AVANZADAS INDIVIDUALES */}
          <Route path="calculadoras/bishop" element={<ProtectedRoute requiredPermission="view_scorebishop"><ScoreBishop /></ProtectedRoute>} />
          <Route path="calculadoras/imc-ganancia" element={<ProtectedRoute requiredPermission="view_calculadora"><IMCGananciaPonderal /></ProtectedRoute>} />
          <Route path="calculadoras/preeclampsia" element={<ProtectedRoute requiredPermission="view_riesgopreeclampsia"><RiesgoPreeclampsia /></ProtectedRoute>} />
          <Route path="calculadoras/crecimiento-fetal" element={<ProtectedRoute requiredPermission="view_crecimientofetal"><CrecimientoFetal /></ProtectedRoute>} />
          <Route path="calculadoras/riesgo-cromosomico" element={<ProtectedRoute requiredPermission="view_riesgocromosomico"><RiesgoCromosomico /></ProtectedRoute>} />
          <Route path="calculadoras/dosis-medicamentos" element={<ProtectedRoute requiredPermission="view_dosismedicamentos"><DosisMedicamentos /></ProtectedRoute>} />
          <Route path="calculadoras/hemorragia-obstetrica" element={<ProtectedRoute requiredPermission="view_hemorragiaobstetrica"><HemorragiaObstetrica /></ProtectedRoute>} />
          <Route path="calculadoras/sufrimiento-fetal" element={<ProtectedRoute requiredPermission="view_sufrimientofetal"><SufrimientoFetal /></ProtectedRoute>} />

          {/* MÓDULO: PARTOS EXTENDIDO */}
          <Route path="partos/:id/partograma" element={<ProtectedRoute requiredPermission="view_registropartograma"><Partograma /></ProtectedRoute>} />
          <Route path="partos/:id/apgar" element={<ProtectedRoute requiredPermission="view_apgarscoredetallado"><ApgarScore /></ProtectedRoute>} />
          <Route path="partos/:id/complicaciones" element={<ProtectedRoute requiredPermission="view_complicacionparto"><ComplicacionesParto /></ProtectedRoute>} />
          <Route path="partos/:id/recien-nacido" element={<ProtectedRoute requiredPermission="view_reciennacido"><RecienNacidos /></ProtectedRoute>} />

          {/* MÓDULO: LABORATORIO EXTENDIDO */}
          <Route path="laboratorio/tipos-examen" element={<ProtectedRoute requiredPermission="view_tipoexamen"><TiposExamen /></ProtectedRoute>} />
          <Route path="laboratorio/resultados" element={<ProtectedRoute requiredPermission="view_resultadolaboratorio"><ResultadosLaboratorio /></ProtectedRoute>} />
          <Route path="laboratorio/valores-referencia" element={<ProtectedRoute requiredPermission="view_valorreferencia"><ValoresReferencia /></ProtectedRoute>} />

          {/* MÓDULO: ANTECEDENTES DETALLADO */}
          <Route path="antecedentes/gineco-obstetricos" element={<ProtectedRoute requiredPermission="view_antecedenteginecoobstetrico"><AntecedentesGinecoObstetricos /></ProtectedRoute>} />
          <Route path="antecedentes/gineco-obstetricos/nuevo" element={<ProtectedRoute requiredPermission="add_antecedenteginecoobstetrico"><FormularioAntecedenteGineco /></ProtectedRoute>} />
          <Route path="antecedentes/gineco-obstetricos/:id/editar" element={<ProtectedRoute requiredPermission="change_antecedenteginecoobstetrico"><FormularioAntecedenteGineco /></ProtectedRoute>} />
          <Route path="antecedentes/patologicos" element={<ProtectedRoute requiredPermission="view_antecedentepatologico"><AntecedentesPatologicos /></ProtectedRoute>} />
          <Route path="antecedentes/patologicos/nuevo" element={<ProtectedRoute requiredPermission="add_antecedentepatologico"><FormularioAntecedentePatologico /></ProtectedRoute>} />
          <Route path="antecedentes/patologicos/:id/editar" element={<ProtectedRoute requiredPermission="change_antecedentepatologico"><FormularioAntecedentePatologico /></ProtectedRoute>} />

          {/* MÓDULO: ECOGRAFÍAS EXTENDIDO */}
          <Route path="ecografias/:id/archivos" element={<ProtectedRoute requiredPermission="view_archivoecografia"><ArchivosEcografia /></ProtectedRoute>} />

          {/* MÓDULO: REPORTES EXTENDIDO */}
          <Route path="reportes/kpis" element={<ProtectedRoute requiredPermission="view_indicadorkpi"><KPIs /></ProtectedRoute>} />
          <Route path="reportes/indicadores" element={<ProtectedRoute requiredPermission="view_indicadorkpi"><Indicadores /></ProtectedRoute>} />
          <Route path="reportes/auditoria" element={<ProtectedRoute requiredPermission="view_auditoriareporte"><AuditoriaReportes /></ProtectedRoute>} />

          {/* MÓDULO: ROLES Y PERMISOS */}
          <Route path="roles" element={<ProtectedRoute requireAdmin={true}><Roles /></ProtectedRoute>} />
          <Route path="roles/nuevo" element={<ProtectedRoute requireAdmin={true}><FormularioRol /></ProtectedRoute>} />
          <Route path="roles/:id" element={<ProtectedRoute requireAdmin={true}><DetalleRol /></ProtectedRoute>} />
          <Route path="roles/:id/editar" element={<ProtectedRoute requireAdmin={true}><FormularioRol /></ProtectedRoute>} />

          {/* MÓDULO: ASISTENTE IA */}
          <Route path="ia-asistente" element={<ProtectedRoute><IAAsistenteMedico /></ProtectedRoute>} />

          {/* RUTAS DE ERROR INTERNAS AL DASHBOARD */}
          <Route path="unauthorized" element={<Unauthorized />} />
          <Route path="404" element={<NotFound />} />

          {/* Catch-all para rutas no encontradas dentro del dashboard */}
          <Route path="*" element={<Navigate to="/dashboard/404" replace />} />
        </Route>

        {/* ==================== RUTAS DE ERROR GLOBALES ==================== */}
        <Route path="/403" element={<Unauthorized />} />
        <Route path="/404" element={<NotFound />} />

        {/* /ayuda redirige al módulo de Ayuda real del dashboard */}
        <Route path="/ayuda" element={<Navigate to="/dashboard/ayuda" replace />} />

        {/* Catch-all global */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
};

export default AppRoutes;
