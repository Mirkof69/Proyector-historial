# =============================================================================
# SISTEMA DE PERMISOS PERSONALIZADOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: usuarios
# Descripción: Sistema completo de permisos granulares para controlar el
#              acceso a diferentes funcionalidades del sistema médico.
# Autor: Sistema de Gestión Médica
# Versión: 1.0.0
# Última actualización: 2025-11-14
# =============================================================================

from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS


# =============================================================================
# PERMISOS BÁSICOS
# =============================================================================

class EsAdministrador(BasePermission):
    """
    Permiso que solo permite acceso a administradores.
    """
    message = "Solo los administradores pueden realizar esta acción"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.es_administrador
        )


class EsMedico(BasePermission):
    """
    Permiso que solo permite acceso a médicos.
    """
    message = "Solo los médicos pueden realizar esta acción"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.rol == 'medico'
        )


class EsEnfermero(BasePermission):
    """
    Permiso que solo permite acceso a enfermeros.
    """
    message = "Solo los enfermeros pueden realizar esta acción"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.rol == 'enfermero'
        )


class EsDoctorLaboratorio(BasePermission):
    """
    Permiso que solo permite acceso a doctores de laboratorio.
    """
    message = "Solo los doctores de laboratorio pueden realizar esta acción"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.rol == 'doctor_laboratorio'
        )


class EsPersonalSalud(BasePermission):
    """
    Permiso que permite acceso a todo el personal de salud
    (médicos, enfermeros, doctores de laboratorio).
    """
    message = "Solo el personal de salud puede realizar esta acción"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.es_personal_salud
        )


class EsPaciente(BasePermission):
    """
    Permiso que solo permite acceso a pacientes.
    """
    message = "Solo los pacientes pueden realizar esta acción"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.rol == 'paciente'
        )


# =============================================================================
# PERMISOS DE LECTURA/ESCRITURA
# =============================================================================

class SoloLecturaOAdministrador(BasePermission):
    """
    Permiso que permite lectura a todos los autenticados,
    pero solo administradores pueden modificar.
    """
    message = "Solo los administradores pueden modificar este recurso"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Lectura permitida para todos
        if request.method in SAFE_METHODS:
            return True

        # Escritura solo para administradores
        return request.user.es_administrador


class SoloLecturaOPersonalSalud(BasePermission):
    """
    Permiso que permite lectura a todos los autenticados,
    pero solo personal de salud puede modificar.
    """
    message = "Solo el personal de salud puede modificar este recurso"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Lectura permitida para todos
        if request.method in SAFE_METHODS:
            return True

        # Escritura solo para personal de salud
        return request.user.es_personal_salud


# =============================================================================
# PERMISOS GRANULARES POR FUNCIONALIDAD
# =============================================================================

class PuedeCrearPacientes(BasePermission):
    """
    Permiso para crear nuevos pacientes.
    """
    message = "No tienes permiso para crear pacientes"

    def has_permission(self, request, view):
        if request.method != 'POST':
            return True

        return (
            request.user and
            request.user.is_authenticated and
            (request.user.puede_crear_pacientes or request.user.es_superusuario)
        )


class PuedeEditarPacientes(BasePermission):
    """
    Permiso para editar pacientes existentes.
    """
    message = "No tienes permiso para editar pacientes"

    def has_permission(self, request, view):
        if request.method not in ['PUT', 'PATCH']:
            return True

        return (
            request.user and
            request.user.is_authenticated and
            (request.user.puede_editar_pacientes or request.user.es_superusuario)
        )


class PuedeEliminarPacientes(BasePermission):
    """
    Permiso para eliminar pacientes.
    """
    message = "No tienes permiso para eliminar pacientes"

    def has_permission(self, request, view):
        if request.method != 'DELETE':
            return True

        return (
            request.user and
            request.user.is_authenticated and
            (request.user.puede_eliminar_pacientes or request.user.es_superusuario)
        )


class PuedeVerHistorialCompleto(BasePermission):
    """
    Permiso para ver historial médico completo de pacientes.
    """
    message = "No tienes permiso para ver el historial completo"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.puede_ver_historial_completo or request.user.es_superusuario)
        )


