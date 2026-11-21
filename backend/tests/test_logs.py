"""Los registros de log deben poder situarse en el tiempo.

Por qué existe este archivo
---------------------------
Todos los registros de `logs/errors.log` salían con `"timestamp": null`. El
formateador declaraba `%(timestamp)s`, pero `timestamp` no es un atributo de
`LogRecord` —el estándar es `asctime`—, así que el campo quedaba vacío en cada
línea.

El daño es operativo y real: durante una auditoría del sistema, una entrada
vieja de un error de exportación de ecografías hizo perseguir un bug **que ya
estaba arreglado**, porque no había forma de saber si era de hace un minuto o
de hace un mes. Un log sin fecha no sirve para diagnosticar.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import datetime
import json
import logging
from io import StringIO

from django.test import TestCase

from settings import LOG_JSON_FORMATTER


def _formateador():
    """El mismo formateador JSON que usa el sistema, con su mismo formato."""
    from django.conf import settings

    config = settings.LOGGING["formatters"]["json"]
    clase = config["()"]
    if isinstance(clase, str):
        modulo, _, nombre = clase.rpartition(".")
        clase = getattr(__import__(modulo, fromlist=[nombre]), nombre)
    kwargs = {k: v for k, v in config.items() if k not in ("()", "format")}
    return clase(config["format"], **kwargs)


def _emitir(mensaje="prueba"):
    """Emite un registro y devuelve el JSON resultante ya parseado."""
    logger = logging.getLogger("test.logs")
    logger.setLevel(logging.INFO)
    logger.handlers = []
    flujo = StringIO()
    manejador = logging.StreamHandler(flujo)
    manejador.setFormatter(_formateador())
    logger.addHandler(manejador)
    logger.propagate = False

    logger.info(mensaje)
    return json.loads(flujo.getvalue().strip())


class TimestampEnLosLogsTest(TestCase):
    """Cada línea de log tiene que decir cuándo ocurrió."""

    def test_el_registro_trae_una_marca_de_tiempo(self):
        """ESPERADO: un campo de fecha con valor. OBTENIDO antes: null."""
        registro = _emitir()

        fecha = registro.get("timestamp") or registro.get("asctime")
        assert fecha, (
            f"El registro salió sin fecha: {registro}. "
            f"Un log sin marca de tiempo no permite diagnosticar nada."
        )

    def test_la_marca_de_tiempo_es_parseable(self):
        """ESPERADO: se puede convertir a una fecha real, no es texto suelto."""
        registro = _emitir()
        fecha = str(registro.get("timestamp") or registro.get("asctime"))

        # Se acepta ISO 8601 o el formato por defecto de logging.
        try:
            datetime.datetime.fromisoformat(fecha.replace("Z", "+00:00"))
        except ValueError:
            datetime.datetime.strptime(fecha[:19], "%Y-%m-%d %H:%M:%S")

    def test_la_marca_de_tiempo_es_de_ahora(self):
        """ESPERADO: menos de un minuto de diferencia con el reloj.

        Verifica que sea la fecha del evento y no una constante cualquiera.
        """
        registro = _emitir()
        fecha = str(registro.get("timestamp") or registro.get("asctime"))
        try:
            momento = datetime.datetime.fromisoformat(fecha.replace("Z", "+00:00"))
        except ValueError:
            momento = datetime.datetime.strptime(fecha[:19], "%Y-%m-%d %H:%M:%S")

        ahora = datetime.datetime.now(momento.tzinfo)
        diferencia = abs((ahora - momento).total_seconds())
        assert diferencia < 60, (
            f"La fecha del log difiere {diferencia:.0f} s del reloj: {fecha!r}"
        )

    def test_se_conserva_el_resto_de_la_informacion(self):
        """ESPERADO: el mensaje, el nivel y el origen siguen presentes."""
        registro = _emitir("mensaje de prueba")

        assert registro["message"] == "mensaje de prueba"
        assert registro["levelname"] == "INFO"
        assert registro["name"] == "test.logs"
        assert registro["lineno"] > 0

    def test_el_formateador_configurado_es_json(self):
        """ESPERADO: sigue siendo el formateador JSON, no se cambió por otro."""
        assert "jsonlogger" in LOG_JSON_FORMATTER
