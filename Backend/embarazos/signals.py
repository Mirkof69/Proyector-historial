"""Signals del módulo de Embarazos.

IMPORTANTE — por qué este módulo estaba muerto
----------------------------------------------
`EmbarazosConfig.ready()` no importaba este archivo, así que NINGUNO de estos
receivers estaba conectado: Django solo los registra cuando el módulo se
importa. Consecuencia real, medida sobre la base: **177 embarazos de alto
riesgo y ni una sola alerta emitida**. Tampoco se calculaba la fecha probable
de parto cuando faltaba, ni se avisaba de un embarazo nuevo o finalizado.
Es la misma clase de fallo silencioso que tuvo la auditoría clínica.

Además, las notificaciones se creaban con `Notificacion.objects.create()`
directo, saltándose `crear_notificacion_clinica()`, que es lo que garantiza:
  - destinatario con FALLBACK (médico null/inactivo → administradores),
  - auditoría de a quién se avisó,
  - anti-fatiga (no repetir una alerta sin leer del mismo evento),
  - difusión en tiempo real.
Dos de esas llamadas ni siquiera pasaban `usuario=`, que es obligatorio
(`null=False`): al conectarlas habrían reventado con IntegrityError en cada
embarazo finalizado — o sea, en cada parto registrado.
"""

from datetime import timedelta

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from notificaciones.models import PrioridadNotificacion
from notificaciones.services import crear_notificacion_clinica

from .models import Embarazo


@receiver(post_save, sender=Embarazo)
def embarazo_creado(sender, instance, created, **_kwargs):
    """Avisa del alta de un embarazo nuevo."""
    if not created:
        return
    crear_notificacion_clinica(
        destinatario_preferido=instance.medico_responsable,
        tipo="alerta_informacion",
        titulo="Nuevo Embarazo Registrado",
        mensaje=(
            f"Se ha registrado un nuevo embarazo para "
            f"{instance.paciente.nombre_completo}"
        ),
        prioridad=PrioridadNotificacion.NORMAL,
        entidad_tipo="embarazo",
        entidad_id=instance.id,
    )


@receiver(post_save, sender=Embarazo)
def embarazo_finalizado(sender, instance, created, **_kwargs):
    """Avisa del cierre del embarazo (se dispara al registrar el parto)."""
    if created or instance.estado != "finalizado":
        return
    crear_notificacion_clinica(
        destinatario_preferido=instance.medico_responsable,
        tipo="alerta_informacion",
        titulo="Embarazo Finalizado",
        mensaje=(
            f"El embarazo de {instance.paciente.nombre_completo} "
            f"ha sido marcado como finalizado"
        ),
        prioridad=PrioridadNotificacion.BAJA,
        entidad_tipo="embarazo",
        entidad_id=instance.id,
    )


@receiver(post_save, sender=Embarazo)
def alertar_embarazo_alto_riesgo(sender, instance, created, **_kwargs):
    """Alerta crítica cuando el embarazo se clasifica de alto riesgo.

    Antes exigía `and instance.medico_responsable`: si el embarazo no tenía
    médico asignado, la alerta CRÍTICA simplemente no se emitía y nadie se
    enteraba. Ahora el destinatario se resuelve con fallback, que es
    justamente para lo que existe.
    """
    if instance.riesgo_embarazo != "alto":
        return
    crear_notificacion_clinica(
        destinatario_preferido=instance.medico_responsable,
        tipo="alerta_critica",
        titulo="ALERTA: Embarazo de Alto Riesgo Detectado",
        mensaje=(
            f"El embarazo de {instance.paciente.nombre_completo} "
            f"ha sido clasificado como de alto riesgo."
        ),
        prioridad=PrioridadNotificacion.CRITICA,
        entidad_tipo="embarazo",
        entidad_id=instance.id,
    )


@receiver(post_save, sender=Embarazo)
def recordatorio_fecha_probable_parto(sender, instance, created, **_kwargs):
    """Recuerda la FPP cuando faltan entre 10 y 15 días."""
    if not instance.fecha_probable_parto or instance.estado != "activo":
        return
    dias_restantes = (instance.fecha_probable_parto - timezone.now().date()).days
    if not 10 <= dias_restantes <= 15:
        return
    # El anti-fatiga de crear_notificacion_clinica evita que se repita en cada
    # guardado mientras siga sin leerse (antes lo intentaba un get_or_create
    # que además no pasaba `usuario`, obligatorio en el modelo).
    crear_notificacion_clinica(
        destinatario_preferido=instance.medico_responsable,
        tipo="recordatorio",
        titulo="Próxima Fecha Probable de Parto",
        mensaje=(
            f"La paciente {instance.paciente.nombre_completo} tiene FPP en "
            f"{dias_restantes} días ({instance.fecha_probable_parto})"
        ),
        prioridad=PrioridadNotificacion.ALTA,
        entidad_tipo="embarazo",
        entidad_id=instance.id,
    )


@receiver(pre_save, sender=Embarazo)
def validar_embarazo(sender, instance, **_kwargs):
    """Calcula la FPP si no viene (regla de Naegele: FUM + 280 días)."""
    if instance.fecha_ultima_menstruacion and not instance.fecha_probable_parto:
        instance.fecha_probable_parto = instance.fecha_ultima_menstruacion + timedelta(
            days=280,
        )
