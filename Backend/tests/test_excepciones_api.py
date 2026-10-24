"""Las ValidationError de los modelos llegan a la pantalla como 400 con su mensaje.

Antes salían como HTTP 500 «Error desconocido» (BUG-004: altura uterina fuera
de rango para la edad gestacional, validada en ControlPrenatal.save()).
"""
from django.core.exceptions import ValidationError

from core.excepciones import manejar_excepcion


def test_validacion_de_campo_es_400_con_el_mensaje():
    mensaje = "Altura uterina de 33.0 cm muy baja para 39 semanas. Esperado: 37 a 41 cm."
    respuesta = manejar_excepcion(ValidationError({"altura_uterina": [mensaje]}), {})
    assert respuesta.status_code == 400
    assert respuesta.data == {"altura_uterina": [mensaje]}


def test_validacion_sin_campo_va_a_non_field_errors():
    respuesta = manejar_excepcion(ValidationError("La fecha del parto es anterior a la FUM."), {})
    assert respuesta.status_code == 400
    assert respuesta.data == {"non_field_errors": ["La fecha del parto es anterior a la FUM."]}


def test_otras_excepciones_siguen_igual():
    assert manejar_excepcion(ValueError("no es de la API"), {}) is None
