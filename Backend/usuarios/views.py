"""Views module."""
import logging
import math
from datetime import timedelta

import pyotp
from django.contrib.auth.models import Permission
from django.middleware.csrf import get_token as csrf_get_token
from django.utils import timezone as tz
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import (
    action,
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from auditoria.sesion import CLAIM as SID_CLAIM
from auditoria.sesion import fijar_sesion, nuevo_sid

from core.throttling import LoginRateThrottle, registrar_intento_fallido

from .auth_cookies import REFRESH_COOKIE, clear_jwt_cookies, set_jwt_cookies
from .models import HorarioAtencion, Usuario
from .permisos_por_rol import permisos_de_usuario
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

logger = logging.getLogger(__name__)

# ── Temp token MFA ────────────────────────────────────────────────────────────
# El temp_token es un JWT de 5 minutos que solo contiene user_id y el claim
# "mfa_pending": true. Se genera con RefreshToken del usuario pero se firma con
# un claim adicional para que el backend pueda distinguirlo de un access token real.

# Propósitos (claims) en auth_cookies.CLAIMS_TEMPORALES: ninguno vale como sesión.
def _build_temp_token(usuario, proposito: str = "mfa_pending", minutos: int = 5) -> str:
    """Genera un JWT temporal que marca el estado pendiente de MFA."""
    refresh = RefreshToken.for_user(usuario)
    access = refresh.access_token
    access.set_exp(lifetime=timedelta(minutes=minutos))
    access[proposito] = True  # claim custom — diferencia de un access válido
    # Blacklistear el refresh para que no pueda usarse directamente
    refresh.blacklist()
    return str(access)


def _nuevo_secreto_mfa(usuario) -> dict:
    """Genera el secreto TOTP del usuario y su QR para Google Authenticator."""
    import base64
    import io

    import qrcode

    secret = pyotp.random_base32()
    usuario.mfa_secret = secret
    usuario.save(update_fields=["mfa_secret"])
    uri = pyotp.TOTP(secret).provisioning_uri(name=usuario.email, issuer_name="Fetal Medical Bolivia")
    buf = io.BytesIO()
    qrcode.make(uri).save(buf)
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}",
        "uri": uri,
        "mensaje": "Escanee el QR con Google Authenticator y confirme con el código de 6 dígitos.",
    }


def _auditar_mfa_activado(request, usuario) -> None:
    # Contrapartida de MFA_DESACTIVADO: sin registrar tambien la activacion,
    # la auditoria mostraria bajas de seguridad sin sus altas y no se podria
    # reconstruir el estado de una cuenta.
    try:
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.registrar(
            usuario=usuario,
            accion="MFA_ACTIVADO",
            modulo="Usuario",
            registro_id=str(usuario.id),
            detalle=f"MFA activado por {usuario.email}",
            request=request,
        )
    except Exception:
        logger.warning("No se pudo auditar el MFA activado", exc_info=True)


