"""Signals para módulo de Citas"""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Cita

try:
    from notificaciones.models import (
        Notificacion,
        PrioridadNotificacion,
        TipoNotificacion,
    )

    NOTIFICACIONES_DISPONIBLES = True
except ImportError:
    NOTIFICACIONES_DISPONIBLES = False


@receiver(post_save, sender=Cita)
def cita_creada_o_actualizada(_sender, instance, created, **_kwargs):
    """Signal ejecutado cuando se crea o actualiza una cita
    """
    if not NOTIFICACIONES_DISPONIBLES:
        return

    # Obtener usuario destino (médico de la cita)
    usuario_destino = instance.medico
    if not usuario_destino:
        return

    fecha_hora_str = f"{instance.fecha_cita.strftime('%d/%m/%Y')} {instance.hora_cita.strftime('%H:%M')}"

    if created:
        # Nueva cita programada
        Notificacion.objects.create(
            usuario=usuario_destino,
            titulo="Cita Programada",
            mensaje=f"Nueva cita programada para {instance.paciente.nombre_completo} el {fecha_hora_str}",
            tipo=TipoNotificacion.CITA_CONFIRMADA,
            entidad_tipo="cita",
            entidad_id=instance.id,
            prioridad=PrioridadNotificacion.NORMAL,
        )

    # Cita actualizada - verificar cambio de estado
    elif hasattr(instance, "_estado_anterior"):
        if instance._estado_anterior != instance.estado:
            if instance.estado == "cancelada":
                Notificacion.objects.create(
                    usuario=usuario_destino,
                    titulo="Cita Cancelada",
                    mensaje=f"La cita de {instance.paciente.nombre_completo} programada para {fecha_hora_str} ha sido cancelada",
                    tipo=TipoNotificacion.CITA_CANCELADA,
                    entidad_tipo="cita",
                    entidad_id=instance.id,
                    prioridad=PrioridadNotificacion.NORMAL,
                )

            elif instance.estado == "completada":
                Notificacion.objects.create(
                    usuario=usuario_destino,
                    titulo="Cita Completada",
                    mensaje=f"La cita de {instance.paciente.nombre_completo} ha sido completada",
                    tipo=TipoNotificacion.CITA_CONFIRMADA,
                    entidad_tipo="cita",
                    entidad_id=instance.id,
                    prioridad=PrioridadNotificacion.BAJA,
                )


@receiver(pre_save, sender=Cita)
def before_save_cita(_sender, instance, **_kwargs):
    """Pre-save para guardar estado anterior
    """
    if instance.pk:
        try:
            anterior = Cita.objects.get(pk=instance.pk)
            instance._estado_anterior = anterior.estado
        except Cita.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_delete, sender=Cita)
def cita_eliminada(_sender, instance, **_kwargs):
    """Signal cuando se elimina una cita
    """
    Notificacion.objects.create(
        titulo="Cita Eliminada",
        mensaje=f"Se ha eliminado la cita de {instance.paciente.nombre_completo} programada para {instance.fecha_cita.strftime('%d/%m/%Y')} {instance.hora_cita.strftime('%H:%M')}",
        tipo="alerta_informacion",
        prioridad="baja",
    )


@receiver(post_save, sender=Cita)
def alerta_cita_urgente(_sender, instance, _created, **_kwargs):
    """Alerta para citas marcadas como urgentes
    """
    if instance.urgente and instance.estado == "programada":
        Notificacion.objects.create(
            titulo="URGENTE: Cita Urgente",
            mensaje=f"Cita URGENTE programada para {instance.paciente.nombre_completo} el {instance.fecha_cita.strftime('%d/%m/%Y')} {instance.hora_cita.strftime('%H:%M')}",
            tipo="alerta_advertencia",
            entidad_tipo="cita",
            entidad_id=instance.id,
            prioridad="alta",
        )


@receiver(post_save, sender=Cita)
def recordatorio_cita_proxima(_sender, instance, _created, **_kwargs):
    """Recordatorio cuando falta poco para la cita
    """
    if instance.estado == "programada":
        tiempo_restante = instance.fecha_hora - timezone.now()
        horas_restantes = tiempo_restante.total_seconds() / 3600

        # Si falta menos de 2 horas
        if 0 < horas_restantes <= 2:
            Notificacion.objects.get_or_create(
                titulo="Cita Próxima",
                mensaje=f"La cita de {instance.paciente.nombre_completo} es en {int(horas_restantes)} hora(s)",
                tipo="cita_proxima",
                entidad_tipo="cita",
                entidad_id=instance.id,
                defaults={"prioridad": "alta"},
            )
