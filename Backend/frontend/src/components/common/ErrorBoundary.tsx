import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Typography } from 'antd';
import { WarningOutlined, ReloadOutlined, HomeOutlined } from '@ant-design/icons';

const { Paragraph } = Typography;

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
            background: '#f0f2f5',
            padding: 24,
          }}
        >
          <Result
            status="error"
            icon={<WarningOutlined style={{ fontSize: 72, color: '#ff4d4f' }} />}
            title="Error Inesperado en la Aplicacion"
            subTitle="El sistema ha encontrado un problema tecnico. Por favor, intente recargar la pagina o volver al inicio."
            extra={[
              <Button
                type="primary"
                key="reload"
                icon={<ReloadOutlined />}
                onClick={this.handleReset}
                aria-label="Recargar pagina"
              >
                Recargar Pagina
              </Button>,
              <Button
                key="home"
                icon={<HomeOutlined />}
                onClick={this.handleGoHome}
                aria-label="Volver al inicio"
              >
                Volver al Inicio
              </Button>,
            ]}
          >
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div style={{ marginTop: 24, textAlign: 'left', maxWidth: 700, margin: '24px auto 0' }}>
                <Paragraph strong>Detalles del Error (solo desarrollo):</Paragraph>
                <Paragraph code style={{ fontSize: 12, background: '#fafafa', padding: 16, borderRadius: 8 }}>
                  {this.state.error.toString()}
                </Paragraph>
                {this.state.errorInfo && (
                  <details style={{ marginTop: 12 }}>
                    <summary style={{ cursor: 'pointer', color: '#1890ff' }}>
                      Ver Component Stack
                    </summary>
                    <pre
                      style={{
                        background: '#fafafa',
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
