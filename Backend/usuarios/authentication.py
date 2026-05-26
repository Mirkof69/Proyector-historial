"""Authentication module."""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from .models import Usuario


class CustomJWTAuthentication(JWTAuthentication):
    """Customjwtauthentication"""
    def get_user(self, validated_token):
        """Get user"""
        try:
            user_id = validated_token.get("user_id")
            user = Usuario.objects.get(id=user_id, activo=True)
            return user
        except Usuario.DoesNotExist as exc:
            raise InvalidToken("Usuario no encontrado") from exc
