"""Signals para módulo de Controles Prenatales.

Notifican al médico del control (con fallback al responsable del embarazo y luego
a administradores) ante el registro de un control, alertas críticas o reclasificación
de riesgo. Antes estaban desconectadas y rotas; ahora usan
notificaciones.services.crear_notificacion_clinica.
"""
from datetime import timedelta

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from notificaciones.models import PrioridadNotificacion, TipoNotificacion
from notificaciones.services import crear_notificacion_clinica

from .models import ControlPrenatal


def _medico_del_control(control):
    """Médico del control; si no hay, el responsable del embarazo (o None)."""
    medico = getattr(control, "medico", None)
    if medico is not None:
        return medico
    embarazo = getattr(control, "embarazo", None)
    return getattr(embarazo, "medico_responsable", None) if embarazo else None


@receiver(post_save, sender=ControlPrenatal)
def control_prenatal_registrado(sender, instance, created, **kwargs):
    """Al registrar un control: avisa al médico y programa el próximo."""
    if not created:
        return
    nombre = getattr(getattr(instance, "paciente", None), "nombre_completo", "paciente")
    crear_notificacion_clinica(
        destinatario_preferido=_medico_del_control(instance),
        tipo=TipoNotificacion.ALERTA_INFORMACION,
        prioridad=PrioridadNotificacion.NORMAL,
        titulo="Control Prenatal Registrado",
        mensaje=f"Control prenatal registrado para {nombre} - {instance.edad_gestacional_texto}.",
        entidad_tipo="control",
        entidad_id=instance.id,
        url=f"/dashboard/controles/{instance.id}",
    )
    programar_proximo_control(instance)


@receiver(pre_save, sender=ControlPrenatal)
def validar_control(sender, instance, **kwargs):
    """Completa datos faltantes del control desde el embarazo."""
    if instance.embarazo:
        if not instance.paciente:
            instance.paciente = instance.embarazo.paciente
        if not instance.peso_pregestacional and instance.embarazo.peso_pregestacional:
            instance.peso_pregestacional = instance.embarazo.peso_pregestacional


@receiver(post_save, sender=ControlPrenatal)
def detectar_anomalias_control(sender, instance, created, **kwargs):
    """Notifica al médico ante alertas críticas del control (hipertensión, FCF, etc.)."""
    alertas_criticas = [a for a in instance.get_alertas() if a["tipo"] == "critico"]
    if not alertas_criticas:
        return
    nombre = getattr(getattr(instance, "paciente", None), "nombre_completo", "paciente")
    detalle = "\n".join(f"- {a['mensaje']}: {a['valor']}" for a in alertas_criticas)
    crear_notificacion_clinica(
        destinatario_preferido=_medico_del_control(instance),
        tipo=TipoNotificacion.ALERTA_CRITICA,
        prioridad=PrioridadNotificacion.CRITICA,
        titulo="⚠️ Alerta Crítica en Control Prenatal",
        mensaje=f"Alertas críticas en el control de {nombre}:\n{detalle}",
        entidad_tipo="control",
        entidad_id=instance.id,
        url=f"/dashboard/controles/{instance.id}",
    )


def programar_proximo_control(control):
    """Programa (notifica) el próximo control según la edad gestacional."""
    if not control.embarazo:
        return
    semanas = control.semanas_gestacion
    intervalo_dias = 28 if semanas < 28 else (14 if semanas < 36 else 7)
    fecha_proximo = control.fecha_control + timedelta(days=intervalo_dias)
    semana_proxima = semanas + (intervalo_dias // 7)
    nombre = getattr(getattr(control, "paciente", None), "nombre_completo", "paciente")
    crear_notificacion_clinica(
        destinatario_preferido=_medico_del_control(control),
        tipo=TipoNotificacion.RECORDATORIO_CONTROL,
        prioridad=PrioridadNotificacion.NORMAL,
        titulo="Próximo Control Prenatal Sugerido",
        mensaje=f"Siguiente control para {nombre} aprox. el {fecha_proximo.strftime('%d/%m/%Y')} (Semana {semana_proxima}).",
        entidad_tipo="embarazo",
        entidad_id=control.embarazo.id,
        url=f"/dashboard/embarazos/{control.embarazo.id}",
    )


@receiver(post_save, sender=ControlPrenatal)
def actualizar_clasificacion_riesgo_embarazo(sender, instance, created, **kwargs):
    """Si el control revela alertas críticas, reclasifica el embarazo a ALTO riesgo y avisa."""
    if not instance.embarazo or not instance.tiene_alertas_criticas():
        return
    if instance.embarazo.riesgo_embarazo != "alto":
        instance.embarazo.riesgo_embarazo = "alto"
        instance.embarazo.save(update_fields=["riesgo_embarazo"])
        nombre = getattr(getattr(instance, "paciente", None), "nombre_completo", "paciente")
        crear_notificacion_clinica(
            destinatario_preferido=_medico_del_control(instance),
            tipo=TipoNotificacion.ALERTA_ADVERTENCIA,
            prioridad=PrioridadNotificacion.ALTA,
            titulo="Embarazo Reclasificado como ALTO RIESGO",
            mensaje=f"El embarazo de {nombre} fue reclasificado por hallazgos del control #{instance.numero_control}.",
            entidad_tipo="embarazo",
            entidad_id=instance.embarazo.id,
            url=f"/dashboard/embarazos/{instance.embarazo.id}",
        )
