import React from 'react';
import { Layout, Button, Dropdown, Avatar, Space } from 'antd';
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
  textColor: string;
  primaryColor: string;
}

const LayoutHeader: React.FC<LayoutHeaderProps> = ({
  isMobile, collapsed, onToggleCollapsed, onOpenMobileDrawer,
  user, themeMenuItems, userMenuItems, textColor, primaryColor,
}) => (
  <Header className="site-layout-background site-header">
    {/* IZQUIERDA: TRIGGER SIDEBAR */}
    <div style={{ display: 'flex', alignItems: 'center' }}>
      {isMobile ? (
        <Button
          type="text"
          icon={<MenuUnfoldOutlined />}
          onClick={onOpenMobileDrawer}
          style={{ fontSize: '18px', width: 46, height: 46 }}
          aria-label="Abrir menu de navegacion"
        />
      ) : (
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={onToggleCollapsed}
          style={{ fontSize: '18px', width: 46, height: 46 }}
          aria-label={collapsed ? 'Expandir menu lateral' : 'Colapsar menu lateral'}
        />
      )}

      <span style={{ marginLeft: 16, fontSize: 16, fontWeight: 500, color: textColor }} />
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
            style={{ backgroundColor: primaryColor || '#1890ff', marginRight: 8 }}
          />
          <div style={{ display: 'flex', flexDirection: 'column', lineHeight: '1.2', marginRight: 4 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: textColor }}>
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
);

export default LayoutHeader;
