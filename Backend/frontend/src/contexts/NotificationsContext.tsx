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
 */
const getWebSocketUrl = (): string => {
    let base: string;
    if (API_URL.startsWith('http')) {
        // http://host:8000/api -> ws://host:8000
        base = API_URL.replace(/^http/, 'ws').replace(/\/api\/?$/, '');
    } else {
        // API relativa (túnel https) -> wss sobre el mismo host
        const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
        base = `${proto}://${window.location.host}`;
    }
    return `${base}/ws/notifications/`;
};

interface NotificationsContextType {
    notifications: Notificacion[];
    unreadCount: number;
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
    const pollingInterval = useRef<NodeJS.Timeout | null>(null);
    const { isAuthenticated } = useAuth();

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

            const data = await notificacionesService.listar();

            // Sort by creation date (newest first)
            const sorted = data.sort((a, b) =>
                new Date(b.fecha_creacion).getTime() - new Date(a.fecha_creacion).getTime()
            );

            setNotifications(sorted);

            // Count unread notifications
            const unread = data.filter(n => !n.leida).length;
            setUnreadCount(unread);
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

        // ✅ SINGLE POLLING INTERVAL for entire application
        // Poll every 30 seconds (instead of every 10 seconds to reduce server load)
        pollingInterval.current = setInterval(() => {
            // Verificar autenticación antes de cada polling
            if (isAuthenticated) {
                refreshNotifications(true); // Silent refresh
            } else {
                // Usuario deslogueado - detener polling
                if (pollingInterval.current) {
                    clearInterval(pollingInterval.current);
                    pollingInterval.current = null;
                }
            }
        }, 30000); // 30 segundos

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
        loading,
        refreshNotifications,
        markAsRead,
        markAllAsRead
    }), [notifications, unreadCount, loading, refreshNotifications, markAsRead, markAllAsRead]);

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
