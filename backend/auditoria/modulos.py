"""Nombre legible de cada módulo de la auditoría.

Los signals genéricos guardan el `model_name` de Django en minúsculas
(«controlprenatal», «examenlaboratorio») y el código propio usa nombres con
mayúscula («Paciente», «Usuario»). En la pantalla eso salía como dos módulos
distintos para lo mismo. Se agrupa sin distinguir mayúsculas y se muestra con
el `verbose_name` del modelo.
"""
from functools import lru_cache


@lru_cache(maxsize=1)
def _por_modelo() -> dict[str, str]:
    from django.apps import apps

    nombres = {}
    for modelo in apps.get_models():
        nombre = str(modelo._meta.verbose_name)
        nombres[modelo._meta.model_name.lower()] = nombre[:1].upper() + nombre[1:]
    return nombres


def legible(modulo: str | None) -> str:
    """«controlprenatal» -> «Control Prenatal»; lo desconocido se devuelve tal cual."""
    if not modulo:
        return "Sistema"
    return _por_modelo().get(modulo.lower(), modulo[:1].upper() + modulo[1:])
