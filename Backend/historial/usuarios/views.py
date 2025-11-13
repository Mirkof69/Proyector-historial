from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Usuario
from .serializers import UsuarioSerializer, LoginSerializer, ChangePasswordSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestión de usuarios
    """
    queryset = Usuario.objects.filter(activo=True)
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar usuarios según rol"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Filtros opcionales
        rol = self.request.query_params.get('rol', None)
        if rol:
            queryset = queryset.filter(rol=rol)
        
        return queryset.order_by('-fecha_creacion')
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Obtener información del usuario actual"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cambiar_password(self, request, pk=None):
        """Cambiar contraseña de un usuario"""
        usuario = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            # Verificar contraseña actual
            if not usuario.check_password(serializer.validated_data['password_actual']):
                return Response(
                    {'error': 'Contraseña actual incorrecta'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Establecer nueva contraseña
            usuario.set_password(serializer.validated_data['password_nueva'])
            usuario.save()
            
            return Response({'mensaje': 'Contraseña actualizada correctamente'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def activar_desactivar(self, request, pk=None):
        """Activar o desactivar un usuario"""
        usuario = self.get_object()
        usuario.activo = not usuario.activo
        usuario.save()
        
        estado = "activado" if usuario.activo else "desactivado"
        return Response({'mensaje': f'Usuario {estado} correctamente'})


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Endpoint de login
    POST: email, password
    Retorna: access_token, refresh_token, user_data
    """
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    # Buscar usuario por email
    try:
        usuario = Usuario.objects.get(email=email, activo=True)
    except Usuario.DoesNotExist:
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Verificar contraseña
    if not usuario.check_password(password):
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generar tokens JWT
    refresh = RefreshToken.for_user(usuario)
    
    return Response({
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': {
            'id': usuario.id,
            'email': usuario.email,
            'nombre': usuario.nombre_completo,
            'rol': usuario.rol,
            'especialidad': usuario.especialidad,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Endpoint de logout
    POST: refresh_token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        return Response({'mensaje': 'Sesión cerrada correctamente'})
    except Exception as e:
        return Response(
            {'error': 'Token inválido'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    Endpoint para refrescar el access token
    POST: refresh_token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        
        return Response({
            'access_token': str(token.access_token)
        })
    except Exception as e:
        return Response(
            {'error': 'Token inválido o expirado'},
            status=status.HTTP_401_UNAUTHORIZED
        )