from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from .models import Usuario

class LoginView(APIView):
    permission_classes = []
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        try:
            usuario = Usuario.objects.get(email=email, activo=True)
            if check_password(password, usuario.password_hash):
                refresh = RefreshToken.for_user(usuario)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {
                        'email': usuario.email,
                        'nombre': usuario.nombre,
                        'rol': usuario.rol
                    }
                })
        except Usuario.DoesNotExist:
            pass
        
        return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)