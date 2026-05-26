/**
 * =============================================================================
 * SYSTEM DIAGNOSTICS HOOK
 * =============================================================================
 * Hook que captura errores del sistema en tiempo real y los envía al IA
 * Detecta: errores 404, 500, errores de red, errores de consola, etc.
 * =============================================================================
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface SystemError {
    timestamp: string;
    type: 'network' | 'console' | 'api' | 'render';
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    details: {
        url?: string;
        status?: number;
        method?: string;
        stack?: string;
        component?: string;
    };
}

const useSystemDiagnostics = () => {
    const [errors, setErrors] = useState<SystemError[]>([]);
    const [isMonitoring, setIsMonitoring] = useState(false);
    const isMountedRef = useRef<boolean>(false);

    // Capturar errores de red (fetch/axios)
    useEffect(() => {
        if (!isMonitoring) return;

        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);

                // Capturar errores 4xx y 5xx
                if (!response.ok) {
                    const error: SystemError = {
                        timestamp: new Date().toISOString(),
                        type: 'network',
                        severity: response.status >= 500 ? 'critical' : 'high',
                        message: `Error ${response.status}: ${response.statusText}`,
                        details: {
                            url: args[0] as string,
                            status: response.status,
                            method: (args[1] as any)?.method || 'GET'
                        }
                    };

                    if (isMountedRef.current) {
                        setErrors(prev => [...prev.slice(-9), error]);
                    }
                }

                return response;
            } catch (err: any) {
                const error: SystemError = {
                    timestamp: new Date().toISOString(),
                    type: 'network',
                    severity: 'critical',
                    message: `Network Error: ${err.message}`,
                    details: {
                        url: args[0] as string,
                        stack: err.stack
                    }
                };

                if (isMountedRef.current) {
                    setErrors(prev => [...prev.slice(-9), error]);
                }
                throw err;
            }
        };

        return () => {
            window.fetch = originalFetch;
        };
    }, [isMonitoring]);

    // Capturar errores de consola
    useEffect(() => {
        if (!isMonitoring) return;

        isMountedRef.current = true;
        const timeoutIds = new Set<NodeJS.Timeout>();

        const originalError = console.error;
        const originalWarn = console.warn;

        const safeSetError = (error: SystemError) => {
            // Use setTimeout to avoid setState during render
            const id = setTimeout(() => {
                if (isMountedRef.current) {
                    setErrors(prev => [...prev.slice(-9), error]);
                }
                timeoutIds.delete(id);
            }, 0);
            timeoutIds.add(id);
        };

        console.error = (...args: any[]) => {
            const message = args.map(arg =>
                typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' ');

            const error: SystemError = {
                timestamp: new Date().toISOString(),
                type: 'console',
                severity: 'medium',
                message: `Console Error: ${message}`,
                details: {}
            };

            safeSetError(error);
            originalError.apply(console, args);
        };

        console.warn = (...args: any[]) => {
            const message = args.map(arg =>
                typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' ');

            const error: SystemError = {
                timestamp: new Date().toISOString(),
                type: 'console',
                severity: 'low',
                message: `Console Warning: ${message}`,
                details: {}
            };

            safeSetError(error);
            originalWarn.apply(console, args);
        };

        return () => {
            console.error = originalError;
            console.warn = originalWarn;
            isMountedRef.current = false;
            timeoutIds.forEach(id => clearTimeout(id));
            timeoutIds.clear();
        };
    }, [isMonitoring]);

    // Capturar errores no manejados
    useEffect(() => {
        if (!isMonitoring) return;

        const handleError = (event: ErrorEvent) => {
            const error: SystemError = {
                timestamp: new Date().toISOString(),
                type: 'render',
                severity: 'high',
                message: event.message,
                details: {
                    stack: event.error?.stack,
                    url: event.filename
                }
            };

            if (isMountedRef.current) {
                setErrors(prev => [...prev.slice(-9), error]);
            }
        };

        window.addEventListener('error', handleError);
        return () => window.removeEventListener('error', handleError);
    }, [isMonitoring]);

    const interpretError = useCallback((error: SystemError): string => {
        let interpretation = `🔍 **Diagnóstico del Error:**\n\n`;
        interpretation += `⏰ **Cuándo:** ${new Date(error.timestamp).toLocaleString('es-ES')}\n`;
        interpretation += `📍 **Dónde:** ${error.details.url || 'N/A'}\n`;
        interpretation += `⚠️ **Gravedad:** ${error.severity.toUpperCase()}\n\n`;

        // Interpretación según el tipo y código
        if (error.details.status === 404) {
            interpretation += `**Problema:** La página o recurso solicitado no existe.\n\n`;
            interpretation += `**Posibles Causas:**\n`;
            interpretation += `• La URL está mal escrita\n`;
            interpretation += `• El recurso fue movido o eliminado\n`;
            interpretation += `• El endpoint de la API no existe\n\n`;
            interpretation += `**Soluciones:**\n`;
            interpretation += `✅ Verifica la URL: \`${error.details.url}\`\n`;
            interpretation += `✅ Revisa las rutas en el código\n`;
            interpretation += `✅ Contacta al administrador si el problema persiste\n`;
        } else if (error.details.status === 500) {
            interpretation += `**Problema:** Error interno del servidor.\n\n`;
            interpretation += `**Posibles Causas:**\n`;
            interpretation += `• Error en el código del backend\n`;
            interpretation += `• Base de datos no responde\n`;
            interpretation += `• Configuración incorrecta del servidor\n\n`;
            interpretation += `**Soluciones:**\n`;
            interpretation += `✅ Recarga la página (F5)\n`;
            interpretation += `✅ Revisa los logs del servidor\n`;
            interpretation += `✅ Contacta al equipo de desarrollo\n`;
        } else if (error.details.status === 401 || error.details.status === 403) {
            interpretation += `**Problema:** ${error.details.status === 401 ? 'No autenticado' : 'No autorizado'}.\n\n`;
            interpretation += `**Posibles Causas:**\n`;
            interpretation += `• Sesión expirada\n`;
            interpretation += `• Token de autenticación inválido\n`;
            interpretation += `• Permisos insuficientes\n\n`;
            interpretation += `**Soluciones:**\n`;
            interpretation += `✅ Vuelve a iniciar sesión\n`;
            interpretation += `✅ Verifica tus permisos de usuario\n`;
            interpretation += `✅ Contacta al administrador para solicitar acceso\n`;
        } else if (error.type === 'network' && !error.details.status) {
            interpretation += `**Problema:** Error de conexión de red.\n\n`;
            interpretation += `**Posibles Causas:**\n`;
            interpretation += `• Sin conexión a internet\n`;
            interpretation += `• Servidor backend no disponible\n`;
            interpretation += `• Firewall bloqueando la conexión\n\n`;
            interpretation += `**Soluciones:**\n`;
            interpretation += `✅ Verifica tu conexión a internet\n`;
            interpretation += `✅ Comprueba que el servidor esté corriendo\n`;
            interpretation += `✅ Revisa la configuración del firewall\n`;
        } else {
            interpretation += `**Mensaje:** ${error.message}\n\n`;
            interpretation += `**Recomendación:**\n`;
            interpretation += `✅ Revisa los detalles en la consola del navegador (F12)\n`;
            interpretation += `✅ Reporta este error al equipo técnico\n`;
        }

        return interpretation;
    }, []);

    const clearErrors = useCallback(() => {
        setErrors([]);
    }, []);

    const toggleMonitoring = useCallback(() => {
        setIsMonitoring(prev => !prev);
    }, []);

    return {
        errors,
        isMonitoring,
        toggleMonitoring,
        interpretError,
        clearErrors,
        hasErrors: errors.length > 0,
        criticalErrors: errors.filter(e => e.severity === 'critical').length,
        highErrors: errors.filter(e => e.severity === 'high').length
    };
};

export default useSystemDiagnostics;
