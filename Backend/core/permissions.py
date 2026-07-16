"""=============================================================================
PERMISOS RBAC — Sistema Clínico Perinatal
=============================================================================
Clases de permisos por rol para proteger endpoints según el tipo de usuario.
=============================================================================
"""

from rest_framework.permissions import BasePermission

_ROLE_HIERARCHY = {
    "administrador": 100,
    "medico": 80,
    "laboratorista": 70,
    "enfermera": 60,
    "recepcion": 10,
}


def _get_role_level(user) -> int:
    return _ROLE_HIERARCHY.get(getattr(user, "rol", ""), 0)


class RolPermiso(BasePermission):
    """Permiso genérico basado en nivel mínimo de rol.
    Las instancias son reutilizables como clases vía __call__ (compatible con DRF)."""
    def __init__(self, roles_requeridos: tuple[str, ...], mensaje: str = ""):
        self._roles = roles_requeridos
        self._nivel_minimo = max(_ROLE_HIERARCHY.get(r, 0) for r in roles_requeridos)
        self.message = mensaje or f"Se requiere uno de estos roles: {', '.join(roles_requeridos)}"

    def __call__(self):
        return self

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and _get_role_level(request.user) >= self._nivel_minimo
            and getattr(request.user, "rol", "") in self._roles
        )


EsSoloMedico = RolPermiso(
    ("medico", "administrador"),
    "Solo médicos y administradores pueden realizar esta acción.",
)
EsMedicoOEnfermera = RolPermiso(
    ("medico", "enfermera", "administrador"),
    "Solo personal clínico puede realizar esta acción.",
)
EsMedicoOEnfermeraOLaboratorista = RolPermiso(
    ("medico", "enfermera", "laboratorista", "administrador"),
    "Solo personal clínico puede realizar esta acción.",
)
EsSoloAdministrador = RolPermiso(
    ("administrador",),
    "Solo administradores pueden realizar esta acción.",
)
PuedeVerAuditoria = RolPermiso(
    ("medico", "administrador"),
    "Solo médicos y administradores pueden consultar la auditoría.",
)
EsLaboratorista = RolPermiso(
    ("laboratorista", "administrador"),
    "Solo laboratoristas pueden realizar esta acción.",
)


class PuedeLeerOEsMedicoParaEscribir(BasePermission):
    """Lectura: todos los autenticados.
    Escritura (POST/PUT/PATCH/DELETE): solo médicos y administradores.
    """

    message = "Solo médicos pueden modificar registros clínicos."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return getattr(request.user, "rol", "") in ("medico", "administrador")


_RUTAS_CLINICAS = (
    "/api/embarazos", "/api/controles", "/api/ecografias", "/api/partos",
    "/api/laboratorios", "/api/ia", "/api/antecedentes", "/api/evoluciones",
    "/api/notas-evolucion", "/api/calculadoras", "/api/vacunas", "/api/triaje",
    "/api/ecografias-archivos", "/api/reportes",
)


class FetalMedicalPermission(BasePermission):
    """
    Permiso base del sistema (política de mínimo privilegio):
    - superuser / administrador -> acceso total
    - medico / laboratorista     -> acceso clínico completo
    - enfermera                  -> triaje, controles, vacunas; NO partos
    - recepcion                  -> solo citas + listado de pacientes
    """

    message = "No tiene permiso para acceder a este recurso."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if getattr(request.user, "is_superuser", False):
            return True
        rol = getattr(request.user, "rol", "")
        if rol == "administrador":
            return True
        path = request.path
        if rol == "recepcion":
            for ruta in _RUTAS_CLINICAS:
                if path.startswith(ruta):
                    self.message = (
                        f"Recepción no tiene acceso a datos clínicos ({ruta}). "
                        "Solo puede gestionar citas y ver el listado de pacientes."
                    )
                    return False
            return True
        if rol == "enfermera":
            for bloqueado in ("/api/partos", "/api/reportes", "/api/calculadoras-avanzadas"):
                if path.startswith(bloqueado):
                    self.message = f"Enfermería no tiene acceso a {bloqueado}."
                    return False
            return True
        if rol in ("medico", "laboratorista"):
            return True
        return request.method in ("GET", "HEAD", "OPTIONS")
