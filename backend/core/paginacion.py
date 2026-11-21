"""Paginación compartida de la API.

Por qué existe este módulo
--------------------------
`PAGE_SIZE = 200` estaba bien como tope, pero el cliente no podía pedir menos:
`page_size_query_param` y `max_page_size` son atributos de la CLASE de
paginación, no ajustes de `REST_FRAMEWORK`. Ponerlos en settings no hace nada
—DRF ni los lee— así que `?page_size=20` se ignoraba y toda pantalla recibía
200 filas aunque mostrara 10.

Definirlos aquí es la única forma de que el parámetro funcione de verdad.
"""
from __future__ import annotations

from rest_framework.pagination import PageNumberPagination


class PaginacionEstandar(PageNumberPagination):
    """Paginación por defecto: el cliente elige el tamaño, con tope."""

    #: Tamaño cuando el cliente no pide nada. Igual que antes, para no cambiar
    #: el comportamiento de las pantallas que ya funcionan.
    page_size = 200

    #: Lo que faltaba: permite `?page_size=20` desde el frontend.
    page_size_query_param = "page_size"

    #: Tope. Sin él, `?page_size=100000` traería la tabla entera de una vez.
    max_page_size = 200
