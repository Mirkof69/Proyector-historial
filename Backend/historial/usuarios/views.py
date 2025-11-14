# =============================================================================
# VIEWS DE USUARIOS
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# App: usuarios
# Descripción: Views completas para gestión de usuarios, autenticación,
#              perfiles, contraseñas, sesiones, bloqueos y administración.
# Autor: Sistema de Gestión Médica
# Versión: 3.0.0 - EXTENDIDO
# Última actualización: 2025-11-14
# =============================================================================

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta, datetime
import logging

from .models import (
    Usuario,
    HistorialSesion,
    TokenRecuperacion,
    TokenVerificacionEmail
)
from .serializers import (
    UsuarioBasicoSerializer,
    UsuarioListaSerializer,
    UsuarioDetalleSerializer,
    UsuarioCrearSerializer,
    UsuarioActualizarSerializer,
    UsuarioAdminActualizarSerializer,
    LoginSerializer,
    LoginResponseSerializer,
    LogoutSerializer,
    CambiarPasswordSerializer,
    SolicitarRecuperacionPasswordSerializer,
    RecuperarPasswordSerializer,
    RestablecerPasswordAdminSerializer,
    VerificarEmailSerializer,
    ReenviarVerificacionEmailSerializer,
    HistorialSesionSerializer,
    BloquearUsuarioSerializer,
    DesbloquearUsuarioSerializer,
    PerfilSerializer,
    EstadisticasUsuarioSerializer,
)
from .permissions import (
    EsAdministrador,
    EsPersonalSalud,
    PuedeModificarPerfil,
    UsuarioActivo,
)

# Configurar logger
logger = logging.getLogger(__name__)


# =============================================================================
# UTILIDADES
# =============================================================================

