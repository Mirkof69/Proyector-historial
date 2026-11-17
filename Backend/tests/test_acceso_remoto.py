"""Lo que queda expuesto cuando el sistema se publica por el túnel HTTPS.

Regresión (07/11/2026): al revisar la publicación por Cloudflare Tunnel se vio
que `/api/token/` entregaba un token completo con solo la contraseña a una cuenta
con MFA obligatorio, sin bloqueo de cuenta ni límite de intentos. Con él se
leyeron las 1.300 pacientes y la lista de respaldos. El túnel además confiaba en
cualquier dominio `*.trycloudflare.com`, que cualquiera puede crear gratis.
"""
import importlib.util
import re
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import get_resolver
from rest_framework.test import APIClient
from rest_framework_simplejwt.views import TokenObtainPairView

from monitoring.views import _check_redis
from usuarios.models import Usuario

RAIZ = Path(settings.BASE_DIR).parent
TOOLS = RAIZ / "tools_remoto"


def _vistas(patrones):
    for patron in patrones:
        if hasattr(patron, "url_patterns"):
            yield from _vistas(patron.url_patterns)
        else:
            yield patron.callback


class SoloElLoginEntregaSesionesTest(TestCase):
    """La única puerta de entrada es /api/usuarios/login/: MFA, bloqueo y límite."""

    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(
            email="med.remoto@hospital.bo", nombre="Rosa", apellido_paterno="Remoto",
            password="clave-segura-123", rol="medico")
        Usuario.objects.filter(pk=cls.medico.pk).update(mfa_obligatorio=True)

    def test_la_clave_sola_no_consigue_token_de_una_cuenta_con_mfa(self):
        cliente = APIClient()
        r = cliente.post("/api/token/", {"email": self.medico.email, "password": "clave-segura-123"}, format="json")
        self.assertNotIn("access", getattr(r, "data", None) or {})
        self.assertEqual(r.status_code, 404)

    def test_ninguna_ruta_usa_el_login_estandar_de_simplejwt(self):
        vistas = [getattr(v, "view_class", None) or getattr(v, "cls", None) for v in _vistas(get_resolver().url_patterns)]
        self.assertFalse([v for v in vistas if isinstance(v, type) and issubclass(v, TokenObtainPairView)])

    def test_el_login_normal_sigue_exigiendo_configurar_el_mfa(self):
        r = APIClient().post("/api/usuarios/login/", {"email": self.medico.email, "password": "clave-segura-123"},
                             format="json")
        self.assertEqual(r.status_code, 403)
        self.assertTrue(r.data["mfa_setup_required"])
        self.assertNotIn("access_token", r.cookies)


class SaludDeRedisTest(SimpleTestCase):
    """El `cache` de Django es un proxy: su clase nunca se llama «Redis»."""

    def _cache_que_responde(self):
        falso = mock.Mock()
        falso.get.return_value = "ok"
        return mock.patch("monitoring.views.cache", falso)

    @override_settings(CACHES={"default": {"BACKEND": "django_redis.cache.RedisCache", "LOCATION": "redis://x"}})
    def test_con_redis_dice_que_esta_sano(self):
        with self._cache_que_responde():
            self.assertEqual(_check_redis()["status"], "healthy")

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    def test_sin_redis_dice_que_usa_el_respaldo(self):
        with self._cache_que_responde():
            self.assertEqual(_check_redis()["status"], "degraded")


