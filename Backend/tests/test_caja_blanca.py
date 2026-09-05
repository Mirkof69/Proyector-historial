"""Pruebas de CAJA BLANCA.

Qué significa aquí
------------------
Se prueba **conociendo el código**. Cada test está escrito mirando una función
concreta y eligiendo entradas que recorren una rama determinada: la condición
que corta antes de tiempo, el bucle que no da ninguna vuelta, el `if` que solo
se cumple en un caso raro.

La pregunta que responde es: **¿todos los caminos del código hacen lo que se
espera, incluidos los que casi nunca se recorren?**

La caja negra no llega aquí. Un `if` que solo se cumple con una entrada
concreta puede estar equivocado durante años sin que ninguna prueba por la
interfaz lo toque. Los bugs más caros de este proyecto eran de ese tipo: un
`max()` donde debía ir `min()`, y una condición del throttle que devolvía
`None` para peticiones autenticadas.

Cada test dice QUÉ RAMA recorre, y declara el ESPERADO frente al OBTENIDO.
"""

from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from auditoria.acciones import ACCIONES_LEGADAS, canonica, nombres_equivalentes
from core.permissions import RolPermiso
from core.throttling import LoginRateThrottle
from pacientes.fonetica import (
    UMBRAL_SIMILITUD,
    clave_fonetica,
    coincide,
    normalizar,
    similitud,
)


class RamasDeLaClaveFoneticaTest(TestCase):
    """`clave_fonetica` aplica ocho sustituciones en orden. Una por test."""

    def test_rama_H_aspirada_inicial(self):
        """Rama: `^(hu|gu|w)` → W.

        ESPERADO: las tres grafías dan la misma inicial. Es la regla que hace
        que Huanca, Guanca y Wanca sean el mismo apellido.
        """
        assert clave_fonetica("Huanca")[0] == "W"
        assert clave_fonetica("Guanca")[0] == "W"
        assert clave_fonetica("Wanca")[0] == "W"

    def test_rama_oclusiva_velar(self):
        """Rama: `qu|k|c(?=[aou])|q` → K.

        ESPERADO: Quispe y Kispe coinciden; Cusi y Kusi también.
        """
        assert clave_fonetica("Quispe") == clave_fonetica("Kispe")
        assert clave_fonetica("Cusi") == clave_fonetica("Kusi")

    def test_rama_sibilante_solo_ante_e_o_i(self):
        """Rama: `c(?=[ei])` → S, pero NO ante a/o/u.

        ESPERADO: la C de Cespedes se vuelve S; la de Cusi no.
        Es el borde entre dos reglas y el sitio donde el orden importa.
        """
        assert clave_fonetica("Cespedes")[0] == "S"
        assert clave_fonetica("Cusi")[0] == "K"

    def test_rama_B_y_V_son_lo_mismo(self):
        """Rama: `b|v` → B."""
        assert clave_fonetica("Vargas") == clave_fonetica("Bargas")

    def test_rama_vocal_final_atona(self):
        """Rama: `[yi]$` → I. Solo al FINAL.

        ESPERADO: Mamani = Mamany. Y la Y interior no se toca.
        """
        assert clave_fonetica("Mamani") == clave_fonetica("Mamany")

    def test_rama_O_y_U_atonas(self):
        """Rama: `[ou]` → O. ESPERADO: Poma = Puma."""
        assert clave_fonetica("Poma") == clave_fonetica("Puma")

    def test_rama_H_muda_desaparece(self):
        """Rama: `.replace("h", "")` — la que corre DESPUÉS de la H aspirada."""
        assert "h" not in clave_fonetica("Bohorquez")

    def test_rama_letras_dobles(self):
        """Rama: `(.)\\1+` → una sola. ESPERADO: Mamanni = Mamani."""
        assert clave_fonetica("Mamanni") == clave_fonetica("Mamani")

    def test_rama_de_entrada_vacia(self):
        """Rama: `normalizar(None)` devuelve "".

        ESPERADO: cadena vacía, no excepción. Es el camino que se recorre
        cuando un apellido materno es nulo, que pasa constantemente.
        """
        assert clave_fonetica(None) == ""
        assert clave_fonetica("") == ""
        assert normalizar(None) == ""


