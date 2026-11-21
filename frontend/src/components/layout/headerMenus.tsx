import React from 'react';
import { Space } from 'antd';
import type { MenuProps } from 'antd';
import type { NavigateFunction } from 'react-router-dom';
import {
  SunOutlined, MoonOutlined, CoffeeOutlined, CheckOutlined,
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
    icon: <SunOutlined />,
    label: 'Tema Claro',
    onClick: () => setTheme('normal'),
  },
  {
    key: 'dark',
    icon: <MoonOutlined />,
    label: 'Tema Oscuro',
    onClick: () => setTheme('dark'),
  },
  {
    key: 'mocha',
    icon: <CoffeeOutlined />,
    label: 'Tema Moca',
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
        label: <Space><span style={{ fontSize: 13 }}>A</span> Normal {fontScale === 'normal' && <CheckOutlined aria-label="seleccionado" />}</Space>,
        onClick: () => setFontScale('normal'),
      },
      {
        key: 'font-grande',
        label: <Space><span style={{ fontSize: 16 }}>A</span> Grande {fontScale === 'grande' && <CheckOutlined aria-label="seleccionado" />}</Space>,
        onClick: () => setFontScale('grande'),
      },
      {
        key: 'font-extra',
        label: <Space><span style={{ fontSize: 19 }}>A</span> Extra grande {fontScale === 'extra' && <CheckOutlined aria-label="seleccionado" />}</Space>,
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
    // Su contraseña y su MFA, para cualquier rol. Antes iba a /configuracion, que es
    // solo del administrador: médicos y enfermeras caían en la página 403.
    onClick: () => navigate('/dashboard/perfil?pestana=seguridad'),
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
