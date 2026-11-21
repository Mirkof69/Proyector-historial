"""Signals de reportes: cada hallazgo clínico crítico genera su alerta médica.

Ver reportes/alertas_clinicas.py. Generar la alerta nunca puede impedir guardar
el control o el resultado: si falla, se registra en el log y se sigue.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="controles.ControlPrenatal", dispatch_uid="alerta_desde_control")
def alerta_desde_control(sender, instance, **kwargs):
    from reportes.alertas_clinicas import desde_control

    try:
        desde_control(instance)
    except Exception:
        logger.exception("No se pudo generar la alerta del control %s", instance.pk)


@receiver(post_save, sender="laboratorio.ResultadoLaboratorio", dispatch_uid="alerta_desde_resultado")
def alerta_desde_resultado(sender, instance, **kwargs):
    from reportes.alertas_clinicas import desde_resultado

    try:
        desde_resultado(instance)
    except Exception:
        logger.exception("No se pudo generar la alerta del resultado %s", instance.pk)
