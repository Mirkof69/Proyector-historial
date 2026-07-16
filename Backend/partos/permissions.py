"""=============================================================================
MÓDULO: PARTOS - PERMISOS PERSONALIZADOS
=============================================================================
Permisos personalizados para control de acceso a partos
=============================================================================
"""

from rest_framework import permissions


class CanEditParto(permissions.BasePermission):
    """Permiso personalizado: Solo el creador, médico responsable o administradores pueden editar
    """

    def has_object_permission(self, request, view, obj):
        """Has object permission"""
        # Permitir lectura a todos los usuarios autenticados
        if request.method in permissions.SAFE_METHODS:
            return True

        # Verificar si es administrador
        if getattr(request.user, 'rol', None) == "administrador":
            return True

        # Verificar si es el creador
        created_by = getattr(obj, 'created_by', None)
        if created_by and getattr(created_by, 'id', None) == getattr(request.user, 'id', None):
            return True

        # Verificar si es el médico responsable
        return bool(getattr(obj, 'medico_responsable_id', None) and getattr(obj, 'medico_responsable_id', None) == getattr(request.user, 'id', None))


class CanFinalizarParto(permissions.BasePermission):
    """Permiso personalizado: Solo médicos y administradores pueden finalizar partos
    """

    def has_permission(self, request, view):
        """Has permission"""
        if not getattr(request.user, 'is_authenticated', False):
            return False

        # Verificar si tiene rol de médico o administrador
        return getattr(request.user, 'rol', None) in ["medico", "administrador", "enfermera"]


class CanViewAuditoria(permissions.BasePermission):
    """Permiso personalizado: Solo administradores pueden ver auditoría completa
    """

    def has_permission(self, request, view):
        """Has permission"""
        if not getattr(request.user, 'is_authenticated', False):
            return False

        # Solo administradores
        return getattr(request.user, 'rol', None) == "administrador"


class CanDeleteParto(permissions.BasePermission):
    """Permiso personalizado: Solo administradores pueden eliminar partos
    """

    def has_object_permission(self, request, view, obj):
        """Has object permission"""
        if request.method != "DELETE":
            return True

        # Solo administradores pueden eliminar
        return getattr(request.user, 'rol', None) == "administrador"


class CanExportData(permissions.BasePermission):
    """Permiso personalizado: Solo médicos y administradores pueden exportar datos
    """

    def has_permission(self, request, view):
        """Has permission"""
        if not getattr(request.user, 'is_authenticated', False):
            return False

        # Médicos y administradores pueden exportar
        return getattr(request.user, 'rol', None) in ["medico", "administrador"]


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permiso personalizado: Solo el propietario puede editar, otros solo lectura
    """

    def has_object_permission(self, request, view, obj):
        """Has object permission"""
        # Permitir lectura a todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Solo el creador puede editar
        created_by = getattr(obj, 'created_by', None)
        if created_by:
            return getattr(created_by, 'id', None) == getattr(request.user, 'id', None)

        return False
