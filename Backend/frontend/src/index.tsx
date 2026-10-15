import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
// Fuentes empaquetadas (sin Google Fonts: la red del hospital puede no tener
// internet). IBM Plex Sans 400/500/600 para la interfaz, Plex Mono 400/500
// para cifras e identificadores.
import '@fontsource/ibm-plex-sans/400.css';
import '@fontsource/ibm-plex-sans/500.css';
import '@fontsource/ibm-plex-sans/600.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
// Capa global de estilos, en este orden (contrato: docs/DISENO_INTERFAZ.md):
// tokens → Tailwind (preflight + utilidades) → base → antd → layout.
import './styles/tokens.css';
import './index.css';
import './styles/base.css';
import './styles/antd.css';
import './styles/layout.css';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);