class PuedeRegistrarControles(BasePermission):
    """
    Permiso para registrar controles prenatales.
    """
    message = "No tienes permiso para registrar controles prenatales"

    def has_permission(self, request, view):
        if request.method != 'POST':
            return True

        return (
            request.user and
            request.user.is_authenticated and
            (request.user.puede_registrar_controles or request.user.es_superusuario)
        )


class PuedeSolicitarLaboratorios(BasePermission):
    """
    Permiso para solicitar exámenes de laboratorio.
    """
    message = "No tienes permiso para solicitar exámenes de laboratorio"

    def has_permission(self, request, view):
        if request.method != 'POST':
            return True

        return (
            request.user and
            request.user.is_authenticated and
            (request.user.puede_solicitar_laboratorios or request.user.es_superusuario)
        )


class PuedeRegistrarResultadosLab(BasePermission):
    """
    Permiso para registrar resultados de laboratorio.
    """
    message = "No tienes permiso para registrar resultados de laboratorio"

    def has_permission(self, request, view):
        if request.method != 'POST':
            return True

        return (
            request.user and
            request.user.is_authenticated and
            (request.user.puede_registrar_resultados_lab or request.user.es_superusuario)
        )


class PuedeAgendarCitas(BasePermission):
    """
    Permiso para agendar citas médicas.
    """
    message = "No tienes permiso para agendar citas"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.puede_agendar_citas or request.user.es_superusuario)
        )


class PuedeGenerarReportes(BasePermission):
    """
    Permiso para generar reportes.
    """
    message = "No tienes permiso para generar reportes"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.puede_generar_reportes or request.user.es_superusuario)
        )


# =============================================================================
# PERMISOS DE OBJETO (has_object_permission)
# =============================================================================

class EsPropietarioOPersonalSalud(BasePermission):
    """
    Permiso que permite acceso solo al propietario del objeto
    o al personal de salud.
    """
    message = "Solo puedes acceder a tus propios datos o ser personal de salud"

    def has_object_permission(self, request, view, obj):
        # Personal de salud puede acceder a todo
        if request.user.es_personal_salud:
            return True

        # Pacientes solo pueden acceder a sus propios datos
        # (Asumiendo que obj tiene un campo 'paciente' o 'usuario')
        if hasattr(obj, 'paciente'):
            return obj.paciente.usuario == request.user
        elif hasattr(obj, 'usuario'):
            return obj.usuario == request.user

        return False


class EsPropietario(BasePermission):
    """
    Permiso que solo permite acceso al propietario del objeto.
    """
    message = "Solo puedes acceder a tus propios datos"

    def has_object_permission(self, request, view, obj):
        # Superusuarios pueden acceder a todo
        if request.user.es_superusuario:
            return True

        # Verificar si el objeto tiene usuario asociado
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user

        # Para modelos Usuario, verificar si es el mismo usuario
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id

        return False


class PuedeLeerPeroSoloModificarPropio(BasePermission):
    """
    Permiso que permite lectura a todos,
    pero solo el propietario o administrador puede modificar.
    """
    message = "Solo puedes modificar tus propios datos"

    def has_object_permission(self, request, view, obj):
        # Lectura permitida para todos
        if request.method in SAFE_METHODS:
            return True

        # Administradores pueden modificar todo
        if request.user.es_administrador:
            return True

        # Solo el propietario puede modificar
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id

        return False


# =============================================================================
# PERMISOS COMPUESTOS
# =============================================================================

class PermisosPacientes(BasePermission):
    """
    Permisos completos para la gestión de pacientes.
    Combina crear, editar y eliminar.
    """
    message = "No tienes los permisos necesarios para esta operación con pacientes"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.es_superusuario:
            return True

        # Verificar según el método HTTP
        if request.method == 'POST':
            return request.user.puede_crear_pacientes

        elif request.method in ['PUT', 'PATCH']:
            return request.user.puede_editar_pacientes

        elif request.method == 'DELETE':
            return request.user.puede_eliminar_pacientes

        # GET, HEAD, OPTIONS permitidos para personal de salud
        elif request.method in SAFE_METHODS:
            return request.user.es_personal_salud

        return False


