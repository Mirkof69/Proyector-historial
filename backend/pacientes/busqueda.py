"""Búsqueda de pacientes sobre campos CIFRADOS.

Por qué existe este módulo
--------------------------
`nombre`, `apellido_paterno`, `apellido_materno`, `ci`, `telefono`, `email` y
`direccion` de Paciente son EncryptedCharField: en la base están cifrados y
cada cifrado usa un IV aleatorio. Cualquier `icontains` en SQL —que es lo que
hace `SearchFilter` de DRF— compara contra el texto CIFRADO y no coincide
nunca. El síntoma no es un error: es que la búsqueda devuelve 0 resultados,
siempre, en todas las pantallas que buscan pacientes.

Estrategia, sin debilitar el cifrado:
  - CI: por `ci_hash` (HMAC-SHA256 del valor en claro) que ya existe en el
    modelo para garantizar unicidad. Coincidencia EXACTA, que es como se
    busca una cédula en recepción.
  - `id_clinico`: está en claro, se resuelve en SQL.
  - Nombres: se descifran y comparan en Python, ignorando tildes y
    mayúsculas (en Bolivia los apellidos se escriben de las dos formas:
    López/Lopez, Cusí/Cusi, Suárez/Suarez).
  - Si la comparación exacta no encuentra a nadie, se reintenta por
    FONÉTICA (ver `pacientes/fonetica.py`): Huanca/Guanca/Wanca,
    Cusi/Kusi, Quispe/Kispe, Poma/Puma son el mismo apellido escrito de
    formas distintas, y buscar una grafía no encontraba las otras. Los
    resultados aproximados salen ordenados por parecido.

Costo
-----
No hay LIKE posible sobre texto cifrado, así que la comparación es en Python.
Para no descifrar los miles de nombres en CADA búsqueda (367 ms con 3.200
pacientes, medido el 01/10/2026), cada proceso guarda en memoria los nombres
ya normalizados y sus claves fonéticas, por esquema (clínica). Se reconstruye
solo cuando cambia la cantidad de pacientes o la última fecha de
actualización (una consulta agregada barata por búsqueda).

Los nombres descifrados viven en la memoria del proceso del servidor, que ya
los descifraba en cada búsqueda; no se escriben en disco ni en ningún caché
compartido.
"""
from __future__ import annotations

import threading
import unicodedata

from .fonetica import clave_fonetica, coincide_claves
from .models import Paciente

_cache: dict[str, tuple[tuple, list[tuple[int, str, list[str]]]]] = {}
_cerrojo = threading.Lock()


def normalizar(texto: str | None) -> str:
    """Minúsculas y sin tildes: "López" se encuentra escribiendo "lopez"."""
    descompuesto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower()


def _indice_nombres() -> list[tuple[int, str, list[str]]]:
    """[(id, nombre normalizado, claves fonéticas de cada palabra)] del esquema actual."""
    from django.db import connection
    from django.db.models import Count, Max

    esquema = getattr(connection, "schema_name", "public")
    agregado = Paciente.objects.aggregate(n=Count("id"), ultima=Max("fecha_actualizacion"), mayor=Max("id"))
    version = (agregado["n"], agregado["ultima"], agregado["mayor"])
    guardado = _cache.get(esquema)
    if guardado and guardado[0] == version:
        return guardado[1]
    with _cerrojo:
        guardado = _cache.get(esquema)
        if guardado and guardado[0] == version:
            return guardado[1]
        indice = []
        for p in Paciente.objects.only("id", "nombre", "apellido_paterno", "apellido_materno"):
            completo = normalizar(f"{p.nombre} {p.apellido_paterno} {p.apellido_materno}")
            indice.append((p.pk, completo, [clave_fonetica(palabra) for palabra in completo.split()]))
        _cache[esquema] = (version, indice)
        return indice


def ids_pacientes_que_coinciden(termino: str) -> list[int]:
    """IDs de pacientes cuyo nombre, CI o id_clínico coinciden con `termino`.

    Devuelve lista vacía si el término viene vacío: quien llama decide si eso
    significa "no filtrar" (lo normal) o "sin resultados". Nunca devuelve
    "todos" ante un término que no coincide con nadie, que en una clínica
    sería peor que no encontrar nada.
    """
    termino = (termino or "").strip()
    if not termino:
        return []

    # 1) ¿Es una CI exacta? Vía hash, sin descifrar ni recorrer nada.
    try:
        from .fields import compute_search_hash

        por_ci = list(
            Paciente.objects.filter(
                ci_hash=compute_search_hash(termino),
            ).values_list("id", flat=True),
        )
    except Exception:  # ENCRYPTION_KEY ausente u otro problema de configuración
        por_ci = []
    if por_ci:
        return por_ci

    # 2) id_clinico está en claro: SQL resuelve.
    ids = set(
        Paciente.objects.filter(id_clinico__icontains=termino).values_list(
            "id", flat=True,
        ),
    )

    # 3) Nombres cifrados: descifrar y comparar en Python.
    #
    # Dos pasadas. La primera busca la subcadena exacta, que es lo que la
    # usuaria espera cuando escribe bien el apellido. La segunda, solo si la
    # primera no encontró nada, compara por fonética: en Bolivia el mismo
    # apellido se escribe de varias formas (Huanca/Guanca/Wanca,
    # Cusi/Kusi, Quispe/Kispe) y buscar la grafía "correcta" no encontraba a
    # nadie. Medido: las 15 variantes más frecuentes fallaban las 15.
    #
    # El orden importa: si hay coincidencia exacta no se abre la búsqueda
    # aproximada, para no mezclar resultados seguros con parecidos.
    objetivo = normalizar(termino)
    indice = _indice_nombres()
    ids |= {pk for pk, completo, _ in indice if objetivo in completo}
    if ids:
        return list(ids)

    # Solo aproximados: se devuelven ordenados de más a menos parecido, para
    # que la paciente más probable salga primero en pantalla.
    claves_termino = [clave_fonetica(palabra) for palabra in objetivo.split()]
    aproximados = [(puntaje, pk) for pk, _, claves in indice
                   if (puntaje := coincide_claves(claves_termino, claves))]
    aproximados.sort(reverse=True)
    return [pk for _, pk in aproximados]
