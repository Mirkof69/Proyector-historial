import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate, useLocation, Outlet } from 'react-router-dom';
import { ConfigProvider, App as AntdApp, Spin, Empty } from 'antd';
import esES from 'antd/locale/es_ES';
import { ThemeProvider } from './contexts/ThemeContext';
import useAntdTheme from './hooks/useAntdTheme';

import { NotificationsProvider } from './contexts/NotificationsContext';
import ErrorBoundary from './components/common/ErrorBoundary';
import PageTransition from './components/common/PageTransition';
import { useAuth } from './hooks/useAuth';

// --- PUBLIC PAGES (eager - needed before auth) ---
import Login from './pages/Login/Login';
import LandingPage from './pages/Dashboard/LandingPage';
import SetupMfa from './pages/SetupMfa/SetupMfa';
import DashboardLayout from './pages/Dashboard/Dashboard';
import NotFound from './pages/NotFound';
import Unauthorized from './pages/Unauthorized';
import { logger } from './utils/logger';

// =============================================================================
// ALL MODULE PAGES ARE LAZY-LOADED
// =============================================================================
const DashboardHome = lazy(() => import('./pages/Dashboard/DashboardHome'));
const DashboardGraficasReales = lazy(() => import('./pages/Dashboard/DashboardGraficasReales'));
const Pacientes = lazy(() => import('./pages/Pacientes/Pacientes'));
const DetallePaciente = lazy(() => import('./pages/Pacientes/DetallePaciente'));
const FormularioPaciente = lazy(() => import('./pages/Pacientes/FormularioPaciente'));
const BusquedaAvanzada = lazy(() => import('./pages/Busqueda/BusquedaAvanzada'));
const GlobalSearch = lazy(() => import('./pages/Busqueda/GlobalSearch'));
const HistoriaClinica = lazy(() => import('./pages/HistoriaClinica/HistoriaClinica'));
const ListaHistoriasClinicas = lazy(() => import('./pages/HistoriaClinica/ListaHistoriasClinicas'));
const Embarazos = lazy(() => import('./pages/Embarazos/Embarazos'));
const DetalleEmbarazo = lazy(() => import('./pages/Embarazos/DetalleEmbarazo'));
const FormularioEmbarazo = lazy(() => import('./pages/Embarazos/FormularioEmbarazo'));
const Controles = lazy(() => import('./pages/Controles/Controles'));
const DetalleControl = lazy(() => import('./pages/Controles/DetalleControl'));
const FormularioControl = lazy(() => import('./pages/Controles/FormularioControl'));
const Ecografias = lazy(() => import('./pages/Ecografias/Ecografias'));
const DetalleEcografia = lazy(() => import('./pages/Ecografias/DetalleEcografia'));
const FormularioEcografia = lazy(() => import('./pages/Ecografias/FormularioEcografia'));
const VisorDICOM = lazy(() => import('./pages/Ecografias/VisorDICOM'));
const ArchivosEcografia = lazy(() => import('./pages/Ecografias/ArchivosEcografia'));
const Laboratorio = lazy(() => import('./pages/Laboratorio/Laboratorio'));
const DetalleLaboratorio = lazy(() => import('./pages/Laboratorio/DetalleLaboratorio'));
const FormularioLaboratorio = lazy(() => import('./pages/Laboratorio/FormularioLaboratorio'));
const TiposExamen = lazy(() => import('./pages/Laboratorio/TiposExamen'));
const ResultadosLaboratorio = lazy(() => import('./pages/Laboratorio/ResultadosLaboratorio'));
const ValoresReferencia = lazy(() => import('./pages/Laboratorio/ValoresReferencia'));
const Citas = lazy(() => import('./pages/Citas/Citas'));
const FormularioCita = lazy(() => import('./pages/Citas/FormularioCita'));
const DetalleCita = lazy(() => import('./pages/Citas/DetalleCita'));
const CalendarioCitas = lazy(() => import('./pages/CalendarioCitas/CalendarioCitas'));
const IAAsistenteMedico = lazy(() => import('./components/IAAsistenteMedico/IAAsistenteMedico'));
const IaMedica = lazy(() => import('./pages/IaMedica/IaMedica'));
const Partos = lazy(() => import('./pages/Partos/Partos'));
const DetalleParto = lazy(() => import('./pages/Partos/DetalleParto'));
const FormularioParto = lazy(() => import('./pages/Partos/FormularioParto'));
const Partograma = lazy(() => import('./pages/Partos/Partograma'));
const ApgarScore = lazy(() => import('./pages/Partos/ApgarScore'));
const ComplicacionesParto = lazy(() => import('./pages/Partos/ComplicacionesParto'));
const RecienNacidos = lazy(() => import('./pages/Partos/RecienNacidos'));
const Reportes = lazy(() => import('./pages/Reportes/Reportes'));
const GenerarReporte = lazy(() => import('./pages/Reportes/GenerarReporte'));
const DetalleReporte = lazy(() => import('./pages/Reportes/DetalleReporte'));
const KPIs = lazy(() => import('./pages/Reportes/KPIs'));
const Indicadores = lazy(() => import('./pages/Reportes/Indicadores'));
const AuditoriaReportes = lazy(() => import('./pages/Reportes/AuditoriaReportes'));
const Calculadoras = lazy(() => import('./pages/Calculadoras/Calculadoras'));
const CalculadorasAvanzadas = lazy(() => import('./pages/CalculadorasAvanzadas/CalculadorasAvanzadas'));
const IndiceCalculadoras = lazy(() => import('./pages/CalculadorasAvanzadas/IndiceCalculadoras'));
const ScoreBishop = lazy(() => import('./pages/CalculadorasAvanzadas/ScoreBishop'));
const IMCGananciaPonderal = lazy(() => import('./pages/CalculadorasAvanzadas/IMCGananciaPonderal'));
const RiesgoPreeclampsia = lazy(() => import('./pages/CalculadorasAvanzadas/RiesgoPreeclampsia'));
const CrecimientoFetal = lazy(() => import('./pages/CalculadorasAvanzadas/CrecimientoFetal'));
const RiesgoCromosomico = lazy(() => import('./pages/CalculadorasAvanzadas/RiesgoCromosomico'));
const DosisMedicamentos = lazy(() => import('./pages/CalculadorasAvanzadas/DosisMedicamentos'));
const HemorragiaObstetrica = lazy(() => import('./pages/CalculadorasAvanzadas/HemorragiaObstetrica'));
const SufrimientoFetal = lazy(() => import('./pages/CalculadorasAvanzadas/SufrimientoFetal'));
const Usuarios = lazy(() => import('./pages/Usuarios/Usuarios'));
const Roles = lazy(() => import('./pages/Roles/Roles'));
const FormularioRol = lazy(() => import('./pages/Roles/FormularioRol'));
const DetalleRol = lazy(() => import('./pages/Roles/DetalleRol'));
const Auditoria = lazy(() => import('./pages/Auditoria/Auditoria'));
const AccessLogs = lazy(() => import('./pages/AccessLogs'));
const Statistics = lazy(() => import('./pages/Statistics'));
const Perfil = lazy(() => import('./pages/Perfil'));
const Configuracion = lazy(() => import('./pages/Configuracion'));
const Ayuda = lazy(() => import('./pages/Ayuda/Ayuda'));
const Evoluciones = lazy(() => import('./pages/Evoluciones/Evoluciones'));
const DetalleEvolucion = lazy(() => import('./pages/Evoluciones/DetalleEvolucion'));
const FormularioEvolucion = lazy(() => import('./pages/Evoluciones/FormularioEvolucion'));
const Antecedentes = lazy(() => import('./pages/Antecedentes/Antecedentes'));
const AntecedentesGinecoObstetricos = lazy(() => import('./pages/Antecedentes/AntecedentesGinecoObstetricos'));
const AntecedentesPatologicos = lazy(() => import('./pages/Antecedentes/AntecedentesPatologicos'));
const FormularioAntecedenteGineco = lazy(() => import('./pages/Antecedentes/FormularioAntecedenteGineco'));
const FormularioAntecedentePatologico = lazy(() => import('./pages/Antecedentes/FormularioAntecedentePatologico'));
const Consultorios = lazy(() => import('./pages/Consultorios/Consultorios'));
const FormularioConsultorio = lazy(() => import('./pages/Consultorios/FormularioConsultorio'));
const DetalleConsultorio = lazy(() => import('./pages/Consultorios/DetalleConsultorio'));
const Triaje = lazy(() => import('./pages/Triaje/Triaje'));
const FormularioTriaje = lazy(() => import('./pages/Triaje/FormularioTriaje'));
const DetalleTriaje = lazy(() => import('./pages/Triaje/DetalleTriaje'));
const Vacunas = lazy(() => import('./pages/Vacunas/Vacunas'));
const FormularioVacuna = lazy(() => import('./pages/Vacunas/FormularioVacuna'));
const DetalleVacuna = lazy(() => import('./pages/Vacunas/DetalleVacuna'));
const TiposVacuna = lazy(() => import('./pages/Vacunas/TiposVacuna'));
const AlertasMedicas = lazy(() => import('./pages/Alertas/AlertasMedicas'));
const DetalleAlerta = lazy(() => import('./pages/Alertas/DetalleAlerta'));
const ConfiguracionAlertas = lazy(() => import('./pages/Alertas/ConfiguracionAlertas'));
const SistemaAlertas = lazy(() => import('./pages/Alertas/SistemaAlertas'));
const NotasEvolucion = lazy(() => import('./pages/NotasEvolucion/NotasEvolucion'));
const FormularioNotaEvolucion = lazy(() => import('./pages/NotasEvolucion/FormularioNotaEvolucion'));
const DetalleNotaEvolucion = lazy(() => import('./pages/NotasEvolucion/DetalleNotaEvolucion'));
const Notificaciones = lazy(() => import('./pages/Notificaciones/Notificaciones'));
const DatabaseBackup = lazy(() => import('./pages/Backup/DatabaseBackup'));

