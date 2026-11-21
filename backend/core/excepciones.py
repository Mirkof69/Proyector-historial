"""Manejador de excepciones de la API.

Varios modelos validan en save() con full_clean() (por ejemplo, el control
prenatal rechaza una altura uterina fuera de rango para la edad gestacional).
Esa ValidationError es de Django, no de DRF, y el manejador por defecto no la
conoce: salía como HTTP 500 y la pantalla decía «Error desconocido» (BUG-004).
Aquí se convierte en un 400 con el mensaje de cada campo, igual que una
validación del serializer.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def manejar_excepcion(exc, context):
    if isinstance(exc, DjangoValidationError):
        detalle = exc.message_dict if hasattr(exc, "error_dict") else {"non_field_errors": exc.messages}
        exc = ValidationError(detail=detalle)
    return exception_handler(exc, context)
