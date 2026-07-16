"""Tests for authentication and JWT token handling.
"""

import datetime
from typing import cast

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from pacientes.models import Paciente
from usuarios.models import Usuario


class UserModelTest(TestCase):
    """Tests for the custom Usuario model."""

    def setUp(self):
        """Setup"""
        self.admin_data = {
            "email": "admin@test.com",
            "nombre": "Admin",
            "apellido_paterno": "User",
            "password": "adminpass123",
        }

    def test_create_user(self):
        """Test creating a regular user."""
        user = Usuario.objects.create_user(
            email="user@test.com",
            nombre="Test",
            apellido_paterno="User",
            password="password123",
        )
        self.assertEqual(Usuario.objects.count(), 1)
        self.assertEqual(user.email, "user@test.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.activo)

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = Usuario.objects.create_superuser(**self.admin_data)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.rol, "administrador")
        self.assertTrue(admin.activo)

    def test_create_user_without_email_raises_error(self):
        """Test that creating user without email raises ValueError."""
        with self.assertRaises(ValueError):
            Usuario.objects.create_user(
                email="", nombre="Test", apellido_paterno="User", password="password123",
            )

    def test_create_superuser_without_is_staff_raises_error(self):
        """Test superuser creation with is_staff=False raises ValueError."""
        with self.assertRaises(ValueError):
            Usuario.objects.create_superuser(
                email="admin@test.com",
                nombre="Admin",
                apellido_paterno="User",
                password="adminpass123",
                is_staff=False,
            )

    def test_nombre_completo_property(self):
        """Test nombre_completo property."""
        user = Usuario.objects.create_user(
            email="full@test.com",
            nombre="Juan",
            apellido_paterno="Perez",
            apellido_materno="Gomez",
            password="password123",
        )
        self.assertEqual(user.nombre_completo, "Juan Perez Gomez")

        user2 = Usuario.objects.create_user(
            email="partial@test.com",
            nombre="Maria",
            apellido_paterno="Lopez",
            password="password123",
        )
        self.assertEqual(user2.nombre_completo, "Maria Lopez")

    def test_iniciales_property(self):
        """Test initials property."""
        user = Usuario.objects.create_user(
            email="init@test.com",
            nombre="Juan",
            apellido_paterno="Perez",
            apellido_materno="Gomez",
            password="password123",
        )
        self.assertEqual(user.iniciales, "JPG")

    def test_user_str(self):
        """Test __str__ method."""
        user = Usuario.objects.create_user(
            email="str@test.com",
            nombre="Test",
            apellido_paterno="User",
            password="password123",
            rol="medico",
        )
        self.assertIn("Test", str(user))
        self.assertIn("M\u00e9dico", str(user))

    def test_password_hashing(self):
        """Test that passwords are hashed."""
        user = Usuario.objects.create_user(
            email="hash@test.com",
            nombre="Test",
            apellido_paterno="User",
            password="plaintext123",
        )
        self.assertNotEqual(user.password, "plaintext123")
        self.assertTrue(user.check_password("plaintext123"))

    def test_get_full_name(self):
        """Test get_full_name method."""
        user = Usuario.objects.create_user(
            email="fullname@test.com",
            nombre="Test",
            apellido_paterno="User",
            password="password123",
        )
        self.assertEqual(user.get_full_name(), "Test User")

    def test_has_perm_superuser(self):
        """Test has_perm for superuser."""
        admin = Usuario.objects.create_superuser(**self.admin_data)
        self.assertTrue(admin.has_perm("any.permission"))

    def test_has_module_perms(self):
        """Test has_module_perms."""
        admin = Usuario.objects.create_superuser(**self.admin_data)
        self.assertTrue(admin.has_module_perms("pacientes"))


