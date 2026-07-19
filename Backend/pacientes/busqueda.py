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

Costo y límite conocido
-----------------------
El filtro por nombre es O(n) sobre los pacientes del tenant, porque no hay
forma de hacer LIKE sobre texto cifrado. Es aceptable en el orden de
magnitud de una clínica (cientos o miles de pacientes) y se midió en
~190-380 ms sobre 450 pacientes. Para volumen mayor la solución correcta es
una columna de tokens de búsqueda normalizados (sin tildes, en minúsculas)
que permita LIKE en SQL sin exponer el dato clínico; está documentado como
pendiente de diseño, no improvisado aquí.
"""
from __future__ import annotations

import unicodedata

from .models import Paciente


def normalizar(texto: str | None) -> str:
    """Minúsculas y sin tildes: "López" se encuentra escribiendo "lopez"."""
    descompuesto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower()


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
    objetivo = normalizar(termino)
    for paciente in Paciente.objects.only(
        "id", "nombre", "apellido_paterno", "apellido_materno",
    ):
        completo = normalizar(
            f"{paciente.nombre} {paciente.apellido_paterno} {paciente.apellido_materno}",
        )
        if objetivo in completo:
            ids.add(paciente.pk)

    return list(ids)