class PermisosControles(BasePermission):
    """
    Permisos completos para la gestión de controles prenatales.
    """
    message = "No tienes los permisos necesarios para esta operación con controles"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.es_superusuario:
            return True

        # Solo médicos y enfermeros pueden crear/modificar controles
        if request.method in ['POST', 'PUT', 'PATCH']:
            return request.user.puede_registrar_controles

        # Lectura permitida para todo el personal de salud
        if request.method in SAFE_METHODS:
            return request.user.es_personal_salud

        # Delete solo administradores
        if request.method == 'DELETE':
            return request.user.es_administrador

        return False


class PermisosLaboratorio(BasePermission):
    """
    Permisos completos para la gestión de laboratorios.
    """
    message = "No tienes los permisos necesarios para esta operación con laboratorios"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.es_superusuario:
            return True

        # Médicos pueden solicitar laboratorios
        if request.method == 'POST' and 'solicitud' in view.action:
            return request.user.puede_solicitar_laboratorios

        # Doctores de laboratorio pueden registrar resultados
        if request.method in ['POST', 'PUT', 'PATCH'] and 'resultado' in view.action:
            return request.user.puede_registrar_resultados_lab

        # Lectura permitida para personal de salud
        if request.method in SAFE_METHODS:
            return request.user.es_personal_salud

        return False


# =============================================================================
# PERMISOS DE USUARIO (perfil propio)
# =============================================================================

class PuedeModificarPerfil(BasePermission):
    """
    Permiso para modificar perfil de usuario.
    Usuarios pueden modificar su propio perfil.
    Administradores pueden modificar cualquier perfil.
    """
    message = "Solo puedes modificar tu propio perfil"

    def has_object_permission(self, request, view, obj):
        # Lectura permitida para el mismo usuario
        if request.method in SAFE_METHODS:
            return obj.id == request.user.id or request.user.es_administrador

        # Modificación solo del propio perfil o administrador
        if request.method in ['PUT', 'PATCH']:
            return obj.id == request.user.id or request.user.es_administrador

        # Eliminación solo administradores
        if request.method == 'DELETE':
            return request.user.es_administrador

        return False


class PuedeCambiarRol(BasePermission):
    """
    Solo administradores pueden cambiar roles de usuarios.
    """
    message = "Solo los administradores pueden cambiar roles de usuarios"

    def has_permission(self, request, view):
        # Verificar si se está intentando cambiar el rol
        if 'rol' in request.data:
            return (
                request.user and
                request.user.is_authenticated and
                request.user.es_administrador
            )
        return True


class PuedeCambiarPermisos(BasePermission):
    """
    Solo administradores pueden cambiar permisos de usuarios.
    """
    message = "Solo los administradores pueden cambiar permisos de usuarios"

    def has_permission(self, request, view):
        # Campos de permisos
        campos_permisos = [
            'puede_crear_pacientes',
            'puede_editar_pacientes',
            'puede_eliminar_pacientes',
            'puede_ver_historial_completo',
            'puede_registrar_controles',
            'puede_solicitar_laboratorios',
            'puede_registrar_resultados_lab',
            'puede_agendar_citas',
            'puede_generar_reportes',
            'es_superusuario',
        ]

        # Verificar si se está intentando cambiar algún permiso
        for campo in campos_permisos:
            if campo in request.data:
                return (
                    request.user and
                    request.user.is_authenticated and
                    request.user.es_administrador
                )

        return True


# =============================================================================
# PERMISOS DE ESTADO
# =============================================================================

class UsuarioActivo(BasePermission):
    """
    Verifica que el usuario esté activo y no eliminado.
    """
    message = "Tu cuenta no está activa o ha sido eliminada"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.activo and
            not request.user.eliminado and
            request.user.estado == 'activo'
        )


