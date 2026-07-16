"""Views module."""
from datetime import timedelta

import pyotp
from django.contrib.auth.models import Permission
from django.middleware.csrf import get_token as csrf_get_token
from django.utils import timezone as tz
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .auth_cookies import REFRESH_COOKIE, clear_jwt_cookies, set_jwt_cookies
from .models import HorarioAtencion, Usuario
from .serializers import (
    AdminChangePasswordSerializer,
    ChangePasswordSerializer,
    HorarioAtencionSerializer,
    LoginSerializer,
    MfaVerifySerializer,
    PermissionSerializer,
    UsuarioCreateUpdateSerializer,
    UsuarioDetailSerializer,
    UsuarioListSerializer,
)

# ── Temp token MFA ────────────────────────────────────────────────────────────
# El temp_token es un JWT de 5 minutos que solo contiene user_id y el claim
# "mfa_pending": true. Se genera con RefreshToken del usuario pero se firma con
# un claim adicional para que el backend pueda distinguirlo de un access token real.

def _build_temp_token(usuario) -> str:
    """Genera un JWT temporal (5 min) que marca el estado 'pendiente MFA'."""
    refresh = RefreshToken.for_user(usuario)
    # Cambiamos la expiración del access token a 5 minutos
    access = refresh.access_token
    access.set_exp(lifetime=timedelta(minutes=5))
    access["mfa_pending"] = True  # claim custom — diferencia de un access válido
    # Blacklistear el refresh para que no pueda usarse directamente
    refresh.blacklist()
    return str(access)


def _decode_temp_token(token_str):
    """Valida el temp_token y retorna el Usuario o lanza excepción."""
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import AccessToken

    try:
        token = AccessToken(token_str)
    except TokenError as exc:
        raise ValueError("temp_token inválido o expirado") from exc

    if not token.get("mfa_pending"):
        raise ValueError("El token no es un temp_token MFA válido")

    user_id = token.get("user_id")
    try:
        return Usuario.objects.get(pk=user_id, activo=True)
    except Usuario.DoesNotExist as exc:
        raise ValueError("Usuario no encontrado") from exc

# ======================================================================================
# USUARIO VIEWSET
# ======================================================================================


