"""Tests para la autenticación JWT de los WebSockets.

La seguridad del canal depende de get_user_from_token: un token inválido o
ausente NUNCA debe autenticar a un usuario.
"""
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from .middleware import get_user_from_token

Usuario = get_user_model()


class WebSocketAuthTest(TestCase):
    def test_token_invalido_devuelve_anonimo(self):
        user = async_to_sync(get_user_from_token)("token-basura-invalido")
        self.assertTrue(user.is_anonymous)

    def test_token_vacio_devuelve_anonimo(self):
        user = async_to_sync(get_user_from_token)("")
        self.assertIsInstance(user, AnonymousUser)

    def test_token_valido_devuelve_usuario(self):
        from rest_framework_simplejwt.tokens import AccessToken
        u = Usuario.objects.create_user(
            email="ws@test.bo", nombre="Ws", apellido_paterno="User", password="x",
        )
        token = str(AccessToken.for_user(u))
        user = async_to_sync(get_user_from_token)(token)
        self.assertFalse(user.is_anonymous)
        self.assertEqual(user.pk, u.pk)
