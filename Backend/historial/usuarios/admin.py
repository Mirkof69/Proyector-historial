# =============================================================================
# CONFIGURACIÓN DEL PANEL DE ADMINISTRACIÓN - USUARIOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: usuarios
# Descripción: Configuración completa del Django Admin para usuarios,
#              sesiones, tokens y gestión completa del sistema.
# Autor: Sistema de Gestión Médica
# Versión: 3.0.0 - EXTENDIDO
# Última actualización: 2025-11-14
# =============================================================================

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Usuario, HistorialSesion, TokenRecuperacion, TokenVerificacionEmail


# =============================================================================
# ADMIN DE USUARIO
# =============================================================================
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """
    Configuración completa del admin para Usuario.
    """
    list_display = [
        'id',
        'email',
        'nombre_completo',
        'rol_badge',
        'especialidad',
        'estado_badge',
        'activo_icon',
        'email_verificado_icon',
        'ultimo_login',
        'fecha_creacion',
    ]

    list_filter = [
        'rol',
        'estado',
        'activo',
        'eliminado',
        'email_verificado',
        'especialidad',
        'es_superusuario',
        'fecha_creacion',
    ]

    search_fields = [
        'email',
        'nombre',
        'apellido_paterno',
        'apellido_materno',
        'cedula_identidad',
        'telefono',
    ]

    readonly_fields = [
        'uuid',
        'nombre_completo',
        'password_hash',
        'fecha_creacion',
        'fecha_modificacion',
        'ultimo_login',
        'ip_ultimo_login',
        'fecha_eliminacion',
        'edad_display',
        'dias_desde_ultimo_cambio_password_display',
    ]

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'uuid',
                'email',
                'email_verificado',
                'password_hash',
            )
        }),
        ('Datos Personales', {
            'fields': (
                'nombre',
                'apellido_paterno',
                'apellido_materno',
                'nombre_completo',
                'fecha_nacimiento',
                'edad_display',
                'genero',
            )
        }),
        ('Identificación Oficial', {
            'fields': (
                'cedula_identidad',
                'departamento_ci',
            )
        }),
        ('Contacto', {
            'fields': (
                'telefono',
                'telefono_secundario',
                'direccion',
                'ciudad',
            )
        }),
        ('Rol y Permisos', {
            'fields': (
                'rol',
                'especialidad',
                'matricula_profesional',
                'institucion',
                'cargo',
                'anos_experiencia',
            )
        }),
        ('Permisos Granulares', {
            'fields': (
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
            ),
            'classes': ('collapse',),
        }),
        ('Estado y Seguridad', {
            'fields': (
                'estado',
                'activo',
                'requiere_cambio_password',
                'ultimo_cambio_password',
                'dias_desde_ultimo_cambio_password_display',
                'intentos_login_fallidos',
                'fecha_bloqueo',
                'razon_bloqueo',
            )
        }),
        ('Sesiones', {
            'fields': (
                'ultimo_login',
                'ip_ultimo_login',
                'user_agent_ultimo_login',
            )
        }),
        ('Preferencias', {
            'fields': (
                'idioma',
                'zona_horaria',
                'notificaciones_email',
                'notificaciones_sms',
            ),
            'classes': ('collapse',),
        }),
        ('Media', {
            'fields': (
                'foto_perfil',
                'firma_digital',
            ),
            'classes': ('collapse',),
        }),
        ('Auditoría', {
            'fields': (
                'fecha_creacion',
                'fecha_modificacion',
                'creado_por',
                'modificado_por',
            ),
            'classes': ('collapse',),
        }),
        ('Soft Delete', {
            'fields': (
                'eliminado',
                'fecha_eliminacion',
                'eliminado_por',
                'razon_eliminacion',
            ),
            'classes': ('collapse',),
        }),
        ('Notas', {
            'fields': (
                'notas_internas',
            ),
            'classes': ('collapse',),
        }),
    )

    actions = [
        'activar_usuarios',
        'desactivar_usuarios',
        'bloquear_usuarios',
        'desbloquear_usuarios',
        'verificar_emails',
    ]

    def rol_badge(self, obj):
        """Muestra el rol con un badge de color"""
        colors = {
            'administrador': '#ff4444',
            'medico': '#00C851',
            'enfermero': '#ffbb33',
            'doctor_laboratorio': '#33b5e5',
            'paciente': '#aa66cc',
        }
        color = colors.get(obj.rol, '#999999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_rol_display()
        )
    rol_badge.short_description = 'Rol'

    def estado_badge(self, obj):
        """Muestra el estado con un badge de color"""
        colors = {
            'activo': '#00C851',
            'inactivo': '#ffbb33',
            'bloqueado': '#ff4444',
            'pendiente': '#33b5e5',
            'eliminado': '#999999',
        }
        color = colors.get(obj.estado, '#999999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'

    def activo_icon(self, obj):
        """Muestra icono de activo/inactivo"""
        if obj.activo:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    activo_icon.short_description = 'Activo'

    def email_verificado_icon(self, obj):
        """Muestra icono de email verificado"""
        if obj.email_verificado:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: orange;">✗</span>')
    email_verificado_icon.short_description = 'Email Verificado'

    def edad_display(self, obj):
        """Muestra la edad calculada"""
        edad = obj.edad
        return f"{edad} años" if edad else "N/A"
    edad_display.short_description = 'Edad'

    def dias_desde_ultimo_cambio_password_display(self, obj):
        """Muestra días desde último cambio de contraseña"""
        dias = obj.dias_desde_ultimo_cambio_password
        if dias is None:
            return "Nunca"
        if dias > 90:
            return format_html('<span style="color: red;">{} días (EXPIRADA)</span>', dias)
        elif dias > 60:
            return format_html('<span style="color: orange;">{} días</span>', dias)
        return f"{dias} días"
    dias_desde_ultimo_cambio_password_display.short_description = 'Días desde cambio de contraseña'

    # Acciones masivas
    def activar_usuarios(self, request, queryset):
        """Activar usuarios seleccionados"""
        count = queryset.update(activo=True, estado='activo')
        self.message_user(request, f'{count} usuario(s) activado(s) exitosamente.')
    activar_usuarios.short_description = 'Activar usuarios seleccionados'

    def desactivar_usuarios(self, request, queryset):
        """Desactivar usuarios seleccionados"""
        count = queryset.update(activo=False, estado='inactivo')
        self.message_user(request, f'{count} usuario(s) desactivado(s) exitosamente.')
    desactivar_usuarios.short_description = 'Desactivar usuarios seleccionados'

    def bloquear_usuarios(self, request, queryset):
        """Bloquear usuarios seleccionados"""
        count = queryset.update(
            estado='bloqueado',
            fecha_bloqueo=timezone.now(),
            razon_bloqueo='Bloqueado por administrador desde panel admin'
        )
        self.message_user(request, f'{count} usuario(s) bloqueado(s) exitosamente.')
    bloquear_usuarios.short_description = 'Bloquear usuarios seleccionados'

    def desbloquear_usuarios(self, request, queryset):
        """Desbloquear usuarios seleccionados"""
        count = queryset.update(
            estado='activo',
            fecha_bloqueo=None,
            razon_bloqueo=None,
            intentos_login_fallidos=0
        )
        self.message_user(request, f'{count} usuario(s) desbloqueado(s) exitosamente.')
    desbloquear_usuarios.short_description = 'Desbloquear usuarios seleccionados'

    def verificar_emails(self, request, queryset):
        """Verificar emails de usuarios seleccionados"""
        count = queryset.update(
            email_verificado=True,
            fecha_verificacion_email=timezone.now()
        )
        self.message_user(request, f'{count} email(s) verificado(s) exitosamente.')
    verificar_emails.short_description = 'Verificar emails seleccionados'


# =============================================================================
# ADMIN DE HISTORIAL DE SESIONES
# =============================================================================
@admin.register(HistorialSesion)
class HistorialSesionAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Historial de Sesiones.
    """
    list_display = [
        'id',
        'usuario_email',
        'accion_badge',
        'exitoso_icon',
        'fecha_hora',
        'ip_address',
        'dispositivo',
        'navegador',
    ]

    list_filter = [
        'accion',
        'exitoso',
        'fecha_hora',
    ]

    search_fields = [
        'usuario__email',
        'usuario__nombre',
        'ip_address',
        'user_agent',
    ]

    readonly_fields = [
        'uuid',
        'usuario',
        'accion',
        'fecha_hora',
        'ip_address',
        'user_agent',
        'dispositivo',
        'navegador',
        'sistema_operativo',
        'ubicacion',
        'exitoso',
        'razon_fallo',
        'token_id',
        'duracion_sesion',
    ]

    def usuario_email(self, obj):
        """Muestra el email del usuario"""
        return obj.usuario.email
    usuario_email.short_description = 'Usuario'

    def accion_badge(self, obj):
        """Muestra la acción con un badge de color"""
        colors = {
            'login': '#00C851',
            'logout': '#33b5e5',
            'login_fallido': '#ff4444',
            'cambio_password': '#ffbb33',
            'recuperacion_password': '#aa66cc',
            'sesion_expirada': '#999999',
        }
        color = colors.get(obj.accion, '#999999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_accion_display()
        )
    accion_badge.short_description = 'Acción'

    def exitoso_icon(self, obj):
        """Muestra icono de éxito/fallo"""
        if obj.exitoso:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    exitoso_icon.short_description = 'Exitoso'

    def has_add_permission(self, request):
        """No permitir crear sesiones manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir modificar sesiones"""
        return False


# =============================================================================
# ADMIN DE TOKENS DE RECUPERACIÓN
# =============================================================================
@admin.register(TokenRecuperacion)
class TokenRecuperacionAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Tokens de Recuperación.
    """
    list_display = [
        'id',
        'usuario_email',
        'token_short',
        'vigente_badge',
        'fecha_creacion',
        'fecha_expiracion',
        'usado_icon',
    ]

    list_filter = [
        'usado',
        'fecha_creacion',
        'fecha_expiracion',
    ]

    search_fields = [
        'usuario__email',
        'token',
        'ip_solicitud',
    ]

    readonly_fields = [
        'uuid',
        'usuario',
        'token',
        'fecha_creacion',
        'fecha_expiracion',
        'usado',
        'fecha_uso',
        'ip_solicitud',
        'ip_uso',
        'vigente_display',
    ]

    def usuario_email(self, obj):
        """Muestra el email del usuario"""
        return obj.usuario.email
    usuario_email.short_description = 'Usuario'

    def token_short(self, obj):
        """Muestra versión acortada del token"""
        return f"{obj.token[:20]}..."
    token_short.short_description = 'Token'

    def vigente_badge(self, obj):
        """Muestra si el token está vigente"""
        if obj.esta_vigente():
            return format_html(
                '<span style="background-color: #00C851; color: white; padding: 3px 10px; border-radius: 3px;">VIGENTE</span>'
            )
        return format_html(
            '<span style="background-color: #ff4444; color: white; padding: 3px 10px; border-radius: 3px;">EXPIRADO/USADO</span>'
        )
    vigente_badge.short_description = 'Estado'

    def usado_icon(self, obj):
        """Muestra icono de usado"""
        if obj.usado:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: orange;">-</span>')
    usado_icon.short_description = 'Usado'

    def vigente_display(self, obj):
        """Muestra si está vigente"""
        return "Sí" if obj.esta_vigente() else "No"
    vigente_display.short_description = 'Vigente'

    def has_add_permission(self, request):
        """No permitir crear tokens manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir modificar tokens"""
        return False


# =============================================================================
# ADMIN DE TOKENS DE VERIFICACIÓN DE EMAIL
# =============================================================================
@admin.register(TokenVerificacionEmail)
class TokenVerificacionEmailAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Tokens de Verificación de Email.
    """
    list_display = [
        'id',
        'usuario_email',
        'token_short',
        'vigente_badge',
        'fecha_creacion',
        'verificado_icon',
    ]

    list_filter = [
        'verificado',
        'fecha_creacion',
        'fecha_expiracion',
    ]

    search_fields = [
        'usuario__email',
        'token',
    ]

    readonly_fields = [
        'uuid',
        'usuario',
        'token',
        'fecha_creacion',
        'fecha_expiracion',
        'verificado',
        'fecha_verificacion',
        'vigente_display',
    ]

    def usuario_email(self, obj):
        """Muestra el email del usuario"""
        return obj.usuario.email
    usuario_email.short_description = 'Usuario'

    def token_short(self, obj):
        """Muestra versión acortada del token"""
        return f"{obj.token[:20]}..."
    token_short.short_description = 'Token'

    def vigente_badge(self, obj):
        """Muestra si el token está vigente"""
        if obj.esta_vigente():
            return format_html(
                '<span style="background-color: #00C851; color: white; padding: 3px 10px; border-radius: 3px;">VIGENTE</span>'
            )
        return format_html(
            '<span style="background-color: #ff4444; color: white; padding: 3px 10px; border-radius: 3px;">EXPIRADO/USADO</span>'
        )
    vigente_badge.short_description = 'Estado'

    def verificado_icon(self, obj):
        """Muestra icono de verificado"""
        if obj.verificado:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: orange;">-</span>')
    verificado_icon.short_description = 'Verificado'

    def vigente_display(self, obj):
        """Muestra si está vigente"""
        return "Sí" if obj.esta_vigente() else "No"
    vigente_display.short_description = 'Vigente'

    def has_add_permission(self, request):
        """No permitir crear tokens manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir modificar tokens"""
        return False


# =============================================================================
# FIN DEL ARCHIVO
# =============================================================================