class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet for comprehensive User management.

    Manages user registration, authentication, roles, permissions,
    and work schedules.

    **Endpoints:**
    - `GET /api/usuarios/` - List all active users (paginated)
    - `POST /api/usuarios/` - Create new user
    - `GET /api/usuarios/{id}/` - Get user details
    - `PUT/PATCH /api/usuarios/{id}/` - Update user
    - `DELETE /api/usuarios/{id}/` - Deactivate user (soft delete)
    - `POST /api/usuarios/{id}/activar/` - Activate user
    - `POST /api/usuarios/{id}/desactivar/` - Deactivate user
    - `POST /api/usuarios/{id}/cambiar_password/` - Change own password
    - `POST /api/usuarios/{id}/admin_cambiar_password/` - Change any user password (admin)
    - `GET /api/usuarios/{id}/permisos/` - Get user permissions
    - `POST /api/usuarios/{id}/asignar_permisos/` - Assign permissions
    - `POST /api/usuarios/{id}/quitar_permisos/` - Remove permissions
    - `GET /api/usuarios/{id}/horarios/` - Get user work schedules
    - `POST /api/usuarios/{id}/agregar_horario/` - Add work schedule
    - `GET /api/usuarios/me/` - Get current user profile
    - `GET /api/usuarios/medicos/` - List active doctors
    - `GET /api/usuarios/enfermeros/` - List active nurses
    - `GET /api/usuarios/todos/` - List ALL users (including inactive, admin only)
    - `GET /api/usuarios/permisos_disponibles/` - List available system permissions

    **Authentication:** JWT Bearer token required
    **Permissions:** Varies by endpoint (some require admin role)
    """

    queryset = Usuario.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["rol", "activo", "is_staff", "is_superuser"]
    search_fields = [
        "nombre",
        "apellido_paterno",
        "apellido_materno",
        "email",
        "especialidad",
    ]
    ordering_fields = ["fecha_creacion", "nombre", "apellido_paterno", "email"]

    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción"""
        if self.action == "list":
            return UsuarioListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return UsuarioCreateUpdateSerializer
        return UsuarioDetailSerializer

    def get_queryset(self):
        """Filtrar usuarios - por defecto solo activos"""
        queryset = super().get_queryset()

        # Para acciones de detalle (retrieve, update, delete, custom detail actions), mostrar TODOS
        # Para acciones de listado, filtrar solo activos (excepto 'todos')
        detail_actions = [
            "retrieve",
            "update",
            "partial_update",
            "destroy",
            "activar",
            "desactivar",
            "cambiar_password",
            "admin_cambiar_password",
            "permisos",
            "asignar_permisos",
            "quitar_permisos",
            "horarios",
            "agregar_horario",
        ]

        if self.action == "list":
            # Para listado, solo mostrar activos
            queryset = queryset.filter(activo=True)
        elif self.action == "todos":
            # Acción especial para mostrar todos incluyendo inactivos
            pass  # No filtrar
        elif self.action in detail_actions:
            # Para detail actions, no filtrar por activo (permite acceder a usuarios inactivos)
            pass  # No filtrar

        # Filtrar por rol si se especifica
        rol = self.request.query_params.get("rol", None)
        if rol:
            queryset = queryset.filter(rol=rol)

        return queryset.order_by("-fecha_creacion")

    def destroy(self, request, *args, **kwargs):
        """Soft delete - marcar como inactivo en lugar de eliminar
        """
        usuario = self.get_object()
        usuario.activo = False
        usuario.save()

        return Response(
            {"mensaje": "Usuario desactivado correctamente (baja lógica)"},
            status=status.HTTP_200_OK,
        )

    # =================================================================================
    # ACCIONES DEL USUARIO ACTUAL
    # =================================================================================

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Obtener información del usuario actual"""
        serializer = UsuarioDetailSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    # =================================================================================
    # ACTIVAR / DESACTIVAR
    # =================================================================================

    @action(detail=True, methods=["post"])
    def activar(self, _request, pk=None):
        """Activar un usuario"""
        usuario = self.get_object()
        usuario.activo = True
        usuario.save()

        return Response(
            {"mensaje": "Usuario activado correctamente", "activo": usuario.activo},
        )

    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        """Desactivar un usuario (baja lógica)"""
        usuario = self.get_object()

        # No permitir desactivar al mismo usuario
        if usuario.id == request.user.id:
            return Response(
                {"error": "No puedes desactivarte a ti mismo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario.activo = False
        usuario.save()

        return Response(
            {"mensaje": "Usuario desactivado correctamente", "activo": usuario.activo},
        )

    # =================================================================================
    # CAMBIO DE CONTRASEÑA
    # =================================================================================

    @action(detail=True, methods=["post"])
    def cambiar_password(self, request, pk=None):
        """Cambiar contraseña del usuario (requiere contraseña actual)"""
        usuario = self.get_object()

        # Solo el mismo usuario puede cambiar su contraseña con este endpoint
        if usuario.id != request.user.id and not request.user.is_superuser:
            return Response(
                {"error": "No tienes permiso para cambiar esta contraseña"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            # Verificar contraseña actual
            if not usuario.check_password(serializer.validated_data["password_actual"]):
                return Response(
                    {"error": "Contraseña actual incorrecta"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Establecer nueva contraseña
            usuario.set_password(serializer.validated_data["password_nueva"])
            usuario.save()

            return Response({"mensaje": "Contraseña actualizada correctamente"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def admin_cambiar_password(self, request, pk=None):
        """Admin cambia contraseña de cualquier usuario (sin requerir contraseña actual)"""
        # Solo administradores
        if not request.user.is_superuser and request.user.rol != "administrador":
            return Response(
                {"error": "Solo administradores pueden usar este endpoint"},
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario = self.get_object()
        serializer = AdminChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            # Establecer nueva contraseña directamente
            usuario.set_password(serializer.validated_data["password_nueva"])
            usuario.save()

            return Response(
                {
                    "mensaje": f"Contraseña de {usuario.nombre_completo} actualizada correctamente por administrador",
                },
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # =================================================================================
    # GESTIÓN DE PERMISOS
    # =================================================================================

    @action(detail=True, methods=["get"])
    def permisos(self, _request, pk=None):
        """Ver permisos asignados al usuario"""
        usuario = self.get_object()
        permisos = usuario.user_permissions.all()
        serializer = PermissionSerializer(permisos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def asignar_permisos(self, request, pk=None):
        """Asignar permisos a un usuario"""
        # Solo administradores
        if not request.user.is_superuser and request.user.rol != "administrador":
            return Response(
                {"error": "Solo administradores pueden asignar permisos"},
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario = self.get_object()
        permisos_ids = request.data.get("permisos_ids", [])

        if not permisos_ids:
            return Response(
                {"error": "Debe proporcionar al menos un permiso"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Buscar permisos
        permisos = Permission.objects.filter(id__in=permisos_ids)

        # Agregar permisos al usuario
        usuario.user_permissions.add(*permisos)

        return Response(
            {
                "mensaje": f"{len(permisos)} permisos asignados correctamente",
                "permisos": PermissionSerializer(
                    usuario.user_permissions.all(), many=True,
                ).data,
            },
        )

    @action(detail=True, methods=["post"])
    def quitar_permisos(self, request, pk=None):
        """Quitar permisos de un usuario"""
        # Solo administradores
        if not request.user.is_superuser and request.user.rol != "administrador":
            return Response(
                {"error": "Solo administradores pueden quitar permisos"},
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario = self.get_object()
        permisos_ids = request.data.get("permisos_ids", [])

        if not permisos_ids:
            return Response(
                {"error": "Debe proporcionar al menos un permiso"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Buscar permisos
        permisos = Permission.objects.filter(id__in=permisos_ids)

        # Quitar permisos del usuario
        usuario.user_permissions.remove(*permisos)

        return Response(
            {
                "mensaje": f"{len(permisos)} permisos quitados correctamente",
                "permisos": PermissionSerializer(
                    usuario.user_permissions.all(), many=True,
                ).data,
            },
        )

    @action(detail=False, methods=["get"])
    def permisos_disponibles(self, request):
        """Listar todos los permisos disponibles en el sistema"""
        # Solo administradores
        if not request.user.is_superuser and request.user.rol != "administrador":
            return Response(
                {"error": "Solo administradores pueden ver permisos disponibles"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Obtener todos los permisos, agrupados por app
        permisos = (
            Permission.objects.select_related("content_type")
            .all()
            .order_by("content_type__app_label", "content_type__model", "codename")
        )

        serializer = PermissionSerializer(permisos, many=True)
        return Response(serializer.data)

    # =================================================================================
    # GESTIÓN DE HORARIOS
    # =================================================================================

    @action(detail=True, methods=["get"], url_path="horarios-atencion")
    def horarios(self, _request, pk=None):
        """Ver horarios de atención del usuario"""
        usuario = self.get_object()
        horarios = usuario.horarios_atencion.all()
        serializer = HorarioAtencionSerializer(horarios, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def agregar_horario(self, request, pk=None):
        """Agregar horario de atención al usuario"""
        usuario = self.get_object()

        # Solo el mismo usuario o un admin puede agregar horarios
        if (
            usuario.id != request.user.id
            and not request.user.is_superuser
            and request.user.rol != "administrador"
        ):
            return Response(
                {"error": "No tienes permiso para modificar estos horarios"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Crear horario
        data = request.data.copy()
        data["usuario"] = usuario.id

        serializer = HorarioAtencionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # =================================================================================
    # LISTADOS ESPECÍFICOS
    # =================================================================================

    @action(detail=False, methods=["get"])
    def medicos(self, request):
        """Obtener lista de médicos activos"""
        medicos = Usuario.objects.filter(rol="medico", activo=True).order_by(
            "apellido_paterno", "nombre",
        )
        serializer = UsuarioListSerializer(
            medicos, many=True, context={"request": request},
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def enfermeros(self, request):
        """Obtener lista de enfermeras activas"""
        # El modelo ROLES usa 'enfermera', no 'enfermero' — corregido
        enfermeros = Usuario.objects.filter(rol="enfermera", activo=True).order_by(
            "apellido_paterno", "nombre",
        )
        serializer = UsuarioListSerializer(
            enfermeros, many=True, context={"request": request},
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def todos(self, request):
        """Listar TODOS los usuarios (incluyendo inactivos)"""
        # Solo administradores
        if not request.user.is_superuser and request.user.rol != "administrador":
            return Response(
                {"error": "Solo administradores pueden ver todos los usuarios"},
                status=status.HTTP_403_FORBIDDEN,
            )

        usuarios = Usuario.objects.all().order_by("-fecha_creacion")
        serializer = UsuarioListSerializer(
            usuarios, many=True, context={"request": request},
        )
        return Response(serializer.data)

    # =================================================================================
    # MFA / TOTP
    # =================================================================================

    @action(
        detail=False,
        methods=["get"],
        url_path="mfa/status",
        permission_classes=[IsAuthenticated],
    )
    def mfa_status(self, request):
        """Estado actual de MFA para el usuario autenticado"""
        return Response({"mfa_enabled": request.user.mfa_enabled})

    @action(
        detail=False,
        methods=["post"],
        url_path="mfa/setup",
        permission_classes=[IsAuthenticated],
    )
    def mfa_setup(self, request):
        """Genera secreto TOTP y QR para Google Authenticator. Confirmar con /mfa/confirm/."""
        import base64
        import io

        import qrcode

        secret = pyotp.random_base32()
        request.user.mfa_secret = secret
        request.user.save(update_fields=["mfa_secret"])
        uri = pyotp.TOTP(secret).provisioning_uri(
            name=request.user.email, issuer_name="Fetal Medical Bolivia",
        )
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf)
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
        return Response(
            {
                "secret": secret,
                "qr_code": f"data:image/png;base64,{qr_b64}",
                "uri": uri,
                "mensaje": 'Escanee el QR con Google Authenticator, luego confirme con POST /mfa/confirm/ {"code":"..."}',
            },
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="mfa/confirm",
        permission_classes=[IsAuthenticated],
    )
    def mfa_confirm(self, request):
        """Activa MFA verificando el primer código TOTP generado por el autenticador"""
        code = str(request.data.get("code", ""))
        if not request.user.mfa_secret:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if pyotp.TOTP(request.user.mfa_secret).verify(code, valid_window=1):
            request.user.mfa_enabled = True
            request.user.save(update_fields=["mfa_enabled"])
            return Response(
                {"mensaje": "MFA activado correctamente", "mfa_enabled": True},
            )
        return Response(
            {"error": "Código inválido o expirado"}, status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="mfa/disable",
        permission_classes=[IsAuthenticated],
    )
    def mfa_disable(self, request):
        """Desactiva MFA. Requiere código TOTP válido para confirmar la desactivación."""
        code = str(request.data.get("code", ""))
        if not request.user.mfa_enabled:
            return Response(
                {"error": "MFA no está activado"}, status=status.HTTP_400_BAD_REQUEST,
            )
        if pyotp.TOTP(request.user.mfa_secret).verify(code, valid_window=1):
            request.user.mfa_enabled = False
            request.user.mfa_secret = None
            request.user.save(update_fields=["mfa_enabled", "mfa_secret"])
            return Response(
                {"mensaje": "MFA desactivado correctamente", "mfa_enabled": False},
            )
        return Response(
            {"error": "Código inválido o expirado"}, status=status.HTTP_400_BAD_REQUEST,
        )


# ======================================================================================
# HORARIO VIEWSET
# ======================================================================================


class HorarioAtencionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de horarios de atención
    """

    queryset = HorarioAtencion.objects.all()
    serializer_class = HorarioAtencionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["usuario", "dia_semana", "activo"]
    ordering_fields = ["dia_semana", "hora_inicio"]

    def get_queryset(self):
        """Filtrar horarios según usuario"""
        queryset = super().get_queryset()

        # Filtrar por usuario si se especifica
        usuario_id = self.request.query_params.get("usuario_id", None)
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)

        return queryset.order_by("dia_semana", "hora_inicio")