// =============================================================================
// CSS IMPORTS
// =============================================================================
import './styles/global-theme.css';
import './styles/antd-overrides.css';
import './styles/theme-dark.css';
import './index.css';
import './App.css';

/**
 * Componente interno que aplica los tokens de Ant Design segÃƒÂºn el tema
 * Debe estar dentro de ThemeProvider para acceder al contexto de tema
 */
/**
 * Estado vacío consistente para TODAS las tablas, listas y selects del sistema.
 * Un solo lugar → toda la app distingue «no hay datos» de «cargando» o «se rompió».
 * Mensaje según el componente para que sea claro bajo presión clínica.
 */
const renderEmpty = (componentName?: string): React.ReactNode => {
  const descripciones: Record<string, string> = {
    Table: 'No hay registros para mostrar',
    List: 'No hay elementos en esta lista',
    Select: 'Sin opciones disponibles',
    TreeSelect: 'Sin opciones disponibles',
    Cascader: 'Sin opciones disponibles',
    Transfer: 'Sin datos',
  };
  const descripcion = descripciones[componentName ?? ''] ?? 'No hay datos disponibles';
  const compacto = componentName === 'Select' || componentName === 'TreeSelect' || componentName === 'Cascader';
  return (
    <Empty
      image={Empty.PRESENTED_IMAGE_SIMPLE}
      description={descripcion}
      style={compacto ? { margin: '8px 0' } : { padding: '20px 0' }}
    />
  );
};

const ThemedConfigProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const themeConfig = useAntdTheme();

  return (
    <ConfigProvider locale={esES} theme={themeConfig} renderEmpty={renderEmpty}>
      {children}
    </ConfigProvider>
  );
};

// ============================================================================
// 3. COMPONENTE PROTECTOR DE RUTAS (GUARD)
// ============================================================================
interface ProtectedRouteProps {
  children: React.ReactElement;
  requiredPermission?: string;
  requireAdmin?: boolean;
}

const ProtectedRoute = ({ children, requiredPermission, requireAdmin }: ProtectedRouteProps) => {
  const location = useLocation();
  const { isAuthenticated, user: currentUser, hasPermission } = useAuth();

  if (!isAuthenticated) {
    logger.log('Ã°Å¸â€â€™ Acceso denegado - Redirigiendo a login');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check Admin role
  if (requireAdmin && currentUser?.rol !== 'administrador') {
    console.warn('Ã¢â€ºâ€ Acceso denegado. Se requiere administrador');
    return <Navigate to="/dashboard/404" replace />;
  }

  // Check specific permission
  if (requiredPermission && !hasPermission(requiredPermission)) {
    console.warn(`Ã¢â€ºâ€ Acceso denegado. Falta permiso: ${requiredPermission}`);
    return <Navigate to="/dashboard/404" replace />;
  }

  return children;
};

const handleLoginSuccess = () => {
  logger.log('✅ Login exitoso');
};

function App() {
  const { isAuthenticated, logout } = useAuth();

  const handleLogout = () => {
    logout();
    logger.log('👋 Sesión cerrada');
  };

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ThemedConfigProvider>
          <NotificationsProvider>
            <AntdApp>
              <Suspense fallback={<div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Spin size="large" tip="Cargando módulo clínico…"><div /></Spin></div>}>
                <Routes>
                {/* ==================================================================== */}
                {/* RUTAS PÃƒÅ¡BLICAS                                                       */}
                {/* ==================================================================== */}

                {/* LANDING PAGE / HOME PÃƒÅ¡BLICA */}
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

                {/* ==================================================================== */}
                {/* RUTAS PROTEGIDAS (DASHBOARD PRINCIPAL)                              */}
                {/* ==================================================================== */}
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
                  {/* ================================================================= */}
                  {/* DASHBOARD HOME                                                    */}
                  {/* ================================================================= */}
                  <Route index element={<DashboardHome />} />
                  <Route path="home" element={<DashboardHome />} />
                  <Route path="graficas" element={<DashboardGraficasReales />} />
                  <Route path="graficas-reales" element={<DashboardGraficasReales />} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: PACIENTES                                                 */}
                  {/* ================================================================= */}
                  <Route path="pacientes" element={<ProtectedRoute requiredPermission="view_paciente"><Pacientes /></ProtectedRoute>} />
                  <Route path="pacientes/nuevo" element={<ProtectedRoute requiredPermission="add_paciente"><FormularioPaciente /></ProtectedRoute>} />
                  <Route path="pacientes/buscar" element={<ProtectedRoute requiredPermission="view_paciente"><BusquedaAvanzada /></ProtectedRoute>} />
                  <Route path="busqueda/global" element={<GlobalSearch />} />
                  <Route path="busqueda" element={<GlobalSearch />} />
                  <Route path="pacientes/:id" element={<ProtectedRoute requiredPermission="view_paciente"><DetallePaciente /></ProtectedRoute>} />
                  <Route path="pacientes/:id/editar" element={<ProtectedRoute requiredPermission="change_paciente"><FormularioPaciente /></ProtectedRoute>} />
                  <Route path="pacientes/:id/historia" element={<ProtectedRoute requiredPermission="view_paciente"><HistoriaClinica /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* ESTADÃƒ STICAS                                                      */}
                  {/* ================================================================= */}
                  <Route path="estadisticas" element={<Statistics />} />

                  {/* ================================================================= */}
                  {/* LOGS DE ACCESO (SOLO ADMIN O CON PERMISO)                         */}
                  {/* ================================================================= */}
                  <Route path="access-logs" element={<AccessLogs />} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: HISTORIA CLÃƒ NICA                                         */}
                  {/* ================================================================= */}
                  <Route path="historia-clinica" element={<ProtectedRoute requiredPermission="view_paciente"><ListaHistoriasClinicas /></ProtectedRoute>} />
                  <Route path="historia-clinica/:id" element={<ProtectedRoute requiredPermission="view_paciente"><HistoriaClinica /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: EMBARAZOS                                                 */}
                  {/* ================================================================= */}
                  <Route path="embarazos" element={<ProtectedRoute requiredPermission="view_embarazo"><Embarazos /></ProtectedRoute>} />
                  <Route path="embarazos/nuevo" element={<ProtectedRoute requiredPermission="add_embarazo"><FormularioEmbarazo /></ProtectedRoute>} />
                  <Route path="embarazos/:id" element={<ProtectedRoute requiredPermission="view_embarazo"><DetalleEmbarazo /></ProtectedRoute>} />
                  <Route path="embarazos/:id/editar" element={<ProtectedRoute requiredPermission="change_embarazo"><FormularioEmbarazo /></ProtectedRoute>} />
                  <Route path="embarazos/:id/timeline" element={<ProtectedRoute requiredPermission="view_embarazo"><DetalleEmbarazo /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: CONTROLES PRENATALES                                      */}
                  {/* ================================================================= */}
                  <Route path="controles" element={<ProtectedRoute requiredPermission="view_controlprenatal"><Controles /></ProtectedRoute>} />
                  <Route path="controles/nuevo" element={<ProtectedRoute requiredPermission="add_controlprenatal"><FormularioControl /></ProtectedRoute>} />
                  <Route path="controles/:id" element={<ProtectedRoute requiredPermission="view_controlprenatal"><DetalleControl /></ProtectedRoute>} />
                  <Route path="controles/:id/editar" element={<ProtectedRoute requiredPermission="change_controlprenatal"><FormularioControl /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: ECOGRAFÃƒ AS                                                */}
                  {/* ================================================================= */}
                  <Route path="ecografias" element={<ProtectedRoute requiredPermission="view_ecografia"><Ecografias /></ProtectedRoute>} />
                  <Route path="ecografias/nuevo" element={<ProtectedRoute requiredPermission="add_ecografia"><FormularioEcografia /></ProtectedRoute>} />
                  <Route path="ecografias/:id" element={<ProtectedRoute requiredPermission="view_ecografia"><DetalleEcografia /></ProtectedRoute>} />
                  <Route path="ecografias/:id/editar" element={<ProtectedRoute requiredPermission="change_ecografia"><FormularioEcografia /></ProtectedRoute>} />
                  <Route path="ecografias/:id/dicom" element={<ProtectedRoute requiredPermission="view_ecografia"><VisorDICOM /></ProtectedRoute>} />
                  <Route path="ecografias/:id/viewer" element={<ProtectedRoute requiredPermission="view_ecografia"><VisorDICOM /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: LABORATORIO                                               */}
                  {/* ================================================================= */}
                  <Route path="laboratorio" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><Laboratorio /></ProtectedRoute>} />
                  <Route path="laboratorios" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><Laboratorio /></ProtectedRoute>} />
                  <Route path="laboratorios/hemogramas" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><Laboratorio /></ProtectedRoute>} />
                  <Route path="laboratorios/bioquimicas" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><Laboratorio /></ProtectedRoute>} />
                  <Route path="laboratorios/marcadores" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><Laboratorio /></ProtectedRoute>} />
                  <Route path="laboratorio/nuevo" element={<ProtectedRoute requiredPermission="add_examenlaboratorio"><FormularioLaboratorio /></ProtectedRoute>} />
                  <Route path="laboratorio/:id" element={<ProtectedRoute requiredPermission="view_examenlaboratorio"><DetalleLaboratorio /></ProtectedRoute>} />
                  <Route path="laboratorio/:id/editar" element={<ProtectedRoute requiredPermission="change_examenlaboratorio"><FormularioLaboratorio /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: CALCULADORAS                                              */}
                  {/* ================================================================= */}
                  <Route path="calculadoras" element={<ProtectedRoute requiredPermission="view_calculoclinico"><Calculadoras /></ProtectedRoute>} />
                  <Route path="calculadoras/:tipo" element={<ProtectedRoute requiredPermission="view_calculoclinico"><Calculadoras /></ProtectedRoute>} />
                  <Route path="calculadoras-avanzadas" element={<ProtectedRoute requiredPermission="view_calculoclinico"><CalculadorasAvanzadas /></ProtectedRoute>} />
                  <Route path="calculadoras-avanzadas/:tipo" element={<ProtectedRoute requiredPermission="view_calculoclinico"><CalculadorasAvanzadas /></ProtectedRoute>} />

                  {/* PANEL/Ãƒ NDICE DE CALCULADORAS AVANZADAS */}
                  <Route path="panel-calculadoras" element={<ProtectedRoute requiredPermission="view_calculoclinico"><IndiceCalculadoras /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: CITAS Y AGENDA                                            */}
                  {/* ================================================================= */}
                  <Route path="citas" element={<ProtectedRoute requiredPermission="view_cita"><Citas /></ProtectedRoute>} />
                  <Route path="citas/nuevo" element={<ProtectedRoute requiredPermission="add_cita"><FormularioCita /></ProtectedRoute>} />
                  <Route path="citas/:id" element={<ProtectedRoute requiredPermission="view_cita"><DetalleCita /></ProtectedRoute>} />
                  <Route path="citas/:id/editar" element={<ProtectedRoute requiredPermission="change_cita"><FormularioCita /></ProtectedRoute>} />
                  <Route path="citas/calendario" element={<ProtectedRoute requiredPermission="view_cita"><CalendarioCitas /></ProtectedRoute>} />
                  <Route path="citas/hoy" element={<ProtectedRoute requiredPermission="view_cita"><Citas /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: PARTOS                                                    */}
                  {/* ================================================================= */}
                  <Route path="partos" element={<ProtectedRoute requiredPermission="view_parto"><Partos /></ProtectedRoute>} />
                  <Route path="partos/nuevo" element={<ProtectedRoute requiredPermission="add_parto"><FormularioParto /></ProtectedRoute>} />
                  <Route path="partos/:id" element={<ProtectedRoute requiredPermission="view_parto"><DetalleParto /></ProtectedRoute>} />
                  <Route path="partos/:id/editar" element={<ProtectedRoute requiredPermission="change_parto"><FormularioParto /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: REPORTES Y ESTADÃƒ STICAS                                   */}
                  {/* ================================================================= */}
                  <Route path="reportes" element={<ProtectedRoute requiredPermission="view_reportegenerado"><Reportes /></ProtectedRoute>} />
                  <Route path="reportes/generar" element={<ProtectedRoute requiredPermission="add_reportegenerado"><GenerarReporte /></ProtectedRoute>} />
                  <Route path="reportes/pdf" element={<Navigate to="/dashboard/reportes/generar" replace />} />
                  <Route path="reportes/pdf-automatico" element={<Navigate to="/dashboard/reportes/generar" replace />} />
                  <Route path="reportes/:id" element={<ProtectedRoute requiredPermission="view_reportegenerado"><DetalleReporte /></ProtectedRoute>} />
                  <Route path="reportes/historial" element={<ProtectedRoute requiredPermission="view_reportegenerado"><Reportes /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: IA MEDICA Y CNN                                           */}
                  {/* ================================================================= */}
                  <Route path="ia-medica/imagenes" element={<IaMedica />} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: ADMINISTRACIÃƒâ€œN Y SISTEMA                                  */}
                  {/* ================================================================= */}
                  <Route path="usuarios" element={<ProtectedRoute requiredPermission="view_usuario"><Usuarios /></ProtectedRoute>} />
                  <Route path="auditoria" element={<ProtectedRoute requiredPermission="view_usuario"><Auditoria /></ProtectedRoute>} />
                  <Route path="perfil" element={<Perfil />} />
                  <Route path="configuracion" element={<ProtectedRoute requiredPermission="view_sistemaconfiguracion"><Configuracion /></ProtectedRoute>} />
                  <Route path="ayuda" element={<Ayuda />} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: NOTIFICACIONES                                            */}
                  {/* ================================================================= */}
                  <Route path="notificaciones" element={<Notificaciones />} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: BACKUP                                                    */}
                  {/* ================================================================= */}
                  <Route path="backup" element={<ProtectedRoute requiredPermission="view_sistemaconfiguracion"><DatabaseBackup /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: EVOLUCIONES                                               */}
                  {/* ================================================================= */}
                  <Route path="evoluciones" element={<Evoluciones />} />
                  <Route path="evoluciones/nuevo" element={<FormularioEvolucion />} />
                  <Route path="evoluciones/:id" element={<DetalleEvolucion />} />
                  <Route path="evoluciones/:id/editar" element={<FormularioEvolucion />} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: ANTECEDENTES                                              */}
                  {/* ================================================================= */}
                  <Route path="antecedentes" element={<Antecedentes />} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: CONSULTORIOS                                              */}
                  {/* ================================================================= */}
                  <Route path="consultorios" element={<Consultorios />} />
                  <Route path="consultorios/nuevo" element={<FormularioConsultorio />} />
                  <Route path="consultorios/:id" element={<DetalleConsultorio />} />
                  <Route path="consultorios/editar/:id" element={<FormularioConsultorio />} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: TRIAJE DE ENFERMERÃƒ A                                      */}
                  {/* ================================================================= */}
                  <Route path="triaje" element={<ProtectedRoute requiredPermission="view_triajeenfermeria"><Triaje /></ProtectedRoute>} />
                  <Route path="triaje/nuevo" element={<ProtectedRoute requiredPermission="add_triajeenfermeria"><FormularioTriaje /></ProtectedRoute>} />
                  <Route path="triaje/:id" element={<ProtectedRoute requiredPermission="view_triajeenfermeria"><DetalleTriaje /></ProtectedRoute>} />
                  <Route path="triaje/:id/editar" element={<ProtectedRoute requiredPermission="change_triajeenfermeria"><FormularioTriaje /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: VACUNAS                                                   */}
                  {/* ================================================================= */}
                  <Route path="vacunas" element={<ProtectedRoute requiredPermission="view_registrovacuna"><Vacunas /></ProtectedRoute>} />
                  <Route path="vacunas/nuevo" element={<ProtectedRoute requiredPermission="add_registrovacuna"><FormularioVacuna /></ProtectedRoute>} />
                  <Route path="vacunas/:id" element={<ProtectedRoute requiredPermission="view_registrovacuna"><DetalleVacuna /></ProtectedRoute>} />
                  <Route path="vacunas/:id/editar" element={<ProtectedRoute requiredPermission="change_registrovacuna"><FormularioVacuna /></ProtectedRoute>} />
                  <Route path="vacunas/tipos" element={<ProtectedRoute requiredPermission="view_tipovacuna"><TiposVacuna /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: ALERTAS MÃƒâ€°DICAS                                           */}
                  {/* ================================================================= */}
                  <Route path="alertas" element={<ProtectedRoute requiredPermission="view_alertamedica"><AlertasMedicas /></ProtectedRoute>} />
                  <Route path="alertas/:id" element={<ProtectedRoute requiredPermission="view_alertamedica"><DetalleAlerta /></ProtectedRoute>} />
                  <Route path="alertas/configuracion" element={<ProtectedRoute requiredPermission="change_alertamedica"><ConfiguracionAlertas /></ProtectedRoute>} />
                  <Route path="alertas/sistema" element={<ProtectedRoute requiredPermission="view_alertamedica"><SistemaAlertas /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: NOTAS DE EVOLUCIÃƒâ€œN                                        */}
                  {/* ================================================================= */}
                  <Route path="notas-evolucion" element={<ProtectedRoute requiredPermission="view_notaevolucion"><NotasEvolucion /></ProtectedRoute>} />
                  <Route path="notas-evolucion/nuevo" element={<ProtectedRoute requiredPermission="add_notaevolucion"><FormularioNotaEvolucion /></ProtectedRoute>} />
                  <Route path="notas-evolucion/:id" element={<ProtectedRoute requiredPermission="view_notaevolucion"><DetalleNotaEvolucion /></ProtectedRoute>} />
                  <Route path="notas-evolucion/:id/editar" element={<ProtectedRoute requiredPermission="change_notaevolucion"><FormularioNotaEvolucion /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* CALCULADORAS AVANZADAS INDIVIDUALES                               */}
                  {/* ================================================================= */}
                  <Route path="calculadoras/bishop" element={<ProtectedRoute requiredPermission="view_scorebishop"><ScoreBishop /></ProtectedRoute>} />
                  <Route path="calculadoras/imc-ganancia" element={<ProtectedRoute requiredPermission="view_calculadora"><IMCGananciaPonderal /></ProtectedRoute>} />
                  <Route path="calculadoras/preeclampsia" element={<ProtectedRoute requiredPermission="view_riesgopreeclampsia"><RiesgoPreeclampsia /></ProtectedRoute>} />
                  <Route path="calculadoras/crecimiento-fetal" element={<ProtectedRoute requiredPermission="view_crecimientofetal"><CrecimientoFetal /></ProtectedRoute>} />
                  <Route path="calculadoras/riesgo-cromosomico" element={<ProtectedRoute requiredPermission="view_riesgocromosomico"><RiesgoCromosomico /></ProtectedRoute>} />
                  <Route path="calculadoras/dosis-medicamentos" element={<ProtectedRoute requiredPermission="view_dosismedicamentos"><DosisMedicamentos /></ProtectedRoute>} />
                  <Route path="calculadoras/hemorragia-obstetrica" element={<ProtectedRoute requiredPermission="view_hemorragiaobstetrica"><HemorragiaObstetrica /></ProtectedRoute>} />
                  <Route path="calculadoras/sufrimiento-fetal" element={<ProtectedRoute requiredPermission="view_sufrimientofetal"><SufrimientoFetal /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: PARTOS EXTENDIDO                                          */}
                  {/* ================================================================= */}
                  <Route path="partos/:id/partograma" element={<ProtectedRoute requiredPermission="view_registropartograma"><Partograma /></ProtectedRoute>} />
                  <Route path="partos/:id/apgar" element={<ProtectedRoute requiredPermission="view_apgarscoredetallado"><ApgarScore /></ProtectedRoute>} />
                  <Route path="partos/:id/complicaciones" element={<ProtectedRoute requiredPermission="view_complicacionparto"><ComplicacionesParto /></ProtectedRoute>} />
                  <Route path="partos/:id/recien-nacido" element={<ProtectedRoute requiredPermission="view_reciennacido"><RecienNacidos /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: LABORATORIO EXTENDIDO                                     */}
                  {/* ================================================================= */}
                  <Route path="laboratorio/tipos-examen" element={<ProtectedRoute requiredPermission="view_tipoexamen"><TiposExamen /></ProtectedRoute>} />
                  <Route path="laboratorio/resultados" element={<ProtectedRoute requiredPermission="view_resultadolaboratorio"><ResultadosLaboratorio /></ProtectedRoute>} />
                  <Route path="laboratorio/valores-referencia" element={<ProtectedRoute requiredPermission="view_valorreferencia"><ValoresReferencia /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: ANTECEDENTES DETALLADO                                    */}
                  {/* ================================================================= */}
                  <Route path="antecedentes/gineco-obstetricos" element={<ProtectedRoute requiredPermission="view_antecedenteginecoobstetrico"><AntecedentesGinecoObstetricos /></ProtectedRoute>} />
                  <Route path="antecedentes/gineco-obstetricos/nuevo" element={<ProtectedRoute requiredPermission="add_antecedenteginecoobstetrico"><FormularioAntecedenteGineco /></ProtectedRoute>} />
                  <Route path="antecedentes/gineco-obstetricos/:id/editar" element={<ProtectedRoute requiredPermission="change_antecedenteginecoobstetrico"><FormularioAntecedenteGineco /></ProtectedRoute>} />
                  <Route path="antecedentes/patologicos" element={<ProtectedRoute requiredPermission="view_antecedentepatologico"><AntecedentesPatologicos /></ProtectedRoute>} />
                  <Route path="antecedentes/patologicos/nuevo" element={<ProtectedRoute requiredPermission="add_antecedentepatologico"><FormularioAntecedentePatologico /></ProtectedRoute>} />
                  <Route path="antecedentes/patologicos/:id/editar" element={<ProtectedRoute requiredPermission="change_antecedentepatologico"><FormularioAntecedentePatologico /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: ECOGRAFÃƒ AS EXTENDIDO                                      */}
                  {/* ================================================================= */}
                  <Route path="ecografias/:id/archivos" element={<ProtectedRoute requiredPermission="view_archivoecografia"><ArchivosEcografia /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: REPORTES EXTENDIDO                                        */}
                  {/* ================================================================= */}
                  <Route path="reportes/kpis" element={<ProtectedRoute requiredPermission="view_indicadorkpi"><KPIs /></ProtectedRoute>} />
                  <Route path="reportes/indicadores" element={<ProtectedRoute requiredPermission="view_indicadorkpi"><Indicadores /></ProtectedRoute>} />
                  <Route path="reportes/auditoria" element={<ProtectedRoute requiredPermission="view_auditoriareporte"><AuditoriaReportes /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃƒâ€œDULO: ROLES Y PERMISOS                                          */}
                  {/* ================================================================= */}
                  <Route path="roles" element={<ProtectedRoute requireAdmin={true}><Roles /></ProtectedRoute>} />
                  <Route path="roles/nuevo" element={<ProtectedRoute requireAdmin={true}><FormularioRol /></ProtectedRoute>} />
                  <Route path="roles/:id" element={<ProtectedRoute requireAdmin={true}><DetalleRol /></ProtectedRoute>} />
                  <Route path="roles/:id/editar" element={<ProtectedRoute requireAdmin={true}><FormularioRol /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* MÃ“DULO: ASISTENTE IA                                             */}
                  {/* ================================================================= */}
                  <Route path="ia-asistente" element={<ProtectedRoute><IAAsistenteMedico /></ProtectedRoute>} />

                  {/* ================================================================= */}
                  {/* RUTAS DE ERROR INTERNAS AL DASHBOARD                             */}
                  {/* ================================================================= */}
                  <Route path="unauthorized" element={<Unauthorized />} />
                  <Route path="404" element={<NotFound />} />

                  {/* Catch-all para rutas no encontradas dentro del dashboard */}
                  <Route path="*" element={<Navigate to="/dashboard/404" replace />} />
                </Route>

                {/* ==================================================================== */}
                {/* RUTAS DE ERROR GLOBALES                                              */}
                {/* ==================================================================== */}
                <Route path="/403" element={<Unauthorized />} />
                <Route path="/404" element={<NotFound />} />

                {/* ==================================================================== */}
                {/* RUTAS ADICIONALES FUERA DEL DASHBOARD                                */}
                {/* ==================================================================== */}
                {/* /ayuda redirige al módulo de Ayuda real del dashboard */}
                <Route path="/ayuda" element={<Navigate to="/dashboard/ayuda" replace />} />

                {/* Catch-all global */}
                <Route path="*" element={<NotFound />} />

              </Routes>
              </Suspense>
            </AntdApp>
          </NotificationsProvider>
        </ThemedConfigProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;


