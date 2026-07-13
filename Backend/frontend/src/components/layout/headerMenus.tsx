import React from 'react';
import { Space } from 'antd';
import type { MenuProps } from 'antd';
import type { NavigateFunction } from 'react-router-dom';
import {
  SunOutlined, MoonOutlined, BgColorsOutlined,
  UserOutlined, SettingOutlined, LogoutOutlined,
} from '@ant-design/icons';
import type { FontScale } from '../../contexts/ThemeContext';

type Theme = 'light' | 'dark' | 'normal' | 'mocha';

export const buildThemeMenuItems = (
  setTheme: (t: Theme) => void,
  fontScale: FontScale,
  setFontScale: (s: FontScale) => void,
): MenuProps['items'] => [
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

export const buildUserMenuItems = (
  navigate: NavigateFunction,
  onLogout: () => void,
): MenuProps['items'] => [
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
  { type: 'divider' },
  {
    key: 'header_logout',
    icon: <LogoutOutlined />,
    label: 'Cerrar Sesión',
    danger: true,
    onClick: onLogout,
  },
];
