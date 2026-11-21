import React from 'react';
import type { MenuProps } from 'antd';
import type { NavigateFunction } from 'react-router-dom';
import {
  DashboardOutlined, UserOutlined, HeartOutlined, MedicineBoxOutlined, CalculatorOutlined,
  TeamOutlined, SettingOutlined, HistoryOutlined, AuditOutlined, ExperimentOutlined, CalendarOutlined,
  BarChartOutlined, SoundOutlined, ApartmentOutlined, QuestionCircleOutlined,
  SafetyCertificateOutlined, FileProtectOutlined, MedicineBoxTwoTone, AlertOutlined, EditOutlined,
  SafetyOutlined, FileTextOutlined, RobotOutlined, ReadOutlined,
} from '@ant-design/icons';
import { authService } from '../../services/authService';

// Verificación de permisos por ruta (codenames exactos del backend).
const checkPermission = (user: any, itemKey: string): boolean => {
  if (user?.rol === 'administrador') return true;

  const routePermissions: Record<string, string> = {
    // Clínicos: recepción no los ve (el backend también se los niega).
    '/dashboard/historia-clinica': 'view_controlprenatal',
    '/dashboard/ia-medica': 'view_imagenecografica',
    '/dashboard/ia-guia': 'view_imagenecografica',
    '/dashboard/ia-asistente': 'view_consultaia',
    '/dashboard/triaje': 'view_triajeenfermeria',
    '/dashboard/pacientes': 'view_paciente',
    '/dashboard/antecedentes': 'view_antecedentepatologico',
    '/dashboard/embarazos': 'view_embarazo',
    '/dashboard/controles': 'view_controlprenatal',
    '/dashboard/partos': 'view_parto',
    '/dashboard/notas-evolucion': 'view_notaevolucion',
    '/dashboard/vacunas': 'view_registrovacuna',
    '/dashboard/ecografias': 'view_ecografia',
    '/dashboard/laboratorios': 'view_examenlaboratorio',
    '/dashboard/calculadoras': 'view_calculohistorial',
    '/dashboard/citas': 'view_cita',
    '/dashboard/reportes': 'view_reportegenerado',
    '/dashboard/reportes/generar': 'add_reportegenerado',
    '/dashboard/reportes/kpis': 'view_dashboardkpi',
    '/dashboard/reportes/indicadores': 'view_dashboardkpi',
    '/dashboard/reportes/auditoria': 'view_auditoriareporte',
    '/dashboard/estadisticas': 'view_dashboardkpi',
    '/dashboard/alertas': 'view_alertamedica',
    '/dashboard/consultorios': 'view_consultorio',
    '/dashboard/roles': 'view_cargo',
    '/dashboard/usuarios': 'view_usuario',
    '/dashboard/access-logs': 'view_registroauditoria',
    '/dashboard/auditoria': 'view_registroauditoria',
    '/dashboard/configuracion': 'view_sistemaconfiguracion',
    '/dashboard/backup': 'view_sistemaconfiguracion',
  };

  // La ruta más específica manda: /dashboard/reportes/kpis no hereda el
  // permiso de /dashboard/reportes.
  const permission = Object.keys(routePermissions)
    .filter(route => itemKey.startsWith(route))
    .sort((a, b) => b.length - a.length)[0];
  if (!permission) return true;
  return authService.hasPermission(routePermissions[permission]);
};

