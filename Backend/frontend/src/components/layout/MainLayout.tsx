/**
 * =============================================================================
 * MAIN LAYOUT - ESTRUCTURA PRINCIPAL
 * =============================================================================
 * Este componente define el esqueleto de la aplicación:
 * 1. Sidebar Lateral (Navegación)
 * 2. Header Superior (Usuario, Temas, Notificaciones)
 * 3. Content Area (Donde se renderizan las páginas)
 * 4. Footer (Pie de página)
 * * Características:
 * - Completamente Responsive (Mobile-First)
 * - Integración con ThemeContext para cambio de colores
 * - Menú dinámico basado en roles de usuario
 * - Manejo de estado colapsable del menú
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Dropdown, Avatar, Space, Drawer } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  UserOutlined,
  HeartOutlined,
  MedicineBoxOutlined,
  CalculatorOutlined,
  TeamOutlined,
  LogoutOutlined,
  SettingOutlined,
  HistoryOutlined,
  BgColorsOutlined,
  MoonOutlined,
  SunOutlined,
  ExperimentOutlined,
  CalendarOutlined,
  BarChartOutlined,
  LineChartOutlined,
  SoundOutlined,
  ApartmentOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  QuestionCircleOutlined,
  SafetyCertificateOutlined,
  FileProtectOutlined,
  MedicineBoxTwoTone,
  AlertOutlined,
  EditOutlined,
  SafetyOutlined,
  FileTextOutlined,
  RobotOutlined
} from '@ant-design/icons';
import type { MenuProps } from 'antd';

// Importaciones de servicios y contextos
import { authService } from '../../services/authService';
import { useTheme } from '../../contexts/ThemeContext'; // Asegúrate de tener este contexto o elimínalo si no lo usas

import './MainLayout.css'; // Archivo CSS para estilos específicos
import NotificationDropdown from './NotificationDropdown';

const { Header, Sider, Content, Footer } = Layout;

// Interfaz de props
interface MainLayoutProps {
  children: React.ReactNode;
  onLogout?: () => void; // Opcional, si se pasa desde arriba
}

const currentYear = new Date().getFullYear();

const MainLayout: React.FC<MainLayoutProps> = ({ children, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authService.getCurrentUser();

  // Hook de Tema (Si no tienes ThemeContext, puedes usar valores fijos o un estado local simple)
  // Si da error, comenta estas líneas y usa colores fijos abajo.
  const { theme, themeName, setTheme, fontScale, setFontScale } = useTheme();

  // Estados locales
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 992);
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false);

  // Efecto para detectar cambio de tamaño de pantalla (Responsive)
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 992;
      setIsMobile(mobile);
      if (!mobile) {
        setMobileDrawerVisible(false); // Cerrar drawer si crece la pantalla
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // ============================================================================
  // DEFINICIÓN DEL MENÚ (ITEMS)
  // ============================================================================

  // Función helper para navegar
  const handleMenuClick: MenuProps['onClick'] = (e) => {
    if (isMobile) setMobileDrawerVisible(false); // Cerrar menú en móvil al hacer click
    navigate(e.key);
  };

  // Función helper para verificar permisos
  const checkPermission = (itemKey: string): boolean => {
    // Si es administrador, tiene acceso a todo
    if (user?.rol === 'administrador') return true;

    // Mapeo de rutas a permisos (CODENAMES EXACTOS DEL BACKEND)
    const routePermissions: Record<string, string> = {
      // Módulos Clínicos
      '/dashboard/triaje': 'view_triajeenfermeria',
      '/dashboard/pacientes': 'view_paciente',
      '/dashboard/antecedentes': 'view_paciente',
      '/dashboard/embarazos': 'view_embarazo',
      '/dashboard/controles': 'view_controlprenatal',
      '/dashboard/partos': 'view_parto',
      '/dashboard/notas-evolucion': 'view_notaevolucion',
      '/dashboard/vacunas': 'view_registrovacuna',

      // Estudios
      '/dashboard/ecografias': 'view_ecografia',
      '/dashboard/laboratorios': 'view_examenlaboratorio',

      // Herramientas
      '/dashboard/calculadoras': 'view_calculoclinico',
      '/dashboard/citas': 'view_cita',
      '/dashboard/reportes': 'view_reportegenerado',
      '/dashboard/estadisticas': 'view_dashboardkpi',
      '/dashboard/alertas': 'view_alertamedica',

      // Administrativo
      '/dashboard/consultorios': 'view_consultorio',
      '/dashboard/roles': 'view_rol',
      '/dashboard/usuarios': 'view_usuario',
      '/dashboard/access-logs': 'view_accesslog',
      '/dashboard/configuracion': 'view_sistemaconfiguracion',
      '/dashboard/backup': 'view_sistemaconfiguracion',
    };

    // Si la ruta no requiere permiso específico (ej: Home, Perfil), permitir
    const permission = Object.keys(routePermissions).find(route => itemKey.startsWith(route));
    if (!permission) return true;

    // Verificar permiso específico
    return authService.hasPermission(routePermissions[permission]);
  };

  const menuItems: MenuProps['items'] = [
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
    {
      type: 'divider',
    },
    {
      key: 'group-clinico',
      label: 'Gestión Clínica',
      type: 'group',
      children: [
        {
          key: '/dashboard/triaje',
          icon: <MedicineBoxOutlined />,
          label: 'Triaje',
        },
        {
          key: '/dashboard/pacientes',
          icon: <UserOutlined />,
          label: 'Pacientes',
        },
        {
          key: '/dashboard/antecedentes',
          icon: <FileProtectOutlined />,
          label: 'Antecedentes',
        },
        {
          key: '/dashboard/embarazos',
          icon: <HeartOutlined />,
          label: 'Embarazos',
        },
        {
          key: '/dashboard/controles',
          icon: <MedicineBoxOutlined />,
          label: 'Controles Prenatales',
        },
        {
          key: '/dashboard/partos',
          icon: <ApartmentOutlined />,
          label: 'Partos',
        },
        {
          key: '/dashboard/notas-evolucion',
          icon: <EditOutlined />,
          label: 'Notas de Evolución',
        },
        {
          key: '/dashboard/vacunas',
          icon: <MedicineBoxTwoTone />,
          label: 'Vacunas',
        },
      ].filter(item => checkPermission(item.key as string))
    },
    {
      key: 'group-estudios',
      label: 'Estudios Auxiliares',
      type: 'group',
      children: [
        {
          key: '/dashboard/ecografias',
          icon: <SoundOutlined />,
          label: 'Ecografías',
        },
        {
          key: '/dashboard/laboratorios',
          icon: <ExperimentOutlined />,
          label: 'Laboratorio',
        },
        {
          key: '/dashboard/ia-medica/imagenes',
          icon: <RobotOutlined />,
          label: 'Análisis CNN (IA)',
        },
      ].filter(item => checkPermission(item.key as string))
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
            {
              key: '/dashboard/calculadoras',
              label: 'Básicas (FPP, IMC)',
            },
            {
              key: '/dashboard/calculadoras-avanzadas',
              label: 'Avanzadas (Doppler)',
            },
          ],
        },
        {
          key: '/dashboard/citas',
          icon: <CalendarOutlined />,
          label: 'Agenda de Citas',
        },
        {
          key: '/dashboard/reportes',
          icon: <BarChartOutlined />,
          label: 'Reportes',
        },
        {
          key: '/dashboard/estadisticas',
          icon: <LineChartOutlined />,
          label: 'Estadísticas',
        },
        {
          key: '/dashboard/alertas',
          icon: <AlertOutlined />,
          label: 'Alertas Médicas',
        },
      ].filter(item => {
        // Validación especial para submenú calculadoras
        if (item.key === 'sub-calculadoras') {
          return checkPermission('/dashboard/calculadoras');
        }
        return checkPermission(item.key as string);
      })
    },
    // Sección Administrativa (Visible solo si tiene permisos explícitos)
    {
      type: 'divider',
    },
    {
      key: '/dashboard/consultorios',
      icon: <SafetyOutlined />,
      label: 'Consultorios',
    },
    {
      key: '/dashboard/roles',
      icon: <SafetyCertificateOutlined />,
      label: 'Roles y Permisos',
    },
    {
      key: '/dashboard/usuarios',
      icon: <TeamOutlined />,
      label: 'Gestión de Usuarios',
    },
    {
      key: '/dashboard/access-logs',
      icon: <HistoryOutlined />,
      label: 'Logs de Acceso',
    },
    {
      key: '/dashboard/configuracion',
      icon: <SettingOutlined />,
      label: 'Configuración',
    },
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
    // Filter out groups that ended up empty
    if (item && (item as any).type === 'group') {
      return (item as any).children && (item as any).children.length > 0;
    }
    // Filter specific items
    if (item && item.key) {
      return checkPermission(item.key as string);
    }
    return true;
  }) as any;

  // ============================================================================
  // MENÚS DESPLEGABLES (HEADER)
  // ============================================================================

  const themeMenuItems: MenuProps['items'] = [
    {
      key: 'normal',
      label: <Space><SunOutlined style={{ color: '#1890ff' }} /> Tema Claro</Space>,
      onClick: () => setTheme('normal'),
    },
    {
      key: 'dark',
      label: <Space><MoonOutlined style={{ color: '#faad14' }} /> Tema Oscuro</Space>,
      onClick: () => setTheme('dark'),
    },
    {
      key: 'mocha',
      label: <Space><BgColorsOutlined style={{ color: '#8b4513' }} /> Tema Moca</Space>,
      onClick: () => setTheme('mocha'),
    },
    { type: 'divider' },
    {
      key: 'font-label',
      type: 'group',
      label: 'Tamaño de texto (accesibilidad)',
      children: [
        {
          key: 'font-normal',
          label: <Space><span style={{ fontSize: 13 }}>A</span> Normal {fontScale === 'normal' ? '✓' : ''}</Space>,
          onClick: () => setFontScale('normal'),
        },
        {
          key: 'font-grande',
          label: <Space><span style={{ fontSize: 16 }}>A</span> Grande {fontScale === 'grande' ? '✓' : ''}</Space>,
          onClick: () => setFontScale('grande'),
        },
        {
          key: 'font-extra',
          label: <Space><span style={{ fontSize: 19 }}>A</span> Extra grande {fontScale === 'extra' ? '✓' : ''}</Space>,
          onClick: () => setFontScale('extra'),
        },
      ],
    },
  ];

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'header_profile',
      icon: <UserOutlined />,
      label: 'Mi Perfil',
      onClick: () => navigate('/dashboard/perfil'),
    },
    {
      key: 'header_settings',
      icon: <SettingOutlined />,
      label: 'Ajustes de Cuenta',
      onClick: () => navigate('/dashboard/configuracion'),
    },
    {
      type: 'divider',
    },
    {
      key: 'header_logout',
      icon: <LogoutOutlined />,
      label: 'Cerrar Sesión',
      danger: true,
      onClick: () => {
        if (onLogout) onLogout();
        else {
          authService.logout();
          navigate('/login');
        }
      },
    },
  ];

  // ============================================================================
  // RENDERIZADO DEL SIDEBAR (COMPONENTE REUTILIZABLE)
  // ============================================================================

  const getSidebarContent = () => {
    const isLightTheme = themeName === 'normal' || themeName === 'light';

    return (
      <>
        <div className="sidebar-logo-container" style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: isLightTheme ? '#ffffff' : '#001529',
          borderBottom: isLightTheme ? '1px solid #f0f0f0' : '1px solid rgba(255,255,255,0.1)'
        }}>
          <div className="sidebar-logo-text" style={{
            color: isLightTheme ? '#001529' : 'white',
            fontSize: collapsed ? 14 : 18,
          }}>
            <div className="sidebar-logo-icon">
              <HeartOutlined />
            </div>
            {!collapsed && <span>Fetal Medical</span>}
          </div>
        </div>

        <Menu
          theme={isLightTheme ? 'light' : 'dark'}
          mode="inline"
          selectedKeys={[location.pathname]}
          defaultOpenKeys={['group-clinico', 'group-estudios']}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </>
    );
  };

  // ============================================================================
  // RENDERIZADO PRINCIPAL
  // ============================================================================

  return (
    <Layout style={{ minHeight: '100vh' }}>

      {/* SIDEBAR DESKTOP (Oculto en móvil) */}
      {!isMobile && (
        <Sider
          trigger={null}
          collapsible
          collapsed={collapsed}
          width={250}
          style={{
            overflow: 'auto',
            height: '100vh',
            position: 'sticky',
            top: 0,
            left: 0,
            zIndex: 10,
            background: 'var(--bg-sidebar, #001529)'
          }}
        >
          {getSidebarContent()}
        </Sider>
      )}

      {/* SIDEBAR MOBILE (Drawer) */}
      {isMobile && (
        <Drawer
          placement="left"
          onClose={() => setMobileDrawerVisible(false)}
          open={mobileDrawerVisible}
          styles={{
            body: {
              padding: 0,
              background: (themeName === 'normal' || themeName === 'light') ? '#ffffff' : '#001529'
            }
          }}
          width={250}
          closable={false}
        >
          {getSidebarContent()}
        </Drawer>
      )}

      {/* CONTENEDOR CENTRAL */}
        <Layout className="site-layout" style={{ transition: 'transform 0.2s' }}>

        {/* HEADER SUPERIOR */}
        <Header
          className="site-layout-background site-header"
        >
          {/* IZQUIERDA: TRIGGER SIDEBAR */}
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {isMobile ? (
              <Button
                type="text"
                icon={<MenuUnfoldOutlined />}
                onClick={() => setMobileDrawerVisible(true)}
                style={{ fontSize: '18px', width: 46, height: 46 }}
                aria-label="Abrir menu de navegacion"
              />
            ) : (
              <Button
                type="text"
                icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                onClick={() => setCollapsed(!collapsed)}
                style={{ fontSize: '18px', width: 46, height: 46 }}
                aria-label={collapsed ? 'Expandir menu lateral' : 'Colapsar menu lateral'}
              />
            )}

            {/* Breadcrumb o Título Dinámico (Opcional) */}
            <span style={{ marginLeft: 16, fontSize: 16, fontWeight: 500, color: theme.colors.text }}>
              {/* Podrías poner el título de la página actual aquí */}
            </span>
          </div>

          {/* DERECHA: HERRAMIENTAS Y PERFIL */}
          <Space size="large">

            {/* Selector de Tema */}
            <Dropdown menu={{ items: themeMenuItems }} placement="bottomRight" arrow>
              <Button type="text" icon={<BgColorsOutlined />} shape="circle" />
            </Dropdown>

            {/* Notificaciones */}
            <NotificationDropdown />

            {/* Perfil de Usuario */}
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" arrow>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                cursor: 'pointer',
                padding: '4px 12px',
                borderRadius: 20,
                background: 'rgba(0,0,0,0.04)',
                transition: 'background 0.3s, transform 0.3s'
              }} className="user-dropdown-trigger">
                <Avatar
                  size="small"
                  src={user?.foto_perfil}
                  icon={<UserOutlined />}
                  style={{ backgroundColor: theme.colors.primary || '#1890ff', marginRight: 8 }}
                />
                <div style={{ display: 'flex', flexDirection: 'column', lineHeight: '1.2', marginRight: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: theme.colors.text }}>
                    {user?.nombre || 'Usuario'}
                  </span>
                  <span style={{ fontSize: 12, color: '#999' }}>
                    {user?.rol?.toUpperCase() || 'INVITADO'}
                  </span>
                </div>
              </div>
            </Dropdown>

          </Space>
        </Header>

        {/* CONTENIDO DE LA PÁGINA (CHILDREN) */}
        <Content
          style={{
            margin: '24px 16px',
            padding: 0,
            minHeight: 280,
            background: 'transparent',
            position: 'relative'
          }}
          className="page-content-fade"
        >
          {children}
        </Content>

        {/* FOOTER */}
        <Footer style={{ textAlign: 'center', color: 'var(--text-tertiary, #bfbfbf)', padding: '16px 0' }}>
          Fetal Medical System ©{currentYear} • Versión 1.5.0 • <SafetyCertificateOutlined /> Conexión Segura
        </Footer>

      </Layout>
    </Layout>
  );
};

export default MainLayout;
