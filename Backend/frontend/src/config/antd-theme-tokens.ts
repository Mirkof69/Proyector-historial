/**
 * =============================================================================
 * TOKENS DE ANT DESIGN — Fetal Medical Bolivia
 * =============================================================================
 * Contrato: docs/DISENO_INTERFAZ.md. Los colores son los MISMOS que
 * src/styles/tokens.css (variables CSS); un test
 * (config/__tests__/antdThemeTokens.test.ts) compara los dos archivos.
 *
 * Dirección: superficies planas separadas por borde de 1 px, sin degradados,
 * sombra solo en lo que flota, un único acento (el primario). El elemento
 * activo del menú usa --color-primario-suave de fondo y texto primario.
 *
 * Todo lo que se puede decir con un token se dice aquí: Ant Design 5 inyecta
 * sus estilos en tiempo de ejecución, y pelear con él desde CSS obligaba a
 * usar `!important`.
 * =============================================================================
 */

import { ThemeConfig, theme } from 'antd';

export type NombreTema = 'light' | 'dark' | 'normal' | 'mocha';

/** Paleta de un tema. Nombres en el mismo orden que tokens.css. */
export interface Paleta {
  primario: string;
  primarioHover: string;
  primarioSuave: string;
  sobrePrimario: string;
  anilloFoco: string;
  fondo: string;
  superficie: string;
  superficie2: string;
  hover: string;
  borde: string;
  bordeSuave: string;
  bordeFuerte: string;
  mascara: string;
  texto: string;
  texto2: string;
  texto3: string;
  exito: string;
  exitoSuave: string;
  exitoBorde: string;
  aviso: string;
  avisoSuave: string;
  avisoBorde: string;
  peligro: string;
  peligroSuave: string;
  peligroBorde: string;
  info: string;
  infoSuave: string;
  infoBorde: string;
  sombraFlotante: string;
  sombraBaja: string;
}

const CLARO: Paleta = {
  primario: '#155E75',
  primarioHover: '#0E4C61',
  primarioSuave: '#E3F1F5',
  sobrePrimario: '#FFFFFF',
  anilloFoco: 'rgba(21, 94, 117, 0.18)',
  fondo: '#F4F6F8',
  superficie: '#FFFFFF',
  superficie2: '#F8FAFB',
  hover: '#EEF2F5',
  borde: '#DDE3E8',
  bordeSuave: '#EBEFF2',
  bordeFuerte: '#C5CED6',
  mascara: 'rgba(13, 19, 24, 0.45)',
  texto: '#15212B',
  texto2: '#4D5D6A',
  texto3: '#7A8995',
  exito: '#1E7B4F',
  exitoSuave: '#E7F4EC',
  exitoBorde: '#A9D5BC',
  aviso: '#A35F00',
  avisoSuave: '#FDF3E1',
  avisoBorde: '#EBC98A',
  peligro: '#B42318',
  peligroSuave: '#FDECEA',
  peligroBorde: '#F0B2AB',
  info: '#1D5FA8',
  infoSuave: '#E8F0FA',
  infoBorde: '#A9C4E6',
  sombraFlotante: '0 6px 16px rgba(21, 33, 43, 0.12), 0 1px 3px rgba(21, 33, 43, 0.08)',
  sombraBaja: '0 1px 2px rgba(21, 33, 43, 0.06)',
};

const OSCURO: Paleta = {
  primario: '#5BB6CC',
  primarioHover: '#7FC8DA',
  primarioSuave: '#14313A',
  sobrePrimario: '#0D1318',
  anilloFoco: 'rgba(91, 182, 204, 0.28)',
  fondo: '#0D1318',
  superficie: '#141C22',
  superficie2: '#1A242C',
  hover: '#1F2A33',
  borde: '#2A3640',
  bordeSuave: '#202B33',
  bordeFuerte: '#3A4954',
  mascara: 'rgba(0, 0, 0, 0.6)',
  texto: '#E5ECF1',
  texto2: '#A7B5C0',
  texto3: '#7D8C97',
  exito: '#4CC38A',
  exitoSuave: '#13291F',
  exitoBorde: '#1F5138',
  aviso: '#E3A33B',
  avisoSuave: '#2E2210',
  avisoBorde: '#5C4419',
  peligro: '#F2766B',
  peligroSuave: '#33171A',
  peligroBorde: '#6B2A27',
  info: '#6AA6E8',
  infoSuave: '#13233A',
  infoBorde: '#274A73',
  sombraFlotante: '0 6px 16px rgba(0, 0, 0, 0.45), 0 1px 3px rgba(0, 0, 0, 0.3)',
  sombraBaja: '0 1px 2px rgba(0, 0, 0, 0.3)',
};