class PublicacionPorTunelTest(SimpleTestCase):
    """Lo que se confía o se expone al publicar: leído de los archivos reales."""

    def setUp(self):
        self.caddy = (TOOLS / "Caddyfile").read_text(encoding="utf-8")

    def test_settings_no_confia_en_dominios_que_cualquiera_puede_crear(self):
        self.assertNotIn("trycloudflare", (Path(settings.BASE_DIR) / "settings.py").read_text(encoding="utf-8"))

    def test_caddy_solo_escucha_en_este_equipo(self):
        self.assertIn("bind 127.0.0.1", self.caddy)

    def test_lo_administrativo_no_sale_a_internet(self):
        bloque = re.search(r"@privado\s+path\s+(.+)", self.caddy).group(1)
        for ruta in ("/admin", "/admin/*", "/api/schema*", "/api/docs*", "/api/redoc*"):
            self.assertIn(ruta, bloque)

    def test_la_ip_real_viene_de_cloudflare_y_no_del_cliente(self):
        self.assertIn("header_up X-Forwarded-For {http.request.header.Cf-Connecting-Ip}", self.caddy)

    def test_las_cookies_salen_marcadas_secure(self):
        self.assertRegex(self.caddy, r'header_down Set-Cookie .*Secure')

    def test_el_host_publico_llega_a_django(self):
        """Con otro Host el CSRF exigiría confiar en otro origen; solo el WebSocket usa localhost."""
        self.assertEqual(self.caddy.count("header_up Host"), 1)
        self.assertLess(self.caddy.index("handle /ws/*"), self.caddy.index("header_up Host"))

    def test_lo_privado_se_bloquea_antes_que_los_servicios(self):
        """Caddy ejecuta `respond` suelto después de los `handle`: no bloqueaba nada."""
        self.assertLess(self.caddy.index("handle @privado"), self.caddy.index("handle /api/*"))
        self.assertNotIn("respond @privado", self.caddy)

    def test_http_sin_cifrar_se_manda_a_https(self):
        self.assertRegex(self.caddy, r"@sin_cifrar header X-Forwarded-Proto http")
        self.assertIn("redir @sin_cifrar https://", self.caddy)

    def test_waitress_solo_confia_en_el_proxy_de_este_equipo(self):
        """Sin esto borra X-Forwarded-*: el CSRF fallaba y toda IP salía 127.0.0.1."""
        lanzador = (RAIZ / "INICIAR.bat").read_text(encoding="utf-8", errors="replace")
        self.assertIn('--trusted-proxy=127.0.0.1 --trusted-proxy-headers="x-forwarded-for x-forwarded-proto"', lanzador)


class ConfigurarRemotoTest(SimpleTestCase):
    """El .env solo gana el comodín de ALLOWED_HOSTS; nunca se reemplaza entero."""

    def setUp(self):
        spec = importlib.util.spec_from_file_location("configurar_remoto", TOOLS / "configurar_remoto.py")
        self.modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.modulo)
        self.dir = Path(settings.BASE_DIR) / "logs" / "_prueba_remoto"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.env = self.dir / ".env"
        self.addCleanup(lambda: (self.env.unlink(missing_ok=True), self.dir.rmdir()))
        self.modulo.ENV_FILE = self.env

    def _env(self, texto):
        self.env.write_text(texto, encoding="utf-8")

    def test_activar_agrega_el_host_y_quita_confianzas_viejas(self):
        self._env("# comentario\nSECRET_KEY=abc=def\nALLOWED_HOSTS=localhost\n"
                  "CSRF_TRUSTED_ORIGINS=http://localhost:3000,https://*.trycloudflare.com,https://a.trycloudflare.com\n"
                  "CORS_ALLOWED_ORIGINS=http://localhost:3000,https://a.trycloudflare.com\n")
        self.assertEqual(self.modulo.activar(), 0)
        texto = self.env.read_text(encoding="utf-8")
        self.assertIn("# comentario", texto)
        self.assertIn("SECRET_KEY=abc=def", texto)
        self.assertIn("ALLOWED_HOSTS=localhost,.trycloudflare.com", texto)
        self.assertIn("CSRF_TRUSTED_ORIGINS=http://localhost:3000\n", texto)
        self.assertIn("CORS_ALLOWED_ORIGINS=http://localhost:3000\n", texto)

    def test_activar_dos_veces_no_duplica(self):
        self._env("ALLOWED_HOSTS=localhost\n")
        self.modulo.activar()
        self.modulo.activar()
        self.assertEqual(self.env.read_text(encoding="utf-8").count(".trycloudflare.com"), 1)

    def test_desactivar_no_toca_el_env(self):
        self._env("SECRET_KEY=nueva\nALLOWED_HOSTS=localhost,.trycloudflare.com\n")
        with mock.patch.object(self.modulo, "_actualizar_dominios", return_value=0):
            self.assertEqual(self.modulo.desactivar(), 0)
        self.assertIn("SECRET_KEY=nueva", self.env.read_text(encoding="utf-8"))

    def test_solo_acepta_direcciones_de_tunel(self):
        with mock.patch.object(self.modulo, "_actualizar_dominios", return_value=0) as dominios:
            self.assertEqual(self.modulo.registrar_tunel("https://evil.com"), 1)
            self.assertEqual(self.modulo.registrar_tunel("https://x.trycloudflare.com');import os;#"), 1)
            dominios.assert_not_called()
            self.assertEqual(self.modulo.registrar_tunel("https://abc-def.trycloudflare.com"), 0)
            dominios.assert_called_once_with("abc-def.trycloudflare.com")
