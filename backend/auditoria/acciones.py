"""Vocabulario único de acciones de auditoría.

Por qué existe este módulo
--------------------------
La auditoría acumuló dos nombres para cada operación: `CREAR` y `crear`,
`EDITAR` y `actualizar`, `DESACTIVAR` y `eliminar`. Medido sobre la base real:
12.068 filas `CREAR` conviviendo con 5.199 `crear`, y 884 `actualizar` mientras
el canónico `EDITAR` no tenía ninguna.

Eso rompe la consulta, que es para lo único que sirve una auditoría: filtrar
por `EDITAR` **no devolvía las 884 ediciones** guardadas como `actualizar`.
Quien revisara el registro concluiría que esas modificaciones nunca ocurrieron.

`canonica()` se aplica en `RegistroAuditoria.registrar()`, de modo que ningún
nombre legado pueda volver a entrar. Los ya guardados se normalizan con una
migración de datos.
"""
from __future__ import annotations

#: Nombre legado -> nombre canónico. Los legados vienen de los signals
#: genéricos de Django, que usaban minúsculas.
ACCIONES_LEGADAS = {
    "crear": "CREAR",
    "actualizar": "EDITAR",
    "eliminar": "DESACTIVAR",
    # Mismo hecho con otro nombre: dar de baja una paciente. Filtrar por
    # DESACTIVAR no la encontraba.
    "DESACTIVAR_PACIENTE": "DESACTIVAR",
}


def canonica(accion: str | None) -> str:
    """Nombre canónico de una acción de auditoría.

    Una acción desconocida se devuelve tal cual: perder el registro sería peor
    que guardarlo con un nombre inesperado. Vacío o `None` devuelven cadena
    vacía en vez de fallar — la auditoría nunca puede tumbar la operación que
    está auditando.
    """
    if not accion:
        return ""
    return ACCIONES_LEGADAS.get(accion, accion)


def nombres_equivalentes(accion: str | None) -> list[str]:
    """Todos los nombres bajo los que puede estar guardada una acción.

    `nombres_equivalentes("EDITAR")` devuelve `["EDITAR", "actualizar"]`.

    Hace falta porque los registros históricos NO se reescriben. La tabla de
    auditoría tiene un trigger `BEFORE UPDATE` que lanza excepción ante
    cualquier modificación, y eso es deliberado: un registro de auditoría que
    se puede editar a posteriori no sirve como evidencia. Así que en vez de
    corregir el pasado se corrige la consulta.
    """
    if not accion:
        return []
    canon = canonica(accion)
    legadas = [k for k, v in ACCIONES_LEGADAS.items() if v == canon]
    return [canon, *legadas]


def filtro_accion(accion: str | None):
    """Condición `Q` que encuentra una acción bajo cualquiera de sus nombres.

    Uso:
        RegistroAuditoria.objects.filter(filtro_accion("EDITAR"))

    Sin esto, filtrar por `EDITAR` devolvía cero pese a haber 884 ediciones
    registradas como `actualizar`.
    """
    from django.db.models import Q

    nombres = nombres_equivalentes(accion)
    if not nombres:
        return Q()
    return Q(accion__in=nombres)
