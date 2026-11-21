import { useCallback } from 'react';
import { authService } from '../services/authService';

/**
 * @deprecated Usa `useAuth().hasPermission` de AuthContext en su lugar.
 * Este hook no reacciona a cambios de estado de autenticación.
 * Se eliminará en una versión futura.
 */
export const usePermissions = () => {
  /**
   * Verifica si el usuario tiene un permiso específico
   */
  const hasPermission = useCallback((permission: string): boolean => {
    try {
      return authService.hasPermission(permission);
    } catch (error) {
      console.warn('Error verificando permiso:', permission, error);
      return false;
    }
  }, []);

  /**
   * Verifica si el usuario tiene al menos uno de los permisos
   */
  const hasAnyPermission = useCallback((permissions: string[]): boolean => {
    return permissions.some(p => hasPermission(p));
  }, [hasPermission]);

  /**
   * Verifica si el usuario tiene todos los permisos
   */
  const hasAllPermissions = useCallback((permissions: string[]): boolean => {
    return permissions.every(p => hasPermission(p));
  }, [hasPermission]);

  /**
   * Verifica si el usuario puede ver un modelo
   */
  const canView = useCallback((model: string): boolean => {
    return hasPermission(`view_${model}`);
  }, [hasPermission]);

  /**
   * Verifica si el usuario puede agregar un modelo
   */
  const canAdd = useCallback((model: string): boolean => {
    return hasPermission(`add_${model}`);
  }, [hasPermission]);

  /**
   * Verifica si el usuario puede cambiar/editar un modelo
   */
  const canChange = useCallback((model: string): boolean => {
    return hasPermission(`change_${model}`);
  }, [hasPermission]);

  /**
   * Verifica si el usuario puede eliminar un modelo
   */
  const canDelete = useCallback((model: string): boolean => {
    return hasPermission(`delete_${model}`);
  }, [hasPermission]);

  /**
   * Verifica si el usuario es administrador
   */
  const isAdmin = useCallback((): boolean => {
    try {
      const user = authService.getCurrentUser();
      return user?.is_superuser || user?.is_staff || false;
    } catch (error) {
      console.warn('Error verificando admin:', error);
      return false;
    }
  }, []);

  /**
   * Verifica si el usuario tiene acceso completo (CRUD) a un modelo
   */
  const hasFullAccess = useCallback((model: string): boolean => {
    return (
      canView(model) &&
      canAdd(model) &&
      canChange(model) &&
      canDelete(model)
    );
  }, [canView, canAdd, canChange, canDelete]);

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    canView,
    canAdd,
    canChange,
    canDelete,
    isAdmin,
    hasFullAccess,
  };
};
