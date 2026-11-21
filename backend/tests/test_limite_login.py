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

    def test_cien_logins_CORRECTOS_desde_una_IP_entran_todos(self):
        """ESPERADO: 100 de 100 entran. Ningún 429.

        Es el caso que reventó en la prueba de carga real y el motivo de que
        el límite cuente solo los fallos. En una clínica todo el personal sale
        por una sola IP: para Django, el cambio de turno son cien peticiones
        desde la misma dirección. Contando todos los intentos, entraban veinte
        y ochenta recibían 429 sin haber hecho nada malo.

        Se usa una tasa DELIBERADAMENTE pequeña —tres— para que, si alguien
        vuelve a contar los aciertos, este test falle con total seguridad y no
        por poco.
        """
        with tasa("3/min"):
            codigos = [self._intento("ClaveCorrecta123!").status_code for _ in range(100)]

        cortados = codigos.count(status.HTTP_429_TOO_MANY_REQUESTS)
        assert cortados == 0, (
            f"{cortados} de 100 inicios de sesión CORRECTOS recibieron 429. "
            f"El límite está contando los aciertos: en una clínica detrás de "
            f"una sola IP eso deja al turno entero fuera del sistema."
        )

    def test_los_fallos_siguen_gastando_cupo_aunque_haya_aciertos_de_por_medio(self):
        """ESPERADO: 429 al cuarto fallo, aunque entre medias haya logins buenos.

        Es la otra mitad del contrato. Si los aciertos "limpiaran" el contador,
        el atacante evadiría el límite intercalando un login válido cualquiera
        entre sus intentos.
        """
        with tasa("3/min"):
            for _ in range(3):
                self._intento("claveIncorrecta")
                self._intento("ClaveCorrecta123!")  # no debe reponer cupo
            respuesta = self._intento("claveIncorrecta")

        assert respuesta.status_code == status.HTTP_429_TOO_MANY_REQUESTS, (
            "Un login correcto entre fallos repuso el cupo: el límite por IP "
            "se puede evadir intercalando credenciales válidas."
        )

    def test_probar_emails_que_no_existen_tambien_gasta_cupo(self):
        """ESPERADO: 429 al cuarto intento contra emails inventados.

        Recorrer una lista de correos para ver cuáles existen es el paso previo
        del ataque. Si esa ruta no gastara cupo, el límite se saltaría sin más
        que usar emails no registrados.
        """
        with tasa("3/min"):
            for _ in range(3):
                self.client.post(
                    self.url,
                    {"email": "noexiste@ninguna.test", "password": "loquesea"},
                    format="json",
                )
            respuesta = self.client.post(
                self.url,
                {"email": "tampoco@ninguna.test", "password": "loquesea"},
                format="json",
            )

        assert respuesta.status_code == status.HTTP_429_TOO_MANY_REQUESTS

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

    def test_el_quinto_intento_avisa_del_bloqueo_temporal(self):
        """BUG-002: la pantalla mostraba «Acceso denegado. Contacte al
        administrador.» y el 5.º intento decía «credenciales incorrectas»."""
        with tasa("1000/min"):
            for _ in range(4):
                assert self._intento("claveIncorrecta").status_code == status.HTTP_401_UNAUTHORIZED
            quinto = self._intento("claveIncorrecta")
            con_la_buena = self._intento("ClaveCorrecta123!")

        for respuesta in (quinto, con_la_buena):
            assert respuesta.status_code == status.HTTP_423_LOCKED
            assert respuesta.data["codigo"] == "cuenta_bloqueada"
            assert "bloqueada temporalmente" in respuesta.data["error"]
            assert respuesta.data["minutos_restantes"] == 15