class RamasDeSimilitudTest(TestCase):
    """`similitud` tiene un corte temprano antes de comparar."""

    def test_rama_del_corte_por_inicial_distinta(self):
        """Rama: `ka[0] != kb[0]` → return 0.0 SIN comparar.

        ESPERADO: exactamente 0.0. Es la guarda que evita que "Fernada" traiga
        a las "Bernarda": sin ella se parecen 0.80, justo el umbral.
        """
        assert similitud("Fernanda", "Bernarda") == 0.0

    def test_rama_de_clave_vacia(self):
        """Rama: `not ka or not kb` → return 0.0.

        ESPERADO: 0.0 y sin reventar al indexar `ka[0]` de una cadena vacía.
        """
        assert similitud("", "Mamani") == 0.0
        assert similitud("Mamani", None) == 0.0

    def test_rama_normal_devuelve_la_proporcion(self):
        """Rama: se llega hasta `SequenceMatcher`.

        ESPERADO: por encima del umbral para una variante real.
        """
        assert similitud("Mamani", "Mamany") >= UMBRAL_SIMILITUD


class RamasDeCoincideTest(TestCase):
    """`coincide` corta en cuanto una palabra del término no llega al umbral."""

    def test_rama_de_termino_vacio(self):
        """Rama: `not palabras_termino` → 0.0."""
        assert coincide("", "Rosa Mamani") == 0.0
        assert coincide("   ", "Rosa Mamani") == 0.0

    def test_rama_de_nombre_vacio(self):
        """Rama: `not palabras_nombre` → 0.0."""
        assert coincide("mamani", "") == 0.0

    def test_rama_del_corte_cuando_UNA_palabra_no_casa(self):
        """Rama: `if mejor < UMBRAL` → return 0.0 sin mirar el resto.

        ESPERADO: 0.0. "rosa" casa pero "zzzz" no, así que el conjunto no casa.
        Quien escribe dos palabras está acotando, no ampliando.
        """
        assert coincide("rosa zzzz", "Rosa Mamani") == 0.0

    def test_rama_de_todas_las_palabras_casando(self):
        """Rama: el bucle termina y se devuelve la media.

        ESPERADO: mayor que 0, y el orden de las palabras no importa.
        """
        assert coincide("rosa mamani", "Rosa Mamani Choque") > 0
        assert coincide("mamani rosa", "Rosa Mamani Choque") > 0


class RamasDelNivelDePermisoTest(TestCase):
    """El bug del `max()` vivía aquí y ninguna prueba de caja negra lo veía."""

    def test_el_nivel_exigido_es_el_MENOR_de_los_roles_permitidos(self):
        """Rama: `min(...)` en `__init__`.

        ESPERADO: con (medico, administrador) el nivel exigido es el de médico.

        Con `max()` salía el de administrador (100), así que una médica fallaba
        `nivel >= minimo` **aunque su rol estuviera explícitamente permitido**.
        Enfermería y medicina se quedaron sin cinco módulos por esta línea.
        """
        permiso = RolPermiso(("medico", "administrador"))

        assert permiso._nivel_minimo < 100, (
            f"El nivel exigido es {permiso._nivel_minimo}. Si es 100, volvió "
            f"el `max()`: solo el administrador pasaría."
        )

    def test_un_rol_desconocido_no_sube_el_liston(self):
        """Rama: `_ROLE_HIERARCHY.get(r, 0)` con la alternativa a 0.

        ESPERADO: el mínimo baja a 0, no revienta con KeyError.
        """
        permiso = RolPermiso(("medico", "rol_inventado"))

        assert permiso._nivel_minimo == 0

    def test_has_permission_exige_ADEMAS_estar_en_la_lista(self):
        """Rama: la segunda condición, `rol in self._roles`.

        ESPERADO: False para recepción aunque su nivel diera.
        Sin esta condición, bastaría el nivel numérico para entrar en
        cualquier módulo.
        """
        permiso = RolPermiso(("medico", "enfermera"))

        class Peticion:
            user = type("U", (), {
                "is_authenticated": True, "rol": "recepcion", "is_superuser": False,
            })()

        assert permiso.has_permission(Peticion(), None) is False

    def test_sin_autenticar_no_pasa_por_ninguna_rama(self):
        """Rama: `request.user and request.user.is_authenticated` → False."""
        permiso = RolPermiso(("medico",))

        class Peticion:
            user = type("U", (), {"is_authenticated": False, "rol": "medico"})()

        assert permiso.has_permission(Peticion(), None) is False