# ======================================================================================
# AUTH ENDPOINTS
# ======================================================================================


@extend_schema(
    tags=["Authentication"],
    summary="User login",
    description="Authenticate user with email and password. Returns access and refresh JWT tokens.",
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description="Authentication successful, returns JWT tokens and user data",
        ),
        400: OpenApiResponse(description="Bad Request - Invalid input data"),
        401: OpenApiResponse(description="Unauthorized - Invalid credentials"),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Endpoint de login
    POST: email, password
    Retorna: access_token, refresh_token, user_data
    """
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    # Buscar usuario por email
    try:
        usuario = Usuario.objects.get(email=email, activo=True)
    except Usuario.DoesNotExist:
        return Response(
            {"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED,
        )

    # Verificar bloqueo de cuenta (máx 5 intentos)
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > tz.now():
        segundos = int((usuario.bloqueado_hasta - tz.now()).total_seconds())
        return Response(
            {"error": f"Cuenta bloqueada. Intente en {segundos} segundos."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Verificar contraseña
    if not usuario.check_password(password):
        usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
        if usuario.intentos_fallidos >= 5:
            from datetime import timedelta

            usuario.bloqueado_hasta = tz.now() + timedelta(minutes=15)
            usuario.intentos_fallidos = 0
        usuario.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])
        # Auditoría: login fallido
        try:
            from auditoria.models import RegistroAuditoria

            RegistroAuditoria.registrar(
                usuario=None,
                accion="LOGIN_FALLIDO",
                modulo="Usuario",
                detalle=f"Login fallido para email: {email}",
                request=request,
            )
        except Exception:
            pass
        return Response(
            {"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED,
        )

    # Resetear intentos fallidos tras login exitoso
    if usuario.intentos_fallidos > 0 or usuario.bloqueado_hasta:
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        usuario.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])

    # Verificar MFA si está habilitado — FLUJO DE 2 PASOS con temp_token
    if usuario.mfa_enabled and usuario.mfa_secret:
        # Emitir temp_token y pedir el TOTP en un segundo endpoint
        temp_token = _build_temp_token(usuario)
        return Response(
            {
                "mfa_required": True,
                "temp_token": temp_token,
                "user_id": str(usuario.id),
                "mensaje": (
                    "Código MFA requerido. "
                    "POST /api/usuarios/mfa-verify/ con {temp_token, totp_code}."
                ),
            },
            status=status.HTTP_200_OK,
        )

    # MFA OBLIGATORIO: médico/admin sin MFA configurado → bloquear
    if getattr(usuario, "mfa_obligatorio", False) and not usuario.mfa_enabled:
        return Response(
            {
                "mfa_setup_required": True,
                "mensaje": (
                    "Su rol requiere autenticación de dos factores (MFA). "
                    "Configure MFA antes de continuar: POST /api/usuarios/mfa/setup/"
                ),
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # Registrar IP de último acceso
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = x_forwarded.split(",")[0] if x_forwarded else request.META.get("REMOTE_ADDR")
    usuario.ultimo_login_ip = ip
    usuario.save(update_fields=["ultimo_login_ip"])

    # Auditoría: login exitoso
    try:
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.registrar(
            usuario=usuario,
            accion="LOGIN",
            modulo="Usuario",
            registro_id=str(usuario.id),
            detalle=f"Login exitoso — rol: {usuario.rol}",
            request=request,
        )
    except Exception:
        pass

    # Generar tokens JWT
    refresh = RefreshToken.for_user(usuario)

    # ACCIONES: Obtener TODOS los permisos (directos + grupos)
    permisos_set = set()

    # 1. Permisos directos
    permisos_set.update(usuario.user_permissions.values_list("codename", flat=True))

    # 2. Permisos de grupos
    for group in usuario.groups.all():
        permisos_set.update(group.permissions.values_list("codename", flat=True))

    # Convertir a lista
    permisos = list(permisos_set)

    # SEGURIDAD: los JWT viajan SOLO como cookies httpOnly (nunca en el body,
    # nunca a localStorage). Se incluye la cookie csrftoken para el
    # double-submit del frontend.
    response = Response(
        {
            "user": {
                "id": usuario.id,
                "email": usuario.email,
                "nombre": usuario.nombre_completo,
                "rol": usuario.rol,
                "especialidad": usuario.especialidad,
                "foto_url": request.build_absolute_uri(usuario.foto.url)
                if usuario.foto
                else None,
                "is_staff": usuario.is_staff,
                "is_superuser": usuario.is_superuser,
                "permisos": permisos,  # Lista de strings [view_paciente, add_paciente...]
            },
        },
        status=status.HTTP_200_OK,
    )
    set_jwt_cookies(response, access=refresh.access_token, refresh=refresh)
    csrf_get_token(request)  # fuerza Set-Cookie: csrftoken en esta respuesta
    return response


@extend_schema(
    tags=["Authentication"],
    summary="User logout",
    description="Blacklist the provided refresh token to end the session.",
    request=dict,
    responses={
        200: OpenApiResponse(description="Session closed successfully"),
        400: OpenApiResponse(description="Bad Request - Invalid token"),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    """Endpoint de logout.

    Lee el refresh de la cookie httpOnly (fallback: body ``refresh_token``),
    lo blacklistea (best-effort) y SIEMPRE limpia las cookies JWT para que la
    sesión del navegador quede cerrada aunque el token ya estuviera vencido.
    """
    refresh_token = request.COOKIES.get(REFRESH_COOKIE) or request.data.get(
        "refresh_token",
    )
    try:
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass  # token vencido/inválido: igual cerramos la sesión del navegador

    response = Response({"mensaje": "Sesión cerrada correctamente"})
    clear_jwt_cookies(response)
    return response


@extend_schema(
    tags=["Authentication"],
    summary="Refresh access token",
    description="Generate a new access token using a valid refresh token.",
    request=dict,
    responses={
        200: OpenApiResponse(description="New access token generated"),
        401: OpenApiResponse(description="Unauthorized - Invalid or expired token"),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """Endpoint para refrescar el access token
    POST: refresh_token
    """
    try:
        refresh_token = request.data.get("refresh_token")
        token = RefreshToken(refresh_token)

        return Response({"access_token": str(token.access_token)})
    except Exception:
        return Response(
            {"error": "Token inválido o expirado"}, status=status.HTTP_401_UNAUTHORIZED,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Get current user",
    description="Retrieve profile information for the currently authenticated user.",
    responses={200: UsuarioDetailSerializer},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """Endpoint para obtener información del usuario actual
    GET: retorna datos del usuario autenticado
    """
    serializer = UsuarioDetailSerializer(request.user, context={"request": request})
    return Response(serializer.data)


@extend_schema(
    tags=["Authentication"],
    summary="Verificar código MFA (paso 2 del login)",
    description=(
        "Verifica el código TOTP del autenticador usando el temp_token recibido en el paso 1. "
        "Si es válido, retorna el par access/refresh JWT definitivo."
    ),
    request=MfaVerifySerializer,
    responses={
        200: OpenApiResponse(description="MFA verificado — retorna JWT completo"),
        400: OpenApiResponse(description="Datos inválidos"),
        401: OpenApiResponse(description="Código TOTP incorrecto o temp_token expirado"),
        403: OpenApiResponse(description="Cuenta bloqueada"),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def mfa_verify_view(request):
    """Paso 2 del login: verifica el código TOTP y emite JWT definitivo.

    POST /api/usuarios/mfa-verify/
    Body: { "temp_token": "...", "totp_code": "123456" }
    """
    serializer = MfaVerifySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    temp_token = serializer.validated_data["temp_token"]
    totp_code = serializer.validated_data["totp_code"]

    # 1. Validar temp_token y obtener usuario
    try:
        usuario = _decode_temp_token(temp_token)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

    # 2. Verificar bloqueo de cuenta
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > tz.now():
        segundos = int((usuario.bloqueado_hasta - tz.now()).total_seconds())
        return Response(
            {"error": f"Cuenta bloqueada. Intente en {segundos} segundos."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # 3. Verificar código TOTP
    if not usuario.mfa_secret:
        return Response(
            {"error": "MFA no configurado para este usuario."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    totp = pyotp.TOTP(usuario.mfa_secret)
    if not totp.verify(totp_code, valid_window=1):
        # Incrementar intentos fallidos MFA
        usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
        if usuario.intentos_fallidos >= 5:
            usuario.bloqueado_hasta = tz.now() + timedelta(minutes=15)
            usuario.intentos_fallidos = 0
        usuario.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])

        # Auditoría
        try:
            from auditoria.models import RegistroAuditoria
            RegistroAuditoria.registrar(
                usuario=usuario,
                accion="MFA_FALLIDO",
                modulo="Usuario",
                registro_id=str(usuario.id),
                detalle=f"Código TOTP inválido en mfa-verify para {usuario.email}",
                request=request,
            )
        except Exception:
            pass

        return Response(
            {"error": "Código MFA inválido o expirado."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # 4. MFA correcto — resetear intentos y emitir JWT definitivo
    if usuario.intentos_fallidos > 0 or usuario.bloqueado_hasta:
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        usuario.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])

    # Registrar IP
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = x_forwarded.split(",")[0] if x_forwarded else request.META.get("REMOTE_ADDR")
    usuario.ultimo_login_ip = ip
    usuario.save(update_fields=["ultimo_login_ip"])

    # Auditoría
    try:
        from auditoria.models import RegistroAuditoria
        RegistroAuditoria.registrar(
            usuario=usuario,
            accion="LOGIN",
            modulo="Usuario",
            registro_id=str(usuario.id),
            detalle=f"Login MFA exitoso — rol: {usuario.rol}",
            request=request,
        )
    except Exception:
        pass

    # Emitir JWT definitivo (sin claim mfa_pending)
    refresh = RefreshToken.for_user(usuario)

    permisos_set = set()
    permisos_set.update(usuario.user_permissions.values_list("codename", flat=True))
    for group in usuario.groups.all():
        permisos_set.update(group.permissions.values_list("codename", flat=True))

    # SEGURIDAD: igual que login_view — JWT solo en cookies httpOnly
    response = Response(
        {
            "user": {
                "id": usuario.id,
                "email": usuario.email,
                "nombre": usuario.nombre_completo,
                "rol": usuario.rol,
                "especialidad": usuario.especialidad,
                "foto_url": (
                    request.build_absolute_uri(usuario.foto.url) if usuario.foto else None
                ),
                "is_staff": usuario.is_staff,
                "is_superuser": usuario.is_superuser,
                "permisos": list(permisos_set),
            },
        },
        status=status.HTTP_200_OK,
    )
    set_jwt_cookies(response, access=refresh.access_token, refresh=refresh)
    csrf_get_token(request)
    return response
