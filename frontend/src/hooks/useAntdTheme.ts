/**
 * =============================================================================
 * USE ANTD THEME HOOK
 * =============================================================================
 * Hook personalizado para obtener los tokens de Ant Design
 * según el tema actual (light/dark)
 * =============================================================================
 */

import { useTheme } from '../contexts/ThemeContext';
import { getThemeTokens } from '../config/antd-theme-tokens';
import type { ThemeConfig } from 'antd';

/**
 * Hook para obtener la configuración de tema de Ant Design
 * @returns {ThemeConfig} Configuración de tokens según el tema actual
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const themeConfig = useAntdTheme();
 *
 *   return (
 *     <ConfigProvider theme={themeConfig}>
 *       <App />
 *     </ConfigProvider>
 *   );
 * }
 * ```
 */
const useAntdTheme = (): ThemeConfig => {
  const { themeName, fontScaleFactor } = useTheme();

  // Obtener tokens según el tema actual
  const themeConfig = getThemeTokens(themeName);

  // Accesibilidad: escalar el tamaño de fuente base según la preferencia del
  // usuario (turnos largos). Se aplica sobre el token, así todo Ant Design se
  // reescala de forma consistente.
  if (fontScaleFactor && fontScaleFactor !== 1) {
    const baseFont = (themeConfig.token?.fontSize as number) ?? 14;
    return {
      ...themeConfig,
      token: {
        ...themeConfig.token,
        fontSize: Math.round(baseFont * fontScaleFactor),
      },
    };
  }

  return themeConfig;
};

export default useAntdTheme;
