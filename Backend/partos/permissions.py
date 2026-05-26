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
        if hasattr(request.user, "rol") and request.user.rol == "administrador":
            return True

        # Verificar si es el creador
        if obj.created_by and obj.created_by.id == request.user.id:
            return True

        # Verificar si es el médico responsable
        if obj.medico_responsable_id and obj.medico_responsable_id == request.user.id:
            return True

        return False


class CanFinalizarParto(permissions.BasePermission):
    """Permiso personalizado: Solo médicos y administradores pueden finalizar partos
    """

    def has_permission(self, request, view):
        """Has permission"""
        if not request.user.is_authenticated:
            return False

        # Verificar si tiene rol de médico o administrador
        if hasattr(request.user, "rol"):
            return request.user.rol in ["medico", "administrador", "enfermera"]

        return False


class CanViewAuditoria(permissions.BasePermission):
    """Permiso personalizado: Solo administradores pueden ver auditoría completa
    """

    def has_permission(self, request, view):
        """Has permission"""
        if not request.user.is_authenticated:
            return False

        # Solo administradores
        if hasattr(request.user, "rol"):
            return request.user.rol == "administrador"

        return False


class CanDeleteParto(permissions.BasePermission):
    """Permiso personalizado: Solo administradores pueden eliminar partos
    """

    def has_object_permission(self, request, view, obj):
        """Has object permission"""
        if request.method != "DELETE":
            return True

        # Solo administradores pueden eliminar
        if hasattr(request.user, "rol"):
            return request.user.rol == "administrador"

        return False


class CanExportData(permissions.BasePermission):
    """Permiso personalizado: Solo médicos y administradores pueden exportar datos
    """

    def has_permission(self, request, view):
        """Has permission"""
        if not request.user.is_authenticated:
            return False

        # Médicos y administradores pueden exportar
        if hasattr(request.user, "rol"):
            return request.user.rol in ["medico", "administrador"]

        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permiso personalizado: Solo el propietario puede editar, otros solo lectura
    """

    def has_object_permission(self, request, view, obj):
        """Has object permission"""
        # Permitir lectura a todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Solo el creador puede editar
        if hasattr(obj, "created_by") and obj.created_by:
            return obj.created_by.id == request.user.id

        return False
