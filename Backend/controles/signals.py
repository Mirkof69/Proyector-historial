"""Signals para módulo de Controles Prenatales"""

from datetime import timedelta

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from notificaciones.models import Notificacion

from .models import ControlPrenatal


@receiver(post_save, sender=ControlPrenatal)
def control_prenatal_registrado(_sender, instance, created, **_kwargs):
    """Signal cuando se registra un control prenatal
    """
    if created:
        # Actualizar último control del embarazo
        if instance.embarazo:
            instance.embarazo.ultimo_control = instance.fecha_control
            instance.embarazo.save(update_fields=["ultimo_control"])

        # Notificación de registro
        Notificacion.objects.create(
            titulo="Control Prenatal Registrado",
            mensaje=f"Control prenatal registrado para {instance.paciente.nombre_completo} - {instance.edad_gestacional_texto}",
            tipo="alerta_informacion",
            entidad_tipo="control",
            entidad_id=instance.id,
            prioridad="normal",
        )

        # Programar próximo control
        programar_proximo_control(instance)


@receiver(pre_save, sender=ControlPrenatal)
def validar_control(_sender, instance, **_kwargs):
    """Validaciones antes de guardar control
    """
    # Usar datos del embarazo si faltan
    if instance.embarazo:
        if not instance.paciente:
            instance.paciente = instance.embarazo.paciente

        # Si no tiene peso pregestacional, intentar traerlo del embarazo
        if not instance.peso_pregestacional and instance.embarazo.peso_pregestacional:
            instance.peso_pregestacional = instance.embarazo.peso_pregestacional


@receiver(post_save, sender=ControlPrenatal)
def detectar_anomalias_control(_sender, instance, _created, **_kwargs):
    """Detectar anomalías en parámetros del control y generar alertas
    """
    alertas = instance.get_alertas()

    # Si hay alertas críticas, generar notificación
    alertas_criticas = [a for a in alertas if a["tipo"] == "critico"]
    if alertas_criticas:
        mensaje = (
            f"Alertas críticas en control de {instance.paciente.nombre_completo}:\n"
            + "\n".join(f"- {a['mensaje']}: {a['valor']}" for a in alertas_criticas)
        )

        Notificacion.objects.create(
            titulo="CRITICO: Alerta Crítica en Control Prenatal",
            mensaje=mensaje,
            tipo="alerta_critica",
            entidad_tipo="control",
            entidad_id=instance.id,
            prioridad="alta",
        )


def programar_proximo_control(control):
    """Programa el próximo control basado en la edad gestacional
    """
    if not control.embarazo:
        return

    semanas = control.semanas_gestacion

    # Determinar frecuencia según semana gestacional
    if semanas < 28:
        # Cada 4 semanas antes de semana 28
        intervalo_dias = 28
    elif semanas < 36:
        # Cada 2 semanas entre semana 28 y 36
        intervalo_dias = 14
    else:
        # Semanal después de semana 36
        intervalo_dias = 7

    fecha_proximo = control.fecha_control + timedelta(days=intervalo_dias)
    semana_proxima = semanas + (intervalo_dias // 7)

    Notificacion.objects.create(
        titulo="Próximo Control Prenatal Sugerido",
        mensaje=f"Siguiente control para {control.paciente.nombre_completo} aproximadamente el {fecha_proximo.strftime('%d/%m/%Y')} (Semana {semana_proxima})",
        tipo="recordatorio_control",
        entidad_tipo="embarazo",
        entidad_id=control.embarazo.id,
        prioridad="normal",
    )


@receiver(post_save, sender=ControlPrenatal)
def actualizar_clasificacion_riesgo_embarazo(_sender, instance, _created, **_kwargs):
    """Actualizar clasificación de riesgo del embarazo basado en hallazgos del control
    """
    if instance.embarazo:
        # Si hay alertas críticas, el riesgo es ALTO
        if instance.tiene_alertas_criticas():
            if instance.embarazo.riesgo_embarazo != "alto":
                instance.embarazo.riesgo_embarazo = "alto"
                instance.embarazo.save(update_fields=["riesgo_embarazo"])

                Notificacion.objects.create(
                    titulo="Embarazo Reclasificado como ALTO RIESGO",
                    mensaje=f"El embarazo de {instance.paciente.nombre_completo} ha sido reclasificado debido a hallazgos en el control #{instance.numero_control}",
                    tipo="alerta_advertencia",
                    entidad_tipo="embarazo",
                    entidad_id=instance.embarazo.id,
                    prioridad="alta",
                )
