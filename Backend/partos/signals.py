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
    """Cuando se registra un parto, finaliza automáticamente el embarazo
    """
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
