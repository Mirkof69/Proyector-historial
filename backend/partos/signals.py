"""Señales para el módulo de Partos
Automatiza acciones cuando se crea/actualiza un parto
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Parto

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Parto)
def finalizar_embarazo_al_registrar_parto(sender, instance, created, **kwargs):
    """Cuando el parto TERMINA, finaliza el embarazo.

    Antes bastaba con guardar el parto: registrar un trabajo de parto en curso
    (`parto_finalizado=False`) ya daba el embarazo por terminado, y dejaba de
    aparecer entre los activos mientras la paciente seguía en sala de partos.
    El formulario marca `parto_finalizado` por defecto, así que el registro
    habitual de un parto ya ocurrido sigue finalizando el embarazo.
    """
    if not instance.parto_finalizado:
        return
    if instance.embarazo:
        embarazo = instance.embarazo

        # Solo finalizar si está activo
        if embarazo.estado == "activo":
            embarazo.estado = "finalizado"
            embarazo.save()

            logger.info(
                "Embarazo %s marcado como FINALIZADO por Parto %s",
                embarazo.id,
                instance.id,
            )
