"""Tests de la migración de auth: JWT en cookies httpOnly + CSRF.

Cubre el contrato completo del flujo cookie-based:
1. Login setea cookies httpOnly y NO expone tokens en el body.
2. Refresh vía cookie rota los tokens y emite nuevas cookies.
3. Logout limpia las cookies y blacklistea el refresh.
4. Un POST autenticado por cookie SIN header X-CSRFToken es rechazado (403).
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from usuarios.models import Usuario


class CookieAuthFlowTest(APITestCase):
    """Flujo completo de autenticación por cookies httpOnly."""

    def setUp(self):
        """Setup"""
        self.client = APIClient()
        self.password = "cookiepass123"
        self.user = Usuario.objects.create_user(
            email="cookieuser@test.com",
            nombre="Cookie",
            apellido_paterno="User",
            password=self.password,
        )
        self.login_url = reverse("login")
        self.refresh_url = reverse("token_refresh")
        self.logout_url = reverse("logout")

    def _login(self, client=None):
        """Helper: login y devuelve la respuesta."""
        client = client or self.client
        return client.post(
            self.login_url,
            {"email": self.user.email, "password": self.password},
            format="json",
        )

    # ── 1. LOGIN ────────────────────────────────────────────────────────────
    def test_login_sets_httponly_cookies_and_no_tokens_in_body(self):
        """El login emite cookies httpOnly y el body no contiene JWT."""
        response = self._login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Tokens SOLO en cookies (nunca en el body → inaccesibles a XSS)
        self.assertNotIn("access_token", response.data)
        self.assertNotIn("refresh_token", response.data)
        self.assertIn("user", response.data)

        access_cookie = response.cookies.get("access_token")
        refresh_cookie = response.cookies.get("refresh_token")
        self.assertIsNotNone(access_cookie)
        self.assertIsNotNone(refresh_cookie)
        self.assertTrue(access_cookie["httponly"])
        self.assertTrue(refresh_cookie["httponly"])
        self.assertEqual(access_cookie["samesite"], "Lax")

        # La cookie csrftoken (double-submit) también se emite
        self.assertIn("csrftoken", response.cookies)

    # ── 2. REFRESH ──────────────────────────────────────────────────────────
    def test_refresh_with_cookie_rotates_tokens(self):
        """El refresh lee la cookie httpOnly y emite nuevas cookies."""
        login_response = self._login()
        old_access = login_response.cookies.get("access_token").value

        # POST sin body: el refresh token viaja en la cookie
        response = self.client.post(self.refresh_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # El body no expone JWT
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

        new_access = response.cookies.get("access_token")
        self.assertIsNotNone(new_access)
        self.assertTrue(new_access["httponly"])
        self.assertNotEqual(new_access.value, old_access)
        # Rotación de refresh activada → nueva cookie de refresh también
        self.assertIn("refresh_token", response.cookies)

    def test_refresh_without_cookie_is_rejected(self):
        """Sin cookie ni body, el refresh devuelve 401."""
        response = APIClient().post(self.refresh_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── 3. LOGOUT ───────────────────────────────────────────────────────────
    def test_logout_clears_cookies(self):
        """El logout limpia las cookies JWT y cierra la sesión."""
        self._login()

        response = self.client.post(self.logout_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Cookies eliminadas (max-age 0 / valor vacío)
        access_cookie = response.cookies.get("access_token")
        refresh_cookie = response.cookies.get("refresh_token")
        self.assertIsNotNone(access_cookie)
        self.assertIsNotNone(refresh_cookie)
        self.assertEqual(access_cookie.value, "")
        self.assertEqual(refresh_cookie.value, "")

        # El refresh blacklisteado ya no sirve para renovar la sesión
        refresh_response = self.client.post(self.refresh_url, {}, format="json")
        self.assertEqual(
            refresh_response.status_code, status.HTTP_401_UNAUTHORIZED,
        )

    # ── 4. CSRF ─────────────────────────────────────────────────────────────
    def test_csrf_rejected_on_cookie_authenticated_post_without_header(self):
        """POST autenticado por cookie SIN X-CSRFToken → 403 (CSRF Failed).

        La protección double-submit exige el header en métodos no-safe
        cuando la autenticación proviene de la cookie httpOnly.
        (enforce_csrf_checks=True: sin él, el test client de Django omite
        el chequeo CSRF marcando _dont_enforce_csrf_checks.)
        """
        csrf_client = APIClient(enforce_csrf_checks=True)
        self._login(client=csrf_client)

        # POST a un endpoint protegido sin header X-CSRFToken
        response = csrf_client.post(
            reverse("paciente-list"),
            {"nombre": "X"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        detail = str(response.data.get("detail", ""))
        self.assertIn("CSRF", detail)

    def test_get_with_cookie_does_not_require_csrf(self):
        """Los métodos safe (GET) autenticados por cookie no exigen CSRF."""
        self._login()
        response = self.client.get(reverse("paciente-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
