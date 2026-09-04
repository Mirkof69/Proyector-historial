"""Límites de tasa de la API.

Por qué existe este módulo
--------------------------
El login ya tenía bloqueo de cuenta: 5 intentos fallidos y la cuenta queda
bloqueada 15 minutos. Eso frena adivinar UNA contraseña, pero por sí solo abre
otra puerta: como no había ningún límite por IP, un atacante podía recorrer la
lista de usuarios haciendo 5 intentos contra cada uno y **dejar sin acceso a
todo el personal del hospital**. En una emergencia obstétrica eso es una
denegación de servicio contra el equipo médico, no una molestia.

Limitar por IP corta ese recorrido antes de que alcance a bloquear cuentas
ajenas. Las dos protecciones son complementarias: el bloqueo de cuenta defiende
la contraseña, el límite por IP defiende la disponibilidad.
"""
from __future__ import annotations

from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Limita los intentos de autenticación por dirección IP.

    Hereda de `AnonRateThrottle` porque quien llama al login todavía no está
    autenticado: la clave del contador es la IP de origen. La tasa se define en
    `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["login"]` y queda desactivada en
    los tests para no volver frágil la suite.
    """

    scope = "login"
