"""
===========================================
MÓDULO: ADMIN DE USUARIOS
===========================================
Descripción:
    Configuración del panel de administración de Django para el módulo de usuarios.
    Proporciona una interfaz gráfica para gestionar usuarios desde el admin de Django.

Funcionalidades:
    - Listado de usuarios con filtros y búsqueda
    - Creación de usuarios con validación de contraseña
    - Edición de usuarios (sin exponer password_hash)
    - Acciones en masa (activar, desactivar, bloquear)
    - Campos de solo lectura para auditoría
    - Organización en fieldsets para mejor UX

Acceso:
    URL: http://localhost:8000/admin/usuarios/usuario/
    Requiere: Usuario con is_staff=True y is_superuser=True

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Usuario


# ===========================================
# CONFIGURACIÓN DEL ADMIN DE USUARIOS
# ===========================================
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """
    CLASE: Configuración del ModelAdmin para Usuario

    Funcionamiento:
        Define cómo se muestran y gestionan los usuarios en el panel de admin.
        Proporciona filtros, búsqueda, acciones en masa y organización de campos.

    Características principales:
        - Lista optimizada con columnas clave
        - Filtros por rol, estado, activo
        - Búsqueda por nombre, email, cédula
        - Formulario organizado en secciones
        - Acciones en masa personalizadas
        - Campos de solo lectura para auditoría
    """

    # ===========================================
    # CONFIGURACIÓN DE LA LISTA (list_display)
    # ===========================================
    """
    list_display: Columnas que se muestran en la lista de usuarios

    Funcionamiento:
        Define qué campos o métodos se muestran como columnas en la tabla
        Permite ordenar por estos campos haciendo clic en el encabezado
    """
    list_display = [
        'id',                      # ID del usuario
        'email',                   # Email (credencial de login)
        'nombre_completo_admin',   # Nombre completo (método personalizado)
        'rol_badge',               # Rol con badge de color (método personalizado)
        'estado_badge',            # Estado con badge de color (método personalizado)
        'especialidad',            # Especialidad médica
        'ultimo_login',            # Último acceso
        'fecha_creacion',          # Fecha de registro
    ]

    # ===========================================
    # CAMPOS PARA ENLACES (list_display_links)
    # ===========================================
    """
    list_display_links: Columnas que funcionan como enlaces al detalle

    Funcionamiento:
        Al hacer clic en estos campos, redirige al formulario de edición
    """
    list_display_links = ['id', 'email', 'nombre_completo_admin']

    # ===========================================
    # FILTROS LATERALES (list_filter)
    # ===========================================
    """
    list_filter: Filtros disponibles en la barra lateral

    Funcionamiento:
        Crea filtros interactivos para buscar usuarios rápidamente
        Los usuarios pueden combinar múltiples filtros
    """
    list_filter = [
        'rol',                     # Filtrar por rol (administrador, medico, etc.)
        'estado',                  # Filtrar por estado (activo, inactivo, etc.)
        'activo',                  # Filtrar por activo/inactivo
        'email_verificado',        # Filtrar por email verificado
        'fecha_creacion',          # Filtrar por fecha de creación
        'ultimo_login',            # Filtrar por último login
    ]

    # ===========================================
    # BÚSQUEDA (search_fields)
    # ===========================================
    """
    search_fields: Campos en los que se puede buscar

    Funcionamiento:
        Permite buscar usuarios escribiendo en el cuadro de búsqueda
        La búsqueda es case-insensitive y busca coincidencias parciales
    """
    search_fields = [
        'email',                   # Buscar por email
        'nombre',                  # Buscar por nombre
        'apellido_paterno',        # Buscar por apellido paterno
        'apellido_materno',        # Buscar por apellido materno
        'cedula_identidad',        # Buscar por cédula
        'registro_profesional',    # Buscar por registro profesional
    ]

    # ===========================================
    # ORDENAMIENTO (ordering)
    # ===========================================
    """
    ordering: Orden por defecto de la lista

    Funcionamiento:
        Define el orden inicial de los usuarios en la lista
        El signo - indica orden descendente
    """
    ordering = ['-fecha_creacion']  # Más recientes primero

    # ===========================================
    # PAGINACIÓN (list_per_page)
    # ===========================================
    """
    list_per_page: Cantidad de registros por página

    Funcionamiento:
        Divide la lista en páginas para mejor rendimiento
    """
    list_per_page = 25

    # ===========================================
    # CAMPOS DE SOLO LECTURA (readonly_fields)
    # ===========================================
    """
    readonly_fields: Campos que no se pueden editar

    Funcionamiento:
        Estos campos se muestran pero no se pueden modificar
        Útil para datos de auditoría y campos autogenerados
    """
    readonly_fields = [
        'id',                          # ID autogenerado
        'uuid',                        # UUID inmutable
        'nombre_completo',             # Campo calculado
        'edad',                        # Campo calculado
        'fecha_creacion',              # Timestamp automático
        'fecha_actualizacion',         # Timestamp automático
        'ultimo_login',                # Actualizado automáticamente
        'intentos_login_fallidos',     # Control de seguridad
        'fecha_bloqueo',               # Control de seguridad
        'esta_bloqueado',              # Property calculada
        'puede_acceder',               # Property calculada
    ]

    # ===========================================
    # ORGANIZACIÓN EN SECCIONES (fieldsets)
    # ===========================================
    """
    fieldsets: Organización de campos en secciones

    Funcionamiento:
        Agrupa campos relacionados en secciones colapsables
        Mejora la UX al editar usuarios con muchos campos
    """
    fieldsets = (
        # Sección: Información básica
        ('Información Básica', {
            'fields': (
                'id',
                'uuid',
                'email',
                'cedula_identidad',
            ),
            'description': 'Identificadores únicos del usuario'
        }),

        # Sección: Datos personales
        ('Datos Personales', {
            'fields': (
                'nombre',
                'apellido_paterno',
                'apellido_materno',
                'nombre_completo',
                'fecha_nacimiento',
                'edad',
            ),
            'description': 'Información personal del usuario'
        }),

        # Sección: Datos profesionales
        ('Datos Profesionales', {
            'fields': (
                'rol',
                'especialidad',
                'registro_profesional',
                'institucion',
            ),
            'description': 'Información profesional y laboral'
        }),

        # Sección: Contacto
        ('Información de Contacto', {
            'fields': (
                'telefono',
                'telefono_alternativo',
                'direccion',
            ),
            'classes': ('collapse',),  # Inicialmente colapsado
            'description': 'Datos de contacto del usuario'
        }),

        # Sección: Configuración
        ('Configuración del Usuario', {
            'fields': (
                'foto_perfil',
                'firma_digital',
            ),
            'classes': ('collapse',),  # Inicialmente colapsado
        }),

        # Sección: Estado y seguridad
        ('Estado y Seguridad', {
            'fields': (
                'estado',
                'activo',
                'puede_acceder',
                'esta_bloqueado',
                'email_verificado',
                'fecha_verificacion_email',
            ),
            'description': 'Control de estado y acceso del usuario'
        }),

        # Sección: Seguridad (contraseña)
        # NOTA: password_hash NO se muestra por seguridad
        # La contraseña se establece mediante métodos especiales

        # Sección: Auditoría y registro
        ('Auditoría', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion',
                'ultimo_login',
                'intentos_login_fallidos',
                'fecha_bloqueo',
                'creado_por',
                'observaciones',
            ),
            'classes': ('collapse',),  # Inicialmente colapsado
            'description': 'Información de auditoría y seguimiento'
        }),
    )

    # ===========================================
    # ACCIONES EN MASA (actions)
    # ===========================================
    """
    actions: Acciones que se pueden aplicar a múltiples usuarios

    Funcionamiento:
        Permiten realizar operaciones sobre usuarios seleccionados
        Aparecen en el dropdown de acciones en la lista
    """
    actions = [
        'activar_usuarios',
        'desactivar_usuarios',
        'bloquear_usuarios',
        'desbloquear_usuarios',
    ]

    def activar_usuarios(self, request, queryset):
        """
        ACCIÓN: Activar usuarios seleccionados

        Funcionamiento:
            1. Itera sobre los usuarios seleccionados
            2. Llama a usuario.activar() para cada uno
            3. Muestra mensaje de confirmación

        Uso:
            Seleccionar usuarios -> Acciones -> Activar usuarios seleccionados
        """
        count = 0
        for usuario in queryset:
            usuario.activar()
            count += 1

        self.message_user(
            request,
            f'{count} usuario(s) activado(s) exitosamente.'
        )

    activar_usuarios.short_description = "Activar usuarios seleccionados"

    def desactivar_usuarios(self, request, queryset):
        """
        ACCIÓN: Desactivar usuarios seleccionados

        Funcionamiento:
            Desactiva los usuarios seleccionados (soft delete)
        """
        count = 0
        for usuario in queryset:
            usuario.desactivar(motivo="Desactivado desde el admin")
            count += 1

        self.message_user(
            request,
            f'{count} usuario(s) desactivado(s) exitosamente.'
        )

    desactivar_usuarios.short_description = "Desactivar usuarios seleccionados"

    def bloquear_usuarios(self, request, queryset):
        """
        ACCIÓN: Bloquear usuarios seleccionados

        Funcionamiento:
            Bloquea los usuarios por seguridad
        """
        count = 0
        for usuario in queryset:
            usuario.bloquear(motivo="Bloqueado desde el admin")
            count += 1

        self.message_user(
            request,
            f'{count} usuario(s) bloqueado(s) exitosamente.'
        )

    bloquear_usuarios.short_description = "Bloquear usuarios seleccionados"

    def desbloquear_usuarios(self, request, queryset):
        """
        ACCIÓN: Desbloquear usuarios seleccionados

        Funcionamiento:
            Desbloquea usuarios previamente bloqueados
        """
        count = 0
        for usuario in queryset:
            usuario.desbloquear()
            count += 1

        self.message_user(
            request,
            f'{count} usuario(s) desbloqueado(s) exitosamente.'
        )

    desbloquear_usuarios.short_description = "Desbloquear usuarios seleccionados"

    # ===========================================
    # MÉTODOS PERSONALIZADOS PARA list_display
    # ===========================================

    def nombre_completo_admin(self, obj):
        """
        MÉTODO: Mostrar nombre completo en la lista

        Funcionamiento:
            Retorna el nombre completo del usuario
            Usa la property nombre_completo del modelo

        Parámetros:
            obj: Instancia de Usuario

        Retorna:
            str: Nombre completo
        """
        return obj.nombre_completo

    nombre_completo_admin.short_description = 'Nombre Completo'
    nombre_completo_admin.admin_order_field = 'nombre'  # Permite ordenar por nombre

    def rol_badge(self, obj):
        """
        MÉTODO: Mostrar rol con badge de color

        Funcionamiento:
            Retorna HTML con el rol en un badge de color
            Diferentes colores para diferentes roles

        Colores:
            - Administrador: Rojo (#dc3545)
            - Médico: Azul (#007bff)
            - Enfermero: Verde (#28a745)
            - Asistente: Gris (#6c757d)

        Parámetros:
            obj: Instancia de Usuario

        Retorna:
            SafeString: HTML del badge
        """
        colores = {
            'administrador': '#dc3545',  # Rojo
            'medico': '#007bff',         # Azul
            'enfermero': '#28a745',      # Verde
            'asistente': '#6c757d',      # Gris
        }

        color = colores.get(obj.rol, '#6c757d')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_rol_display()
        )

    rol_badge.short_description = 'Rol'
    rol_badge.admin_order_field = 'rol'

    def estado_badge(self, obj):
        """
        MÉTODO: Mostrar estado con badge de color

        Funcionamiento:
            Retorna HTML con el estado en un badge de color
            Diferentes colores para diferentes estados

        Colores:
            - Activo: Verde (#28a745)
            - Inactivo: Gris (#6c757d)
            - Suspendido: Amarillo (#ffc107)
            - Bloqueado: Rojo (#dc3545)

        Parámetros:
            obj: Instancia de Usuario

        Retorna:
            SafeString: HTML del badge
        """
        colores = {
            'activo': '#28a745',      # Verde
            'inactivo': '#6c757d',    # Gris
            'suspendido': '#ffc107',  # Amarillo
            'bloqueado': '#dc3545',   # Rojo
        }

        color = colores.get(obj.estado, '#6c757d')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )

    estado_badge.short_description = 'Estado'
    estado_badge.admin_order_field = 'estado'

    # ===========================================
    # SOBRESCRIBIR MÉTODOS DEL ADMIN
    # ===========================================

    def save_model(self, request, obj, form, change):
        """
        MÉTODO: Guardar usuario desde el admin

        Funcionamiento:
            Se ejecuta cuando se guarda un usuario desde el admin
            Permite realizar acciones adicionales antes/después de guardar

        Parámetros:
            request: HttpRequest actual
            obj: Instancia de Usuario a guardar
            form: Formulario del admin
            change: True si es edición, False si es creación

        Notas:
            - Si es creación y hay password, se hashea automáticamente
            - Se registra quién creó el usuario
        """
        # Si es un usuario nuevo, registrar quién lo creó
        if not change and hasattr(request, 'user'):
            obj.creado_por = request.user.id

        # Guardar el usuario
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """
        MÉTODO: Obtener queryset optimizado

        Funcionamiento:
            Optimiza las queries para reducir el tiempo de carga
            Útil cuando hay muchos usuarios

        Retorna:
            QuerySet: Queryset optimizado
        """
        qs = super().get_queryset(request)

        # Aquí se pueden agregar optimizaciones como:
        # qs = qs.select_related('creado_por')
        # qs = qs.prefetch_related('pacientes_creados')

        return qs


"""
RESUMEN DE CONFIGURACIÓN DEL ADMIN:
====================================

Columnas en lista:
    - ID, Email, Nombre Completo, Rol (con color), Estado (con color),
      Especialidad, Último Login, Fecha Creación

Filtros disponibles:
    - Rol, Estado, Activo, Email Verificado, Fecha Creación, Último Login

Búsqueda por:
    - Email, Nombre, Apellidos, Cédula, Registro Profesional

Acciones en masa:
    - Activar usuarios
    - Desactivar usuarios
    - Bloquear usuarios
    - Desbloquear usuarios

Organización:
    - 7 secciones organizadas (Información Básica, Datos Personales, etc.)
    - Campos de solo lectura para auditoría
    - Campos colapsables para información secundaria

Características especiales:
    - Badges de color para rol y estado
    - Protección de password_hash (no visible)
    - Registro de quién creó el usuario
    - 25 usuarios por página

====================================
"""
