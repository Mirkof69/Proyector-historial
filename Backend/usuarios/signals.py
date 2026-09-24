"""Mantiene a cada usuario en el grupo de permisos de su rol.

Ver `usuarios/permisos_por_rol.py`: sin esto un médico nuevo no veía casi
ninguna pantalla hasta que alguien le asignara permisos a mano.
"""
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Usuario
from .permisos_por_rol import asignar_grupo_de_rol, sincronizar_grupos


@receiver(post_save, sender=Usuario)
def grupo_segun_rol(sender, instance, raw=False, **kwargs):
    if raw:          # carga de fixtures: no tocar relaciones
        return
    asignar_grupo_de_rol(instance)


def sincronizar_tras_migrar(sender, **kwargs):
    """Tras `migrate`, los grupos por rol quedan con los permisos al día."""
    if sender.name == "usuarios":
        sincronizar_grupos()


post_migrate.connect(sincronizar_tras_migrar)