def obtener_ip_cliente(request):
    """
    Obtiene la dirección IP del cliente desde el request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def obtener_user_agent(request):
    """
    Obtiene el user agent del navegador.
    """
    return request.META.get('HTTP_USER_AGENT', '')


def registrar_sesion(usuario, accion, request, exitoso=True, razon_fallo=None):
    """
    Registra una acción de sesión en el historial.

    Args:
        usuario: Usuario que realiza la acción
        accion: Tipo de acción (login, logout, etc.)
        request: Request HTTP
        exitoso: Si la acción fue exitosa
        razon_fallo: Razón del fallo si aplica
    """
    try:
        HistorialSesion.objects.create(
            usuario=usuario,
            accion=accion,
            fecha_hora=timezone.now(),
            ip_address=obtener_ip_cliente(request),
            user_agent=obtener_user_agent(request),
            exitoso=exitoso,
            razon_fallo=razon_fallo
        )
    except Exception as e:
        logger.error(f"Error al registrar sesión: {str(e)}")


def enviar_email_recuperacion(usuario, token):
    """
    Envía email de recuperación de contraseña.

    Args:
        usuario: Usuario que solicita recuperación
        token: Token de recuperación
    """
    try:
        asunto = 'Recuperación de contraseña - Sistema Médico'
        mensaje = f"""
        Hola {usuario.nombre},

        Has solicitado recuperar tu contraseña.

        Usa el siguiente token para restablecer tu contraseña:
        {token.token}

        Este token expira en 24 horas.

        Si no solicitaste este cambio, ignora este mensaje.

        Saludos,
        Sistema de Historial Médico
        """

        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Error al enviar email de recuperación: {str(e)}")
        return False


def enviar_email_verificacion(usuario, token):
    """
    Envía email de verificación de cuenta.

    Args:
        usuario: Usuario que verifica email
        token: Token de verificación
    """
    try:
        asunto = 'Verifica tu cuenta - Sistema Médico'
        mensaje = f"""
        Hola {usuario.nombre},

        Gracias por registrarte en el Sistema de Historial Médico.

        Para activar tu cuenta, usa el siguiente token:
        {token.token}

        Este token expira en 7 días.

        Saludos,
        Sistema de Historial Médico
        """

        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Error al enviar email de verificación: {str(e)}")
        return False


# =============================================================================
# AUTENTICACIÓN
# =============================================================================

class LoginView(APIView):
    """
    Vista para login de usuarios.
    Valida credenciales, verifica estado de cuenta y genera tokens JWT.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        """
        POST /api/usuarios/login/
        Autenticar usuario y generar tokens.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        recordarme = serializer.validated_data.get('recordarme', False)

        try:
            # Buscar usuario
            usuario = Usuario.objects.get(
                email=email,
                eliminado=False
            )

            # Verificar si puede hacer login
            puede_login, mensaje_error = usuario.verificar_puede_login()
            if not puede_login:
                registrar_sesion(
                    usuario,
                    'login_fallido',
                    request,
                    exitoso=False,
                    razon_fallo=mensaje_error
                )
                return Response(
                    {'error': mensaje_error},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Verificar contraseña
            if not usuario.check_password(password):
                usuario.registrar_login_fallido()
                registrar_sesion(
                    usuario,
                    'login_fallido',
                    request,
                    exitoso=False,
                    razon_fallo='Contraseña incorrecta'
                )
                return Response(
                    {'error': 'Credenciales inválidas'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Login exitoso
            usuario.registrar_login_exitoso(
                ip_address=obtener_ip_cliente(request),
                user_agent=obtener_user_agent(request)
            )

            # Generar tokens JWT
            refresh = RefreshToken.for_user(usuario)

            # Extender tiempo de refresh token si "recordarme" está activo
            if recordarme:
                refresh.access_token.set_exp(lifetime=timedelta(days=30))

            # Registrar en historial
            registrar_sesion(usuario, 'login', request, exitoso=True)

            # Preparar respuesta
            respuesta_data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'usuario': UsuarioDetalleSerializer(usuario).data,
                'mensaje': 'Login exitoso'
            }

            # Advertir si la contraseña expiró
            if usuario.password_expirado:
                respuesta_data['advertencia'] = 'Tu contraseña ha expirado. Deberías cambiarla pronto.'

            # Advertir si requiere cambio de contraseña
            if usuario.requiere_cambio_password:
                respuesta_data['requiere_cambio_password'] = True
                respuesta_data['advertencia'] = 'Debes cambiar tu contraseña.'

            return Response(respuesta_data, status=status.HTTP_200_OK)

        except Usuario.DoesNotExist:
            # No revelar si el usuario existe o no (seguridad)
            return Response(
                {'error': 'Credenciales inválidas'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """
    Vista para cerrar sesión.
    Invalida el refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        POST /api/usuarios/logout/
        Cerrar sesión del usuario.
        """
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Registrar en historial
            registrar_sesion(request.user, 'logout', request, exitoso=True)

            return Response(
                {'mensaje': 'Sesión cerrada exitosamente'},
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {'error': 'Token inválido o expirado'},
                status=status.HTTP_400_BAD_REQUEST
            )


# =============================================================================
# VIEWSET DE USUARIOS (CRUD)
# =============================================================================

class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de usuarios.
    Incluye CRUD, búsqueda, filtros y acciones personalizadas.
    """
    queryset = Usuario.objects.filter(eliminado=False)
    permission_classes = [permissions.IsAuthenticated, UsuarioActivo]

    def get_serializer_class(self):
        """Retorna el serializer según la acción"""
        if self.action == 'list':
            return UsuarioListaSerializer
        elif self.action == 'retrieve':
            return UsuarioDetalleSerializer
        elif self.action == 'create':
            return UsuarioCrearSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            if self.request.user.es_administrador:
                return UsuarioAdminActualizarSerializer
            return UsuarioActualizarSerializer
        return UsuarioBasicoSerializer

    def get_queryset(self):
        """
        Filtra el queryset según el usuario y parámetros.
        """
        queryset = Usuario.objects.filter(eliminado=False)

        # Filtros
        rol = self.request.query_params.get('rol')
        estado = self.request.query_params.get('estado')
        especialidad = self.request.query_params.get('especialidad')
        activo = self.request.query_params.get('activo')
        buscar = self.request.query_params.get('buscar')

        if rol:
            queryset = queryset.filter(rol=rol)

        if estado:
            queryset = queryset.filter(estado=estado)

        if especialidad:
            queryset = queryset.filter(especialidad=especialidad)

        if activo is not None:
            activo_bool = activo.lower() == 'true'
            queryset = queryset.filter(activo=activo_bool)

        if buscar:
            queryset = queryset.filter(
                Q(nombre__icontains=buscar) |
                Q(apellido_paterno__icontains=buscar) |
                Q(apellido_materno__icontains=buscar) |
                Q(email__icontains=buscar) |
                Q(cedula_identidad__icontains=buscar)
            )

        return queryset.order_by('-fecha_creacion')

    def create(self, request, *args, **kwargs):
        """
        POST /api/usuarios/
        Crear nuevo usuario.
        Solo administradores.
        """
        if not request.user.es_administrador:
            return Response(
                {'error': 'Solo administradores pueden crear usuarios'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()

        # Enviar email de verificación
        token = TokenVerificacionEmail.objects.filter(usuario=usuario).first()
        if token:
            enviar_email_verificacion(usuario, token)

        return Response(
            UsuarioDetalleSerializer(usuario).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """
        PUT /api/usuarios/{id}/
        Actualizar usuario completo.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Verificar permisos
        if not request.user.es_administrador and request.user.id != instance.id:
            return Response(
                {'error': 'No tienes permiso para editar este usuario'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(UsuarioDetalleSerializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/usuarios/{id}/
        Eliminar usuario (soft delete).
        Solo administradores.
        """
        if not request.user.es_administrador:
            return Response(
                {'error': 'Solo administradores pueden eliminar usuarios'},
                status=status.HTTP_403_FORBIDDEN
            )

        instance = self.get_object()

        # No permitir auto-eliminación
        if request.user.id == instance.id:
            return Response(
                {'error': 'No puedes eliminarte a ti mismo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Soft delete
        instance.eliminado = True
        instance.fecha_eliminacion = timezone.now()
        instance.eliminado_por = request.user
        instance.save()

        return Response(
            {'mensaje': 'Usuario eliminado exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        GET /api/usuarios/me/
        Obtener perfil del usuario actual.
        """
        serializer = PerfilSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def medicos(self, request):
        """
        GET /api/usuarios/medicos/
        Listar solo médicos activos.
        """
        medicos = Usuario.objects.filter(
            rol='medico',
            activo=True,
            eliminado=False
        )
        serializer = UsuarioBasicoSerializer(medicos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def enfermeros(self, request):
        """
        GET /api/usuarios/enfermeros/
        Listar solo enfermeros activos.
        """
        enfermeros = Usuario.objects.filter(
            rol='enfermero',
            activo=True,
            eliminado=False
        )
        serializer = UsuarioBasicoSerializer(enfermeros, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[EsAdministrador])
    def estadisticas(self, request):
        """
        GET /api/usuarios/estadisticas/
        Obtener estadísticas de usuarios.
        Solo administradores.
        """
        # Estadísticas generales
        total = Usuario.objects.filter(eliminado=False).count()
        activos = Usuario.objects.filter(eliminado=False, activo=True).count()
        inactivos = total - activos
        bloqueados = Usuario.objects.filter(
            eliminado=False,
            estado='bloqueado'
        ).count()

        # Por rol
        por_rol = {}
        for rol_key, rol_name in Usuario.ROLES:
            count = Usuario.objects.filter(
                eliminado=False,
                rol=rol_key
            ).count()
            por_rol[rol_name] = count

        # Nuevos este mes
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        nuevos_mes = Usuario.objects.filter(
            eliminado=False,
            fecha_creacion__gte=inicio_mes
        ).count()

        # Logins hoy
        inicio_hoy = timezone.now().replace(hour=0, minute=0, second=0)
        logins_hoy = HistorialSesion.objects.filter(
            accion='login',
            fecha_hora__gte=inicio_hoy
        ).count()

        data = {
            'total_usuarios': total,
            'usuarios_activos': activos,
            'usuarios_inactivos': inactivos,
            'usuarios_bloqueados': bloqueados,
            'por_rol': por_rol,
            'nuevos_este_mes': nuevos_mes,
            'logins_hoy': logins_hoy,
        }

        serializer = EstadisticasUsuarioSerializer(data)
        return Response(serializer.data)


# =============================================================================
# CAMBIO DE CONTRASEÑA
# =============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cambiar_password(request):
    """
    POST /api/usuarios/cambiar-password/
    Cambiar contraseña del usuario actual.
    """
    serializer = CambiarPasswordSerializer(
        data=request.data,
        context={
            'request': request,
            'ip_address': obtener_ip_cliente(request)
        }
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {'mensaje': 'Contraseña cambiada exitosamente'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def solicitar_recuperacion_password(request):
    """
    POST /api/usuarios/solicitar-recuperacion-password/
    Solicitar recuperación de contraseña.
    """
    serializer = SolicitarRecuperacionPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']

    try:
        usuario = Usuario.objects.get(
            email=email,
            activo=True,
            eliminado=False
        )

        # Generar token
        token = TokenRecuperacion.generar_token(
            usuario,
            ip_address=obtener_ip_cliente(request)
        )

        # Enviar email
        enviado = enviar_email_recuperacion(usuario, token)

        if enviado:
            # Registrar en historial
            registrar_sesion(
                usuario,
                'recuperacion_password',
                request,
                exitoso=True
            )

    except Usuario.DoesNotExist:
        # No revelar si el email existe o no (seguridad)
        pass

    # Siempre retornar éxito (no revelar si el email existe)
    return Response(
        {'mensaje': 'Si el email existe, recibirás instrucciones de recuperación'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def recuperar_password(request):
    """
    POST /api/usuarios/recuperar-password/
    Recuperar contraseña con token.
    """
    serializer = RecuperarPasswordSerializer(
        data=request.data,
        context={'ip_address': obtener_ip_cliente(request)}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {'mensaje': 'Contraseña recuperada exitosamente. Ya puedes iniciar sesión.'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([EsAdministrador])
def restablecer_password_admin(request):
    """
    POST /api/usuarios/restablecer-password-admin/
    Restablecer contraseña de un usuario (solo admin).
    """
    serializer = RestablecerPasswordAdminSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    usuario = serializer.save()

    return Response(
        {
            'mensaje': 'Contraseña restablecida exitosamente',
            'requiere_cambio': usuario.requiere_cambio_password
        },
        status=status.HTTP_200_OK
    )


# =============================================================================
# VERIFICACIÓN DE EMAIL
# =============================================================================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verificar_email(request):
    """
    POST /api/usuarios/verificar-email/
    Verificar email con token.
    """
    serializer = VerificarEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    usuario = serializer.save()

    return Response(
        {
            'mensaje': 'Email verificado exitosamente',
            'usuario': UsuarioBasicoSerializer(usuario).data
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reenviar_verificacion_email(request):
    """
    POST /api/usuarios/reenviar-verificacion/
    Reenviar email de verificación.
    """
    serializer = ReenviarVerificacionEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Obtener usuario si existe
    usuario_obj = serializer.context.get('usuario_obj')
    if usuario_obj:
        # Generar nuevo token
        token = TokenVerificacionEmail.generar_token(usuario_obj)
        enviar_email_verificacion(usuario_obj, token)

    # Siempre retornar éxito (no revelar si el email existe)
    return Response(
        {'mensaje': 'Si el email existe y no está verificado, recibirás un nuevo correo'},
        status=status.HTTP_200_OK
    )


# =============================================================================
# BLOQUEO Y DESBLOQUEO
# =============================================================================

@api_view(['POST'])
@permission_classes([EsAdministrador])
def bloquear_usuario(request):
    """
    POST /api/usuarios/bloquear/
    Bloquear un usuario.
    """
    serializer = BloquearUsuarioSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    usuario = serializer.save()

    return Response(
        {
            'mensaje': 'Usuario bloqueado exitosamente',
            'usuario': UsuarioBasicoSerializer(usuario).data
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([EsAdministrador])
def desbloquear_usuario(request):
    """
    POST /api/usuarios/desbloquear/
    Desbloquear un usuario.
    """
    serializer = DesbloquearUsuarioSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    usuario = serializer.save()

    return Response(
        {
            'mensaje': 'Usuario desbloqueado exitosamente',
            'usuario': UsuarioBasicoSerializer(usuario).data
        },
        status=status.HTTP_200_OK
    )


# =============================================================================
# HISTORIAL DE SESIONES
# =============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def historial_sesiones(request):
    """
    GET /api/usuarios/historial-sesiones/
    Obtener historial de sesiones del usuario actual.
    """
    sesiones = HistorialSesion.objects.filter(
        usuario=request.user
    ).order_by('-fecha_hora')[:50]  # Últimas 50 sesiones

    serializer = HistorialSesionSerializer(sesiones, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([EsAdministrador])
def historial_sesiones_usuario(request, usuario_id):
    """
    GET /api/usuarios/{id}/historial-sesiones/
    Obtener historial de sesiones de un usuario específico.
    Solo administradores.
    """
    try:
        usuario = Usuario.objects.get(id=usuario_id, eliminado=False)
    except Usuario.DoesNotExist:
        return Response(
            {'error': 'Usuario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    sesiones = HistorialSesion.objects.filter(
        usuario=usuario
    ).order_by('-fecha_hora')

    serializer = HistorialSesionSerializer(sesiones, many=True)
    return Response(serializer.data)


# =============================================================================
# PERFIL DE USUARIO
# =============================================================================

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def perfil(request):
    """
    GET/PUT/PATCH /api/usuarios/perfil/
    Obtener o actualizar perfil del usuario actual.
    """
    usuario = request.user

    if request.method == 'GET':
        serializer = PerfilSerializer(usuario)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = UsuarioActualizarSerializer(
            usuario,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            PerfilSerializer(usuario).data,
            status=status.HTTP_200_OK
        )


# =============================================================================
# ACTIVACIÓN Y DESACTIVACIÓN
# =============================================================================

@api_view(['POST'])
@permission_classes([EsAdministrador])
def activar_usuario(request, usuario_id):
    """
    POST /api/usuarios/{id}/activar/
    Activar un usuario inactivo.
    """
    try:
        usuario = Usuario.objects.get(id=usuario_id, eliminado=False)
    except Usuario.DoesNotExist:
        return Response(
            {'error': 'Usuario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    usuario.activo = True
    usuario.estado = 'activo'
    usuario.save()

    return Response(
        {
            'mensaje': 'Usuario activado exitosamente',
            'usuario': UsuarioBasicoSerializer(usuario).data
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([EsAdministrador])
def desactivar_usuario(request, usuario_id):
    """
    POST /api/usuarios/{id}/desactivar/
    Desactivar un usuario.
    """
    try:
        usuario = Usuario.objects.get(id=usuario_id, eliminado=False)
    except Usuario.DoesNotExist:
        return Response(
            {'error': 'Usuario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # No permitir auto-desactivación
    if request.user.id == usuario.id:
        return Response(
            {'error': 'No puedes desactivarte a ti mismo'},
            status=status.HTTP_400_BAD_REQUEST
        )

    usuario.activo = False
    usuario.estado = 'inactivo'
    usuario.save()

    return Response(
        {
            'mensaje': 'Usuario desactivado exitosamente',
            'usuario': UsuarioBasicoSerializer(usuario).data
        },
        status=status.HTTP_200_OK
    )


# =============================================================================
# REGISTRO PÚBLICO
# =============================================================================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def registro_publico(request):
    """
    POST /api/usuarios/registro/
    Registro público de nuevos usuarios (pacientes).
    """
    # Forzar rol de paciente
    data = request.data.copy()
    data['rol'] = 'paciente'

    serializer = UsuarioCrearSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    usuario = serializer.save()

    # Enviar email de verificación
    token = TokenVerificacionEmail.objects.filter(usuario=usuario).first()
    if token:
        enviar_email_verificacion(usuario, token)

    return Response(
        {
            'mensaje': 'Usuario registrado exitosamente. Revisa tu email para verificar tu cuenta.',
            'usuario': UsuarioBasicoSerializer(usuario).data
        },
        status=status.HTTP_201_CREATED
    )


# =============================================================================
# BÚSQUEDA AVANZADA
# =============================================================================

@api_view(['GET'])
@permission_classes([EsPersonalSalud])
def buscar_usuarios(request):
    """
    GET /api/usuarios/buscar/
    Búsqueda avanzada de usuarios.
    """
    query = request.query_params.get('q', '')
    if len(query) < 2:
        return Response(
            {'error': 'La búsqueda debe tener al menos 2 caracteres'},
            status=status.HTTP_400_BAD_REQUEST
        )

    usuarios = Usuario.objects.filter(
        Q(nombre__icontains=query) |
        Q(apellido_paterno__icontains=query) |
        Q(apellido_materno__icontains=query) |
        Q(email__icontains=query) |
        Q(cedula_identidad__icontains=query),
        eliminado=False
    )[:20]  # Limitar a 20 resultados

    serializer = UsuarioBasicoSerializer(usuarios, many=True)
    return Response(serializer.data)


# =============================================================================
# FIN DEL ARCHIVO
# =============================================================================
