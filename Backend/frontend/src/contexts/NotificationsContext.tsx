/**
 * =============================================================================
 * NOTIFICATIONS CONTEXT - Centralized Notification Management
 * =============================================================================
 * Single source of truth for notifications across the entire application
 * Prevents duplicate polling and ensures consistent notification state
 * =============================================================================
 */

import React, { createContext, useState, useEffect, useRef, ReactNode, useCallback, useContext, useMemo } from 'react';
import { notificacionesService, Notificacion } from '../services/notificacionesService';
import { useAuth } from '../hooks/useAuth';
import { API_URL } from '../services/api';

/**
 * URL del WebSocket de notificaciones (ws/notifications/ del backend Channels).
 * El backend autentica vía la cookie httpOnly `access_token`, que el
 * navegador envía automáticamente en el handshake (mismo host).
 *
 * En PRODUCCIÓN la API la sirve un servidor WSGI en el 8000 (waitress: 5–50 ms
 * por petición, medido el 01/10/2026; con uvicorn eran 100–250 ms en Windows)
 * y los WebSockets un uvicorn aparte en el 8010 (INICIAR.bat). En
 * desarrollo un solo uvicorn en el 8000 atiende las dos cosas.
 * `REACT_APP_WS_URL` fija la dirección a mano si el despliegue es otro.
 */
export const PUERTO_WS_PRODUCCION = '8010';

export const getWebSocketUrl = (
    apiUrl: string = API_URL,
    entorno: string | undefined = process.env.NODE_ENV,
    fija: string | undefined = process.env.REACT_APP_WS_URL,
): string => {
    if (fija) return fija;
    let base: string;
    if (apiUrl.startsWith('http')) {
        const url = new URL(apiUrl);
        const proto = url.protocol === 'https:' ? 'wss' : 'ws';
        const puerto = entorno === 'production' && url.port === '8000' ? PUERTO_WS_PRODUCCION : url.port;
        base = `${proto}://${url.hostname}${puerto ? `:${puerto}` : ''}`;
    } else {
        // API relativa (túnel https) -> wss sobre el mismo host
        const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
        base = `${proto}://${window.location.host}`;
    }
    return `${base}/ws/notifications/`;
};

interface NotificationsContextType {
    /** Las últimas pendientes, para el desplegable de la campana. */
    notifications: Notificacion[];
    /** Cuántas hay pendientes EN TOTAL, no cuántas se descargaron. */
    unreadCount: number;
    /** De ésas, cuántas son urgentes o críticas. */
    urgentCount: number;
    loading: boolean;
    refreshNotifications: (silent?: boolean) => Promise<void>;
    markAsRead: (id: number) => Promise<void>;
    markAllAsRead: () => Promise<void>;
}

const NotificationsContext = createContext<NotificationsContextType | undefined>(undefined);

interface NotificationsProviderProps {
    children: ReactNode;
}

