"""Signals para módulo de Citas.

Notifican al médico de la cita (con fallback a administradores) ante creación,
cambio de estado, urgencia o proximidad. Antes varias creaban Notificacion sin
usuario (campo requerido) y usaban el param _sender; ahora usan
notificaciones.services.crear_notificacion_clinica.
"""
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from notificaciones.models import PrioridadNotificacion, TipoNotificacion
from notificaciones.services import crear_notificacion_clinica

from .models import Cita


def _fecha_hora(instance) -> str:
    return f"{instance.fecha_cita.strftime('%d/%m/%Y')} {instance.hora_cita.strftime('%H:%M')}"


@receiver(post_save, sender=Cita)
def cita_creada_o_actualizada(sender, instance, created, **kwargs):
    """Notifica al médico al crear la cita o al cambiar su estado."""
    nombre = getattr(getattr(instance, "paciente", None), "nombre_completo", "paciente")
    medico = getattr(instance, "medico", None)
    if created:
        crear_notificacion_clinica(
            destinatario_preferido=medico,
            tipo=TipoNotificacion.CITA_CONFIRMADA,
            prioridad=PrioridadNotificacion.NORMAL,
            titulo="Cita Programada",
            mensaje=f"Nueva cita para {nombre} el {_fecha_hora(instance)}.",
            entidad_tipo="cita", entidad_id=instance.id,
            url=f"/dashboard/citas/{instance.id}",
        )
    elif getattr(instance, "_estado_anterior", None) != instance.estado:
        if instance.estado == "cancelada":
            crear_notificacion_clinica(
                destinatario_preferido=medico,
                tipo=TipoNotificacion.CITA_CANCELADA,
                prioridad=PrioridadNotificacion.NORMAL,
                titulo="Cita Cancelada",
                mensaje=f"La cita de {nombre} del {_fecha_hora(instance)} fue cancelada.",
                entidad_tipo="cita", entidad_id=instance.id,
                url=f"/dashboard/citas/{instance.id}",
            )
        elif instance.estado == "completada":
            crear_notificacion_clinica(
                destinatario_preferido=medico,
                tipo=TipoNotificacion.CITA_CONFIRMADA,
                prioridad=PrioridadNotificacion.BAJA,
                titulo="Cita Completada",
                mensaje=f"La cita de {nombre} fue completada.",
                entidad_tipo="cita", entidad_id=instance.id,
                url=f"/dashboard/citas/{instance.id}",
            )


@receiver(pre_save, sender=Cita)
def before_save_cita(sender, instance, **kwargs):
    """Guarda el estado anterior para detectar cambios en post_save."""
    if instance.pk:
        try:
            instance._estado_anterior = Cita.objects.get(pk=instance.pk).estado
        except Cita.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_delete, sender=Cita)
def cita_eliminada(sender, instance, **kwargs):
    """Avisa al médico (o admins) que una cita fue eliminada."""
    nombre = getattr(getattr(instance, "paciente", None), "nombre_completo", "paciente")
    crear_notificacion_clinica(
        destinatario_preferido=getattr(instance, "medico", None),
        tipo=TipoNotificacion.ALERTA_INFORMACION,
        prioridad=PrioridadNotificacion.BAJA,
        titulo="Cita Eliminada",
        mensaje=f"Se eliminó la cita de {nombre} del {_fecha_hora(instance)}.",
        entidad_tipo="cita", entidad_id=getattr(instance, "id", None),
    )


@receiver(post_save, sender=Cita)
def alerta_cita_urgente(sender, instance, created, **kwargs):
    """Alerta cuando una cita se marca como urgente."""
    if getattr(instance, "urgente", False) and instance.estado == "programada":
        nombre = getattr(getattr(instance, "paciente", None), "nombre_completo", "paciente")
        crear_notificacion_clinica(
            destinatario_preferido=getattr(instance, "medico", None),
            tipo=TipoNotificacion.ALERTA_ADVERTENCIA,
            prioridad=PrioridadNotificacion.ALTA,
            titulo="⚠️ Cita Urgente",
            mensaje=f"Cita URGENTE para {nombre} el {_fecha_hora(instance)}.",
            entidad_tipo="cita", entidad_id=instance.id,
            url=f"/dashboard/citas/{instance.id}",
        )


@receiver(post_save, sender=Cita)
def recordatorio_cita_proxima(sender, instance, created, **kwargs):
    """Recordatorio cuando faltan ≤2h para una cita programada."""
    if instance.estado != "programada":
        return
    try:
        horas = (instance.fecha_hora - timezone.now()).total_seconds() / 3600
    except (AttributeError, TypeError):
        return
    if 0 < horas <= 2:
        nombre = getattr(getattr(instance, "paciente", None), "nombre_completo", "paciente")
        crear_notificacion_clinica(
            destinatario_preferido=getattr(instance, "medico", None),
            tipo=TipoNotificacion.CITA_PROXIMA,
            prioridad=PrioridadNotificacion.ALTA,
            titulo="Cita Próxima",
            mensaje=f"La cita de {nombre} es en {int(horas)} hora(s).",
            entidad_tipo="cita", entidad_id=instance.id,
            url=f"/dashboard/citas/{instance.id}",
        )