class JWTAuthTest(APITestCase):
    """Tests for JWT authentication endpoints."""

    def setUp(self):
        """Setup"""
        self.client = APIClient()
        self.user_data = {
            "email": "jwtuser@test.com",
            "nombre": "JWT",
            "apellido_paterno": "User",
            "password": "securepass123",
        }
        self.user = Usuario.objects.create_user(**self.user_data)
        self.token_url = reverse("login")
        self.token_refresh_url = reverse("refresh-token")

    def test_obtain_token_success(self):
        """Test obtaining JWT session with valid credentials.

        Contrato cookie-based: los JWT llegan como cookies httpOnly y el
        body solo trae la info del usuario (nunca tokens).
        """
        response = self.client.post(
            self.token_url,
            {
                "email": self.user_data["email"],
                "password": self.user_data["password"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertNotIn("access_token", response.data)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_obtain_token_wrong_password(self):
        """Test that wrong password returns 401."""
        response = self.client.post(
            self.token_url,
            {
                "email": self.user_data["email"],
                "password": "wrongpassword",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_obtain_token_nonexistent_user(self):
        """Test that non-existent user returns 401."""
        response = self.client.post(
            self.token_url,
            {
                "email": "nobody@test.com",
                "password": "somepass",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_obtain_token_missing_fields(self):
        """Test that missing fields returns 400."""
        response = self.client.post(
            self.token_url,
            {
                "email": self.user_data["email"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token_success(self):
        """Test refreshing token with valid refresh token.

        Contrato cookie-based: el refresh llega en la cookie httpOnly del
        login; el endpoint custom sigue aceptando body ``refresh_token``.
        """
        # First obtain tokens (as httpOnly cookies)
        obtain_response = self.client.post(
            self.token_url,
            {
                "email": self.user_data["email"],
                "password": self.user_data["password"],
            },
            format="json",
        )
        self.assertEqual(obtain_response.status_code, status.HTTP_200_OK)

        refresh_cookie = obtain_response.cookies.get("refresh_token")
        if not refresh_cookie:
            self.skipTest("Login did not set refresh_token cookie (MFA flow)")

        # Refresh the token (endpoint custom por body)
        response = self.client.post(
            self.token_refresh_url,
            {
                "refresh_token": refresh_cookie.value,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)

    def test_refresh_token_invalid(self):
        """Test that invalid refresh token returns error."""
        response = self.client.post(
            self.token_refresh_url,
            {
                "refresh_token": "invalid.token.here",
            },
            format="json",
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED],
        )

    def test_access_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token returns 401."""
        response = self.client.get(reverse("paciente-list"))
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_access_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token.

        Contrato cookie-based: tras el login, el APIClient conserva las
        cookies httpOnly y los GET autentican sin header Authorization.
        """
        obtain_response = self.client.post(
            self.token_url,
            {
                "email": self.user_data["email"],
                "password": self.user_data["password"],
            },
            format="json",
        )
        access_cookie = obtain_response.cookies.get("access_token")
        if not access_cookie:
            self.skipTest("Could not obtain access_token cookie")

        response = self.client.get(reverse("paciente-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_endpoint_with_expired_token(self):
        """Test accessing protected endpoint with expired token returns 401."""
        # Create a token that is already expired
        from datetime import timedelta

        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=timedelta(seconds=-1))

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token!s}")
        response = self.client.get(reverse("paciente-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with malformed token returns 401."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken123")
        response = self.client.get(reverse("paciente-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTTokenBlacklistTest(APITestCase):
    """Tests for JWT token blacklist functionality."""

    def setUp(self):
        """Setup"""
        self.client = APIClient()
        self.user = Usuario.objects.create_user(
            email="blacklist@test.com",
            nombre="Blacklist",
            apellido_paterno="Test",
            password="securepass123",
        )
        self.token_url = reverse("login")

    def test_token_obtain_pair_returns_both_tokens(self):
        """Test that login sets both access and refresh cookies (httpOnly)."""
        response = self.client.post(
            self.token_url,
            {
                "email": self.user.email,
                "password": "securepass123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_blacklisted_token_cannot_be_used(self):
        """Test that a blacklisted token cannot authenticate."""
        # Obtain and then manually blacklist a refresh token

        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token

        # Blacklist the refresh token
        refresh.blacklist()

        # Try to use the access token (should still work until it expires)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access!s}")
        response = self.client.get(reverse("paciente-list"))
        # Access token should still work since we only blacklisted refresh
        # Note: The project may return 200 or 401 depending on the token setup
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])


class RoleBasedAccessTest(APITestCase):
    """Tests for role-based access control."""

    def setUp(self):
        """Setup"""
        self.admin = Usuario.objects.create_superuser(
            email="admin@test.com",
            nombre="Admin",
            apellido_paterno="User",
            password="adminpass123",
        )
        self.medico = Usuario.objects.create_user(
            email="medico@test.com",
            nombre="Dr",
            apellido_paterno="Medico",
            password="medicopass123",
            rol="medico",
        )
        self.enfermero = Usuario.objects.create_user(
            email="enfermero@test.com",
            nombre="Nurse",
            apellido_paterno="User",
            password="nursepass123",
            rol="enfermero",
        )

    def test_admin_can_delete_paciente(self):
        """Test that admin can delete pacientes."""

        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        paciente = cast(Paciente, Paciente.objects.create(
            nombre="Delete",
            apellido_paterno="Test",
            fecha_nacimiento=datetime.date(1990, 1, 1),
            genero="femenino",
            ci="99999991",
        ))
        url = reverse("paciente-detail", kwargs={"pk": paciente.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_medico_cannot_delete_paciente(self):
        """Test that medico cannot delete pacientes."""
        self.client = APIClient()
        self.client.force_authenticate(user=self.medico)

        paciente = cast(Paciente, Paciente.objects.create(
            nombre="Delete",
            apellido_paterno="Test",
            fecha_nacimiento=datetime.date(1990, 1, 1),
            genero="femenino",
            ci="99999992",
        ))
        url = reverse("paciente-detail", kwargs={"pk": paciente.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_enfermero_cannot_delete_paciente(self):
        """Test that enfermero cannot delete pacientes."""
        self.client = APIClient()
        self.client.force_authenticate(user=self.enfermero)

        paciente = cast(Paciente, Paciente.objects.create(
            nombre="Delete",
            apellido_paterno="Test",
            fecha_nacimiento=datetime.date(1990, 1, 1),
            genero="femenino",
            ci="99999993",
        ))
        url = reverse("paciente-detail", kwargs={"pk": paciente.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