class EmailVerificado(BasePermission):
    """
    Requiere que el usuario haya verificado su email.
    """
    message = "Debes verificar tu email antes de continuar"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.email_verificado
        )


class NoRequiereCambioPassword(BasePermission):
    """
    Verifica que el usuario no requiera cambiar su contraseña.
    """
    message = "Debes cambiar tu contraseña antes de continuar"

    def has_permission(self, request, view):
        # Permitir acceso a endpoints de cambio de contraseña
        if 'password' in view.basename or 'cambiar-password' in request.path:
            return True

        return (
            request.user and
            request.user.is_authenticated and
            not request.user.requiere_cambio_password
        )


# =============================================================================
# PERMISOS COMBINADOS CON OR/AND
# =============================================================================

class EsAdministradorOMedicoAsignado(BasePermission):
    """
    Permite acceso a administradores o al médico asignado al paciente.
    """
    message = "Solo administradores o el médico asignado pueden realizar esta acción"

    def has_object_permission(self, request, view, obj):
        if request.user.es_administrador:
            return True

        # Verificar si el usuario es el médico asignado
        if hasattr(obj, 'medico_responsable'):
            return obj.medico_responsable == request.user

        if hasattr(obj, 'embarazo') and hasattr(obj.embarazo, 'medico_responsable'):
            return obj.embarazo.medico_responsable == request.user

        return False


# =============================================================================
# PERMISOS ESPECIALES
# =============================================================================

class PuedeVerReportes(BasePermission):
    """
    Permiso para ver reportes según el rol.
    Pacientes solo ven sus propios reportes.
    Personal de salud ve reportes de sus pacientes.
    Administradores ven todos los reportes.
    """
    message = "No tienes permiso para ver este reporte"

    def has_object_permission(self, request, view, obj):
        if request.user.es_administrador:
            return True

        if request.user.es_personal_salud:
            # Personal de salud puede ver reportes si tiene permiso
            return request.user.puede_generar_reportes

        # Pacientes solo ven sus propios reportes
        if hasattr(obj, 'paciente'):
            return obj.paciente.usuario == request.user

        return False


class PuedeAccederDashboard(BasePermission):
    """
    Permiso para acceder al dashboard según el rol.
    """
    message = "No tienes permiso para acceder al dashboard"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.es_personal_salud or request.user.es_administrador)
        )


# =============================================================================
# UTILIDADES
# =============================================================================

def verificar_permiso_personalizado(usuario, permiso):
    """
    Función auxiliar para verificar permisos personalizados.

    Args:
        usuario: Instancia de Usuario
        permiso: String con el nombre del permiso

    Returns:
        bool: True si el usuario tiene el permiso
    """
    if not usuario or not usuario.is_authenticated:
        return False

    if usuario.es_superusuario:
        return True

    return usuario.tiene_permiso(permiso)


def obtener_permisos_usuario(usuario):
    """
    Obtiene todos los permisos de un usuario.

    Args:
        usuario: Instancia de Usuario

    Returns:
        dict: Diccionario con todos los permisos
    """
    if not usuario:
        return {}

    return {
        'es_superusuario': usuario.es_superusuario,
        'es_administrador': usuario.es_administrador,
        'es_medico': usuario.es_medico,
        'es_personal_salud': usuario.es_personal_salud,
        'puede_crear_pacientes': usuario.puede_crear_pacientes,
        'puede_editar_pacientes': usuario.puede_editar_pacientes,
        'puede_eliminar_pacientes': usuario.puede_eliminar_pacientes,
        'puede_ver_historial_completo': usuario.puede_ver_historial_completo,
        'puede_registrar_controles': usuario.puede_registrar_controles,
        'puede_solicitar_laboratorios': usuario.puede_solicitar_laboratorios,
        'puede_registrar_resultados_lab': usuario.puede_registrar_resultados_lab,
        'puede_agendar_citas': usuario.puede_agendar_citas,
        'puede_generar_reportes': usuario.puede_generar_reportes,
    }


# =============================================================================
# FIN DEL ARCHIVO
# =============================================================================
