"""Tests del límite de intentos de login por IP.

Por qué existe este archivo
---------------------------
El bloqueo de cuenta (5 intentos → 15 min) ya existía y funciona, pero por sí
solo permite un ataque de disponibilidad: sin límite por IP, un atacante puede
recorrer la lista de usuarios y bloquear a TODO el personal del hospital. En
una emergencia obstétrica eso deja al equipo médico fuera del sistema.

La tasa real está desactivada en la suite (`DEFAULT_THROTTLE_RATES` usa un
valor enorme cuando `TESTING`) para no volver frágiles los demás tests. Eso
dejaría la protección sin verificar, así que aquí se fija a propósito.

Nota sobre cómo se fija la tasa
-------------------------------
Se parchea el atributo `rate` de la clase en vez de usar
`override_settings(REST_FRAMEWORK=...)`. DRF resuelve `THROTTLE_RATES` cuando
se importa la clase del throttle, así que el override no revierte de forma
fiable y estos tests pasaban o fallaban según el orden de ejecución.
`SimpleRateThrottle.__init__` respeta un `rate` ya definido, de modo que
parchearlo es exacto y determinista.
"""

from unittest.mock import patch

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from core.throttling import LoginRateThrottle
from usuarios.models import Usuario


def tasa(valor):
    """Fija la tasa del throttle de login mientras dure el bloque `with`."""
    # `create=True` porque la clase no declara `rate`: lo resuelve en
    # `__init__` a partir de `THROTTLE_RATES`. Definirlo hace que lo use tal cual.
    return patch.object(LoginRateThrottle, "rate", valor, create=True)


class LimiteDeLoginPorIPTest(APITestCase):
    """El login debe cortar por IP antes de que el atacante bloquee cuentas."""

    def setUp(self):
        """Usuario real y contador de throttling limpio.

        El contador vive en la caché y es global al proceso: sin limpiarlo, el
        resultado dependería del orden en que corren los tests.
        """
        cache.clear()
        self.usuario = Usuario.objects.create_user(
            email="medica@limite.test",
            nombre="Ana",
            apellido_paterno="Quispe",
            password="ClaveCorrecta123!",
        )
        self.url = "/api/usuarios/login/"

    def tearDown(self):
        """No dejar el contador sucio para el resto de la suite."""
        cache.clear()

    def _intento(self, password):
        return self.client.post(
            self.url,
            {"email": self.usuario.email, "password": password},
            format="json",
        )

    def test_corta_con_429_al_pasar_el_limite(self):
        """Superado el límite, la respuesta es 429 y no otro intento fallido.

        Importa que sea 429 y no 401: un 401 seguiría incrementando el contador
        de intentos fallidos de la cuenta, que es justo el ataque a evitar.
        """
        with tasa("3/min"):
            for _ in range(3):
                self._intento("claveIncorrecta")
            respuesta = self._intento("claveIncorrecta")

        assert respuesta.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_el_limite_protege_a_la_cuenta_de_quedar_bloqueada(self):
        """El corte por IP debe llegar ANTES del bloqueo de cuenta.

        Es el punto de todo el cambio: con 3 intentos por IP y 5 para bloquear,
        el atacante nunca alcanza a bloquear la cuenta de la médica.
        """
        with tasa("3/min"):
            for _ in range(10):
                self._intento("claveIncorrecta")

        self.usuario.refresh_from_db()
        assert self.usuario.bloqueado_hasta is None, (
            "La cuenta se bloqueó pese al límite por IP: el atacante todavía "
            "puede dejar sin acceso al personal."
        )

    def test_con_tasa_amplia_el_login_normal_no_se_corta(self):
        """El uso legítimo no debe encontrarse nunca un 429.

        Con la tasa de producción (20/min) una recepcionista que tipea rápido
        no debe verse afectada.
        """
        with tasa("20/min"):
            for _ in range(8):
                respuesta = self._intento("ClaveCorrecta123!")
                assert respuesta.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    def test_el_bloqueo_de_cuenta_sigue_funcionando(self):
        """El límite por IP no debe haber anulado la protección que ya existía.

        Con la tasa amplia, los 5 intentos fallidos deben seguir bloqueando la
        cuenta: las dos defensas son complementarias, no alternativas.
        """
        with tasa("1000/min"):
            for _ in range(5):
                self._intento("claveIncorrecta")

        self.usuario.refresh_from_db()
        assert self.usuario.bloqueado_hasta is not None, (
            "El bloqueo de cuenta dejó de funcionar al agregar el límite por IP."
        )
