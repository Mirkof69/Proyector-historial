"""Signals para módulo de Pacientes.

Notifican a quien registró al paciente (created_by, con fallback a administradores)
al crear el paciente, detectar factores de alto riesgo o un cumpleaños próximo.

Se ELIMINÓ el antiguo `calcular_datos_paciente`: asignaba `instance.edad` y
`instance.nombre_completo`, que hoy son PROPERTIES calculadas (no campos), por lo
que crasheaba con AttributeError. Ya no hace falta: se calculan al accederlas.
"""
from datetime import date

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from notificaciones.models import PrioridadNotificacion, TipoNotificacion
from notificaciones.services import crear_notificacion_clinica

from .models import Paciente


def _es_recepcion(usuario) -> bool:
    return getattr(usuario, "rol", "") == "recepcion"


@receiver(post_save, sender=Paciente)
def paciente_creado(sender, instance, created, **kwargs):
    """Avisa al registrante al crear un paciente y evalúa factores de riesgo."""
    if not created:
        return
    crear_notificacion_clinica(
        destinatario_preferido=getattr(instance, "created_by", None),
        tipo=TipoNotificacion.ALERTA_INFORMACION,
        prioridad=PrioridadNotificacion.BAJA,
        titulo="Paciente Registrada",
        mensaje=f"Se registró a {instance.nombre_completo} en el sistema.",
        entidad_tipo="paciente", entidad_id=instance.id,
        url=f"/dashboard/pacientes/{instance.id}",
    )
    verificar_paciente_alto_riesgo(instance)


def _cumpleanos_en(anio: int, nacimiento: date) -> date:
    """El cumpleaños en `anio`. Quien nació un 29 de febrero lo cumple el 28 en
    los años no bisiestos: antes `date(anio, 2, 29)` lanzaba ValueError y el
    alta de esa paciente respondía 500."""
    try:
        return nacimiento.replace(year=anio)
    except ValueError:
        return date(anio, 2, 28)


@receiver(post_save, sender=Paciente)
def verificar_cumpleanos_proximo(sender, instance, created, **kwargs):
    """Recuerda el cumpleaños del paciente si es dentro de 7 días."""
    if not instance.fecha_nacimiento:
        return
    hoy = timezone.localdate()
    prox = _cumpleanos_en(hoy.year, instance.fecha_nacimiento)
    if prox < hoy:
        prox = _cumpleanos_en(hoy.year + 1, instance.fecha_nacimiento)
    dias = (prox - hoy).days
    if 0 <= dias <= 7:
        crear_notificacion_clinica(
            destinatario_preferido=getattr(instance, "created_by", None),
            tipo=TipoNotificacion.RECORDATORIO,
            prioridad=PrioridadNotificacion.BAJA,
            titulo="Cumpleaños Próximo",
            mensaje=f"El cumpleaños de {instance.nombre_completo} es en {dias} día(s).",
            entidad_tipo="paciente", entidad_id=instance.id,
            url=f"/dashboard/pacientes/{instance.id}",
        )


def verificar_paciente_alto_riesgo(paciente):
    """Notifica si la paciente tiene factores de riesgo por edad."""
    factores = []
    edad = getattr(paciente, "edad", None)
    if edad and edad >= 35:
        factores.append("Edad materna avanzada (≥35 años)")
    if edad and edad < 18:
        factores.append("Edad materna muy joven (<18 años)")
    if not factores:
        return
    detalle = "\n".join(f"- {f}" for f in factores)
    registrante = getattr(paciente, "created_by", None)
    crear_notificacion_clinica(
        # Es un dato clínico: si la registró recepción, va a los administradores
        # (el destino por defecto) y no a quien no puede ver la ficha.
        destinatario_preferido=None if _es_recepcion(registrante) else registrante,
        tipo=TipoNotificacion.ALERTA_ADVERTENCIA,
        prioridad=PrioridadNotificacion.NORMAL,
        titulo="Factores de Riesgo Detectados",
        mensaje=f"Factores de riesgo para {paciente.nombre_completo}:\n{detalle}",
        entidad_tipo="paciente", entidad_id=paciente.id,
        url=f"/dashboard/pacientes/{paciente.id}",
    )
