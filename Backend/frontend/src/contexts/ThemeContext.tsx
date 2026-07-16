/**
 * =============================================================================
 * THEME CONTEXT - SISTEMA DE TEMAS REACT
 * =============================================================================
 * Proporciona contexto global para el tema (claro/oscuro)
 * Maneja localStorage y preferencias del sistema
 * =============================================================================
 */

import React, { createContext, useState, useEffect, ReactNode, useContext } from 'react';

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

// Definición de colores para cada tema
const themeColors: Record<Theme, ThemeColors> = {
  light: {
    primary: '#1890ff',
    secondary: '#52c41a',
    background: '#f0f2f5',
    surface: '#ffffff',
    text: '#262626',
    textSecondary: '#8c8c8c',
    border: '#d9d9d9',
    error: '#ff4d4f',
    warning: '#faad14',
    success: '#52c41a',
    info: '#1890ff',
    headerBg: '#ffffff',
    sidebarBg: '#001529'
  },
  normal: {
    primary: '#1890ff',
    secondary: '#52c41a',
    background: '#f0f2f5',
    surface: '#ffffff',
    text: '#262626',
    textSecondary: '#8c8c8c',
    border: '#d9d9d9',
    error: '#ff4d4f',
    warning: '#faad14',
    success: '#52c41a',
    info: '#1890ff',
    headerBg: '#ffffff',
    sidebarBg: '#001529'
  },
  dark: {
    primary: '#177ddc',
    secondary: '#49aa19',
    background: '#141414',
    surface: '#1f1f1f',
    text: '#e8e8e8',
    textSecondary: '#a6a6a6',
    border: '#434343',
    error: '#a61d24',
    warning: '#d89614',
    success: '#49aa19',
    info: '#177ddc',
    headerBg: '#1f1f1f',
    sidebarBg: '#000c17'
  },
  mocha: {
    primary: '#d4a574',
    secondary: '#8b7355',
    background: '#2b2420',
    surface: '#3a3330',
    text: '#f5e6d3',
    textSecondary: '#c4b5a0',
    border: '#5a504a',
    error: '#d97757',
    warning: '#e6b85c',
    success: '#9ac273',
    info: '#7eb3d4',
    headerBg: '#3a3330',
    sidebarBg: '#1a1614'
  }
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
    if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
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
      const themeColors: Record<Theme, string> = {
        light: '#ffffff',
        normal: '#ffffff',
        dark: '#0a0a0a',
        mocha: '#2b2420'
      };
      metaThemeColor.setAttribute('content', themeColors[theme]);
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
