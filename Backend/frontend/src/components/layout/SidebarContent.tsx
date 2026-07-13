import React from 'react';
import { Menu } from 'antd';
import type { MenuProps } from 'antd';
import { HeartOutlined } from '@ant-design/icons';

interface SidebarContentProps {
  isLightTheme: boolean;
  collapsed: boolean;
  selectedKey: string;
  menuItems: MenuProps['items'];
  onMenuClick: MenuProps['onClick'];
}

const SidebarContent: React.FC<SidebarContentProps> = ({
  isLightTheme, collapsed, selectedKey, menuItems, onMenuClick,
}) => (
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
      selectedKeys={[selectedKey]}
      defaultOpenKeys={['group-clinico', 'group-estudios']}
      items={menuItems}
      onClick={onMenuClick}
      style={{ borderRight: 0 }}
    />
  </>
);

export default SidebarContent;
