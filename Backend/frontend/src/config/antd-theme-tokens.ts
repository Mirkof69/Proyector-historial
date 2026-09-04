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
    // Los valores salen de antd-overrides.css, donde vivian con !important.
    // Varios de los que habia aqui estaban MUERTOS: headerBg decia '#fafafa'
    // pero el CSS imponia '#f9fafb', asi que lo que se veia era el segundo.
    // Ahora el token coincide con lo que ve el usuario.
    Table: {
      colorBgContainer: '#ffffff',
      headerBg: '#f9fafb',
      headerColor: '#111827',
      colorText: '#6b7280',
      rowHoverBg: '#f5f5f5',
      rowSelectedBg: 'rgba(37, 99, 235, 0.08)',
      rowSelectedHoverBg: 'rgba(37, 99, 235, 0.12)',
      footerBg: '#f9fafb',
      footerColor: '#6b7280',
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
      textHoverBg: 'rgba(255, 255, 255, 0.08)',
      colorText: '#d1d5db',
    },
    Select: {
      borderRadius: 8,
      controlHeight: 36,
      colorBgElevated: 'rgba(20, 20, 20, 0.95)',
      boxShadowSecondary: '0 8px 24px 0 rgba(0, 0, 0, 0.6)',
      selectorBg: 'rgba(26, 26, 26, 0.6)',
      colorBorder: 'rgba(255, 255, 255, 0.12)',
      colorText: '#f9fafb',
      // Opcion seleccionada dentro del desplegable.
      optionSelectedBg: 'rgba(59, 130, 246, 0.2)',
      optionSelectedColor: '#60a5fa',
      optionSelectedFontWeight: 600,
    },
    Modal: {
      borderRadiusLG: 16,
      contentBg: 'rgba(20, 20, 20, 0.85)',
      headerBg: 'rgba(26, 26, 26, 0.6)',
      footerBg: 'rgba(26, 26, 26, 0.6)',
      colorText: '#f9fafb',
    },
    Tabs: {
      borderRadius: 8,
    },
    // Table: los valores de aqui estaban MUERTOS. theme-dark-fixes.css los
    // pisaba con !important, asi que lo que se veia en pantalla eran los del
    // CSS (rgba(26,26,26,0.8)), no estos. Se alinean a lo que el usuario ve.
    Table: {
      colorBgContainer: 'rgba(20, 20, 20, 0.7)',
      headerBg: 'rgba(26, 26, 26, 0.8)',
      headerColor: '#f9fafb',
      headerSplitColor: 'rgba(255, 255, 255, 0.12)',
      rowHoverBg: 'rgba(42, 42, 42, 0.5)',
      rowSelectedBg: 'rgba(59, 130, 246, 0.12)',
      rowSelectedHoverBg: 'rgba(59, 130, 246, 0.18)',
      footerBg: 'rgba(26, 26, 26, 0.8)',
      footerColor: '#d1d5db',
      borderColor: 'rgba(255, 255, 255, 0.06)',
      colorText: '#d1d5db',
    },
    // Los siguientes tambien salen de theme-dark-fixes.css, donde vivian a
    // base de !important porque Ant Design 5 inyecta sus estilos DESPUES de
    // las hojas estaticas y una regla normal no le gana. Como tokens los
    // aplica el propio Ant Design, sin pelea. Lo unico que se queda en CSS es
    // `backdrop-filter`, que Ant Design no expone.
    Input: {
      borderRadius: 8,
      controlHeight: 36,
      colorBgContainer: 'rgba(26, 26, 26, 0.6)',
      colorBorder: 'rgba(255, 255, 255, 0.12)',
      colorText: '#f9fafb',
    },
    Card: {
      borderRadius: 12,
      borderRadiusLG: 16,
      colorBgContainer: 'rgba(20, 20, 20, 0.7)',
      colorBorderSecondary: 'rgba(255, 255, 255, 0.1)',
      colorText: '#f9fafb',
      headerBg: 'rgba(26, 26, 26, 0.6)',
    },
    Pagination: {
      colorBgContainer: 'rgba(26, 26, 26, 0.6)',
      colorBorder: 'rgba(255, 255, 255, 0.12)',
      // Pagina activa: el azul de marca sobre fondo oscuro.
      itemActiveBg: 'rgba(59, 130, 246, 0.3)',
      colorPrimary: '#3b82f6',
      colorPrimaryBorder: '#3b82f6',
    },
    Tag: {
      defaultBg: 'rgba(42, 42, 42, 0.6)',
      defaultColor: '#d1d5db',
      colorBorder: 'rgba(255, 255, 255, 0.12)',
    },
    Drawer: {
      colorBgElevated: 'rgba(20, 20, 20, 0.85)',
      colorText: '#f9fafb',
      colorSplit: 'rgba(255, 255, 255, 0.08)',
    },
    DatePicker: {
      colorBgElevated: 'rgba(20, 20, 20, 0.95)',
      colorBorder: 'rgba(255, 255, 255, 0.12)',
      colorText: '#f9fafb',
      colorTextHeading: '#f9fafb',
      colorSplit: 'rgba(255, 255, 255, 0.08)',
      cellActiveWithRangeBg: 'rgba(42, 42, 42, 0.7)',
      boxShadowSecondary: '0 8px 24px 0 rgba(0, 0, 0, 0.6)',
    },
    Descriptions: {
      colorFillAlter: 'rgba(26, 26, 26, 0.6)',
      colorSplit: 'rgba(255, 255, 255, 0.08)',
      colorText: '#f9fafb',
    },
    // Superficies flotantes (tooltip, popover, notificaciones, desplegables).
    //
    // Estos valores vivian en theme-dark-fixes.css a base de `!important`:
    // seis por componente, unos 40 en total. Hacia falta porque Ant Design 5
    // inyecta sus estilos en tiempo de ejecucion, DESPUES de las hojas
    // estaticas, asi que una regla CSS normal nunca le ganaba.
    //
    // Aqui no hay pelea: son los tokens que el propio Ant Design usa para
    // pintarse. Lo unico que se queda en CSS es `backdrop-filter`, que Ant
    // Design no expone como token — y que nunca necesito `!important`, porque
    // Ant Design tampoco lo define y no habia nada que sobrescribir.
    Tooltip: {
      colorBgSpotlight: 'rgba(20, 20, 20, 0.95)',
      colorTextLightSolid: '#f9fafb',
    },
    Notification: {
      colorBgElevated: 'rgba(20, 20, 20, 0.9)',
      boxShadowSecondary: '0 8px 32px 0 rgba(0, 0, 0, 0.7)',
    },
    Popover: {
      colorBgElevated: 'rgba(20, 20, 20, 0.95)',
      boxShadowSecondary: '0 8px 24px 0 rgba(0, 0, 0, 0.6)',
    },
    Message: {
      colorBgElevated: 'rgba(20, 20, 20, 0.95)',
      boxShadowSecondary: '0 4px 12px 0 rgba(0, 0, 0, 0.5)',
    },
    Dropdown: {
      colorBgElevated: 'rgba(20, 20, 20, 0.95)',
      boxShadowSecondary: '0 8px 24px 0 rgba(0, 0, 0, 0.6)',
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
