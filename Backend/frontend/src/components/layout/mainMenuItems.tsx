import React from 'react';
import type { MenuProps } from 'antd';
import type { NavigateFunction } from 'react-router-dom';
import {
  DashboardOutlined, UserOutlined, HeartOutlined, MedicineBoxOutlined, CalculatorOutlined,
  TeamOutlined, SettingOutlined, HistoryOutlined, ExperimentOutlined, CalendarOutlined,
  BarChartOutlined, LineChartOutlined, SoundOutlined, ApartmentOutlined, QuestionCircleOutlined,
  SafetyCertificateOutlined, FileProtectOutlined, MedicineBoxTwoTone, AlertOutlined, EditOutlined,
  SafetyOutlined, FileTextOutlined, RobotOutlined,
} from '@ant-design/icons';
import { authService } from '../../services/authService';

// Verificación de permisos por ruta (codenames exactos del backend).
const checkPermission = (user: any, itemKey: string): boolean => {
  if (user?.rol === 'administrador') return true;

  const routePermissions: Record<string, string> = {
    '/dashboard/triaje': 'view_triajeenfermeria',
    '/dashboard/pacientes': 'view_paciente',
    '/dashboard/antecedentes': 'view_paciente',
    '/dashboard/embarazos': 'view_embarazo',
    '/dashboard/controles': 'view_controlprenatal',
    '/dashboard/partos': 'view_parto',
    '/dashboard/notas-evolucion': 'view_notaevolucion',
    '/dashboard/vacunas': 'view_registrovacuna',
    '/dashboard/ecografias': 'view_ecografia',
    '/dashboard/laboratorios': 'view_examenlaboratorio',
    '/dashboard/calculadoras': 'view_calculoclinico',
    '/dashboard/citas': 'view_cita',
    '/dashboard/reportes': 'view_reportegenerado',
    '/dashboard/estadisticas': 'view_dashboardkpi',
    '/dashboard/alertas': 'view_alertamedica',
    '/dashboard/consultorios': 'view_consultorio',
    '/dashboard/roles': 'view_rol',
    '/dashboard/usuarios': 'view_usuario',
    '/dashboard/access-logs': 'view_accesslog',
    '/dashboard/configuracion': 'view_sistemaconfiguracion',
    '/dashboard/backup': 'view_sistemaconfiguracion',
  };

  const permission = Object.keys(routePermissions).find(route => itemKey.startsWith(route));
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
          { key: '/dashboard/calculadoras', label: 'Básicas (FPP, IMC)' },
          { key: '/dashboard/calculadoras-avanzadas', label: 'Avanzadas (Doppler)' },
        ],
      },
      { key: '/dashboard/citas', icon: <CalendarOutlined />, label: 'Agenda de Citas' },
      { key: '/dashboard/reportes', icon: <BarChartOutlined />, label: 'Reportes' },
      { key: '/dashboard/estadisticas', icon: <LineChartOutlined />, label: 'Estadísticas' },
      { key: '/dashboard/alertas', icon: <AlertOutlined />, label: 'Alertas Médicas' },
    ].filter(item => {
      if (item.key === 'sub-calculadoras') {
        return checkPermission(user, '/dashboard/calculadoras');
      }
      return checkPermission(user, item.key as string);
    }),
  },
  { type: 'divider' },
  { key: '/dashboard/consultorios', icon: <SafetyOutlined />, label: 'Consultorios' },
  { key: '/dashboard/roles', icon: <SafetyCertificateOutlined />, label: 'Roles y Permisos' },
  { key: '/dashboard/usuarios', icon: <TeamOutlined />, label: 'Gestión de Usuarios' },
  { key: '/dashboard/access-logs', icon: <HistoryOutlined />, label: 'Logs de Acceso' },
  { key: '/dashboard/configuracion', icon: <SettingOutlined />, label: 'Configuración' },
  {
    key: 'ayuda',
    label: 'Ayuda',
    icon: <QuestionCircleOutlined />,
    onClick: () => navigate('/ayuda'),
  },
  {
    key: 'ia-asistente',
    label: 'IA Assistant',
    icon: <RobotOutlined />,
    onClick: () => navigate('/ia-asistente'),
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
