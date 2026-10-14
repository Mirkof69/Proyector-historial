"""MFA obligatorio en producción: que un médico nuevo pueda entrar, y que el
token temporal del MFA nunca valga como sesión.

Dos fallos reales encontrados el 02/10/2026 al probar el sistema en producción
(DEBUG=False):

1. Callejón sin salida. En producción el rol médico/administrador exige MFA.
   El login respondía 403 «configure MFA» SIN dar sesión, y /mfa/setup/ exige
   sesión: un médico recién creado no podía entrar nunca.
2. El temp_token del paso 2 del login es un access JWT firmado igual que uno
   real. Mandado como «Authorization: Bearer», entraba con solo la contraseña,
   sin el código TOTP.
"""
import pyotp
from rest_framework.test import APIClient, APITestCase

from auditoria.models import RegistroAuditoria
from usuarios.models import Usuario

CLAVE = "Clave-de-prueba-MFA-1!"


class MfaObligatorioPrimeraVezTest(APITestCase):
    def setUp(self):
        self.medica = Usuario.objects.create_user(
            email="dra.nueva@mfa.test", nombre="Rosa", apellido_paterno="Mamani",
            password=CLAVE, rol="medico",
        )
        # En los tests DEBUG es True y save() no lo marca: se fuerza como en producción.
        Usuario.objects.filter(pk=self.medica.pk).update(mfa_obligatorio=True)
        self.cliente = APIClient()

    def _login(self):
        return self.cliente.post("/api/usuarios/login/", {"email": self.medica.email, "password": CLAVE},
                                 format="json")

    def test_login_da_un_token_para_configurar(self):
        """ESPERADO: 403 con mfa_setup_required y temp_token, sin cookies de sesión."""
        r = self._login()
        assert r.status_code == 403
        assert r.data["mfa_setup_required"] is True
        assert r.data["temp_token"]
        assert "access_token" not in r.cookies

    def test_flujo_completo_activa_el_mfa_y_abre_la_sesion(self):
        """ESPERADO: QR → código correcto → 200, MFA activo, cookies, LOGIN y MFA_ACTIVADO auditados."""
        token = self._login().data["temp_token"]
        qr = self.cliente.post("/api/usuarios/mfa-setup-inicial/", {"temp_token": token}, format="json")
        assert qr.status_code == 200, qr.data
        assert qr.data["qr_code"].startswith("data:image/png;base64,")

        malo = self.cliente.post("/api/usuarios/mfa-confirmar-inicial/",
                                 {"temp_token": token, "code": "000000"}, format="json")
        assert malo.status_code == 400

        activados = RegistroAuditoria.objects.filter(accion="MFA_ACTIVADO").count()
        ok = self.cliente.post("/api/usuarios/mfa-confirmar-inicial/",
                               {"temp_token": token, "code": pyotp.TOTP(qr.data["secret"]).now()}, format="json")
        assert ok.status_code == 200, ok.data
        assert ok.data["user"]["email"] == self.medica.email
        assert "access_token" in ok.cookies
        self.medica.refresh_from_db()
        assert self.medica.mfa_enabled is True
        assert RegistroAuditoria.objects.filter(accion="MFA_ACTIVADO").count() == activados + 1

        # Con la sesión recién abierta ya puede usar el sistema.
        assert self.cliente.get("/api/usuarios/me/").status_code == 200

    def test_el_token_viejo_no_reemplaza_un_mfa_ya_activo(self):
        """ESPERADO: 400 — quien robe el token no puede cambiar el secreto después."""
        token = self._login().data["temp_token"]
        Usuario.objects.filter(pk=self.medica.pk).update(mfa_enabled=True, mfa_secret=pyotp.random_base32())
        r = self.cliente.post("/api/usuarios/mfa-setup-inicial/", {"temp_token": token}, format="json")
        assert r.status_code == 400

    def test_sin_token_o_con_otro_proposito_no_sirve(self):
        """ESPERADO: 401 — sin token, o con el del paso 2 del login (otro propósito)."""
        from usuarios.views import _build_temp_token

        assert self.cliente.post("/api/usuarios/mfa-setup-inicial/", {}, format="json").status_code == 401
        otro = _build_temp_token(self.medica, "mfa_pending")
        r = self.cliente.post("/api/usuarios/mfa-setup-inicial/", {"temp_token": otro}, format="json")
        assert r.status_code == 401


class TokenTemporalNoEsSesionTest(APITestCase):
    def setUp(self):
        self.medica = Usuario.objects.create_user(
            email="dra.mfa.activo@mfa.test", nombre="Ana", apellido_paterno="Quispe",
            password=CLAVE, rol="medico",
        )

    def _bearer(self, proposito):
        from usuarios.views import _build_temp_token

        cliente = APIClient()
        cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {_build_temp_token(self.medica, proposito)}")
        return cliente.get("/api/usuarios/me/")

    def test_token_del_paso_2_no_entra_sin_el_codigo(self):
        """ESPERADO: 401 — antes devolvía 200 y saltaba el TOTP."""
        assert self._bearer("mfa_pending").status_code == 401

    def test_token_de_configuracion_no_entra(self):
        """ESPERADO: 401 — solo sirve para generar el QR y activar el MFA."""
        assert self._bearer("mfa_setup_pending").status_code == 401


class RestablecerMfaTest(APITestCase):
    """Un médico que pierde el celular no puede quedar fuera para siempre."""

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            email="admin@mfa.test", nombre="Admin", apellido_paterno="Sistema",
            password=CLAVE, rol="administrador",
        )
        self.medica = Usuario.objects.create_user(
            email="dra.sin.celular@mfa.test", nombre="Lucía", apellido_paterno="Torrez",
            password=CLAVE, rol="medico",
        )
        Usuario.objects.filter(pk=self.medica.pk).update(
            mfa_obligatorio=True, mfa_enabled=True, mfa_secret=pyotp.random_base32())

    def test_el_administrador_lo_restablece_y_queda_auditado(self):
        """ESPERADO: 200, MFA y secreto borrados, MFA_RESTABLECIDO auditado, y al
        entrar se le pide configurarlo de nuevo."""
        self.client.force_authenticate(user=self.admin)
        antes = RegistroAuditoria.objects.filter(accion="MFA_RESTABLECIDO").count()
        r = self.client.post(f"/api/usuarios/{self.medica.pk}/restablecer-mfa/")
        assert r.status_code == 200, r.data
        self.medica.refresh_from_db()
        assert self.medica.mfa_enabled is False
        assert not self.medica.mfa_secret
        assert RegistroAuditoria.objects.filter(accion="MFA_RESTABLECIDO").count() == antes + 1

        login = APIClient().post("/api/usuarios/login/", {"email": self.medica.email, "password": CLAVE},
                                 format="json")
        assert login.status_code == 403
        assert login.data["mfa_setup_required"] is True

    def test_otro_medico_no_puede(self):
        """ESPERADO: 403 — quitar el segundo factor de otro es cosa del administrador."""
        otro = Usuario.objects.create_user(
            email="otro@mfa.test", nombre="Juan", apellido_paterno="Vargas", password=CLAVE, rol="medico",
        )
        self.client.force_authenticate(user=otro)
        r = self.client.post(f"/api/usuarios/{self.medica.pk}/restablecer-mfa/")
        assert r.status_code == 403
        self.medica.refresh_from_db()
        assert self.medica.mfa_enabled is True
