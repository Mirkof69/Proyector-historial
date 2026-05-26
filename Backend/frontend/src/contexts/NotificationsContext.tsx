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

    useEffect(() => {
        // ✅ AUTHENTICATION FIX: Solo cargar si hay sesión activa
        if (!isAuthenticated) {
            console.log('⚠️ No hay sesión activa - omitiendo carga de notificaciones');
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