export const buildMainMenuItems = (user: any, navigate: NavigateFunction): MenuProps['items'] => ([
  {
    key: '/dashboard/home',
    icon: <DashboardOutlined />,
    label: 'Panel Principal',
  },
  {
    key: '/dashboard/historia-clinica',
    icon: <FileTextOutlined />,
    label: 'Historial Clínico',
  },
  { type: 'divider' },
  {
    key: 'group-clinico',
    label: 'Gestión Clínica',
    type: 'group',
    children: [
      { key: '/dashboard/triaje', icon: <MedicineBoxOutlined />, label: 'Triaje' },
      { key: '/dashboard/pacientes', icon: <UserOutlined />, label: 'Pacientes' },
      { key: '/dashboard/antecedentes', icon: <FileProtectOutlined />, label: 'Antecedentes' },
      { key: '/dashboard/embarazos', icon: <HeartOutlined />, label: 'Embarazos' },
      { key: '/dashboard/controles', icon: <MedicineBoxOutlined />, label: 'Controles Prenatales' },
      { key: '/dashboard/partos', icon: <ApartmentOutlined />, label: 'Partos' },
      { key: '/dashboard/notas-evolucion', icon: <EditOutlined />, label: 'Notas de Evolución' },
      { key: '/dashboard/vacunas', icon: <MedicineBoxTwoTone />, label: 'Vacunas' },
    ].filter(item => checkPermission(user, item.key as string)),
  },
  {
    key: 'group-estudios',
    label: 'Estudios Auxiliares',
    type: 'group',
    children: [
      { key: '/dashboard/ecografias', icon: <SoundOutlined />, label: 'Ecografías' },
      { key: '/dashboard/laboratorios', icon: <ExperimentOutlined />, label: 'Laboratorio' },
      { key: '/dashboard/ia-medica/imagenes', icon: <RobotOutlined />, label: 'Análisis CNN (IA)' },
      { key: '/dashboard/ia-guia', icon: <ReadOutlined />, label: 'Guía de IA' },
    ].filter(item => checkPermission(user, item.key as string)),
  },
  {
    key: 'group-herramientas',
    label: 'Herramientas',
    type: 'group',
    children: [
      {
        key: 'sub-calculadoras',
        icon: <CalculatorOutlined />,
        label: 'Calculadoras',
        children: [
          { key: '/dashboard/calculadoras', label: 'Calculadoras rápidas' },
          { key: '/dashboard/panel-calculadoras', label: 'Calculadoras especializadas' },
        ],
      },
      { key: '/dashboard/citas', icon: <CalendarOutlined />, label: 'Agenda de Citas' },
      {
        // Centro de reportes: UNA página con pestañas (tiempo real, estadísticas
        // por fecha, KPIs, indicadores, PDF y auditoría); cada pestaña se
        // muestra según el permiso del rol (ver pages/Reportes/CentroReportes).
        key: '/dashboard/reportes',
        icon: <BarChartOutlined />,
        label: 'Centro de reportes',
      },
      { key: '/dashboard/alertas', icon: <AlertOutlined />, label: 'Alertas Médicas' },
    ].filter(item => {
      if (item.key === 'sub-calculadoras') {
        return checkPermission(user, '/dashboard/calculadoras');
      }
      if (item.key === '/dashboard/reportes') {
        // Se ve si el rol puede abrir AL MENOS una pestaña del centro.
        return ['/dashboard/reportes', '/dashboard/estadisticas', '/dashboard/reportes/kpis',
          '/dashboard/reportes/generar', '/dashboard/reportes/auditoria'].some((ruta) => checkPermission(user, ruta));
      }
      return checkPermission(user, item.key as string);
    }),
  },
  { type: 'divider' },
  { key: '/dashboard/consultorios', icon: <SafetyOutlined />, label: 'Consultorios' },
  { key: '/dashboard/roles', icon: <SafetyCertificateOutlined />, label: 'Cargos y permisos' },
  { key: '/dashboard/usuarios', icon: <TeamOutlined />, label: 'Gestión de Usuarios' },
  { key: '/dashboard/access-logs', icon: <HistoryOutlined />, label: 'Logs de Acceso' },
  // Todo lo que hace cada persona, con filtros; antes solo se llegaba desde una pestaña de Reportes.
  { key: '/dashboard/auditoria', icon: <AuditOutlined />, label: 'Auditoría' },
  { key: '/dashboard/configuracion', icon: <SettingOutlined />, label: 'Configuración' },
  {
    key: 'ayuda',
    label: 'Ayuda',
    icon: <QuestionCircleOutlined />,
    onClick: () => navigate('/ayuda'),
  },
  {
    key: '/dashboard/ia-asistente',
    label: 'Asistente IA',
    icon: <RobotOutlined />,
    onClick: () => navigate('/dashboard/ia-asistente'),
  },
].filter(item => {
  if (item && (item as any).type === 'group') {
    return (item as any).children && (item as any).children.length > 0;
  }
  if (item && item.key) {
    return checkPermission(user, item.key as string);
  }
  return true;
}) as any);
