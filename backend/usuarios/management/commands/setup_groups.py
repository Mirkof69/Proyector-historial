"""Crea los grupos de permisos por rol y los asigna a todos los usuarios.

    python manage.py setup_groups

Antes este comando configuraba solo «Medicos» y «Enfermeros», con pocos
módulos, y no asignaba los grupos a nadie. Ahora delega en la tabla única de
`usuarios/permisos_por_rol.py`. Los usuarios nuevos o con rol cambiado se
asignan solos (señal); este comando repara los que ya existían.
"""
from django.core.management.base import BaseCommand

from usuarios.models import Usuario
from usuarios.permisos_por_rol import asignar_grupo_de_rol, sincronizar_grupos


class Command(BaseCommand):
    help = "Sincroniza los grupos de permisos por rol y los asigna a los usuarios"

    def handle(self, *args, **options):
        for grupo, n in sincronizar_grupos().items():
            self.stdout.write(f"  {grupo:<22} {n:>4} permisos")
        usuarios = list(Usuario.objects.all())
        for u in usuarios:
            asignar_grupo_de_rol(u)
        self.stdout.write(self.style.SUCCESS(f"{len(usuarios)} usuarios con el grupo de su rol"))
