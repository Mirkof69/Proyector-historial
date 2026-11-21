/**
 * =============================================================================
 * THEME CONTEXT - SISTEMA DE TEMAS REACT
 * =============================================================================
 * Proporciona contexto global para el tema (claro/oscuro)
 * Maneja localStorage y preferencias del sistema
 * =============================================================================
 */

import React, { createContext, useState, useEffect, ReactNode, useContext } from 'react';
import { PALETAS, type Paleta } from '../config/antd-theme-tokens';

// Tipos
type Theme = 'light' | 'dark' | 'normal' | 'mocha';

// Escala de fuente para accesibilidad (turnos largos, personal con presbicia).
// Se persiste y multiplica el token fontSize de Ant Design.
export type FontScale = 'normal' | 'grande' | 'extra';
export const FONT_SCALE_FACTOR: Record<FontScale, number> = {
  normal: 1,
  grande: 1.15,
  extra: 1.3,
};

interface ThemeColors {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  error: string;
  warning: string;
  success: string;
  info: string;
  headerBg: string;
  sidebarBg: string;
}

interface ThemeObject {
  name: Theme;
  colors: ThemeColors;
}

interface ThemeContextType {
  theme: ThemeObject;
  themeName: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
  fontScale: FontScale;
  fontScaleFactor: number;
  setFontScale: (scale: FontScale) => void;
}

// Colores de cada tema para el código que los necesite en JS. Salen de la
// misma paleta que Ant Design y tokens.css (contrato docs/DISENO_INTERFAZ.md).
// En componentes, preferir las variables CSS de tokens.css o theme.useToken() de Ant Design.
const aColores = (p: Paleta): ThemeColors => ({
  primary: p.primario,
  secondary: p.texto2,
  background: p.fondo,
  surface: p.superficie,
  text: p.texto,
  textSecondary: p.texto2,
  border: p.borde,
  error: p.peligro,
  warning: p.aviso,
  success: p.exito,
  info: p.info,
  headerBg: p.superficie,
  sidebarBg: p.superficie,
});

const themeColors: Record<Theme, ThemeColors> = {
  light: aColores(PALETAS.light),
  normal: aColores(PALETAS.normal),
  dark: aColores(PALETAS.dark),
  mocha: aColores(PALETAS.mocha),
};

// Crear contexto (exportado para hooks que usan useContext internamente)
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Hook personalizado
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme debe ser usado dentro de ThemeProvider');
  }
  return context;
};

// Props del Provider
interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: Theme;
}

/**
 * Theme Provider Component
 * Envuelve la aplicación para proporcionar funcionalidad de temas
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = 'light'
}) => {
  const initialSavedTheme = localStorage.getItem('app-theme');

  const [theme, setThemeState] = useState<Theme>(() => {
    const savedTheme = initialSavedTheme as Theme;
    if (savedTheme && savedTheme in themeColors) {
      return savedTheme;
    }

    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }

    return defaultTheme;
  });

  // Aplicar tema al DOM
  useEffect(() => {
    const root = document.documentElement;

    // Remover todas las clases de tema
    root.classList.remove('light', 'dark', 'normal', 'mocha');

    // Aplicar clase del tema actual
    root.classList.add(theme);

    // También mantener data-theme para compatibilidad
    root.setAttribute('data-theme', theme);

    // Guardar en localStorage
    localStorage.setItem('app-theme', theme);

    // Actualizar meta theme-color para Android/iOS
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', themeColors[theme].headerBg);
    }
  }, [theme]);

  // Escuchar cambios en preferencia del sistema
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = (e: MediaQueryListEvent) => {
      if (!initialSavedTheme) {
        setThemeState(e.matches ? 'dark' : 'light');
      }
    };

    // Agregar listener
    mediaQuery.addEventListener('change', handleChange);

    // Cleanup
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [initialSavedTheme]);

  // Función para alternar tema
  const toggleTheme = () => {
    setThemeState(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  // Función para establecer tema específico
  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  // ── Escala de fuente (accesibilidad) ──────────────────────────────────────
  const [fontScale, setFontScaleState] = useState<FontScale>(() => {
    const saved = localStorage.getItem('app-font-scale') as FontScale | null;
    return saved && saved in FONT_SCALE_FACTOR ? saved : 'normal';
  });

  useEffect(() => {
    localStorage.setItem('app-font-scale', fontScale);
    document.documentElement.setAttribute('data-font-scale', fontScale);
  }, [fontScale]);

  const setFontScale = (scale: FontScale) => setFontScaleState(scale);

  // Crear objeto de tema completo
  const themeObject: ThemeObject = {
    name: theme,
    colors: themeColors[theme]
  };

  // Valor del contexto
  const value: ThemeContextType = {
    theme: themeObject,
    themeName: theme,
    toggleTheme,
    setTheme,
    fontScale,
    fontScaleFactor: FONT_SCALE_FACTOR[fontScale],
    setFontScale
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// ThemeContext exportado para uso en hooks que necesitan acceso directo al contexto
export { ThemeContext };
