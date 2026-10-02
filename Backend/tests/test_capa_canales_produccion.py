"""Las notificaciones en tiempo real tienen que cruzar de la API a los WebSockets.

En producción son procesos distintos (waitress y uvicorn). Con la capa en
memoria la alerta no llegaba nunca: el frontend deja de sondear cuando el
WebSocket conecta. Ver notifications_websocket/checks.py.
"""
import asyncio
import socket

import pytest
from django.test import override_settings

from notifications_websocket.checks import capa_de_canales_compartida

EN_MEMORIA = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
REDIS = {"default": {"BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
                     "CONFIG": {"hosts": [{"address": "redis://127.0.0.1:6379/0", "protocol": 2}]}}}


@override_settings(DEBUG=False, CHANNEL_LAYERS=EN_MEMORIA)
def test_produccion_sin_redis_avisa():
    """ESPERADO: un aviso W001 al arrancar. OBTENIDO: la lista de comprobaciones."""
    avisos = capa_de_canales_compartida()
    assert [a.id for a in avisos] == ["notifications_websocket.W001"]


@override_settings(DEBUG=False, CHANNEL_LAYERS=REDIS)
def test_produccion_con_redis_no_avisa():
    assert capa_de_canales_compartida() == []


@override_settings(DEBUG=True, CHANNEL_LAYERS=EN_MEMORIA)
def test_desarrollo_en_memoria_no_avisa():
    """En desarrollo un solo proceso sirve la API y los sockets."""
    assert capa_de_canales_compartida() == []


def _redis_activo() -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", 6379)) == 0


@pytest.mark.skipif(not _redis_activo(), reason="Redis no está corriendo en 127.0.0.1:6379")
def test_mensaje_cruza_entre_dos_capas_independientes():
    """Dos capas = dos procesos. ESPERADO: lo que publica una lo recibe la otra.

    Con la configuración de settings (pub/sub, RESP2), también contra el Redis
    3.0 para Windows, que no conoce HELLO ni BZPOPMIN.
    """
    from channels_redis.pubsub import RedisPubSubChannelLayer

    hosts = REDIS["default"]["CONFIG"]["hosts"]

    async def ida_y_vuelta():
        api, sockets = RedisPubSubChannelLayer(hosts=hosts), RedisPubSubChannelLayer(hosts=hosts)
        try:
            canal = await sockets.new_channel()
            await sockets.group_add("user_1_notifications", canal)
            await asyncio.sleep(0.2)
            await api.group_send("user_1_notifications", {"type": "notification.message", "id": 7})
            return await asyncio.wait_for(sockets.receive(canal), 5)
        finally:
            await sockets.flush()
            await api.flush()

    assert asyncio.run(ida_y_vuelta())["id"] == 7
