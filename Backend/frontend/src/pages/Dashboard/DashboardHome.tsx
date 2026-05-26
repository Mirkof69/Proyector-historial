import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Typography, Divider, Button, Alert, Row, Col } from 'antd';
import { ReloadOutlined, RobotOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/es';

import { authService } from '../../services/authService';
import { citasService } from '../../services/citasService';
import { reportesService } from '../../services/reportesService';
import activityLogsService from '../../services/activityLogsService';
import './DashboardHome.css';
import { IAAsistenteMedico } from '../../components/IAAsistenteMedico/IAAsistenteMedico';
import { GlobalLoader } from '../../components/common/GlobalLoader';
import DashboardHeader from './components/dashboard/DashboardHeader';
import DashboardStatsCards from './components/dashboard/DashboardStatsCards';
import DashboardQuickAccess from './components/dashboard/DashboardQuickAccess';
import DashboardAgenda from './components/dashboard/DashboardAgenda';
import DashboardTendencias from './components/dashboard/DashboardTendencias';
import DashboardActividadReciente from './components/dashboard/DashboardActividadReciente';
import DashboardAlertasMedicas from './components/dashboard/DashboardAlertasMedicas';

dayjs.extend(relativeTime);
dayjs.locale('es');

const { Text } = Typography;

interface DashboardStats {
  total_pacientes: number;
  pacientes_nuevos_mes: number;
  embarazos_activos: number;
  embarazos_riesgo_alto: number;
  controles_hoy: number;
  alertas_pendientes: number;
  citas_hoy_count: number;
}

interface ActividadReciente {
  id: number;
  usuario: string;
  accion: string;
  fecha: string;
  tipo: 'info' | 'warning' | 'success' | 'danger';
  _uniqueKey?: string;
}

interface CitaHoy {
  id: number;
  paciente_nombre: string;
  hora: string;
  motivo: string;
  estado: string;
  _uniqueKey?: string;
}

interface AlertaMedica {
  id: number;
  titulo: string;
  mensaje: string;
  tipo: 'critica' | 'urgente' | 'moderada' | 'info';
  paciente_nombre?: string;
  paciente_id?: number;
  fecha_creacion: string;
  requiere_accion_inmediata?: boolean;
  _uniqueKey?: string;
}

const DashboardHome: React.FC = () => {
  const navigate = useNavigate();
  const user = authService.getCurrentUser();

  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    total_pacientes: 0,
    pacientes_nuevos_mes: 0,
    embarazos_activos: 0,
    embarazos_riesgo_alto: 0,
    controles_hoy: 0,
    alertas_pendientes: 0,
    citas_hoy_count: 0
  });
  const [actividades, setActividades] = useState<ActividadReciente[]>([]);
  const [citasHoy, setCitasHoy] = useState<CitaHoy[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [alertasMedicas, setAlertasMedicas] = useState<AlertaMedica[]>([]);

  const cardPermissions: Record<string, string> = useMemo(() => ({
    'Pacientes': 'view_paciente',
    'Controles': 'view_controlprenatal',
    'Agenda de Citas': 'view_cita',
    'Reportes': 'view_reportegenerado',
    'Calculadoras': 'view_calculoclinico',
    'Gestión de Usuarios': 'view_usuario',
    'Triaje': 'view_triaje',
    'Vacunas': 'view_vacuna',
    'Evoluciones': 'view_evolucion',
  }), []);

  const handleNavigate = useCallback((path: string, cardTitle: string) => {
    if (path === '/perfil') {
      navigate(path);
      return;
    }

    const requiredPermission = cardPermissions[cardTitle];
    if (requiredPermission) {
      if (authService.hasPermission(requiredPermission)) {
        navigate(path);
      } else {
        navigate('/dashboard/404');
      }
      return;
    }

    navigate(path);
  }, [navigate, cardPermissions]);

  const showQuickAccess = useCallback((cardTitle: string): boolean => {
    const requiredPermission = cardPermissions[cardTitle];
    if (!requiredPermission) return true;
    return authService.hasPermission(requiredPermission);
  }, [cardPermissions]);

  const cargarDatosDashboard = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    setError(null);
    const startTime = performance.now();

    try {
      const [statsBasicas, citasData, logsResponse] = await Promise.all([
        reportesService.obtenerStatsBasicas(),
        authService.hasPermission('view_cita') ? citasService.listar().catch(() => []) : Promise.resolve([]),
        activityLogsService.getAccessLogs({ page_size: 5 }).catch(() => ({ results: [] }))
      ]);

      let alertas: any[] = [];
      if (statsBasicas.alertas_pendientes > 0 || statsBasicas.embarazos_riesgo_alto > 0) {
        alertas = await reportesService.getAlertasActivas().catch(() => []);
      }

      const hoy = dayjs().format('YYYY-MM-DD');
      const citasHoyData = Array.isArray(citasData) ? citasData.filter((c: any) =>
        dayjs(c.fecha_hora || c.fecha).format('YYYY-MM-DD') === hoy
      ) : [];

      setStats({
        total_pacientes: statsBasicas.total_pacientes || 0,
        pacientes_nuevos_mes: statsBasicas.pacientes_nuevos_mes || 0,
        embarazos_activos: statsBasicas.embarazos_activos || 0,
        embarazos_riesgo_alto: statsBasicas.embarazos_riesgo_alto || 0,
        controles_hoy: statsBasicas.controles_hoy || 0,
        alertas_pendientes: statsBasicas.alertas_pendientes || statsBasicas.embarazos_riesgo_alto || 0,
        citas_hoy_count: statsBasicas.citas_hoy_count || 0
      });

      const logsReales = logsResponse.results || [];
      const actividadesConKeys = logsReales.map((log: any, index: number) => ({
        id: log.id,
        usuario: log.user_name || log.usuario || 'Sistema',
        accion: log.details || log.accion || log.action || `Evento: ${log.modulo || 'sistema'}`,
        fecha: log.created_at || log.fecha,
        tipo: ((log.action === 'login' || log.accion === 'crear') ? 'success' :
          (log.action === 'logout' || log.accion === 'eliminar') ? 'warning' :
            log.accion === 'eliminar' || log.action === 'delete' ? 'danger' : 'info') as 'info' | 'warning' | 'success' | 'danger',
        _uniqueKey: `log-${log.id || index}-${Date.now()}`
      }));

      setActividades(actividadesConKeys as any);

      const citasHoyFormateadas = citasHoyData.slice(0, 5).map((cita: any, index: number) => ({
        id: cita.id,
        paciente_nombre: cita.paciente_nombre || `Paciente ${cita.paciente}`,
        hora: dayjs(cita.fecha_hora || cita.fecha).format('HH:mm'),
        motivo: cita.motivo || cita.tipo || 'Consulta',
        estado: cita.estado || 'PENDIENTE',
        _uniqueKey: `cita-${cita.id}-${index}-${Date.now()}`
      }));

      setCitasHoy(citasHoyFormateadas);

      const diasMes = dayjs().daysInMonth();
      const diasData = [];

      for (let i = 1; i <= diasMes; i++) {
        const fechaDia = dayjs().date(i).format('YYYY-MM-DD');
        if (dayjs(fechaDia).isAfter(dayjs())) break;

        const pacientesDia = 0;
        const citasDia = Array.isArray(citasData) ? citasData.filter((c: any) => {
          const fechaCita = dayjs(c.fecha_hora || c.fecha).format('YYYY-MM-DD');
          return fechaCita === fechaDia;
        }).length : 0;

        if (pacientesDia > 0 || citasDia > 0 || i === dayjs().date()) {
          diasData.push({ name: `Día ${i}`, pacientes: pacientesDia, citas: citasDia });
        }
      }

      if (diasData.length === 0) {
        diasData.push({ name: `Día ${dayjs().date()}`, pacientes: 0, citas: 0 });
      }

      setChartData(diasData);

      const alertasConKeys = alertas.slice(0, 5).map((alerta: any, index: number) => ({
        ...alerta,
        _uniqueKey: `alerta-${alerta.id}-${index}-${Date.now()}`
      }));
      setAlertasMedicas(alertasConKeys);

      if (alertas.length > alertasMedicas.length && alertasMedicas.length > 0) {
        try {
          const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');
          audio.volume = 0.3;
          audio.play().catch(() => {});
        } catch (e) {}
      }

      const endTime = performance.now();
      const loadTime = ((endTime - startTime) / 1000).toFixed(2);

      setLastUpdated(new Date());
      setLoading(false);
    } catch (err) {
      if (!isSilent) setError("No se pudo conectar con el servicio de estadísticas.");
      setLoading(false);
    }
  }, [alertasMedicas.length]);

  useEffect(() => {
    cargarDatosDashboard();
    const interval = setInterval(() => { cargarDatosDashboard(true); }, 30000);
    return () => clearInterval(interval);
  }, [cargarDatosDashboard]);

  const handleSearch = useCallback((value: string) => {
    if (value.trim()) { navigate(`/dashboard/pacientes?search=${value}`); }
  }, [navigate]);

  if (loading && !lastUpdated) {
    return <GlobalLoader tip="Sincronizando datos clínicos…" className="dashboard-loading-container" />;
  }

  if (error) {
    return (
      <div style={{ padding: 40 }}>
        <Alert
          message="Error de Conexión"
          description={error}
          type="error"
          showIcon
          action={<Button icon={<ReloadOutlined />} onClick={() => cargarDatosDashboard()}>Reintentar</Button>}
        />
      </div>
    );
  }

  return (
    <div className="dashboard-container animate-fade-in">
      <DashboardHeader user={user} onSearch={handleSearch} />
      <DashboardStatsCards stats={stats} />
      <DashboardQuickAccess showQuickAccess={showQuickAccess} onNavigate={handleNavigate} />
      <DashboardAgenda citasHoy={citasHoy} />
      <DashboardTendencias chartData={chartData} />

      <Divider orientation="left" style={{ fontSize: 18, fontWeight: 600, marginTop: 40 }}>
        🤖 Asistente Médico con Inteligencia Artificial
      </Divider>

      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <IAAsistenteMedico />
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        <DashboardActividadReciente actividades={actividades} />
        <DashboardAlertasMedicas alertasMedicas={alertasMedicas} />
      </Row>

      <div style={{ marginTop: 40, textAlign: 'center', color: '#888' }}>
        <Divider />
        <Text type="secondary">
          Sistema de Historial Clínico Gineco-Obstétrico • Última actualización: {lastUpdated ? dayjs(lastUpdated).format('DD/MM/YYYY HH:mm:ss') : '-'}
        </Text>
      </div>
    </div>
  );
};

export default DashboardHome;