export const NotificationsProvider: React.FC<NotificationsProviderProps> = ({ children }) => {
    const [notifications, setNotifications] = useState<Notificacion[]>([]);
    const [loading, setLoading] = useState(false);
    const [unreadCount, setUnreadCount] = useState(0);
    const [urgentCount, setUrgentCount] = useState(0);
    const pollingInterval = useRef<NodeJS.Timeout | null>(null);
    /**
     * Si el WebSocket está vivo, el sondeo sobra: el servidor avisa solo.
     * Antes ambos corrían a la vez, así que cada usuaria pagaba el sondeo
     * completo cada 30 s aunque el tiempo real ya estuviera funcionando.
     */
    const wsConectado = useRef(false);
    const { isAuthenticated } = useAuth();

    /**
     * Refresca la campana con el resumen del servidor.
     *
     * Antes esto llamaba a `listar()`, la lista completa. Medido contra el
     * servidor real, con una médica que tenía 7.136 notificaciones acumuladas:
     * 55 KB y 2,2 s por refresco, cada 30 s y por cada usuaria. Con cien
     * personas trabajando, unas siete peticiones ocupadas de forma permanente
     * en pintar un número.
     *
     * Y el número salía mal: `listar()` viene paginado de 200 en 200, así que
     * contar `!leida` sobre lo recibido topaba el badge en 200 aunque hubiera
     * 7.135 pendientes. El servidor ahora manda el conteo ya hecho.
     */
    const refreshNotifications = useCallback(async (silent = false) => {
        try {
            // ✅ AUTHENTICATION FIX: Verificar que hay token antes de intentar cargar
            if (!isAuthenticated) {
                // No hay sesión - no intentar cargar notificaciones
                return;
            }

            if (!silent) {
                setLoading(true);
            }

            const resumen = await notificacionesService.resumen();

            setNotifications(resumen.ultimas);
            setUnreadCount(resumen.pendientes);
            setUrgentCount(resumen.urgentes);
        } catch (error: any) {
            // ✅ AUTHENTICATION FIX: Solo mostrar error si NO es 401
            if (error?.response?.status !== 401 && error?.message !== 'No refresh token available') {
                console.error('Error fetching notifications:', error);
            }
            // Si es error de autenticación, ignorar silenciosamente
        } finally {
            if (!silent) {
                setLoading(false);
            }
        }
    }, [isAuthenticated]);

    const markAsRead = useCallback(async (id: number) => {
        try {
            await notificacionesService.marcarLeida(id);

            // Update local state optimistically
            setNotifications(prev =>
                prev.map(n => n.id === id ? { ...n, leida: true } : n)
            );

            // Decrease unread count
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch (error) {
            console.error('Error marking notification as read:', error);
            // Refresh to get correct state from server
            await refreshNotifications(true);
        }
    }, [refreshNotifications]);

    const markAllAsRead = useCallback(async () => {
        try {
            await notificacionesService.marcarTodasLeidas();

            // Update local state
            setNotifications(prev => prev.map(n => ({ ...n, leida: true })));
            setUnreadCount(0);
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
            // Refresh to get correct state from server
            await refreshNotifications(true);
        }
    }, [refreshNotifications]);

    // ── WebSocket en tiempo real (ws/notifications/) ─────────────────────────
    // El polling de abajo queda como fallback si el WS no conecta.
    const wsRef = useRef<WebSocket | null>(null);
    const wsRetryRef = useRef<number>(0);

    useEffect(() => {
        if (!isAuthenticated) return;

        let disposed = false;
        let reconnectTimer: NodeJS.Timeout | null = null;

        const connect = () => {
            if (disposed) return;

            try {
                // La cookie httpOnly `access_token` viaja en el handshake WS
                const ws = new WebSocket(getWebSocketUrl());
                wsRef.current = ws;

                ws.onopen = () => {
                    wsRetryRef.current = 0;
                    wsConectado.current = true;
                };

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        // Cualquier notificación entrante refresca la lista completa
                        if (data.type === 'notification' || data.type === 'pending_notifications') {
                            refreshNotifications(true);
                        }
                    } catch {
                        // Mensaje no-JSON: ignorar
                    }
                };

                ws.onclose = (event) => {
                    wsRef.current = null;
                    // Se cayo el tiempo real: el sondeo vuelve a hacer falta.
                    wsConectado.current = false;
                    // 4001 = token inválido: no reintentar hasta re-login
                    if (disposed || event.code === 4001) return;
                    // Backoff exponencial con tope de 60s
                    const delay = Math.min(60000, 2000 * 2 ** wsRetryRef.current);
                    wsRetryRef.current += 1;
                    reconnectTimer = setTimeout(connect, delay);
                };

                ws.onerror = () => {
                    ws.close();
                };
            } catch {
                // WebSocket no soportado o URL inválida: el polling sigue funcionando
            }
        };

        connect();

        return () => {
            disposed = true;
            if (reconnectTimer) clearTimeout(reconnectTimer);
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
        };
    }, [isAuthenticated, refreshNotifications]);

    useEffect(() => {
        // ✅ AUTHENTICATION FIX: Solo cargar si hay sesión activa
        if (!isAuthenticated) {
            return; // No cargar notificaciones si no hay autenticación
        }

        // Initial load (con autenticación válida)
        refreshNotifications();

        // Sondeo de respaldo, SOLO si el WebSocket no está conectado.
        //
        // Antes el sondeo corría siempre, en paralelo al tiempo real, así que
        // cada usuaria pedía la lista completa cada 30 s aunque el servidor ya
        // le estuviera avisando de cada novedad. Ahora, con el WS vivo, el
        // sondeo no hace ninguna petición: el tick comprueba y no llama.
        //
        // El intervalo sube a 60 s porque ya no es la vía principal, es la red
        // de seguridad para cuando el tiempo real no está disponible.
        pollingInterval.current = setInterval(() => {
            if (!isAuthenticated) {
                // Usuario deslogueado - detener polling
                if (pollingInterval.current) {
                    clearInterval(pollingInterval.current);
                    pollingInterval.current = null;
                }
                return;
            }
            if (wsConectado.current) {
                // El tiempo real ya cubre esto. No pedir nada.
                return;
            }
            refreshNotifications(true); // Silent refresh
        }, 60000);

        // Cleanup on unmount
        return () => {
            if (pollingInterval.current) {
                clearInterval(pollingInterval.current);
                pollingInterval.current = null;
            }
        };
    }, [isAuthenticated, refreshNotifications]);

    const contextValue = useMemo(() => ({
        notifications,
        unreadCount,
        urgentCount,
        loading,
        refreshNotifications,
        markAsRead,
        markAllAsRead
    }), [notifications, unreadCount, urgentCount, loading, refreshNotifications, markAsRead, markAllAsRead]);

    return (
        <NotificationsContext.Provider
            value={contextValue}
        >
            {children}
        </NotificationsContext.Provider>
    );
};

/**
 * Custom hook to use notifications context
 * Must be used within NotificationsProvider
 */
export const useNotifications = (): NotificationsContextType => {
    const context = useContext(NotificationsContext);

    if (!context) {
        throw new Error('useNotifications must be used within NotificationsProvider');
    }

    return context;
};

export default NotificationsContext;
