"""Mantenimiento de la tabla de notificaciones.

Por qué existe este módulo
--------------------------
Había tres rutinas de mantenimiento y las tres borraban cero filas. Siempre.
Medido sobre el tenant `clinica_demo` el 5 de septiembre de 2026, con 15.698
notificaciones acumuladas:

    archivar_notificaciones_expiradas   archivaba 0
    limpiar_notificaciones_antiguas     borraba   0
    accion limpiar_antiguas del viewset borraba   4

La causa era una cadena de condiciones que nunca se cumplían:

  - `archivar_notificaciones_expiradas` exige `fecha_expiracion <= ahora`, y
    **ninguna de las 15.698 tenía fecha de expiración puesta**: el campo es
    opcional y nada lo rellena.
  - `limpiar_notificaciones_antiguas` exige `leida=True AND archivada=True`.
    Como nada se archivaba, la segunda condición valía siempre falso.
  - La acción del viewset exige `leida=True`, y **15.694 de 15.698 estaban sin
    leer** — porque la campana del encabezado mostraba 0 y nadie las abría.

Todo el mantenimiento estaba escrito para un sistema donde la gente lee sus
notificaciones. En éste no las lee nadie, así que la tabla solo crecía.

Qué hace esto en su lugar
-------------------------
Archiva **por antigüedad**, que es un criterio que sí se cumple solo. Archivar
no borra: la fila sigue ahí y se puede consultar; simplemente deja de contar en
la campana, que es lo que hacía falta.

Las ventanas dependen de la prioridad, porque no es lo mismo un recordatorio de
control que una alerta crítica:

    baja, normal      60 días
    alta             120 días
    urgente, crítica 365 días

Borrar es aparte y mucho más conservador: solo se borran las de prioridad baja
o normal que además ya estén archivadas y leídas. **Una alerta urgente o
crítica no se borra nunca de forma automática**, aunque se archive: es
evidencia clínica y la decisión de eliminarla no la toma una tarea de cron.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from .models import Notificacion, PrioridadNotificacion

logger = logging.getLogger(__name__)

#: Días que una notificación sin leer sigue contando en la campana, según su
#: prioridad. Pasado ese plazo se archiva: ya no es un aviso útil, y dejarla
#: contando solo consigue que el número deje de significar nada.
DIAS_PARA_ARCHIVAR = {
    PrioridadNotificacion.BAJA: 60,
    PrioridadNotificacion.NORMAL: 60,
    PrioridadNotificacion.ALTA: 120,
    PrioridadNotificacion.URGENTE: 365,
    PrioridadNotificacion.CRITICA: 365,
}

#: Días que se conserva una notificación ya archivada Y leída antes de
#: borrarla. Solo se aplica a prioridad baja y normal.
DIAS_PARA_BORRAR = 180

#: Prioridades que NUNCA se borran automáticamente. Se archivan, pero la fila
#: se queda: una alerta crítica es evidencia de que el sistema avisó.
PRIORIDADES_QUE_NO_SE_BORRAN = (
    PrioridadNotificacion.ALTA,
    PrioridadNotificacion.URGENTE,
    PrioridadNotificacion.CRITICA,
)


def archivar_por_antiguedad(*, simular: bool = False) -> dict[str, int]:
    """Archiva las notificaciones que ya son demasiado viejas para avisar.

    Con `simular=True` cuenta lo que haría sin tocar nada, para poder ver el
    efecto antes de aplicarlo en una base real.

    Devuelve cuántas se archivaron por prioridad, más el total.
    """
    ahora = timezone.now()
    resultado: dict[str, int] = {}

    for prioridad, dias in DIAS_PARA_ARCHIVAR.items():
        corte = ahora - timedelta(days=dias)
        pendientes = Notificacion.objects.filter(
            archivada=False,
            prioridad=prioridad,
            fecha_creacion__lt=corte,
        )
        if simular:
            cuantas = pendientes.count()
        else:
            # `update` en una sola consulta: recorrer 15.000 filas en Python
            # para marcarlas una a una es justo el tipo de cosa que satura la
            # base que esto intenta aliviar.
            cuantas = pendientes.update(archivada=True)
        resultado[str(prioridad)] = cuantas

    resultado["total"] = sum(
        v for k, v in resultado.items() if k != "total"
    )
    logger.info(
        "Mantenimiento de notificaciones: %s archivadas%s",
        resultado["total"],
        " (simulado)" if simular else "",
    )
    return resultado


def borrar_archivadas_antiguas(*, simular: bool = False) -> int:
    """Borra las notificaciones rutinarias que ya no le sirven a nadie.

    Solo las de prioridad baja o normal, archivadas, leídas y con más de
    `DIAS_PARA_BORRAR` días. Las de prioridad alta hacia arriba se quedan.
    """
    corte = timezone.now() - timedelta(days=DIAS_PARA_BORRAR)
    candidatas = Notificacion.objects.filter(
        archivada=True,
        leida=True,
        fecha_creacion__lt=corte,
    ).exclude(prioridad__in=PRIORIDADES_QUE_NO_SE_BORRAN)

    cuantas = candidatas.count()
    if not simular and cuantas:
        candidatas.delete()

    logger.info(
        "Mantenimiento de notificaciones: %s borradas%s",
        cuantas,
        " (simulado)" if simular else "",
    )
    return cuantas


def estado_actual() -> dict[str, int]:
    """Foto de la tabla, para saber si el mantenimiento está haciendo efecto.

    Es lo que hay que mirar para responder «¿está creciendo esto sin control?».
    """
    activas = Notificacion.objects.filter(archivada=False)
    return {
        "total": Notificacion.objects.count(),
        "activas": activas.count(),
        "pendientes": activas.filter(leida=False).count(),
        "urgentes_pendientes": activas.filter(
            leida=False,
        ).filter(
            Q(prioridad=PrioridadNotificacion.URGENTE)
            | Q(prioridad=PrioridadNotificacion.CRITICA),
        ).count(),
        "archivadas": Notificacion.objects.filter(archivada=True).count(),
    }


def mantener(*, simular: bool = False) -> dict:
    """Pasada completa: archivar lo viejo y borrar lo rutinario ya archivado.

    Es lo que llaman tanto el comando de gestión como la tarea de Celery, para
    que el mantenimiento sea el mismo se ejecute como se ejecute.
    """
    antes = estado_actual()
    archivadas = archivar_por_antiguedad(simular=simular)
    borradas = borrar_archivadas_antiguas(simular=simular)
    despues = estado_actual() if not simular else antes

    return {
        "antes": antes,
        "archivadas": archivadas,
        "borradas": borradas,
        "despues": despues,
        "simulado": simular,
    }
