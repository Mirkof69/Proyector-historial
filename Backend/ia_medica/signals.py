"""Cierre automático de las predicciones de peso al nacer.

Al guardar un recién nacido, las predicciones abiertas de ESE embarazo hechas
antes del nacimiento se cierran con el peso real. Si el embarazo es múltiple
no se cierra nada: el modelo no predice gemelos y no se sabe a qué bebé
correspondería la ecografía.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


def cerrar_predicciones(recien_nacido) -> int:
    from .models import PrediccionPesoNacimiento

    parto = recien_nacido.parto
    if not parto or not parto.embarazo_id or not recien_nacido.peso_nacimiento:
        return 0
    if parto.embarazo.tipo_embarazo != "simple" or parto.recien_nacidos.count() > 1:
        # Si llegó un segundo bebé después de cerrar con el primero, se reabre.
        PrediccionPesoNacimiento.objects.filter(recien_nacido__parto=parto).update(
            recien_nacido=None, peso_real_g=None, error_modelo_g=None, error_hadlock_g=None, fecha_cierre=None)
        return 0
    abiertas = PrediccionPesoNacimiento.objects.filter(
        embarazo_id=parto.embarazo_id, recien_nacido__isnull=True, fecha__lte=recien_nacido.fecha_nacimiento or parto.fecha_parto)
    for prediccion in abiertas:
        prediccion.cerrar(recien_nacido)
    return len(abiertas)


@receiver(post_save, sender="partos.RecienNacido")
def al_registrar_recien_nacido(sender, instance, **kwargs):
    try:
        cerrar_predicciones(instance)
    except Exception:  # medir el modelo nunca puede impedir registrar un nacimiento
        import logging

        logging.getLogger(__name__).warning("No se pudieron cerrar las predicciones de peso", exc_info=True)
