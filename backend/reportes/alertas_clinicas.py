"""Alertas médicas a partir de los hallazgos clínicos reales.

La pantalla «Alertas Médicas» lee la tabla AlertaMedica, que solo se llenaba a
mano: estaba vacía mientras 2.348 controles tenían alertas críticas calculadas
(hipertensión, FCF anormal, proteinuria…) y el laboratorio marcaba valores
críticos. Aquí cada hallazgo crítico se convierte en una alerta:

- Control prenatal: cada alerta de ControlPrenatal.get_alertas(), con la
  prioridad de su gravedad (baja, media, alta, crítica o emergencia). Antes
  solo las «critico», y por categoría: toda hipertensión salía «crítica» y no
  había ninguna alerta media ni baja.
- Laboratorio: cada ResultadoLaboratorio crítico (prioridad crítica) y cada
  uno fuera de rango (resultado anormal, prioridad media).

Es idempotente (una alerta por control y categoría, o por resultado): guardar
dos veces el mismo control no duplica nada. Si el embarazo ya no está activo,
la alerta se guarda como resuelta, con la fecha del hallazgo, para que las
estadísticas cuenten el hecho sin dejarlo pendiente para siempre.
"""
from __future__ import annotations

import logging
from datetime import datetime, time

from django.utils import timezone

logger = logging.getLogger(__name__)



def _momento(fecha) -> datetime:
    """Fecha del hallazgo como datetime con zona (los controles guardan solo la fecha)."""
    if isinstance(fecha, datetime):
        return fecha if timezone.is_aware(fecha) else timezone.make_aware(fecha)
    return timezone.make_aware(datetime.combine(fecha or timezone.localdate(), time(9, 0)))


def _estado(embarazo, momento: datetime) -> dict:
    if embarazo is None or getattr(embarazo, "estado", "activo") == "activo":
        return {"estado": "activa"}
    return {"estado": "resuelta", "fecha_resolucion": momento,
            "comentario_resolucion": "Embarazo finalizado: alerta cerrada al cargar el historial."}


def desde_control(control) -> int:
    """Crea las alertas críticas de un control prenatal. Devuelve cuántas creó."""
    from reportes.models import AlertaMedica

    creadas = 0
    momento = _momento(getattr(control, "fecha_control", None))
    for alerta in control.get_alertas():
        categoria = alerta.get("categoria", "")
        if categoria == "nutricional":  # el IMC se ve en el control; repetido en cada uno sería ruido
            continue
        if AlertaMedica.objects.filter(modulo_origen="controles", registro_origen_id=control.pk,
                                       datos_contexto__categoria=categoria).exists():
            continue
        nueva = AlertaMedica.objects.create(
            titulo=alerta["mensaje"][:200],
            descripcion=(f"Control prenatal n.º {control.numero_control or '-'} del "
                         f"{momento:%d/%m/%Y}: {alerta['mensaje']} ({alerta.get('valor', '')})."),
            tipo=("riesgo_alto" if categoria == "preeclampsia"
                  else "valor_critico" if alerta.get("tipo") == "critico" else "resultado_anormal"),
            prioridad=alerta.get("gravedad", "alta"),
            paciente_id=control.paciente_id,
            embarazo_id=control.embarazo_id,
            medico_responsable_id=getattr(control, "medico_id", None) or getattr(control, "created_by_id", None),
            modulo_origen="controles",
            registro_origen_id=control.pk,
            datos_contexto={"categoria": categoria, "origen": "control_prenatal"},
            valor_actual=str(alerta.get("valor", ""))[:100],
            accion_recomendada=alerta.get("recomendacion", ""),
            **_estado(control.embarazo, momento),
        )
        # fecha_creacion es auto_now_add: se lleva a la fecha real del hallazgo.
        AlertaMedica.objects.filter(pk=nueva.pk).update(fecha_creacion=momento)
        creadas += 1
    return creadas


def desde_resultado(resultado) -> int:
    """Crea la alerta de un resultado de laboratorio crítico."""
    from reportes.models import AlertaMedica

    if resultado.es_normal or resultado.valor_numerico is None:
        return 0
    if AlertaMedica.objects.filter(modulo_origen="laboratorio", registro_origen_id=resultado.pk).exists():
        return 0
    examen = resultado.examen
    momento = _momento(getattr(examen, "fecha_resultado", None) or getattr(examen, "fecha_solicitud", None))
    referencia = resultado.valor_referencia
    parametro = getattr(referencia, "parametro", "") or "Resultado"
    unidad = getattr(referencia, "unidad", "") or ""
    valor = resultado.valor_numerico if resultado.valor_numerico is not None else resultado.valor_texto
    embarazo = examen.control_prenatal.embarazo if examen.control_prenatal_id else None
    nueva = AlertaMedica.objects.create(
        titulo=(f"VALOR CRÍTICO: {parametro}" if resultado.es_critico else f"Fuera de rango: {parametro}")[:200],
        descripcion=f"Laboratorio del {momento:%d/%m/%Y}: {parametro} = {valor} {unidad}".strip(),
        tipo="valor_critico" if resultado.es_critico else "resultado_anormal",
        prioridad="critica" if resultado.es_critico else "media",
        paciente_id=examen.paciente_id,
        embarazo_id=getattr(embarazo, "pk", None),
        medico_responsable_id=getattr(examen, "medico_solicitante_id", None),
        modulo_origen="laboratorio",
        registro_origen_id=resultado.pk,
        datos_contexto={"categoria": "laboratorio", "origen": "resultado_laboratorio", "examen": examen.pk},
        valor_actual=str(valor)[:100],
        accion_recomendada=("Confirmar el valor y comunicar a la médica tratante de inmediato."
                            if resultado.es_critico else "Revisar en el próximo control."),
        **_estado(embarazo, momento),
    )
    AlertaMedica.objects.filter(pk=nueva.pk).update(fecha_creacion=momento)
    return 1
