"""Tests de las acciones de auditoría que faltaban por emitir.

Por qué existe este archivo
---------------------------
`RegistroAuditoria.ACCIONES` declara 22 acciones. Medido contra la base real,
solo se emitían seis. Las demás estaban declaradas y no salían nunca, así que
la auditoría respondía "quién creó" y "quién editó", pero no:

  - quién EXPORTÓ datos de pacientes a Excel o PDF (20 endpoints)
  - quién DESACTIVÓ o volvió a ACTIVAR una paciente o un usuario
  - quién CAMBIÓ EL ROL de alguien (es una escalada de privilegios)
  - quién activó o desactivó su MFA, y quién falló al verificarlo
  - quién lanzó un BACKUP de la base

Para un hospital, la exportación y el cambio de rol son justo los dos hechos
que hay que poder reconstruir: uno saca datos clínicos del sistema y el otro
da acceso a los de otros.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import datetime

from rest_framework.test import APIClient, APITestCase

from auditoria.acceso import accion_para_ruta
from auditoria.models import RegistroAuditoria
from pacientes.models import Paciente
from usuarios.models import Usuario


class AccionSegunLaRutaTest(APITestCase):
    """Una descarga no es lo mismo que una consulta, y debe distinguirse."""

    def test_una_exportacion_se_registra_como_EXPORTAR(self):
        """ESPERADO: 'EXPORTAR' — sacar datos del sistema no es solo mirarlos."""
        for ruta in (
            "/api/pacientes/exportar-excel/",
            "/api/pacientes/14/exportar-pdf/",
            "/api/ecografias/7/exportar-csv/",
            "/api/pacientes/14/historia-clinica/",
        ):
            assert accion_para_ruta(ruta) == "EXPORTAR", (
                f"{ruta} deberia registrarse como EXPORTAR, no como VER."
            )

    def test_una_consulta_normal_sigue_siendo_VER(self):
        """ESPERADO: 'VER' — abrir una ficha no saca nada del sistema."""
        for ruta in ("/api/pacientes/", "/api/pacientes/14/", "/api/embarazos/3/"):
            assert accion_para_ruta(ruta) == "VER"


class _Base(APITestCase):
    """Una administradora y una paciente, que es lo que casi todo test necesita."""

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            email="admin@auditoria.test",
            nombre="Ana",
            apellido_paterno="Poma",
            password="clave-de-prueba-123",
            rol="administrador",
            is_staff=True,
        )
        self.paciente = Paciente.objects.create(
            nombre="Rosa",
            apellido_paterno="Mamani",
            apellido_materno="Choque",
            fecha_nacimiento=datetime.date(1992, 3, 3),
            genero="femenino",
            ci="4433221",
        )
        self.client.force_authenticate(user=self.admin)

    def _registros(self, accion):
        return RegistroAuditoria.objects.filter(accion=accion)


class DesactivarYActivarTest(_Base):
    """Sacar de circulación una historia clínica tiene que quedar registrado."""

    def test_desactivar_una_paciente_deja_DESACTIVAR(self):
        """ESPERADO: 1 registro nuevo con quién lo hizo."""
        antes = self._registros("DESACTIVAR").count()

        respuesta = self.client.delete(f"/api/pacientes/{self.paciente.id}/")
        assert respuesta.status_code in (200, 204), respuesta.data

        registros = self._registros("DESACTIVAR")
        assert registros.count() == antes + 1
        r = registros.order_by("-id").first()
        assert r.usuario_id == self.admin.id
        assert r.registro_id == str(self.paciente.id)

    def test_reactivar_una_paciente_deja_ACTIVAR(self):
        """ESPERADO: 1 registro ACTIVAR.

        Reactivar es tan sensible como desactivar: devuelve a circulación una
        historia que alguien había retirado.
        """
        self.paciente.activo = False
        self.paciente.save(update_fields=["activo"])
        antes = self._registros("ACTIVAR").count()

        self.client.post(f"/api/pacientes/{self.paciente.id}/activar/")

        assert self._registros("ACTIVAR").count() == antes + 1


class CambioDeRolTest(_Base):
    """Cambiar el rol de alguien es dar o quitar acceso a datos clínicos."""

    def test_cambiar_el_rol_deja_CAMBIO_ROL(self):
        """ESPERADO: 1 registro que diga el rol anterior y el nuevo."""
        otra = Usuario.objects.create_user(
            email="enf@auditoria.test",
            nombre="Luz",
            apellido_paterno="Cusi",
            password="clave-de-prueba-123",
            rol="enfermera",
        )
        antes = self._registros("CAMBIO_ROL").count()

        respuesta = self.client.patch(
            f"/api/usuarios/{otra.id}/", {"rol": "medico"}, format="json",
        )
        assert respuesta.status_code == 200, respuesta.data

        registros = self._registros("CAMBIO_ROL")
        assert registros.count() == antes + 1
        detalle = registros.order_by("-id").first().detalle
        assert "enfermera" in detalle and "medico" in detalle, (
            f"El detalle deberia decir de que rol a cual: {detalle!r}"
        )

    def test_editar_otro_campo_no_deja_CAMBIO_ROL(self):
        """ESPERADO: 0 nuevos — solo el cambio de rol es escalada de acceso."""
        otra = Usuario.objects.create_user(
            email="enf2@auditoria.test",
            nombre="Luz",
            apellido_paterno="Cusi",
            password="clave-de-prueba-123",
            rol="enfermera",
        )
        antes = self._registros("CAMBIO_ROL").count()

        self.client.patch(f"/api/usuarios/{otra.id}/", {"nombre": "Luzmila"}, format="json")

        assert self._registros("CAMBIO_ROL").count() == antes


class MfaAuditadoTest(APITestCase):
    """Activar o quitar el segundo factor cambia la seguridad de la cuenta."""

    def setUp(self):
        self.medica = Usuario.objects.create_user(
            email="dra.mfa@auditoria.test",
            nombre="Elena",
            apellido_paterno="Choque",
            password="clave-de-prueba-123",
            rol="medico",
        )
        self.client.force_authenticate(user=self.medica)

    def test_desactivar_mfa_deja_MFA_DESACTIVADO(self):
        """ESPERADO: 1 registro — quitarse el MFA baja la seguridad.

        Se envía un código TOTP válido porque el endpoint lo exige: desactivar
        el segundo factor sin demostrar que se tiene sería una puerta abierta.
        """
        import pyotp

        secreto = pyotp.random_base32()
        self.medica.mfa_secret = secreto
        self.medica.mfa_enabled = True
        self.medica.save(update_fields=["mfa_secret", "mfa_enabled"])
        antes = RegistroAuditoria.objects.filter(accion="MFA_DESACTIVADO").count()

        respuesta = self.client.post(
            "/api/usuarios/mfa/disable/",
            {"code": pyotp.TOTP(secreto).now()},
            format="json",
        )
        assert respuesta.status_code == 200, respuesta.data

        assert RegistroAuditoria.objects.filter(accion="MFA_DESACTIVADO").count() == antes + 1

    def test_sin_codigo_valido_no_se_desactiva_ni_se_audita(self):
        """ESPERADO: 400 y 0 registros — no basta con pedirlo."""
        import pyotp

        self.medica.mfa_secret = pyotp.random_base32()
        self.medica.mfa_enabled = True
        self.medica.save(update_fields=["mfa_secret", "mfa_enabled"])
        antes = RegistroAuditoria.objects.filter(accion="MFA_DESACTIVADO").count()

        respuesta = self.client.post(
            "/api/usuarios/mfa/disable/", {"code": "000000"}, format="json",
        )

        assert respuesta.status_code == 400
        self.medica.refresh_from_db()
        assert self.medica.mfa_enabled is True
        assert RegistroAuditoria.objects.filter(accion="MFA_DESACTIVADO").count() == antes


class CuentaBloqueadaTest(APITestCase):
    """El bloqueo por intentos fallidos es un evento de seguridad."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="bloqueo@auditoria.test",
            nombre="Ana",
            apellido_paterno="Flores",
            password="ClaveCorrecta123!",
            rol="medico",
        )

    def test_al_bloquearse_queda_CUENTA_BLOQUEADA(self):
        """ESPERADO: 1 registro al llegar al quinto intento fallido.

        Sin esto, en la auditoría solo se ven cinco LOGIN_FALLIDO sueltos y no
        el hecho de que la cuenta quedó fuera de servicio 15 minutos.
        """
        cliente = APIClient()
        antes = RegistroAuditoria.objects.filter(accion="CUENTA_BLOQUEADA").count()

        for _ in range(5):
            cliente.post(
                "/api/usuarios/login/",
                {"email": self.usuario.email, "password": "mala"},
                format="json",
            )

        self.usuario.refresh_from_db()
        assert self.usuario.bloqueado_hasta is not None, "La cuenta no se bloqueó."
        assert RegistroAuditoria.objects.filter(accion="CUENTA_BLOQUEADA").count() == antes + 1


