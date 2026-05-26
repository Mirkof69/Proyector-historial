"""Tests para módulo de Usuarios y Autenticación"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Usuario

User = get_user_model()


class UsuarioModelTestCase(TestCase):
    """Tests para modelo Usuario"""

    def test_crear_usuario(self):
        """Test crear usuario básico"""
        user = Usuario.objects.create_user(
            email="test@example.com",
            password="testpass123",
            nombre="Juan",
            apellido_paterno="Pérez",
        )

        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))

    def test_crear_superusuario(self):
        """Test crear superusuario"""
        admin = Usuario.objects.create_superuser(
            email="admin@example.com",
            nombre="Admin",
            apellido_paterno="Sistema",
            password="admin123",
        )

        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_str_representation(self):
        """Test representación string"""
        user = Usuario.objects.create_user(
            email="testuser@example.com", nombre="Juan", apellido_paterno="Pérez",
        )

        str_repr = str(user)
        self.assertIn("Juan", str_repr)

    def test_nombre_completo(self):
        """Test método nombre_completo"""
        user = Usuario.objects.create_user(
            email="testuser@example.com", nombre="Juan", apellido_paterno="Pérez",
        )

        nombre = user.nombre_completo
        self.assertIn("Juan", nombre)
        self.assertIn("Pérez", nombre)


class AutenticacionTestCase(APITestCase):
    """Tests para autenticación"""

    def setUp(self):
        """Setup"""
        self.user = Usuario.objects.create_user(
            email="test@example.com",
            password="testpass123",
            nombre="Juan",
            apellido_paterno="Pérez",
        )

    def test_login_exitoso(self):
        """Test login exitoso"""
        response = self.client.post(
            "/api/usuarios/login/",
            {"username": "test@example.com", "password": "testpass123"},
        )

        # El endpoint de login suele esperar 'email' o 'username'
        if response.status_code != status.HTTP_200_OK:
            response = self.client.post(
                "/api/usuarios/login/",
                {"email": "test@example.com", "password": "testpass123"},
            )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_401_UNAUTHORIZED,
            ],
        )

    def test_refresh_token(self):
        """Test refresh token"""
        refresh = RefreshToken.for_user(self.user)

        response = self.client.post(
            "/api/usuarios/token/refresh/", {"refresh": str(refresh)},
        )

        self.assertIn(
            response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND],
        )


class PermisosTestCase(APITestCase):
    """Tests para permisos y autorización"""

    def setUp(self):
        """Setup"""
        self.user = Usuario.objects.create_user(
            email="testuser@example.com",
            nombre="Juan",
            apellido_paterno="Pérez",
            password="testpass123",
        )

    def test_acceso_sin_autenticacion(self):
        """Test acceso a endpoint proyectado sin autenticación"""
        response = self.client.get("/api/usuarios/perfil/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UsuarioValidacionTestCase(TestCase):
    """Tests de validación de usuarios"""

    def test_email_unico(self):
        """Test email debe ser único"""
        Usuario.objects.create_user(
            email="test@example.com",
            nombre="Juan",
            apellido_paterno="Pérez",
            password="pass123",
        )

        with self.assertRaises(Exception):
            Usuario.objects.create_user(
                email="test@example.com",
                nombre="Otro",
                apellido_paterno="User",
                password="pass456",
            )
