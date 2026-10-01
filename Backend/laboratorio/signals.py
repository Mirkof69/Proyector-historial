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
    """Avisa al médico de inmediato si un resultado NUEVO es crítico.

    Antes: al EDITAR un resultado leía `instance.estado` (el resultado no
    tiene ese campo) y respondía 500; y por cada parámetro creado mandaba un
    aviso «resultado disponible» (un hemograma = 10 avisos). El aviso de
    «examen listo» lo da el examen al completarse (`examen_completado`).
    """
    if not created or not verificar_resultado_critico(instance):
        return
    paciente = getattr(getattr(instance, "examen", None), "paciente", None)
    nombre = getattr(paciente, "nombre_completo", "paciente")
    referencia = getattr(instance, "valor_referencia", None)
    parametro = getattr(referencia, "parametro", "parámetro")
    unidad = getattr(referencia, "unidad", "")
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


@receiver(pre_save, sender=ResultadoLaboratorio)
def interpretar_resultado(sender, instance, **kwargs):
    """Interpreta el resultado automáticamente antes de guardar."""
    # `is not None`: un resultado de 0 también se interpreta.
    if instance.valor_numerico is not None and instance.valor_referencia_id:
        evaluacion = instance.valor_referencia.evaluar_valor(instance.valor_numerico)
        instance.es_normal = evaluacion["es_normal"]
        instance.es_critico = evaluacion["es_critico"]
        # Antes se AÑADÍA en cada guardado: al editar un resultado la línea
        # «Interpretación: …» se repetía. Se reemplaza la anterior.
        previas = [linea for linea in (instance.observaciones or "").splitlines()
                   if not linea.startswith("Interpretación: ")]
        instance.observaciones = "\n".join([*previas, f"Interpretación: {evaluacion['mensaje']}"]).strip()


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


@receiver(pre_save, sender=ExamenLaboratorio)
def recordar_estado_anterior(sender, instance, **kwargs):
    """Guarda el estado previo para avisar solo en el PASO a «completado»."""
    instance._estado_anterior = (
        sender.objects.filter(pk=instance.pk).values_list("estado", flat=True).first() if instance.pk else None
    )


@receiver(post_save, sender=ExamenLaboratorio)
def examen_completado(sender, instance, created, **kwargs):
    """Notifica cuando un examen pasa a completado (con o sin críticos).

    Antes avisaba en CADA guardado de un examen ya completado: corregir una
    observación volvía a mandar «examen completado».
    """
    if created or instance.estado != "completado":
        return
    if getattr(instance, "_estado_anterior", None) == "completado":
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
    if resultado.valor_numerico is None or not getattr(resultado, "valor_referencia", None):
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
