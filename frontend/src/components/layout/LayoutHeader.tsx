import React from 'react';
import { Layout, Button, Dropdown, Avatar } from 'antd';
import type { MenuProps } from 'antd';
import {
  MenuUnfoldOutlined, MenuFoldOutlined, BgColorsOutlined, UserOutlined,
} from '@ant-design/icons';
import NotificationDropdown from './NotificationDropdown';

const { Header } = Layout;

interface LayoutHeaderProps {
  isMobile: boolean;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onOpenMobileDrawer: () => void;
  user: any;
  themeMenuItems: MenuProps['items'];
  userMenuItems: MenuProps['items'];
}

/** Cabecera: botón del menú lateral a la izquierda; tema, avisos y perfil a la derecha. */
const LayoutHeader: React.FC<LayoutHeaderProps> = ({
  isMobile, collapsed, onToggleCollapsed, onOpenMobileDrawer,
  user, themeMenuItems, userMenuItems,
}) => (
  <Header className="site-header">
    {/* IZQUIERDA: TRIGGER SIDEBAR */}
    {isMobile ? (
      <Button
        type="text"
        className="site-header__boton"
        icon={<MenuUnfoldOutlined />}
        onClick={onOpenMobileDrawer}
        aria-label="Abrir menu de navegacion"
      />
    ) : (
      <Button
        type="text"
        className="site-header__boton"
        icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        onClick={onToggleCollapsed}
        aria-label={collapsed ? 'Expandir menu lateral' : 'Colapsar menu lateral'}
      />
    )}

    {/* DERECHA: HERRAMIENTAS Y PERFIL */}
    <div className="site-header__acciones">
      {/* Selector de Tema */}
      <Dropdown menu={{ items: themeMenuItems }} placement="bottomRight">
        <Button
          type="text"
          className="site-header__boton"
          icon={<BgColorsOutlined />}
          aria-label="Tema y tamaño de texto"
        />
      </Dropdown>

      {/* Notificaciones */}
      <NotificationDropdown />

      {/* Perfil de Usuario */}
      <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
        <div className="user-dropdown-trigger">
          <Avatar
            size="small"
            className="user-dropdown-trigger__avatar"
            src={user?.foto_perfil}
            icon={<UserOutlined />}
          />
          <div className="user-dropdown-trigger__datos">
            <span className="user-dropdown-trigger__nombre">
              {user?.nombre || 'Usuario'}
            </span>
            <span className="user-dropdown-trigger__rol">
              {user?.rol?.toUpperCase() || 'INVITADO'}
            </span>
          </div>
        </div>
      </Dropdown>
    </div>
  </Header>
);

export default LayoutHeader;
