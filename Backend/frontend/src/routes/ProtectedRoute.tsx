import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { logger } from '../utils/logger';

interface ProtectedRouteProps {
  children: React.ReactElement;
  requiredPermission?: string;
  requireAdmin?: boolean;
}

const ProtectedRoute = ({ children, requiredPermission, requireAdmin }: ProtectedRouteProps) => {
  const location = useLocation();
  const { isAuthenticated, user: currentUser, hasPermission } = useAuth();

  if (!isAuthenticated) {
    logger.log('🔒 Acceso denegado - Redirigiendo a login');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check Admin role
  if (requireAdmin && currentUser?.rol !== 'administrador') {
    console.warn('⛔ Acceso denegado. Se requiere administrador');
    return <Navigate to="/dashboard/404" replace />;
  }

  // Check specific permission
  if (requiredPermission && !hasPermission(requiredPermission)) {
    console.warn(`⛔ Acceso denegado. Falta permiso: ${requiredPermission}`);
    return <Navigate to="/dashboard/404" replace />;
  }

  return children;
};

export default ProtectedRoute;