class RamasDelLimiteDeLoginTest(TestCase):
    """`allow_request` tiene tres salidas antes de contar nada."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _peticion(self):
        class Peticion:
            META = {"REMOTE_ADDR": "10.0.0.7"}
            user = type("U", (), {"is_authenticated": False})()
        return Peticion()

    def test_rama_sin_tasa_configurada_deja_pasar(self):
        """Rama: `if self.rate is None: return True`.

        ESPERADO: True. Es el camino en los tests del resto de la suite, donde
        el límite está desactivado para no volverlos frágiles.
        """
        with patch.object(LoginRateThrottle, "rate", None, create=True):
            throttle = LoginRateThrottle()
            assert throttle.allow_request(self._peticion(), None) is True

    def test_rama_del_historial_todavia_con_hueco(self):
        """Rama: `len(self.history) < self.num_requests` → True."""
        with patch.object(LoginRateThrottle, "rate", "3/min", create=True):
            throttle = LoginRateThrottle()
            assert throttle.allow_request(self._peticion(), None) is True

    def test_rama_del_historial_lleno(self):
        """Rama: `len(self.history) >= self.num_requests` → throttle_failure.

        ESPERADO: False al cuarto, tras tres fallos registrados.
        """
        with patch.object(LoginRateThrottle, "rate", "3/min", create=True):
            for _ in range(3):
                t = LoginRateThrottle()
                t.allow_request(self._peticion(), None)
                t.registrar_fallo(self._peticion())

            assert LoginRateThrottle().allow_request(self._peticion(), None) is False

    def test_rama_que_descarta_los_intentos_ya_caducados(self):
        """Rama: el `while` que saca del historial lo que salió de la ventana.

        ESPERADO: vuelve a dejar pasar. Se simula el paso del tiempo moviendo
        el reloj del throttle, que es lo que lee ese bucle.
        """
        with patch.object(LoginRateThrottle, "rate", "3/min", create=True):
            for _ in range(3):
                t = LoginRateThrottle()
                t.allow_request(self._peticion(), None)
                t.registrar_fallo(self._peticion())

            assert LoginRateThrottle().allow_request(self._peticion(), None) is False

            # 61 segundos después: la ventana de un minuto ya pasó, así que el
            # bucle debe vaciar el historial y volver a dejar pasar. Se adelanta
            # el reloj que lee ese bucle en vez de esperar de verdad.
            import time as _time

            with patch.object(
                LoginRateThrottle, "timer", staticmethod(lambda: _time.time() + 61),
            ):
                assert LoginRateThrottle().allow_request(self._peticion(), None) is True

    def test_rama_de_la_clave_de_cache_con_usuario_AUTENTICADO(self):
        """Rama: `get_cache_key` sobrescrito, que ya no devuelve None.

        ESPERADO: una clave, no None.

        `AnonRateThrottle` devolvía None aquí —"solo limito a los anónimos"— y
        eso era un agujero: bastaba iniciar sesión una vez con una cuenta
        propia para saltarse el límite y probar contraseñas ajenas sin freno.
        """
        class PeticionAutenticada:
            META = {"REMOTE_ADDR": "10.0.0.7"}
            user = type("U", (), {"is_authenticated": True})()

        with patch.object(LoginRateThrottle, "rate", "3/min", create=True):
            clave = LoginRateThrottle().get_cache_key(PeticionAutenticada(), None)

        assert clave is not None, (
            "Con sesión iniciada el límite deja de aplicarse: volvió el "
            "comportamiento de AnonRateThrottle."
        )
        assert "10.0.0.7" in clave


class RamasDelVocabularioDeAuditoriaTest(TestCase):
    """`canonica` y `nombres_equivalentes` tienen alternativas silenciosas."""

    def test_rama_del_nombre_legado(self):
        """Rama: la clave está en el diccionario.

        ESPERADO: 'actualizar' se traduce a 'EDITAR'.
        """
        assert canonica("actualizar") == "EDITAR"

    def test_rama_del_nombre_desconocido(self):
        """Rama: `.get(accion, accion)` con la alternativa.

        ESPERADO: se devuelve tal cual. Perder el registro sería peor que
        guardarlo con un nombre inesperado.
        """
        assert canonica("ACCION_QUE_NO_EXISTE") == "ACCION_QUE_NO_EXISTE"

    def test_rama_de_la_entrada_vacia(self):
        """Rama: `if not accion: return ""`.

        ESPERADO: cadena vacía, nunca una excepción. La auditoría no puede
        tumbar la operación que está auditando.
        """
        assert canonica(None) == ""
        assert canonica("") == ""
        assert nombres_equivalentes(None) == []

    def test_todos_los_nombres_legados_tienen_vuelta(self):
        """Recorre el diccionario entero, no un ejemplo.

        ESPERADO: para cada legado, `nombres_equivalentes` del canónico lo
        incluye. Si no, filtrar por el canónico se dejaría registros fuera.
        """
        for legado, canonico in ACCIONES_LEGADAS.items():
            assert legado in nombres_equivalentes(canonico), (
                f"Filtrar por '{canonico}' no encontraría los guardados como "
                f"'{legado}'."
            )
