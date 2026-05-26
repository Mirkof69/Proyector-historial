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
  const { themeName } = useTheme();

  // Obtener tokens según el tema actual
  const themeConfig = getThemeTokens(themeName);

  return themeConfig;
};

export default useAntdTheme;
