"""Comprobación de arranque: en producción las notificaciones necesitan Redis.

La API (waitress) y los WebSockets (uvicorn) corren en procesos distintos. Con
la capa en memoria, lo que se publica en un proceso no llega al otro, y el
frontend deja de sondear en cuanto el WebSocket conecta: las alertas no se ven
hasta recargar la página. Con DEBUG la API y los sockets comparten proceso y
la capa en memoria basta.
"""
from django.conf import settings
from django.core.checks import Warning, register


@register()
def capa_de_canales_compartida(app_configs=None, **kwargs):
    capa = settings.CHANNEL_LAYERS.get("default", {}).get("BACKEND", "")
    if settings.DEBUG or not capa.endswith("InMemoryChannelLayer"):
        return []
    return [Warning(
        "Las notificaciones en tiempo real usan la capa en memoria: no cruzan del "
        "proceso de la API al de los WebSockets.",
        hint="Defina REDIS_URL (INICIAR_PRODUCCION.bat arranca Redis y la define).",
        id="notifications_websocket.W001",
    )]
