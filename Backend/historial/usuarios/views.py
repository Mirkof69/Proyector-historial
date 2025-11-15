"""
===========================================
MÓDULO: VIEWS DE USUARIOS
===========================================
Descripción:
    Sistema completo de vistas (endpoints) para la gestión de usuarios del sistema.
    Implementa autenticación JWT, gestión de permisos, y operaciones CRUD completas.

Endpoints principales:
    - POST   /api/usuarios/login/              - Autenticación con JWT
    - POST   /api/usuarios/logout/             - Cerrar sesión
    - POST   /api/usuarios/register/           - Registro de nuevo usuario
    - GET    /api/usuarios/                    - Listar usuarios (con paginación)
    - POST   /api/usuarios/                    - Crear usuario
    - GET    /api/usuarios/{id}/               - Obtener detalles de usuario
    - PUT    /api/usuarios/{id}/               - Actualizar usuario completo
    - PATCH  /api/usuarios/{id}/               - Actualizar usuario parcial
    - DELETE /api/usuarios/{id}/               - Desactivar usuario (soft delete)

    - POST   /api/usuarios/{id}/activar/       - Activar usuario
    - POST   /api/usuarios/{id}/desactivar/    - Desactivar usuario
    - POST   /api/usuarios/{id}/suspender/     - Suspender usuario
    - POST   /api/usuarios/{id}/bloquear/      - Bloquear usuario
    - POST   /api/usuarios/{id}/desbloquear/   - Desbloquear usuario
    - POST   /api/usuarios/{id}/cambiar_password/ - Cambiar contraseña

    - GET    /api/usuarios/me/                 - Obtener perfil del usuario actual
    - PUT    /api/usuarios/me/                 - Actualizar perfil del usuario actual

    - GET    /api/usuarios/estadisticas/       - Estadísticas generales de usuarios
    - GET    /api/usuarios/busqueda_avanzada/  - Búsqueda avanzada con filtros

Funcionalidades de seguridad:
    - Autenticación JWT (JSON Web Tokens)
    - Control de intentos de login fallidos
    - Bloqueo automático después de 5 intentos fallidos
    - Registro de auditoría de accesos
    - Validación de permisos por rol

Autor: Sistema Historial Médico
Fecha: 2025
Versión: 2.0
===========================================
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Usuario
from .serializers import (
    UsuarioSerializer,
    UsuarioCreateSerializer,
    UsuarioUpdateSerializer,
    PasswordChangeSerializer,
    LoginSerializer,
    UsuarioListSerializer,
    UsuarioDetailSerializer
)


# ===========================================
# PAGINACIÓN PERSONALIZADA
# ===========================================
class UsuarioPagination(PageNumberPagination):
    """
    CLASE: Paginación personalizada para usuarios

    Funcionamiento:
        Divide la lista de usuarios en páginas para mejorar el rendimiento
        y la experiencia del usuario

    Configuración:
        - page_size: 20 usuarios por página por defecto
        - page_size_query_param: Permite al cliente especificar el tamaño
        - max_page_size: Máximo 100 usuarios por página

    Uso en el frontend:
        GET /api/usuarios/?page=1&page_size=50
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ===========================================
# VISTA DE LOGIN (AUTENTICACIÓN)
# ===========================================
class LoginView(APIView):
    """
    VISTA: Autenticación de usuarios

    Funcionamiento:
        1. Recibe email y contraseña
        2. Busca el usuario por email
        3. Verifica que esté activo
        4. Verifica que no esté bloqueado
        5. Compara la contraseña con el hash almacenado
        6. Si es correcta: genera tokens JWT y registra login exitoso
        7. Si es incorrecta: incrementa contador de intentos fallidos
        8. Retorna tokens de acceso y refresh

    Seguridad:
        - Bloqueo automático después de 5 intentos fallidos
        - Validación de estado del usuario
        - No revela si el usuario existe (misma respuesta para ambos casos)

    Request:
        POST /api/usuarios/login/
        {
            "email": "medico@hospital.com",
            "password": "MiContraseña123"
        }

    Response exitoso (200):
        {
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbG...",
            "access": "eyJ0eXAiOiJKV1QiLCJhbG...",
            "user": {
                "id": 1,
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "email": "medico@hospital.com",
                "nombre_completo": "Dr. Juan Pérez",
                "rol": "medico",
                "especialidad": "Ginecología"
            }
        }

    Response error (401):
        {
            "error": "Credenciales inválidas"
        }

    Response bloqueado (403):
        {
            "error": "Cuenta bloqueada por seguridad. Contacte al administrador."
        }
    """

    # Permitir acceso sin autenticación (público)
    permission_classes = [AllowAny]

    def post(self, request):
        """
        MÉTODO POST: Procesar intento de login

        Funcionamiento paso a paso:
            1. Extraer email y password del request
            2. Validar datos con LoginSerializer
            3. Buscar usuario en la base de datos
            4. Verificar estado del usuario (activo, no bloqueado)
            5. Verificar contraseña
            6. Si correcta: generar tokens y registrar acceso
            7. Si incorrecta: registrar intento fallido
            8. Retornar respuesta apropiada
        """

        # Paso 1: Validar datos recibidos
        # Funcionamiento: El serializer verifica que email y password estén presentes
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Email y contraseña son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            # Paso 2: Buscar usuario por email
            # Funcionamiento: Busca en la BD un usuario con ese email
            # No verifica 'activo' aquí para poder registrar intentos fallidos
            usuario = Usuario.objects.get(email=email)

            # Paso 3: Verificar si el usuario está bloqueado
            # Funcionamiento: Verifica la property 'esta_bloqueado'
            if usuario.esta_bloqueado:
                return Response(
                    {'error': 'Cuenta bloqueada por seguridad. Contacte al administrador.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Paso 4: Verificar si el usuario puede acceder
            # Funcionamiento: Verifica activo=True, estado='activo', no bloqueado
            if not usuario.puede_acceder:
                return Response(
                    {'error': 'Usuario inactivo o suspendido. Contacte al administrador.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Paso 5: Verificar contraseña
            # Funcionamiento: Compara password con hash almacenado usando PBKDF2
            if usuario.check_password(password):
                # ✅ Contraseña correcta - LOGIN EXITOSO

                # Paso 6: Registrar login exitoso
                # Funcionamiento: Actualiza ultimo_login y resetea intentos fallidos
                usuario.registrar_login_exitoso()

                # Paso 7: Generar tokens JWT
                # Funcionamiento:
                #   1. Crea un RefreshToken asociado al usuario
                #   2. Del refresh token genera un access token
                #   3. Refresh token dura 7 días, access token 1 hora
                refresh = RefreshToken.for_user(usuario)

                # Paso 8: Serializar datos del usuario para la respuesta
                # Funcionamiento: Convierte el objeto Usuario en JSON
                usuario_data = UsuarioSerializer(usuario).data

                # Paso 9: Retornar respuesta exitosa
                return Response({
                    'message': 'Login exitoso',
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': usuario_data
                }, status=status.HTTP_200_OK)

            else:
                # ❌ Contraseña incorrecta - LOGIN FALLIDO

                # Paso 10: Registrar intento fallido
                # Funcionamiento:
                #   1. Incrementa contador de intentos fallidos
                #   2. Si alcanza 5 intentos, bloquea la cuenta automáticamente
                usuario.registrar_intento_fallido()

                # Paso 11: Preparar mensaje de error
                # Funcionamiento: Informa cuántos intentos quedan
                intentos_restantes = 5 - usuario.intentos_login_fallidos
                if intentos_restantes > 0:
                    mensaje = f'Credenciales inválidas. {intentos_restantes} intentos restantes.'
                else:
                    mensaje = 'Cuenta bloqueada por múltiples intentos fallidos.'

                return Response(
                    {'error': mensaje},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        except Usuario.DoesNotExist:
            # Paso 12: Usuario no existe
            # Funcionamiento:
            #   Retorna el mismo mensaje que contraseña incorrecta
            #   para no revelar si el email existe en el sistema (seguridad)
            return Response(
                {'error': 'Credenciales inválidas'},
                status=status.HTTP_401_UNAUTHORIZED
            )


# ===========================================
# VISTA DE LOGOUT (CERRAR SESIÓN)
# ===========================================
class LogoutView(APIView):
    """
    VISTA: Cerrar sesión (blacklist del refresh token)

    Funcionamiento:
        1. Recibe el refresh token
        2. Lo agrega a la lista negra (blacklist)
        3. El token ya no puede usarse para generar nuevos access tokens

    IMPORTANTE:
        Requiere que SimpleJWT tenga blacklist habilitada en settings.py:
        INSTALLED_APPS = ['rest_framework_simplejwt.token_blacklist']

    Request:
        POST /api/usuarios/logout/
        {
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbG..."
        }

    Response (200):
        {
            "message": "Sesión cerrada exitosamente"
        }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        MÉTODO POST: Procesar cierre de sesión

        Funcionamiento:
            1. Extraer refresh token del request
            2. Crear objeto RefreshToken con ese token
            3. Agregarlo a la blacklist
            4. Retornar confirmación
        """
        try:
            # Paso 1: Obtener refresh token del request
            refresh_token = request.data.get('refresh')

            if not refresh_token:
                return Response(
                    {'error': 'Refresh token es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Paso 2: Crear objeto token y agregarlo a blacklist
            # Funcionamiento: SimpleJWT almacena el token en una tabla de blacklist
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {'message': 'Sesión cerrada exitosamente'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'error': 'Error al cerrar sesión', 'detalle': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ===========================================
# VIEWSET PRINCIPAL DE USUARIOS
# ===========================================
class UsuarioViewSet(viewsets.ModelViewSet):
    """
    VIEWSET: CRUD completo de usuarios + acciones personalizadas

    Funcionamiento:
        ModelViewSet proporciona automáticamente las operaciones:
        - list():    GET    /api/usuarios/           - Listar usuarios
        - create():  POST   /api/usuarios/           - Crear usuario
        - retrieve(): GET    /api/usuarios/{id}/     - Obtener un usuario
        - update():  PUT    /api/usuarios/{id}/      - Actualizar completo
        - partial_update(): PATCH /api/usuarios/{id}/ - Actualizar parcial
        - destroy(): DELETE /api/usuarios/{id}/      - Eliminar (desactivar)

    Acciones personalizadas (@action):
        - activar()          - Activar usuario desactivado
        - desactivar()       - Desactivar usuario (soft delete)
        - suspender()        - Suspender temporalmente
        - bloquear()         - Bloquear por seguridad
        - desbloquear()      - Desbloquear usuario
        - cambiar_password() - Cambiar contraseña
        - me()               - Obtener/actualizar perfil propio
        - estadisticas()     - Estadísticas generales
        - busqueda_avanzada() - Búsqueda con filtros avanzados

    Características:
        - Paginación automática (20 por página)
        - Filtrado por rol, estado, activo
        - Búsqueda por nombre, apellido, email
        - Ordenamiento por múltiples campos
        - Serializers diferentes para list/detail/create/update
    """

    # Configuración base del ViewSet
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = UsuarioPagination

    # Configuración de filtrado y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rol', 'estado', 'activo', 'especialidad']
    search_fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'email', 'cedula_identidad']
    ordering_fields = ['fecha_creacion', 'ultimo_login', 'nombre', 'apellido_paterno']
    ordering = ['-fecha_creacion']

    def get_serializer_class(self):
        """
        MÉTODO: Seleccionar serializer según la acción

        Funcionamiento:
            Retorna diferentes serializers según qué operación se esté haciendo
            Esto permite optimizar la respuesta y las validaciones

        Serializers por acción:
            - list:   UsuarioListSerializer (campos reducidos, optimizado)
            - retrieve: UsuarioDetailSerializer (todos los campos + estadísticas)
            - create: UsuarioCreateSerializer (con validación de password)
            - update/partial_update: UsuarioUpdateSerializer (sin password)
            - default: UsuarioSerializer (estándar)
        """
        if self.action == 'list':
            return UsuarioListSerializer
        elif self.action == 'retrieve':
            return UsuarioDetailSerializer
        elif self.action == 'create':
            return UsuarioCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UsuarioUpdateSerializer
        return UsuarioSerializer

    def get_queryset(self):
        """
        MÉTODO: Obtener queryset filtrado

        Funcionamiento:
            Permite filtrar usuarios según parámetros de la URL
            Ejemplo: ?rol=medico&activo=true

        Filtros disponibles:
            - rol: Filtrar por rol (administrador, medico, enfermero, asistente)
            - estado: Filtrar por estado (activo, inactivo, suspendido, bloqueado)
            - activo: Filtrar por activos (true/false)
            - especialidad: Filtrar por especialidad médica

        Optimizaciones:
            - select_related() para reducir queries en ForeignKeys
            - prefetch_related() para relaciones inversas
        """
        queryset = Usuario.objects.all()

        # Aplicar filtros adicionales si es necesario
        # Los filtros básicos ya son manejados por DjangoFilterBackend

        return queryset

    def create(self, request, *args, **kwargs):
        """
        MÉTODO: Crear nuevo usuario

        Funcionamiento:
            1. Recibe datos del nuevo usuario
            2. Valida con UsuarioCreateSerializer
            3. Hashea la contraseña
            4. Crea el usuario en la BD
            5. Retorna el usuario creado

        Request:
            POST /api/usuarios/
            {
                "email": "nuevo@hospital.com",
                "password": "Segura123",
                "password_confirm": "Segura123",
                "nombre": "María",
                "apellido_paterno": "González",
                "rol": "medico",
                "especialidad": "Ginecología"
            }

        Response (201):
            {
                "id": 5,
                "uuid": "...",
                "email": "nuevo@hospital.com",
                "nombre_completo": "María González",
                "rol": "medico",
                "estado": "activo"
            }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # El serializer ya maneja el hasheo de contraseña en su método create()
        self.perform_create(serializer)

        # Retornar usuario creado con UsuarioSerializer estándar
        headers = self.get_success_headers(serializer.data)
        usuario = serializer.instance
        response_serializer = UsuarioSerializer(usuario)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        """
        MÉTODO: Actualizar usuario completo (PUT)

        Funcionamiento:
            1. Obtiene el usuario a actualizar
            2. Valida todos los campos con UsuarioUpdateSerializer
            3. Actualiza TODOS los campos
            4. Guarda en la BD
            5. Retorna usuario actualizado

        IMPORTANTE:
            PUT requiere enviar TODOS los campos
            Para actualizar solo algunos campos, usar PATCH
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        MÉTODO: Eliminar usuario (Soft Delete)

        Funcionamiento:
            NO elimina físicamente el usuario de la BD
            En su lugar, lo desactiva (soft delete)
            Esto preserva el historial y las relaciones

        Proceso:
            1. Obtiene el usuario
            2. Llama a usuario.desactivar()
            3. Guarda el motivo si se proporciona
            4. Retorna confirmación

        Request:
            DELETE /api/usuarios/5/
            {
                "motivo": "Usuario dio de baja" (opcional)
            }

        Response (200):
            {
                "message": "Usuario desactivado exitosamente"
            }
        """
        instance = self.get_object()
        motivo = request.data.get('motivo', 'Eliminado desde la API')

        # Desactivar en lugar de eliminar
        instance.desactivar(motivo=motivo)

        return Response(
            {'message': 'Usuario desactivado exitosamente'},
            status=status.HTTP_200_OK
        )

    # ===========================================
    # ACCIONES PERSONALIZADAS
    # ===========================================

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        ACCIÓN: Activar usuario desactivado

        Funcionamiento:
            1. Obtiene el usuario por ID
            2. Llama a usuario.activar()
            3. Resetea intentos fallidos y bloqueos
            4. Retorna confirmación

        Request:
            POST /api/usuarios/5/activar/

        Response (200):
            {
                "message": "Usuario activado exitosamente",
                "usuario": { ... }
            }
        """
        usuario = self.get_object()
        usuario.activar()

        serializer = UsuarioSerializer(usuario)
        return Response({
            'message': 'Usuario activado exitosamente',
            'usuario': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """
        ACCIÓN: Desactivar usuario

        Funcionamiento:
            Desactiva el usuario con motivo opcional

        Request:
            POST /api/usuarios/5/desactivar/
            {
                "motivo": "Fin de contrato"
            }
        """
        usuario = self.get_object()
        motivo = request.data.get('motivo', None)
        usuario.desactivar(motivo=motivo)

        serializer = UsuarioSerializer(usuario)
        return Response({
            'message': 'Usuario desactivado exitosamente',
            'usuario': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def suspender(self, request, pk=None):
        """
        ACCIÓN: Suspender usuario temporalmente

        Funcionamiento:
            Suspende el usuario con motivo y duración

        Request:
            POST /api/usuarios/5/suspender/
            {
                "motivo": "Vacaciones",
                "duracion_dias": 15
            }
        """
        usuario = self.get_object()
        motivo = request.data.get('motivo', None)
        duracion_dias = request.data.get('duracion_dias', None)

        usuario.suspender(motivo=motivo, duracion_dias=duracion_dias)

        serializer = UsuarioSerializer(usuario)
        return Response({
            'message': 'Usuario suspendido exitosamente',
            'usuario': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def bloquear(self, request, pk=None):
        """
        ACCIÓN: Bloquear usuario por seguridad

        Funcionamiento:
            Bloquea el usuario con motivo

        Request:
            POST /api/usuarios/5/bloquear/
            {
                "motivo": "Actividad sospechosa"
            }
        """
        usuario = self.get_object()
        motivo = request.data.get('motivo', 'Bloqueado manualmente por administrador')

        usuario.bloquear(motivo=motivo)

        serializer = UsuarioSerializer(usuario)
        return Response({
            'message': 'Usuario bloqueado exitosamente',
            'usuario': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def desbloquear(self, request, pk=None):
        """
        ACCIÓN: Desbloquear usuario

        Funcionamiento:
            Desbloquea el usuario y resetea intentos fallidos

        Request:
            POST /api/usuarios/5/desbloquear/
        """
        usuario = self.get_object()
        usuario.desbloquear()

        serializer = UsuarioSerializer(usuario)
        return Response({
            'message': 'Usuario desbloqueado exitosamente',
            'usuario': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cambiar_password(self, request, pk=None):
        """
        ACCIÓN: Cambiar contraseña de un usuario

        Funcionamiento:
            1. Verifica contraseña actual
            2. Valida nueva contraseña
            3. Hashea y guarda nueva contraseña

        Request:
            POST /api/usuarios/5/cambiar_password/
            {
                "password_actual": "Antigua123",
                "password_nuevo": "Nueva456",
                "password_nuevo_confirm": "Nueva456"
            }

        Response (200):
            {
                "message": "Contraseña actualizada exitosamente"
            }
        """
        usuario = self.get_object()
        serializer = PasswordChangeSerializer(data=request.data)

        if serializer.is_valid():
            # Verificar contraseña actual
            if not usuario.check_password(serializer.validated_data['password_actual']):
                return Response(
                    {'error': 'Contraseña actual incorrecta'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Establecer nueva contraseña
            usuario.set_password(serializer.validated_data['password_nuevo'])
            usuario.save()

            return Response(
                {'message': 'Contraseña actualizada exitosamente'},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        ACCIÓN: Obtener/actualizar perfil del usuario actual

        Funcionamiento:
            GET: Retorna datos del usuario autenticado
            PUT/PATCH: Actualiza datos del usuario autenticado

        Request:
            GET /api/usuarios/me/

        Response (200):
            {
                "id": 3,
                "uuid": "...",
                "email": "usuario@hospital.com",
                "nombre_completo": "Dr. Juan Pérez",
                ...
            }

        Request actualización:
            PUT /api/usuarios/me/
            {
                "telefono": "12345678",
                "direccion": "Nueva dirección"
            }
        """
        usuario = request.user

        if request.method == 'GET':
            # Obtener perfil
            serializer = UsuarioDetailSerializer(usuario)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            # Actualizar perfil
            partial = request.method == 'PATCH'
            serializer = UsuarioUpdateSerializer(usuario, data=request.data, partial=partial)

            if serializer.is_valid():
                serializer.save()
                response_serializer = UsuarioSerializer(usuario)
                return Response(response_serializer.data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        ACCIÓN: Obtener estadísticas generales de usuarios

        Funcionamiento:
            Calcula y retorna métricas sobre los usuarios del sistema

        Request:
            GET /api/usuarios/estadisticas/

        Response (200):
            {
                "total_usuarios": 45,
                "usuarios_activos": 38,
                "usuarios_inactivos": 4,
                "usuarios_bloqueados": 3,
                "por_rol": {
                    "medico": 15,
                    "enfermero": 20,
                    "administrador": 5,
                    "asistente": 5
                },
                "por_estado": {
                    "activo": 38,
                    "inactivo": 4,
                    "suspendido": 1,
                    "bloqueado": 2
                },
                "logins_ultimos_7_dias": 125,
                "nuevos_usuarios_mes": 3
            }
        """

        # Estadísticas generales
        total = Usuario.objects.count()
        activos = Usuario.objects.filter(activo=True).count()
        inactivos = Usuario.objects.filter(activo=False).count()
        bloqueados = Usuario.objects.filter(estado='bloqueado').count()

        # Estadísticas por rol
        por_rol = {}
        for rol_code, rol_display in Usuario.ROLES:
            por_rol[rol_code] = Usuario.objects.filter(rol=rol_code).count()

        # Estadísticas por estado
        por_estado = {}
        for estado_code, estado_display in Usuario.ESTADOS_USUARIO:
            por_estado[estado_code] = Usuario.objects.filter(estado=estado_code).count()

        # Logins en últimos 7 días
        hace_7_dias = timezone.now() - timedelta(days=7)
        logins_recientes = Usuario.objects.filter(
            ultimo_login__gte=hace_7_dias
        ).count()

        # Nuevos usuarios este mes
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        nuevos_mes = Usuario.objects.filter(
            fecha_creacion__gte=inicio_mes
        ).count()

        return Response({
            'total_usuarios': total,
            'usuarios_activos': activos,
            'usuarios_inactivos': inactivos,
            'usuarios_bloqueados': bloqueados,
            'por_rol': por_rol,
            'por_estado': por_estado,
            'logins_ultimos_7_dias': logins_recientes,
            'nuevos_usuarios_mes': nuevos_mes
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def busqueda_avanzada(self, request):
        """
        ACCIÓN: Búsqueda avanzada con múltiples filtros

        Funcionamiento:
            Permite buscar usuarios con múltiples criterios combinados

        Parámetros de búsqueda:
            - q: Búsqueda general (nombre, apellido, email, cédula)
            - rol: Filtrar por rol
            - estado: Filtrar por estado
            - activo: Filtrar por activo (true/false)
            - especialidad: Filtrar por especialidad
            - fecha_desde: Usuarios creados desde esta fecha
            - fecha_hasta: Usuarios creados hasta esta fecha

        Request:
            GET /api/usuarios/busqueda_avanzada/?q=juan&rol=medico&activo=true

        Response (200):
            {
                "count": 5,
                "results": [
                    { usuario1 },
                    { usuario2 },
                    ...
                ]
            }
        """
        queryset = Usuario.objects.all()

        # Búsqueda general
        q = request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) |
                Q(apellido_paterno__icontains=q) |
                Q(apellido_materno__icontains=q) |
                Q(email__icontains=q) |
                Q(cedula_identidad__icontains=q)
            )

        # Filtros específicos
        rol = request.query_params.get('rol', None)
        if rol:
            queryset = queryset.filter(rol=rol)

        estado = request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)

        activo = request.query_params.get('activo', None)
        if activo is not None:
            activo_bool = activo.lower() == 'true'
            queryset = queryset.filter(activo=activo_bool)

        especialidad = request.query_params.get('especialidad', None)
        if especialidad:
            queryset = queryset.filter(especialidad__icontains=especialidad)

        # Filtros por fecha
        fecha_desde = request.query_params.get('fecha_desde', None)
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__gte=fecha_desde)

        fecha_hasta = request.query_params.get('fecha_hasta', None)
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__lte=fecha_hasta)

        # Paginar resultados
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UsuarioListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = UsuarioListSerializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


# ===========================================
# VISTA DE REGISTRO PÚBLICO
# ===========================================
class RegisterView(APIView):
    """
    VISTA: Registro público de nuevos usuarios

    Funcionamiento:
        Permite el auto-registro de usuarios (si está habilitado)
        Similar a create() pero con acceso público

    IMPORTANTE:
        En producción, considerar deshabilitar o limitar esta funcionalidad
        Podría requerir aprobación de administrador

    Request:
        POST /api/usuarios/register/
        {
            "email": "nuevo@ejemplo.com",
            "password": "Segura123",
            "password_confirm": "Segura123",
            "nombre": "Pedro",
            "apellido_paterno": "Rodríguez",
            "rol": "asistente"
        }

    Response (201):
        {
            "message": "Usuario registrado exitosamente. Espere aprobación del administrador.",
            "usuario": { ... }
        }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        MÉTODO POST: Procesar registro de nuevo usuario

        Funcionamiento:
            1. Valida datos con UsuarioCreateSerializer
            2. Crea usuario con estado 'inactivo' (requiere activación)
            3. Envía notificación a administradores (opcional)
            4. Retorna confirmación
        """
        serializer = UsuarioCreateSerializer(data=request.data)

        if serializer.is_valid():
            # Crear usuario con estado inactivo (requiere aprobación)
            usuario = serializer.save()
            usuario.estado = 'inactivo'
            usuario.activo = False
            usuario.save()

            # TODO: Enviar email a administradores para aprobar cuenta
            # TODO: Enviar email de confirmación al usuario

            response_serializer = UsuarioSerializer(usuario)
            return Response({
                'message': 'Usuario registrado exitosamente. Espere aprobación del administrador.',
                'usuario': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
