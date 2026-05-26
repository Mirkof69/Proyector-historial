"""Signals para módulo de Embarazos"""

from datetime import timedelta

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from notificaciones.models import Notificacion

from .models import Embarazo


@receiver(post_save, sender=Embarazo)
def embarazo_creado_o_actualizado(_sender, instance, created, **_kwargs):
    """Signal ejecutado cuando se crea o actualiza un embarazo
    """
    # Obtener médico responsable para notificación
    usuario_destino = instance.medico_responsable

    if created and usuario_destino:
        # Nuevo embarazo registrado - notificar al médico responsable
        Notificacion.objects.create(
            usuario=usuario_destino,
            titulo="Nuevo Embarazo Registrado",
            mensaje=f"Se ha registrado un nuevo embarazo para {instance.paciente.nombre_completo}",
            tipo="alerta_informacion",
            entidad_tipo="embarazo",
            entidad_id=instance.id,
            prioridad="normal",
        )

    elif not created and usuario_destino:
        # Embarazo actualizado
        if instance.estado == "finalizado":
            Notificacion.objects.create(
                titulo="Embarazo Finalizado",
                mensaje=f"El embarazo de {instance.paciente.nombre_completo} ha sido marcado como finalizado",
                tipo="alerta_informacion",
                entidad_tipo="embarazo",
                entidad_id=instance.id,
                prioridad="baja",
            )


@receiver(pre_save, sender=Embarazo)
def validar_embarazo(_sender, instance, **_kwargs):
    """Validaciones antes de guardar embarazo
    """
    # Calcular fecha probable de parto si no está calculada
    if instance.fecha_ultima_menstruacion and not instance.fecha_probable_parto:
        instance.fecha_probable_parto = instance.fecha_ultima_menstruacion + timedelta(
            days=280,
        )


@receiver(post_save, sender=Embarazo)
def alertar_embarazo_alto_riesgo(_sender, instance, _created, **_kwargs):
    """Alerta cuando un embarazo es de alto riesgo
    """
    if instance.riesgo_embarazo == "alto" and instance.medico_responsable:
        Notificacion.objects.create(
            usuario=instance.medico_responsable,
            titulo="ALERTA: Embarazo de Alto Riesgo Detectado",
            mensaje=f"El embarazo de {instance.paciente.nombre_completo} ha sido clasificado como de alto riesgo.",
            tipo="alerta_critica",
            entidad_tipo="embarazo",
            entidad_id=instance.id,
            prioridad="critica",
        )


@receiver(post_save, sender=Embarazo)
def recordatorio_fecha_probable_parto(_sender, instance, _created, **_kwargs):
    """Crear recordatorio cuando faltan 2 semanas para FPP
    """
    if instance.fecha_probable_parto and instance.estado == "activo":
        dias_restantes = (instance.fecha_probable_parto - timezone.now().date()).days

        if 10 <= dias_restantes <= 15:  # Entre 2 y 3 semanas
            Notificacion.objects.get_or_create(
                titulo="Próxima Fecha Probable de Parto",
                mensaje=f"La paciente {instance.paciente.nombre_completo} tiene FPP en {dias_restantes} días ({instance.fecha_probable_parto})",
                tipo="recordatorio",
                entidad_tipo="embarazo",
                entidad_id=instance.id,
                defaults={"prioridad": "alta"},
            )