def _decode_temp_token(token_str, proposito: str = "mfa_pending"):
    """Valida el temp_token y retorna el Usuario o lanza excepción."""
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import AccessToken

    try:
        token = AccessToken(token_str)
    except TokenError as exc:
        raise ValueError("temp_token inválido o expirado") from exc

    if not token.get(proposito):
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

    #: Solo el administrador. Antes el ViewSet entero pedía solo sesión: recepción
    #: podía crear usuarios, borrarlos, desactivar al administrador o
    #: ascenderse a superusuario con un PATCH.
    ACCIONES_SOLO_ADMIN = frozenset({"create", "destroy", "activar", "desactivar", "restablecer_mfa"})
    #: Campos que un usuario no administrador no puede tocar ni en su propio perfil.
    #: La contraseña se cambia por `cambiar_password`, que pide la actual.
    CAMPOS_PROTEGIDOS = ("rol", "is_staff", "is_superuser", "activo", "email",
                         "permisos_ids", "grupos_ids", "password", "password_confirm")

    @staticmethod
    def _es_admin(usuario) -> bool:
        return bool(usuario.is_superuser or getattr(usuario, "rol", "") == "administrador")

    def get_permissions(self):
        permisos = super().get_permissions()
        usuario = getattr(getattr(self, "request", None), "user", None)
        if (self.action in self.ACCIONES_SOLO_ADMIN and usuario is not None
                and usuario.is_authenticated and not self._es_admin(usuario)):
            raise PermissionDenied("Solo un administrador puede hacer esto.")
        return permisos

    def update(self, request, *args, **kwargs):
        """El administrador edita a cualquiera; los demás, solo su perfil.

        La página de perfil envía el usuario completo (con rol, is_staff…), así
        que para no romperla los campos protegidos se descartan en silencio en
        vez de rechazar la petición.
        """
        if self._es_admin(request.user):
            return super().update(request, *args, **kwargs)
        instancia = self.get_object()
        if instancia.pk != request.user.pk:
            raise PermissionDenied("Solo puede editar su propio perfil.")
        datos = request.data.copy()
        for campo in self.CAMPOS_PROTEGIDOS:
            datos.pop(campo, None)
        serializer = self.get_serializer(instancia, data=datos, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
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

    def perform_update(self, serializer):
        """Guarda el usuario y deja constancia si le cambio el rol.

        Un cambio de rol no es una edicion mas: da o quita acceso a datos
        clinicos de otras pacientes. En la auditoria tiene que verse como el
        hecho que es, con el rol anterior y el nuevo, no escondido dentro de
        un EDITAR generico.
        """
        rol_anterior = serializer.instance.rol
        usuario = serializer.save()

        if usuario.rol != rol_anterior:
            try:
                from auditoria.models import RegistroAuditoria

                RegistroAuditoria.registrar(
                    usuario=self.request.user
                    if getattr(self.request.user, "is_authenticated", False)
                    else None,
                    accion="CAMBIO_ROL",
                    modulo="Usuario",
                    registro_id=str(usuario.id),
                    detalle=(
                        f"Rol de {usuario.email}: {rol_anterior} -> {usuario.rol}"
                    ),
                    request=self.request,
                )
            except Exception:
                logger.warning("No se pudo auditar el cambio de rol", exc_info=True)

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

    @action(detail=True, methods=["post"], url_path="restablecer-mfa")
    def restablecer_mfa(self, request, pk=None):
        """El administrador borra el MFA de alguien que perdió o cambió el celular.

        Sin esto, un médico sin su teléfono quedaba fuera para siempre: el MFA
        es obligatorio para su rol y nadie podía quitárselo. Al entrar de nuevo
        el sistema le pide configurarlo otra vez (con su contraseña).
        """
        usuario = self.get_object()
        usuario.mfa_enabled = False
        usuario.mfa_secret = None
        usuario.save(update_fields=["mfa_enabled", "mfa_secret"])
        try:
            from auditoria.models import RegistroAuditoria

            RegistroAuditoria.registrar(
                usuario=request.user,
                accion="MFA_RESTABLECIDO",
                modulo="Usuario",
                registro_id=str(usuario.id),
                detalle=f"MFA de {usuario.email} restablecido por {request.user.email}",
                request=request,
            )
        except Exception:
            logger.warning("No se pudo auditar el MFA restablecido", exc_info=True)
        return Response({"mensaje": f"MFA de {usuario.nombre_completo} restablecido: lo configurará al entrar."})

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
        return Response(_nuevo_secreto_mfa(request.user))

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
            _auditar_mfa_activado(request, request.user)

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

            # Quitarse el segundo factor BAJA la seguridad de una cuenta con
            # acceso a datos clinicos: es justo lo que hay que poder revisar.
            try:
                from auditoria.models import RegistroAuditoria

                RegistroAuditoria.registrar(
                    usuario=request.user,
                    accion="MFA_DESACTIVADO",
                    modulo="Usuario",
                    registro_id=str(request.user.id),
                    detalle=f"MFA desactivado por {request.user.email}",
                    request=request,
                )
            except Exception:
                logger.warning("No se pudo auditar el MFA desactivado", exc_info=True)

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


def _respuesta_cuenta_bloqueada(usuario):
    """423 con el tiempo que falta. Antes era un 403 que la pantalla de login
    mostraba como «Acceso denegado. Contacte al administrador.» (BUG-002)."""
    minutos = max(1, math.ceil((usuario.bloqueado_hasta - tz.now()).total_seconds() / 60))
    return Response(
        {
            "error": (
                "Cuenta bloqueada temporalmente por 5 intentos fallidos. "
                f"Podrá intentar de nuevo en {minutos} minuto{'s' if minutos != 1 else ''}."
            ),
            "codigo": "cuenta_bloqueada",
            "minutos_restantes": minutos,
        },
        status=status.HTTP_423_LOCKED,
    )


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
        423: OpenApiResponse(description="Locked - cuenta bloqueada 15 min tras 5 intentos fallidos"),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
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
        # Probar emails que no existen es exactamente el recorrido que el
        # limite por IP tiene que cortar, asi que gasta cupo.
        registrar_intento_fallido(request)
        return Response(
            {"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED,
        )

    # Verificar bloqueo de cuenta (máx 5 intentos)
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > tz.now():
        return _respuesta_cuenta_bloqueada(usuario)

    # Verificar contraseña
    if not usuario.check_password(password):
        # Gasta cupo de la IP. Un login CORRECTO no llega hasta aqui y por eso
        # no consume nada: cien personas entrando bien no se estorban.
        registrar_intento_fallido(request)
        usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
        if usuario.intentos_fallidos >= 5:
            from datetime import timedelta

            usuario.bloqueado_hasta = tz.now() + timedelta(minutes=15)
            usuario.intentos_fallidos = 0
            # El bloqueo es un hecho distinto de los intentos fallidos: la
            # cuenta queda fuera de servicio 15 minutos. En una guardia eso
            # deja a alguien sin poder trabajar, y hay que poder verlo.
            try:
                from auditoria.models import RegistroAuditoria

                RegistroAuditoria.registrar(
                    usuario=None,
                    accion="CUENTA_BLOQUEADA",
                    modulo="Usuario",
                    registro_id=str(usuario.id),
                    detalle=f"Cuenta {email} bloqueada 15 min por 5 intentos fallidos",
                    request=request,
                )
            except Exception:
                pass
        usuario.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])
        bloqueada_ahora = usuario.bloqueado_hasta is not None and usuario.bloqueado_hasta > tz.now()
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
        if bloqueada_ahora:
            # El quinto intento ya avisa del bloqueo, no «credenciales inválidas».
            return _respuesta_cuenta_bloqueada(usuario)
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

    # MFA OBLIGATORIO: médico/admin sin MFA configurado → no hay sesión todavía.
    # Antes era un callejón sin salida: /mfa/setup/ exige sesión y aquí no se
    # daba ninguna, así que un médico nuevo en producción no podía entrar nunca.
    # Ahora recibe un token que SOLO sirve para configurar el MFA (10 min: hay
    # que instalar la app y escanear el QR).
    if getattr(usuario, "mfa_obligatorio", False) and not usuario.mfa_enabled:
        return Response(
            {
                "mfa_setup_required": True,
                "temp_token": _build_temp_token(usuario, "mfa_setup_pending", minutos=10),
                "mensaje": (
                    "Su rol requiere autenticación de dos factores (MFA). "
                    "Configúrela antes de continuar: POST /api/usuarios/mfa-setup-inicial/"
                ),
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    # Registrar IP de último acceso
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = x_forwarded.split(",")[0] if x_forwarded else request.META.get("REMOTE_ADDR")
    usuario.ultimo_login_ip = ip
    # Este login no pasa por django.contrib.auth.login(): last_login quedaba
    # congelado y «Último acceso» del perfil y de Usuarios mostraba fechas viejas.
    usuario.last_login = tz.now()
    usuario.save(update_fields=["ultimo_login_ip", "last_login"])

    # Sesión de auditoría: todo lo que haga con este token queda asociado.
    sid = nuevo_sid()
    fijar_sesion(request, sid)

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
    refresh[SID_CLAIM] = sid  # se copia al access y sobrevive a los refresh

    # Directos y de grupos, menos los módulos que quita el cargo.
    permisos = permisos_de_usuario(usuario)

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
    usuario_del_token = None
    try:
        if refresh_token:
            token = RefreshToken(refresh_token)
            if token.get(SID_CLAIM):
                fijar_sesion(request, token[SID_CLAIM])
            # Con el access ya vencido request.user es anónimo: el LOGOUT quedaba sin usuario.
            usuario_del_token = Usuario.objects.filter(pk=token.get("user_id")).first()
            token.blacklist()
    except Exception:
        pass  # token vencido/inválido: igual cerramos la sesión del navegador

    # `LOGOUT` estaba declarada en RegistroAuditoria.ACCIONES desde el
    # principio pero nunca se emitía: la auditoría sabía cuándo entraba cada
    # usuario y no cuándo salía, así que no se podía delimitar una sesión.
    try:
        from auditoria.models import RegistroAuditoria

        usuario = request.user if getattr(request, "user", None) else None
        if not getattr(usuario, "is_authenticated", False):
            usuario = usuario_del_token
        RegistroAuditoria.registrar(
            usuario=usuario,
            accion="LOGOUT",
            modulo="Usuario",
            detalle="Cierre de sesión",
            request=request,
        )
    except Exception:  # auditar nunca puede impedir cerrar la sesión
        pass

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


def _emitir_sesion(request, usuario, detalle: str) -> Response:
    """Cierra un login con MFA: IP, sesión de auditoría, LOGIN y cookies httpOnly.

    La usan el paso 2 del login (mfa-verify) y la activación inicial del MFA.
    """
    # Registrar IP
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = x_forwarded.split(",")[0] if x_forwarded else request.META.get("REMOTE_ADDR")
    usuario.ultimo_login_ip = ip
    # Este login no pasa por django.contrib.auth.login(): last_login quedaba
    # congelado y «Último acceso» del perfil y de Usuarios mostraba fechas viejas.
    usuario.last_login = tz.now()
    usuario.save(update_fields=["ultimo_login_ip", "last_login"])

    # Sesión de auditoría: todo lo que haga con este token queda asociado.
    sid = nuevo_sid()
    fijar_sesion(request, sid)

    # Auditoría
    try:
        from auditoria.models import RegistroAuditoria
        RegistroAuditoria.registrar(
            usuario=usuario,
            accion="LOGIN",
            modulo="Usuario",
            registro_id=str(usuario.id),
            detalle=f"{detalle} — rol: {usuario.rol}",
            request=request,
        )
    except Exception:
        pass

    # Emitir JWT definitivo (sin claim mfa_pending)
    refresh = RefreshToken.for_user(usuario)
    refresh[SID_CLAIM] = sid

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
                "permisos": permisos_de_usuario(usuario),
            },
        },
        status=status.HTTP_200_OK,
    )
    set_jwt_cookies(response, access=refresh.access_token, refresh=refresh)
    csrf_get_token(request)
    return response


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
@throttle_classes([LoginRateThrottle])
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
        # Un temp_token invalido o caducado es un intento fallido como
        # cualquier otro: gasta cupo de la IP.
        registrar_intento_fallido(request)
        return Response({"error": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

    # 2. Verificar bloqueo de cuenta
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > tz.now():
        return _respuesta_cuenta_bloqueada(usuario)

    # 3. Verificar código TOTP
    if not usuario.mfa_secret:
        return Response(
            {"error": "MFA no configurado para este usuario."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    totp = pyotp.TOTP(usuario.mfa_secret)
    if not totp.verify(totp_code, valid_window=1):
        # Adivinar codigos TOTP tambien gasta cupo de la IP.
        registrar_intento_fallido(request)
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

    return _emitir_sesion(request, usuario, "Login MFA exitoso")


@extend_schema(
    tags=["Authentication"],
    summary="Configurar MFA por primera vez (sin sesión)",
    description=(
        "Para quien su rol exige MFA y aún no lo tiene: con el temp_token que devolvió "
        "el login (mfa_setup_required) genera el secreto y el QR."
    ),
    responses={200: OpenApiResponse(description="QR y secreto"), 401: OpenApiResponse(description="Token inválido")},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def mfa_setup_inicial_view(request):
    try:
        usuario = _decode_temp_token(str(request.data.get("temp_token", "")), "mfa_setup_pending")
    except ValueError as exc:
        registrar_intento_fallido(request)
        return Response({"error": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
    if usuario.mfa_enabled:
        # Un token viejo no puede reemplazar el secreto de un MFA ya activo.
        return Response({"error": "El MFA ya está activo: inicie sesión."}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_nuevo_secreto_mfa(usuario))


@extend_schema(
    tags=["Authentication"],
    summary="Activar MFA por primera vez y entrar",
    description="Verifica el primer código TOTP, activa el MFA y abre la sesión (cookies httpOnly).",
    responses={200: OpenApiResponse(description="MFA activo y sesión abierta"),
               400: OpenApiResponse(description="Código inválido"), 401: OpenApiResponse(description="Token inválido")},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def mfa_confirmar_inicial_view(request):
    try:
        usuario = _decode_temp_token(str(request.data.get("temp_token", "")), "mfa_setup_pending")
    except ValueError as exc:
        registrar_intento_fallido(request)
        return Response({"error": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
    if usuario.mfa_enabled or not usuario.mfa_secret:
        return Response({"error": "Genere primero el QR."}, status=status.HTTP_400_BAD_REQUEST)
    if not pyotp.TOTP(usuario.mfa_secret).verify(str(request.data.get("code", "")), valid_window=1):
        registrar_intento_fallido(request)
        return Response({"error": "Código inválido o expirado"}, status=status.HTTP_400_BAD_REQUEST)
    usuario.mfa_enabled = True
    usuario.save(update_fields=["mfa_enabled"])
    _auditar_mfa_activado(request, usuario)
    return _emitir_sesion(request, usuario, "Login al activar MFA")
