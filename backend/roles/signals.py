"""Si cambia el rol base de un cargo, cambia el rol de quienes lo tienen."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Cargo


@receiver(post_save, sender=Cargo)
def propagar_rol_base(sender, instance, raw=False, **kwargs):
    if raw:
        return
    # save() por usuario: el rol decide su grupo de permisos y si el MFA es obligatorio.
    for usuario in instance.usuarios.exclude(rol=instance.rol_base):
        usuario.save()