class MfaActivadoTest(APITestCase):
    """Activar el segundo factor también se registra."""

    def setUp(self):
        self.medica = Usuario.objects.create_user(
            email="dra.mfaon@auditoria.test",
            nombre="Rosa",
            apellido_paterno="Yujra",
            password="clave-de-prueba-123",
            rol="medico",
        )
        self.client.force_authenticate(user=self.medica)

    def test_activar_mfa_deja_MFA_ACTIVADO(self):
        """ESPERADO: 1 registro.

        Sin la contrapartida de MFA_DESACTIVADO, la auditoría mostraría bajas
        de seguridad sin sus altas y no se podría reconstruir el estado en que
        quedó una cuenta.
        """
        import pyotp

        secreto = pyotp.random_base32()
        self.medica.mfa_secret = secreto
        self.medica.save(update_fields=["mfa_secret"])
        antes = RegistroAuditoria.objects.filter(accion="MFA_ACTIVADO").count()

        respuesta = self.client.post(
            "/api/usuarios/mfa/confirm/",
            {"code": pyotp.TOTP(secreto).now()},
            format="json",
        )
        assert respuesta.status_code == 200, respuesta.data

        assert RegistroAuditoria.objects.filter(accion="MFA_ACTIVADO").count() == antes + 1


class TodasLasAccionesSeEmitenTest(APITestCase):
    """Ninguna acción puede quedar declarada y sin emitirse nunca.

    Es la trampa que motivó todo esto: `VER`, `EXPORTAR`, `CAMBIO_ROL` y ocho
    más estaban en `ACCIONES` desde el principio y no salían jamás. Quien
    mirara la lista creería que el sistema las registra.
    """

    #: Se emiten desde los signals genéricos de Django, no con `accion="..."`.
    POR_SIGNALS = {"crear", "actualizar", "eliminar", "CREAR", "EDITAR", "DESACTIVAR"}
    #: Se emiten con una variable, no con un literal (ver auditoria/acceso.py).
    POR_VARIABLE = {"VER", "EXPORTAR"}

    def test_cada_accion_declarada_se_emite_en_algun_sitio(self):
        """ESPERADO: lista vacía de acciones huérfanas."""
        import pathlib
        import re

        raiz = pathlib.Path(__file__).resolve().parent.parent
        codigo = ""
        for archivo in raiz.rglob("*.py"):
            if any(x in archivo.parts for x in (".venv", "node_modules", "tests", "__pycache__")):
                continue
            codigo += archivo.read_text(encoding="utf-8", errors="replace")

        emitidas = set(re.findall(r"accion=[\"']([A-Za-z_]+)[\"']", codigo))
        emitidas |= self.POR_SIGNALS | self.POR_VARIABLE

        declaradas = {a for a, _ in RegistroAuditoria.ACCIONES}
        huerfanas = sorted(declaradas - emitidas)

        assert huerfanas == [], (
            f"Declaradas en ACCIONES pero que no se emiten en ningún sitio: "
            f"{huerfanas}. O se cablean, o se quitan de la lista."
        )
