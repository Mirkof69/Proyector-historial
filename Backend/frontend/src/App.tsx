import React from 'react';
import { App as AntdApp } from 'antd';
import { ThemeProvider } from './contexts/ThemeContext';
import { NotificationsProvider } from './contexts/NotificationsContext';
import ErrorBoundary from './components/common/ErrorBoundary';
import ThemedConfigProvider from './providers/ThemedConfigProvider';
import AppRoutes from './routes/AppRoutes';

// =============================================================================
// CSS IMPORTS
// =============================================================================
import './styles/global-theme.css';
import './styles/antd-overrides.css';
import './styles/theme-dark.css';
import './index.css';
import './App.css';

/**
 * Shell de la aplicación: torre de providers (error boundary → tema → config
 * antd → notificaciones → antd App) envolviendo el enrutador. La tabla de rutas,
 * el guard de permisos y el catálogo de páginas lazy viven en ./routes.
 */
function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ThemedConfigProvider>
          <NotificationsProvider>
            <AntdApp>
              <AppRoutes />
            </AntdApp>
          </NotificationsProvider>
        </ThemedConfigProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
