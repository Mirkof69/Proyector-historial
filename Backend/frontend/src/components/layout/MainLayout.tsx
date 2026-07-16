/**
 * =============================================================================
 * MAIN LAYOUT - ESTRUCTURA PRINCIPAL
 * =============================================================================
 * Esqueleto de la app: Sidebar (navegación), Header (usuario/temas/notif),
 * Content (páginas) y Footer. Responsive, con menú por roles y colapsable.
 * El catálogo de menú, los menús del header, el sidebar y el header viven en
 * archivos aparte (ver ./mainMenuItems, ./headerMenus, ./SidebarContent,
 * ./LayoutHeader).
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { Layout, Drawer } from 'antd';
import type { MenuProps } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { SafetyCertificateOutlined } from '@ant-design/icons';
import { authService } from '../../services/authService';
import { useTheme } from '../../contexts/ThemeContext';
import { buildMainMenuItems } from './mainMenuItems';
import { buildThemeMenuItems, buildUserMenuItems } from './headerMenus';
import SidebarContent from './SidebarContent';
import LayoutHeader from './LayoutHeader';
import './MainLayout.css';

const { Sider, Content, Footer } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
  onLogout?: () => void;
}

const currentYear = new Date().getFullYear();

const MainLayout: React.FC<MainLayoutProps> = ({ children, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authService.getCurrentUser();

  const { theme, themeName, setTheme, fontScale, setFontScale } = useTheme();

  // Estados locales
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 992);
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false);

  // Responsive: detectar cambio de tamaño de pantalla
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 992;
      setIsMobile(mobile);
      if (!mobile) {
        setMobileDrawerVisible(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    if (isMobile) setMobileDrawerVisible(false);
    navigate(e.key);
  };

  const handleUserLogout = () => {
    if (onLogout) onLogout();
    else {
      authService.logout();
      navigate('/login');
    }
  };

  const menuItems = buildMainMenuItems(user, navigate);
  const themeMenuItems = buildThemeMenuItems(setTheme, fontScale, setFontScale);
  const userMenuItems = buildUserMenuItems(navigate, handleUserLogout);

  const isLightTheme = themeName === 'normal' || themeName === 'light';

  const sidebar = (
    <SidebarContent
      isLightTheme={isLightTheme}
      collapsed={collapsed}
      selectedKey={location.pathname}
      menuItems={menuItems}
      onMenuClick={handleMenuClick}
    />
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* SIDEBAR DESKTOP */}
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
          {sidebar}
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
              background: isLightTheme ? '#ffffff' : '#001529'
            }
          }}
          width={250}
          closable={false}
        >
          {sidebar}
        </Drawer>
      )}

      {/* CONTENEDOR CENTRAL */}
      <Layout className="site-layout" style={{ transition: 'transform 0.2s' }}>
        <LayoutHeader
          isMobile={isMobile}
          collapsed={collapsed}
          onToggleCollapsed={() => setCollapsed(!collapsed)}
          onOpenMobileDrawer={() => setMobileDrawerVisible(true)}
          user={user}
          themeMenuItems={themeMenuItems}
          userMenuItems={userMenuItems}
          textColor={theme.colors.text}
          primaryColor={theme.colors.primary}
        />

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
