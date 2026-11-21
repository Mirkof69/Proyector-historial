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
        # MIN, no MAX. Aqui habia un `max(...)` y era un bug grave: como
        # "administrador" (nivel 100) aparece en casi todas las tuplas, el nivel
        # exigido acababa siendo 100 SIEMPRE, y un medico (80) fallaba la
        # comprobacion `nivel >= minimo` aunque su rol estuviera explicitamente
        # entre los permitidos. En la clinica eso significaba que enfermeria no
        # podia registrar un triaje, los medicos no podian escribir evoluciones
        # ni consultar la auditoria, y el laboratorista no podia cargar
        # resultados: solo el administrador usaba esos cinco modulos.
        #
        # El nombre de la variable ya decia lo que habia que calcular: el nivel
        # MINIMO entre los roles permitidos. Quien no este en `self._roles`
        # sigue quedando fuera por la segunda condicion de `has_permission`.
        self._nivel_minimo = min(_ROLE_HIERARCHY.get(r, 0) for r in roles_requeridos)
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


#: Acciones de /api/pacientes/<id>/... con datos clínicos. Recepción registra y
#: busca pacientes, pero antes estas acciones le quedaban abiertas porque el
#: bloqueo iba solo por prefijo y /api/pacientes/ no es un prefijo clínico.
_ACCIONES_CLINICAS_DE_PACIENTE = (
    "/historia-clinica", "/historial-completo", "/antecedentes-", "/examenes-laboratorio",
    "/evaluar-riesgos", "/estadisticas", "/reporte-pdf", "/exportar-",
)


def _es_accion_clinica_de_paciente(path: str) -> bool:
    return path.startswith("/api/pacientes/") and any(a in path for a in _ACCIONES_CLINICAS_DE_PACIENTE)


#: Huecos entre esta clase y la tabla de roles (usuarios/permisos_por_rol.py) que halló la automatización de
#: pruebas (BUG-001, 13/11/2026). En estos módulos el rol solo puede LEER: la API dejaba crear y editar.
_SOLO_LECTURA = {
    "enfermera": ("/api/embarazos", "/api/ecografias", "/api/ecografias-archivos", "/api/laboratorios",
                  "/api/antecedentes"),
    "laboratorista": ("/api/pacientes", "/api/embarazos", "/api/controles", "/api/ecografias",
                      "/api/ecografias-archivos", "/api/citas", "/api/antecedentes"),
}
#: Módulos que la tabla no le da al rol en absoluto (la API se los dejaba leer y escribir).
_SIN_ACCESO = {
    "laboratorista": ("/api/partos", "/api/notas-evolucion", "/api/evoluciones", "/api/vacunas", "/api/reportes",
                      "/api/triaje", "/api/calculadoras-avanzadas"),
}
#: Consultas que viajan por POST (búsquedas): no modifican datos y siguen permitidas en solo lectura.
_CONSULTAS_POR_POST = ("/buscar", "/busqueda")


def _bloqueo_por_tabla_de_roles(rol: str, path: str, metodo: str) -> str | None:
    """Mensaje de rechazo si la tabla de roles no le permite al rol esta operación; None si la permite."""
    for prefijo in _SIN_ACCESO.get(rol, ()):
        if path.startswith(prefijo):
            return f"Su rol no tiene acceso a {prefijo}."
    if metodo not in ("GET", "HEAD", "OPTIONS") and not any(c in path for c in _CONSULTAS_POR_POST):
        for prefijo in _SOLO_LECTURA.get(rol, ()):
            if path.startswith(prefijo):
                return f"Su rol solo puede consultar {prefijo}; no puede crear ni modificar registros."
    return None


class FetalMedicalPermission(BasePermission):
    """
    Permiso base del sistema (política de mínimo privilegio):
    - superuser / administrador -> acceso total
    - medico                     -> acceso clínico completo
    - laboratorista              -> laboratorio; solo lectura de pacientes, embarazos, controles,
                                    ecografías, citas y antecedentes; sin partos, notas, vacunas ni reportes
    - enfermera                  -> triaje, controles, vacunas; solo lectura de embarazos, ecografías,
                                    laboratorio y antecedentes; NO partos
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
            if _es_accion_clinica_de_paciente(path):
                self.message = "Recepción no tiene acceso a la información clínica de la paciente."
                return False
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
            motivo = _bloqueo_por_tabla_de_roles(rol, path, request.method)
            if motivo:
                self.message = motivo
                return False
            return True
        if rol == "laboratorista":
            motivo = _bloqueo_por_tabla_de_roles(rol, path, request.method)
            if motivo:
                self.message = motivo
                return False
            return True
        if rol == "medico":
            return True
        # Rol desconocido o vacío: sin acceso. Antes podía LEER todo el sistema.
        self.message = "Su usuario no tiene un rol asignado. Pida al administrador que le asigne uno."
        return False