/** Paleta de cada tema. `normal` = claro con fondo blanco; `mocha` = oscuro cálido. */
export const PALETAS: Record<NombreTema, Paleta> = {
  light: CLARO,
  normal: { ...CLARO, fondo: '#FFFFFF' },
  dark: OSCURO,
  mocha: {
    primario: '#D9A56B',
    primarioHover: '#E6BC8A',
    primarioSuave: '#3A2C1D',
    sobrePrimario: '#16130F',
    anilloFoco: 'rgba(217, 165, 107, 0.28)',
    fondo: '#16130F',
    superficie: '#1E1A15',
    superficie2: '#26211B',
    hover: '#2C261F',
    borde: '#3A332A',
    bordeSuave: '#2C261F',
    bordeFuerte: '#4A4236',
    mascara: 'rgba(0, 0, 0, 0.6)',
    texto: '#EDE6DC',
    texto2: '#BFB3A3',
    texto3: '#968B7C',
    exito: '#7CC48F',
    exitoSuave: '#1C2A1F',
    exitoBorde: '#355A3E',
    aviso: '#E3A33B',
    avisoSuave: '#33260F',
    avisoBorde: '#644A1C',
    peligro: '#EF7F6E',
    peligroSuave: '#3A1D18',
    peligroBorde: '#6E3329',
    info: '#82AEE0',
    infoSuave: '#1A2638',
    infoBorde: '#34506F',
    sombraFlotante: '0 6px 16px rgba(0, 0, 0, 0.5), 0 1px 3px rgba(0, 0, 0, 0.35)',
    sombraBaja: '0 1px 2px rgba(0, 0, 0, 0.35)',
  },
};

export const FUENTE = "'IBM Plex Sans', 'Segoe UI', system-ui, sans-serif";
export const FUENTE_MONO = "'IBM Plex Mono', ui-monospace, 'Cascadia Mono', Consolas, monospace";

