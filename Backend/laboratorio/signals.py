"""Signals para módulo de Laboratorio.

Notifican al médico solicitante (con fallback a administradores) cuando un examen
se solicita/completa o cuando un resultado es crítico. Antes estaban DESCONECTADAS
(apps.ready vacío) y rotas (param _sender, Notificacion sin usuario); ahora usan
notificaciones.services.crear_notificacion_clinica, que resuelve destinatario,
audita y difunde.
"""
from decimal import Decimal

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from notificaciones.models import PrioridadNotificacion, TipoNotificacion
from notificaciones.services import crear_notificacion_clinica

from .models import ExamenLaboratorio, ResultadoLaboratorio, ValorReferencia


def _medico_del_resultado(resultado):
    """Médico solicitante del examen asociado al resultado (o None)."""
    examen = getattr(resultado, "examen", None)
    return getattr(examen, "medico_solicitante", None) if examen else None


@receiver(post_save, sender=ResultadoLaboratorio)
def resultado_laboratorio_procesado(sender, instance, created, **kwargs):
    """Notifica al médico cuando se procesa un resultado (crítico o normal)."""
    if not (created or instance.estado == "completado"):
        return

    paciente = getattr(getattr(instance, "examen", None), "paciente", None)
    nombre = getattr(paciente, "nombre_completo", "paciente")
    parametro = getattr(getattr(instance, "valor_referencia", None), "parametro", "parámetro")

    if verificar_resultado_critico(instance):
        unidad = getattr(getattr(instance, "valor_referencia", None), "unidad", "")
        crear_notificacion_clinica(
            destinatario_preferido=_medico_del_resultado(instance),
            tipo=TipoNotificacion.EXAMEN_CRITICO,
            prioridad=PrioridadNotificacion.CRITICA,
            titulo="⚠️ RESULTADO CRÍTICO DE LABORATORIO",
            mensaje=f"Resultado CRÍTICO para {nombre}: {parametro} = {instance.valor_numerico} {unidad}. Requiere atención inmediata.",
            entidad_tipo="resultado_laboratorio",
            entidad_id=instance.id,
            url=f"/dashboard/laboratorio/resultados/{instance.id}",
        )
    else:
        crear_notificacion_clinica(
            destinatario_preferido=_medico_del_resultado(instance),
            tipo=TipoNotificacion.EXAMEN_LISTO,
            prioridad=PrioridadNotificacion.NORMAL,
            titulo="Resultado de Laboratorio Disponible",
            mensaje=f"Nuevo resultado disponible para {nombre}: {parametro}.",
            entidad_tipo="resultado_laboratorio",
            entidad_id=instance.id,
            url=f"/dashboard/laboratorio/resultados/{instance.id}",
        )


@receiver(pre_save, sender=ResultadoLaboratorio)
def interpretar_resultado(sender, instance, **kwargs):
    """Interpreta el resultado automáticamente antes de guardar."""
    if instance.valor_numerico and instance.valor_referencia:
        evaluacion = instance.valor_referencia.evaluar_valor(instance.valor_numerico)
        instance.es_normal = evaluacion["es_normal"]
        instance.es_critico = evaluacion["es_critico"]
        instance.observaciones = (
            f"{instance.observaciones}\nInterpretación: {evaluacion['mensaje']}".strip()
        )


@receiver(post_save, sender=ExamenLaboratorio)
def examen_solicitado(sender, instance, created, **kwargs):
    """Notifica al médico solicitante cuando se solicita un examen."""
    if not created:
        return
    nombre = getattr(getattr(instance, "paciente", None), "nombre_completo", "paciente")
    crear_notificacion_clinica(
        destinatario_preferido=getattr(instance, "medico_solicitante", None),
        tipo=TipoNotificacion.EXAMEN_SOLICITADO,
        prioridad=PrioridadNotificacion.NORMAL,
        titulo="Examen de Laboratorio Solicitado",
        mensaje=f"Se solicitó un examen de laboratorio para {nombre}.",
        entidad_tipo="examen",
        entidad_id=instance.id,
        url=f"/dashboard/laboratorio/examenes/{instance.id}",
    )


@receiver(post_save, sender=ExamenLaboratorio)
def examen_completado(sender, instance, created, **kwargs):
    """Notifica cuando un examen se completa (con o sin resultados críticos)."""
    if created or instance.estado != "completado":
        return
    nombre = getattr(getattr(instance, "paciente", None), "nombre_completo", "paciente")
    criticos = instance.resultados.filter(es_critico=True).count()
    if criticos > 0:
        crear_notificacion_clinica(
            destinatario_preferido=getattr(instance, "medico_solicitante", None),
            tipo=TipoNotificacion.EXAMEN_CRITICO,
            prioridad=PrioridadNotificacion.CRITICA,
            titulo="⚠️ Examen Completado con Resultados Críticos",
            mensaje=f"Examen de {nombre} completado con {criticos} resultado(s) crítico(s). Revisar de inmediato.",
            entidad_tipo="examen",
            entidad_id=instance.id,
            url=f"/dashboard/laboratorio/examenes/{instance.id}",
        )
    else:
        crear_notificacion_clinica(
            destinatario_preferido=getattr(instance, "medico_solicitante", None),
            tipo=TipoNotificacion.EXAMEN_LISTO,
            prioridad=PrioridadNotificacion.NORMAL,
            titulo="Examen de Laboratorio Completado",
            mensaje=f"Examen de {nombre} completado. Resultados dentro de rangos normales.",
            entidad_tipo="examen",
            entidad_id=instance.id,
            url=f"/dashboard/laboratorio/examenes/{instance.id}",
        )


def verificar_resultado_critico(resultado):
    """True si el valor cae 30% fuera del rango de referencia."""
    if not resultado.valor_numerico or not getattr(resultado, "valor_referencia", None):
        return False
    rango = obtener_rango_referencia(resultado)
    if not rango:
        return False
    if rango.valor_minimo is not None and resultado.valor_numerico < (rango.valor_minimo * Decimal("0.7")):
        return True
    return bool(rango.valor_maximo is not None and resultado.valor_numerico > rango.valor_maximo * Decimal("1.3"))


def obtener_rango_referencia(resultado):
    """Rango de referencia aplicable para un resultado (o None)."""
    try:
        return ValorReferencia.objects.filter(
            tipo_examen=resultado.valor_referencia.tipo_examen,
        ).first()
    except Exception:
        return None
