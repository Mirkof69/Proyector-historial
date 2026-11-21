import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Typography } from 'antd';
import { WarningOutlined, ReloadOutlined, HomeOutlined } from '@ant-design/icons';

const { Paragraph } = Typography;

// Cada compilación vacía build/: una pestaña abierta antes sigue pidiendo los
// archivos de la versión anterior y la pantalla diferida no carga. Basta recargar
// para tomar la versión nueva; se hace sola, una vez por minuto como máximo.
const CLAVE_RECARGA = 'recarga-por-version-nueva';

export function esVersionNueva(error: Error | null): boolean {
  return !!error && (error.name === 'ChunkLoadError' || /Loading (CSS )?chunk [\w-]+ failed/i.test(error.message));
}

function recargarUnaVez(): boolean {
  try {
    const ultima = Number(sessionStorage.getItem(CLAVE_RECARGA) || 0);
    if (Date.now() - ultima < 60_000) return false;
    sessionStorage.setItem(CLAVE_RECARGA, String(Date.now()));
  } catch {
    return false;
  }
  window.location.reload();
  return true;
}

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (esVersionNueva(error) && recargarUnaVez()) return;
    console.error('ErrorBoundary caught error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  private handleGoHome = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/dashboard';
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'var(--bg-secondary)',
            padding: 24,
          }}
        >
          <Result
            status="error"
            icon={<WarningOutlined style={{ fontSize: 72, color: 'var(--color-peligro)' }} />}
            title={esVersionNueva(this.state.error) ? 'Hay una versión nueva del sistema' : 'Error inesperado en la aplicación'}
            subTitle={esVersionNueva(this.state.error)
              ? 'Recargue la página para usar la versión actualizada.'
              : 'El sistema encontró un problema técnico. Recargue la página o vuelva al inicio.'}
            extra={[
              <Button
                type="primary"
                key="reload"
                icon={<ReloadOutlined />}
                onClick={this.handleReset}
                aria-label="Recargar página"
              >
                Recargar página
              </Button>,
              <Button
                key="home"
                icon={<HomeOutlined />}
                onClick={this.handleGoHome}
                aria-label="Volver al inicio"
              >
                Volver al inicio
              </Button>,
            ]}
          >
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div style={{ marginTop: 24, textAlign: 'left', maxWidth: 700, margin: '24px auto 0' }}>
                <Paragraph strong>Detalles del Error (solo desarrollo):</Paragraph>
                <Paragraph code style={{ fontSize: 12, background: 'var(--color-superficie-2)', padding: 16, borderRadius: 8 }}>
                  {this.state.error.toString()}
                </Paragraph>
                {this.state.errorInfo && (
                  <details style={{ marginTop: 12 }}>
                    <summary style={{ cursor: 'pointer', color: 'var(--color-primario)' }}>
                      Ver Component Stack
                    </summary>
                    <pre
                      style={{
                        background: 'var(--color-superficie-2)',
                        padding: 12,
                        borderRadius: 4,
                        overflow: 'auto',
                        fontSize: 12,
                        maxHeight: 300,
                        marginTop: 8,
                      }}
                    >
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}
          </Result>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
