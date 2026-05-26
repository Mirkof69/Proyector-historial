"""=============================================================================
PERMISOS RBAC — Sistema Clínico Perinatal
=============================================================================
Clases de permisos por rol para proteger endpoints según el tipo de usuario.
Aplicar en cada ViewSet usando permission_classes = [EsSoloMedico].
=============================================================================
"""

from rest_framework.permissions import BasePermission


class EsSoloMedico(BasePermission):
    """Solo médicos y administradores pueden acceder."""

    message = "Solo médicos y administradores pueden realizar esta acción."

    def has_permission(self, request, view):
        """Has permission"""
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "rol")
            and request.user.rol in ("medico", "administrador")
        )


class EsMedicoOEnfermera(BasePermission):
    """Médicos, enfermeras y administradores pueden acceder."""

    message = "Solo personal clínico puede realizar esta acción."

    def has_permission(self, request, view):
        """Has permission"""
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "rol")
            and request.user.rol in ("medico", "enfermera", "administrador")
        )


class EsMedicoOEnfermeraOLaboratorista(BasePermission):
    """Médicos, enfermeras, laboratoristas y administradores pueden acceder."""

    message = "Solo personal clínico puede realizar esta acción."

    def has_permission(self, request, view):
        """Has permission"""
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "rol")
            and request.user.rol
            in ("medico", "enfermera", "laboratorista", "administrador")
        )


class EsSoloAdministrador(BasePermission):
    """Solo administradores pueden acceder."""

    message = "Solo administradores pueden realizar esta acción."

    def has_permission(self, request, view):
        """Has permission"""
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "rol")
            and request.user.rol == "administrador"
        )


class PuedeVerAuditoria(BasePermission):
    """Médicos y administradores pueden ver el log de auditoría."""

    message = "Solo médicos y administradores pueden consultar la auditoría."

    def has_permission(self, request, view):
        """Has permission"""
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "rol")
            and request.user.rol in ("medico", "administrador")
        )


class EsLaboratorista(BasePermission):
    """Solo laboratoristas y administradores pueden acceder."""

    message = "Solo laboratoristas pueden realizar esta acción."

    def has_permission(self, request, view):
        """Has permission"""
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "rol")
            and request.user.rol in ("laboratorista", "administrador")
        )


class PuedeLeerOEsMedicoParaEscribir(BasePermission):
    """Lectura: todos los autenticados.
    Escritura (POST/PUT/PATCH/DELETE): solo médicos y administradores.
    """

    message = "Solo médicos pueden modificar registros clínicos."

    def has_permission(self, request, view):
        """Has permission"""
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return hasattr(request.user, "rol") and request.user.rol in (
            "medico",
            "administrador",
        )


# ── Prefijos de URL que solo pueden ver roles clínicos ────────────────────────
_RUTAS_CLINICAS = (
    "/api/embarazos",
    "/api/controles",
    "/api/ecografias",
    "/api/partos",
    "/api/laboratorios",
    "/api/ia",
    "/api/antecedentes",
    "/api/evoluciones",
    "/api/notas-evolucion",
    "/api/calculadoras",
    "/api/vacunas",
    "/api/triaje",
    "/api/ecografias-archivos",
    "/api/reportes",
)


class FetalMedicalPermission(BasePermission):
    """
    Permiso base del sistema (política de mínimo privilegio):
    - superuser / administrador → acceso total
    - medico / laboratorista  → acceso clínico completo
    - enfermera               → triaje, controles, vacunas; NO partos
    - recepcion               → solo citas + listado de pacientes
    """

    message = "No tiene permiso para acceder a este recurso."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        rol = getattr(request.user, "rol", "")
        if rol == "administrador":
            return True
        path = request.path
        # Recepcion: bloqueado de todas las rutas clínicas
        if rol == "recepcion":
            for ruta in _RUTAS_CLINICAS:
                if path.startswith(ruta):
                    self.message = (
                        f"Recepción no tiene acceso a datos clínicos ({ruta}). "
                        "Solo puede gestionar citas y ver el listado de pacientes."
                    )
                    return False
            return True
        # Enfermera: bloqueado de partos y reportes avanzados
        if rol == "enfermera":
            for bloqueado in ("/api/partos", "/api/reportes", "/api/calculadoras-avanzadas"):
                if path.startswith(bloqueado):
                    self.message = f"Enfermería no tiene acceso a {bloqueado}."
                    return False
            return True
        # Médico y laboratorista: acceso clínico total
        if rol in ("medico", "laboratorista"):
            return True
        # Rol desconocido: solo lectura
        return request.method in ("GET", "HEAD", "OPTIONS")
