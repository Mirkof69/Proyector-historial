import React from 'react';
import { Menu } from 'antd';
import type { MenuProps } from 'antd';
import { HeartOutlined } from '@ant-design/icons';

interface SidebarContentProps {
  collapsed: boolean;
  selectedKey: string;
  menuItems: MenuProps['items'];
  onMenuClick: MenuProps['onClick'];
}

/**
 * Logo + menú de navegación. Los colores del menú (superficie, elemento activo
 * en --color-primario-suave con texto primario) salen de los tokens de Ant
 * Design de cada tema; el estilo de las piezas propias, de styles/layout.css.
 */
const SidebarContent: React.FC<SidebarContentProps> = ({
  collapsed, selectedKey, menuItems, onMenuClick,
}) => (
  <>
    <div className={`sidebar-logo-container${collapsed ? ' sidebar-logo-container--colapsado' : ''}`}>
      <div className="sidebar-logo-icon" aria-hidden="true">
        <HeartOutlined />
      </div>
      {!collapsed && <span className="sidebar-logo-text">Fetal Medical</span>}
    </div>

    <Menu
      mode="inline"
      selectedKeys={[selectedKey]}
      defaultOpenKeys={['group-clinico', 'group-estudios']}
      items={menuItems}
      onClick={onMenuClick}
    />
  </>
);

export default SidebarContent;
