/**
 * =============================================================================
 * ANT DESIGN THEME TOKENS - CONFIGURACIÓN SIMPLIFICADA
 * =============================================================================
 * Sistema de tokens para ConfigProvider de Ant Design
 * Soporte completo de modo claro y oscuro
 * Compatible con clase .dark en <html>
 * Colores coordinados para contexto médico gineco-obstétrico
 * =============================================================================
 */

import { ThemeConfig, theme } from 'antd';

// Medical color palette - coordinated for clinical context
const MEDICAL_PRIMARY = '#1890ff';
const MEDICAL_SUCCESS = '#52c41a';
const MEDICAL_WARNING = '#faad14';
const MEDICAL_ERROR = '#ff4d4f';
const MEDICAL_INFO = '#1890ff';

/**
 * TEMA CLARO (LIGHT MODE)
 */
const lightThemeTokens: ThemeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    // Colores principales - coordinated medical palette
    colorPrimary: MEDICAL_PRIMARY,
    colorSuccess: MEDICAL_SUCCESS,
    colorWarning: MEDICAL_WARNING,
    colorError: MEDICAL_ERROR,
    colorInfo: MEDICAL_INFO,
    colorLink: MEDICAL_PRIMARY,
    colorLinkHover: '#1d4ed8',
    colorLinkActive: '#1e40af',

    // Textos
    colorText: '#1a1a2e',
    colorTextSecondary: '#595959',
    colorTextTertiary: '#8c8c8c',
    colorTextQuaternary: '#bfbfbf',

    colorBgBase: '#ffffff',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorBgLayout: '#f0f5ff',
    colorBgSpotlight: '#e6f4ff',
    colorBgMask: 'rgba(0, 0, 0, 0.45)',

    colorBorder: '#d9d9d9',
    colorBorderSecondary: '#f0f0f0',
    colorSplit: '#d9d9d9',

    // Rellenos
    colorFill: 'rgba(0, 0, 0, 0.04)',
    colorFillSecondary: 'rgba(0, 0, 0, 0.02)',
    colorFillTertiary: 'rgba(0, 0, 0, 0.01)',
    colorFillQuaternary: 'rgba(0, 0, 0, 0.01)',

    // Tipografía
    fontSize: 14,
    fontSizeHeading1: 38,
    fontSizeHeading2: 30,
    fontSizeHeading3: 24,
    fontSizeHeading4: 20,
    fontSizeHeading5: 16,
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",

    // Línea de altura
    lineHeight: 1.5715,
    lineHeightHeading1: 1.21,
    lineHeightHeading2: 1.35,
    lineHeightHeading3: 1.35,
    lineHeightHeading4: 1.4,
    lineHeightHeading5: 1.5,

    // Radio de bordes - slightly more rounded for modern feel
    borderRadius: 8,
    borderRadiusLG: 12,
    borderRadiusSM: 6,
    borderRadiusXS: 4,

    // Control
    controlHeight: 36,
    controlHeightLG: 44,
    controlHeightSM: 28,

    // Motion - smooth transitions
    motionUnit: 0.1,
    motionBase: 0,
    motionEaseInOut: 'cubic-bezier(0.645, 0.045, 0.355, 1)',
    motionEaseOut: 'cubic-bezier(0.215, 0.61, 0.355, 1)',
    motionDurationFast: '0.1s',
    motionDurationMid: '0.2s',
    motionDurationSlow: '0.3s',

    // Sombras
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
    boxShadowSecondary: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
    boxShadowTertiary: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',

    // Z-index
    zIndexBase: 0,
    zIndexPopupBase: 1000,

    // Wireframe
    wireframe: false,
  },
  components: {
    Button: {
      borderRadius: 8,
      fontWeight: 500,
      controlHeight: 36,
      controlHeightLG: 44,
      controlHeightSM: 28,
    },
    Card: {
      borderRadius: 12,
      borderRadiusLG: 16,
    },
    Input: {
      borderRadius: 8,
      controlHeight: 36,
    },
    Select: {
      borderRadius: 8,
      controlHeight: 36,
    },
    Modal: {
      borderRadiusLG: 16,
    },
    Tabs: {
      borderRadius: 8,
    },
    Table: {
      colorBgContainer: '#ffffff',
      headerBg: '#fafafa',
      headerColor: '#1a1a2e',
      rowHoverBg: '#f5f5f5',
      borderColor: '#f0f0f0',
    },
  },
};

