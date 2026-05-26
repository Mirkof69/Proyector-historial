"""Signals para módulo de Laboratorio"""

from decimal import Decimal

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from notificaciones.models import Notificacion

from .models import ExamenLaboratorio, ResultadoLaboratorio, ValorReferencia


@receiver(post_save, sender=ResultadoLaboratorio)
def resultado_laboratorio_procesado(_sender, instance, created, **_kwargs):
    """Signal cuando se procesa un resultado de laboratorio
    """
    if created or instance.estado == "completado":
        # Verificar si el resultado está fuera del rango normal
        es_critico = verificar_resultado_critico(instance)

        if es_critico:
            # Resultado crítico - alerta inmediata
            Notificacion.objects.create(
                titulo="CRITICO: RESULTADO CRÍTICO DE LABORATORIO",
                mensaje=f"Resultado CRÍTICO para {instance.examen.paciente.nombre_completo}: {instance.valor_referencia.parametro} = {instance.valor_numerico} {instance.valor_referencia.unidad}",
                tipo="alerta_critica",
                entidad_tipo="resultado_laboratorio",
                entidad_id=instance.id,
                prioridad="alta",
            )
        else:
            # Resultado normal
            Notificacion.objects.create(
                titulo="Resultado de Laboratorio Disponible",
                mensaje=f"Nuevo resultado disponible para {instance.examen.paciente.nombre_completo}: {instance.valor_referencia.parametro}",
                tipo="alerta_informacion",
                entidad_tipo="resultado_laboratorio",
                entidad_id=instance.id,
                prioridad="normal",
            )


@receiver(pre_save, sender=ResultadoLaboratorio)
def interpretar_resultado(_sender, instance, **_kwargs):
    """Interpretar resultado automáticamente antes de guardar
    """
    if instance.valor_numerico and instance.valor_referencia:
        # Usar la evaluación automática del modelo
        evaluacion = instance.valor_referencia.evaluar_valor(instance.valor_numerico)
        instance.es_normal = evaluacion["es_normal"]
        instance.es_critico = evaluacion["es_critico"]
        instance.observaciones = (
            f"{instance.observaciones}\nInterpretación: {evaluacion['mensaje']}".strip()
        )


@receiver(post_save, sender=ExamenLaboratorio)
def examen_solicitado(_sender, instance, created, **_kwargs):
    """Signal cuando se solicita un examen
    """
    if created:
        Notificacion.objects.create(
            titulo="Examen de Laboratorio Solicitado",
            mensaje=f"Se ha solicitado examen de laboratorio para {instance.paciente.nombre_completo}",
            tipo="examen_solicitado",
            entidad_tipo="examen",
            entidad_id=instance.id,
            prioridad="normal",
        )


@receiver(post_save, sender=ExamenLaboratorio)
def examen_completado(_sender, instance, created, **_kwargs):
    """Notificar cuando todos los resultados están completos
    """
    if not created and instance.estado == "completado":
        # Verificar si hay resultados críticos
        resultados_criticos = instance.resultados.filter(es_critico=True).count()

        if resultados_criticos > 0:
            Notificacion.objects.create(
                titulo="ALERTA: Examen Completado con Resultados Críticos",
                mensaje=f"Examen de {instance.paciente.nombre_completo} completado con {resultados_criticos} resultado(s) crítico(s). Revisar inmediatamente.",
                tipo="examen_critico",
                entidad_tipo="examen",
                entidad_id=instance.id,
                prioridad="alta",
            )
        else:
            Notificacion.objects.create(
                titulo="Examen de Laboratorio Completado",
                mensaje=f"Examen de {instance.paciente.nombre_completo} completado. Todos los resultados dentro de rangos normales.",
                tipo="examen_listo",
                entidad_tipo="examen",
                entidad_id=instance.id,
                prioridad="normal",
            )


def verificar_resultado_critico(resultado):
    """Verifica si un resultado es crítico basado en rangos
    """
    if not resultado.valor_numerico or not resultado.tipo_examen:
        return False

    rango = obtener_rango_referencia(resultado)
    if not rango:
        return False

    # Criterio: 30% fuera del rango normal
    if resultado.valor_numerico < (rango.valor_minimo * Decimal("0.7")):
        return True
    if resultado.valor_numerico > (rango.valor_maximo * Decimal("1.3")):
        return True

    return False


def obtener_rango_referencia(resultado):
    """Obtiene el rango de referencia aplicable para un resultado
    """
    try:
        # Obtener género del paciente
        _genero = (
            resultado.examen.paciente.genero
            if hasattr(resultado.examen.paciente, "genero")
            else None
        )

        # Obtener edad gestacional si aplica
        _edad_gestacional = None
        if resultado.examen.embarazo:
            _edad_gestacional = resultado.examen.embarazo.semanas_gestacion

        # Buscar rango más específico
        query = ValorReferencia.objects.filter(
            tipo_examen=resultado.valor_referencia.tipo_examen,
        )

        return query.first()

    except Exception:
        return None