/** Construye la configuración de Ant Design a partir de una paleta. */
const construirTema = (p: Paleta, oscuro: boolean): ThemeConfig => {
  const control = {
    colorBgContainer: p.superficie,
    colorBorder: p.borde,
    hoverBorderColor: p.bordeFuerte,
    activeBorderColor: p.primario,
    activeShadow: `0 0 0 2px ${p.anilloFoco}`,
    colorText: p.texto,
    colorTextPlaceholder: p.texto3,
  };
  const flotante = {
    colorBgElevated: p.superficie,
    boxShadowSecondary: p.sombraFlotante,
  };

  return {
    algorithm: oscuro ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      // Semillas (de ellas deriva el algoritmo los tonos intermedios)
      colorPrimary: p.primario,
      colorSuccess: p.exito,
      colorWarning: p.aviso,
      colorError: p.peligro,
      colorInfo: p.info,
      colorLink: p.primario,
      colorTextBase: p.texto,
      colorBgBase: p.superficie,

      colorLinkHover: p.primarioHover,
      colorLinkActive: p.primarioHover,
      colorPrimaryBg: p.primarioSuave,
      colorPrimaryBgHover: p.primarioSuave,

      // Estados: fondo suave + borde, igual que --color-*-suave / -borde
      colorSuccessBg: p.exitoSuave,
      colorSuccessBorder: p.exitoBorde,
      colorWarningBg: p.avisoSuave,
      colorWarningBorder: p.avisoBorde,
      colorErrorBg: p.peligroSuave,
      colorErrorBorder: p.peligroBorde,
      colorInfoBg: p.infoSuave,
      colorInfoBorder: p.infoBorde,

      // Texto
      colorText: p.texto,
      colorTextHeading: p.texto,
      colorTextSecondary: p.texto2,
      colorTextLabel: p.texto2,
      colorTextDescription: p.texto2,
      colorTextTertiary: p.texto3,
      colorTextQuaternary: p.texto3,
      colorTextPlaceholder: p.texto3,
      colorTextDisabled: p.texto3,
      // Texto sobre el primario (botón principal, casilla marcada, paso
      // activo…). En los temas oscuros el primario es claro: texto oscuro.
      colorTextLightSolid: p.sobrePrimario,

      // Superficies
      colorBgLayout: p.fondo,
      colorBgContainer: p.superficie,
      colorBgElevated: p.superficie,
      colorBgSpotlight: p.texto,
      colorBgMask: p.mascara,
      colorFillAlter: p.superficie2,
      colorFillContent: p.hover,
      colorBorder: p.borde,
      colorBorderSecondary: p.borde,
      colorSplit: p.bordeSuave,
      controlItemBgHover: p.hover,
      controlItemBgActive: p.primarioSuave,
      controlItemBgActiveHover: p.primarioSuave,
      controlOutline: p.anilloFoco,
      controlOutlineWidth: 2,

      // Tipografía (escala del contrato: 12 · 13 · 14 · 16 · 18 · 22 · 28)
      fontFamily: FUENTE,
      fontFamilyCode: FUENTE_MONO,
      fontSize: 14,
      fontSizeSM: 12,
      fontSizeLG: 16,
      fontSizeXL: 18,
      fontSizeHeading1: 28,
      fontSizeHeading2: 22,
      fontSizeHeading3: 18,
      fontSizeHeading4: 16,
      fontSizeHeading5: 14,
      fontWeightStrong: 600,

      // Radio: 4 · 6 · 8 (nada de 12–24 px)
      borderRadius: 6,
      borderRadiusLG: 8,
      borderRadiusSM: 4,
      borderRadiusXS: 2,

      // Controles
      controlHeight: 36,
      controlHeightLG: 40,
      controlHeightSM: 28,

      // Sombra solo en lo que flota
      boxShadow: p.sombraFlotante,
      boxShadowSecondary: p.sombraFlotante,
      boxShadowTertiary: p.sombraBaja,

      // Sin animaciones de Ant Design: en el Chrome del consultorio los
      // desplegables (buscador de paciente, campana, menú del perfil,
      // calendario) quedaban atascados en la animación de entrada, invisibles
      // y «temblando», aunque existían en la página. Aparecen al instante.
      motion: false,
      motionDurationFast: '0.12s',
      motionDurationMid: '0.16s',
      motionDurationSlow: '0.24s',

      wireframe: false,
    },
    components: {
      Layout: {
        bodyBg: p.fondo,
        headerBg: p.superficie,
        headerColor: p.texto,
        headerHeight: 56,
        headerPadding: '0 16px',
        siderBg: p.superficie,
        lightSiderBg: p.superficie,
        triggerBg: p.superficie,
        triggerColor: p.texto2,
        footerBg: 'transparent',
        footerPadding: '16px 0',
      },
      Menu: {
        itemBg: p.superficie,
        subMenuItemBg: p.superficie,
        popupBg: p.superficie,
        itemColor: p.texto2,
        itemHoverColor: p.texto,
        itemHoverBg: p.hover,
        itemActiveBg: p.primarioSuave,
        itemSelectedBg: p.primarioSuave,
        itemSelectedColor: p.primario,
        horizontalItemSelectedColor: p.primario,
        groupTitleColor: p.texto3,
        groupTitleFontSize: 12,
        itemBorderRadius: 6,
        subMenuItemBorderRadius: 6,
        itemMarginInline: 8,
        itemHeight: 36,
        iconSize: 16,
        collapsedIconSize: 16,
        activeBarBorderWidth: 0,
        activeBarWidth: 0,
        // Menús con theme="dark" (si alguno queda) siguen la misma paleta
        darkItemBg: p.superficie,
        darkSubMenuItemBg: p.superficie,
        darkPopupBg: p.superficie,
        darkItemColor: p.texto2,
        darkItemHoverColor: p.texto,
        darkItemHoverBg: p.hover,
        darkItemSelectedBg: p.primarioSuave,
        darkItemSelectedColor: p.primario,
        darkGroupTitleColor: p.texto3,
      },
      Button: {
        fontWeight: 500,
        primaryColor: p.sobrePrimario,
        primaryShadow: 'none',
        defaultShadow: 'none',
        dangerShadow: 'none',
        defaultBg: p.superficie,
        defaultColor: p.texto,
        defaultBorderColor: p.borde,
        defaultHoverBg: p.superficie,
        defaultHoverBorderColor: p.primario,
        defaultHoverColor: p.primario,
        textHoverBg: p.hover,
        colorText: p.texto,
      },
      Card: {
        colorBgContainer: p.superficie,
        colorBorderSecondary: p.borde,
        colorText: p.texto,
        headerBg: 'transparent',
        headerFontSize: 16,
        headerFontSizeSM: 14,
        borderRadiusLG: 8,
        boxShadowTertiary: p.sombraBaja,
      },
      Table: {
        colorBgContainer: p.superficie,
        colorText: p.texto,
        headerBg: p.superficie2,
        headerColor: p.texto,
        headerSplitColor: p.borde,
        headerSortActiveBg: p.hover,
        headerSortHoverBg: p.hover,
        bodySortBg: p.superficie2,
        rowHoverBg: p.hover,
        rowSelectedBg: p.primarioSuave,
        rowSelectedHoverBg: p.primarioSuave,
        rowExpandedBg: p.superficie2,
        footerBg: p.superficie2,
        footerColor: p.texto2,
        borderColor: p.bordeSuave,
        fixedHeaderSortActiveBg: p.hover,
        // Filas de ~46 px (contrato: 44–48)
        cellPaddingBlock: 12,
        cellPaddingInline: 16,
        headerBorderRadius: 8,
      },
      Input: { ...control },
      InputNumber: { ...control },
      Select: {
        ...control,
        ...flotante,
        selectorBg: p.superficie,
        optionSelectedBg: p.primarioSuave,
        optionSelectedColor: p.texto,
        optionSelectedFontWeight: 500,
        optionActiveBg: p.hover,
      },
      DatePicker: {
        ...control,
        ...flotante,
        cellActiveWithRangeBg: p.primarioSuave,
        cellHoverBg: p.hover,
      },
      Modal: {
        contentBg: p.superficie,
        headerBg: p.superficie,
        footerBg: 'transparent',
        titleColor: p.texto,
        titleFontSize: 16,
        colorText: p.texto,
        borderRadiusLG: 8,
        boxShadow: p.sombraFlotante,
      },
      Drawer: {
        colorBgElevated: p.superficie,
        colorText: p.texto,
        colorSplit: p.borde,
      },
      Tag: {
        defaultBg: p.superficie2,
        defaultColor: p.texto2,
        colorBorder: p.borde,
        borderRadiusSM: 4,
      },
      Tabs: {
        itemColor: p.texto2,
        itemHoverColor: p.texto,
        itemSelectedColor: p.primario,
        itemActiveColor: p.primario,
        inkBarColor: p.primario,
        cardBg: p.superficie2,
        titleFontSize: 14,
      },
      Descriptions: {
        labelBg: p.superficie2,
        titleColor: p.texto,
        labelColor: p.texto2,
        contentColor: p.texto,
        colorSplit: p.borde,
      },
      Statistic: {
        titleFontSize: 13,
        contentFontSize: 28,
      },
      Form: {
        labelColor: p.texto,
        labelFontSize: 13,
        labelRequiredMarkColor: p.peligro,
      },
      Pagination: {
        itemActiveBg: p.superficie,
        itemBg: p.superficie,
        colorBgContainer: p.superficie,
        colorBorder: p.borde,
      },
      Progress: {
        defaultColor: p.primario,
        remainingColor: p.bordeSuave,
      },
      Collapse: {
        headerBg: p.superficie2,
        contentBg: p.superficie,
      },
      Timeline: {
        dotBg: p.superficie,
        tailColor: p.borde,
      },
      Calendar: {
        fullBg: p.superficie,
        fullPanelBg: p.superficie,
        itemActiveBg: p.primarioSuave,
      },
      Segmented: {
        itemSelectedBg: p.superficie,
        trackBg: p.superficie2,
      },
      Alert: {
        withDescriptionIconSize: 20,
      },
      // Superficies flotantes: superficie + borde de la sombra flotante, sin
      // desenfoques ni transparencias.
      Tooltip: {
        // Tooltip invertido: fondo de texto, letra de superficie (≥ 12:1).
        colorBgSpotlight: p.texto,
        colorTextLightSolid: p.superficie,
      },
      Notification: { ...flotante },
      Popover: { ...flotante },
      Message: { contentBg: p.superficie, ...flotante },
      Dropdown: { ...flotante },
    },
  };
};

const TEMAS: Record<NombreTema, ThemeConfig> = {
  light: construirTema(PALETAS.light, false),
  normal: construirTema(PALETAS.normal, false),
  dark: construirTema(PALETAS.dark, true),
  mocha: construirTema(PALETAS.mocha, true),
};

/**
 * Configuración de Ant Design para un tema (light | dark | normal | mocha).
 * Devuelve siempre el mismo objeto por tema (estable entre renders).
 */
export const getThemeTokens = (themeName: NombreTema): ThemeConfig =>
  TEMAS[themeName] ?? TEMAS.light;