/**
 * TEMA OSCURO (DARK MODE)
 */
const darkThemeTokens: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    // Colores principales - adjusted for dark mode
    colorPrimary: '#40a9ff',
    colorSuccess: '#73d13d',
    colorWarning: '#ffc53d',
    colorError: '#ff7875',
    colorInfo: '#40a9ff',
    colorLink: '#69c0ff',
    colorLinkHover: '#91d5ff',
    colorLinkActive: '#40a9ff',

    colorText: '#e8e8e8',
    colorTextSecondary: '#bfbfbf',
    colorTextTertiary: '#8c8c8c',
    colorTextQuaternary: '#595959',

    colorBgBase: '#0a0a1a',
    colorBgContainer: '#141428',
    colorBgElevated: '#141428',
    colorBgLayout: '#0d0d20',
    colorBgSpotlight: '#1a1a3e',
    colorBgMask: 'rgba(0, 0, 0, 0.75)',

    colorBorder: '#2a2a4a',
    colorBorderSecondary: '#1a1a3e',
    colorSplit: '#2a2a4a',

    // Rellenos
    colorFill: 'rgba(255, 255, 255, 0.08)',
    colorFillSecondary: 'rgba(255, 255, 255, 0.04)',
    colorFillTertiary: 'rgba(255, 255, 255, 0.02)',
    colorFillQuaternary: 'rgba(255, 255, 255, 0.01)',

    // Tipografía
    fontSize: 14,
    fontSizeHeading1: 38,
    fontSizeHeading2: 30,
    fontSizeHeading3: 24,
    fontSizeHeading4: 20,
    fontSizeHeading5: 16,
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",

    // Línea de altura
    lineHeight: 1.5715,
    lineHeightHeading1: 1.21,
    lineHeightHeading2: 1.35,
    lineHeightHeading3: 1.35,
    lineHeightHeading4: 1.4,
    lineHeightHeading5: 1.5,

    // Radio de bordes
    borderRadius: 8,
    borderRadiusLG: 12,
    borderRadiusSM: 6,
    borderRadiusXS: 4,

    // Control
    controlHeight: 36,
    controlHeightLG: 44,
    controlHeightSM: 28,

    // Motion
    motionUnit: 0.1,
    motionBase: 0,
    motionEaseInOut: 'cubic-bezier(0.645, 0.045, 0.355, 1)',
    motionEaseOut: 'cubic-bezier(0.215, 0.61, 0.355, 1)',
    motionDurationFast: '0.1s',
    motionDurationMid: '0.2s',
    motionDurationSlow: '0.3s',

    // Sombras (más sutiles en dark)
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.4), 0 1px 2px -1px rgba(0, 0, 0, 0.4)',
    boxShadowSecondary: '0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -2px rgba(0, 0, 0, 0.5)',
    boxShadowTertiary: '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -4px rgba(0, 0, 0, 0.5)',

    // Z-index
    zIndexBase: 0,
    zIndexPopupBase: 1000,

    // Wireframe
    wireframe: false,
  },
  components: {
    Button: {
      borderRadius: 8,
      fontWeight: 500,
      controlHeight: 36,
      controlHeightLG: 44,
      controlHeightSM: 28,
    },
    Card: {
      borderRadius: 12,
      borderRadiusLG: 16,
    },
    Input: {
      borderRadius: 8,
      controlHeight: 36,
    },
    Select: {
      borderRadius: 8,
      controlHeight: 36,
    },
    Modal: {
      borderRadiusLG: 16,
    },
    Tabs: {
      borderRadius: 8,
    },
    Table: {
      colorBgContainer: '#141428',
      headerBg: '#1a1a3e',
      headerColor: '#e8e8e8',
      rowHoverBg: '#1a1a3e',
      borderColor: '#2a2a4a',
      colorText: '#e8e8e8',
    },
  },
};

/**
 * ALGORITMO PARA SELECCIONAR TEMA
 * Retorna el tema apropiado basado en el nombre
 */
export const getThemeTokens = (themeName: 'light' | 'dark' | 'normal' | 'mocha'): ThemeConfig => {
  if (themeName === 'dark' || themeName === 'mocha') {
    return darkThemeTokens;
  }
  return lightThemeTokens;
};
