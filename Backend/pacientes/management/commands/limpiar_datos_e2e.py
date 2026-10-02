"""Borra los datos que crean las pruebas E2E (pacientes con apellido «E2E»).

Uso: python manage.py limpiar_datos_e2e --schema=clinica_demo

Borra en orden (imágenes, ecografías, exámenes de laboratorio, controles,
partos, embarazos, pacientes) porque la historia clínica está protegida contra el borrado en
cascada. Los exámenes quedan cuando una corrida se corta antes de deshacer
la importación del laboratorio. Los usuarios de prueba (correo @e2e.test)
no se borran —su auditoría es inmutable (Ley 164)—: se desactivan y se les
quita el cargo; luego se borran los cargos «E2E …». Nunca toca pacientes reales: solo las de apellido paterno «E2E».
"""
import os

from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = "Borra las pacientes de prueba E2E y toda su historia"

    def add_arguments(self, parser):
        parser.add_argument("--schema", default="clinica_demo")

    def handle(self, *args, **opciones):
        from controles.models import ControlPrenatal
        from ecografias.models import Ecografia, ImagenEcografia
        from embarazos.models import Embarazo
        from laboratorio.models import ExamenLaboratorio
        from pacientes.models import Paciente
        from partos.models import Parto
        from roles.models import Cargo
        from usuarios.models import Usuario

        with schema_context(opciones["schema"]):
            # El apellido va cifrado: no se puede filtrar en la base, se compara
            # ya descifrado.
            ids = [p.id for p in Paciente.objects.only("id", "apellido_paterno") if p.apellido_paterno == "E2E"]
            for imagen in ImagenEcografia.objects.filter(ecografia__paciente_id__in=ids):
                ruta = imagen.imagen.path if imagen.imagen else None
                imagen.delete()
                if ruta and os.path.exists(ruta):
                    os.remove(ruta)
            cuentas = {
                "ecografías": Ecografia.objects.filter(paciente_id__in=ids).delete()[0],
                "exámenes": ExamenLaboratorio.objects.filter(paciente_id__in=ids).delete()[0],
                "controles": ControlPrenatal.objects.filter(paciente_id__in=ids).delete()[0],
                "partos": Parto.objects.filter(paciente_id__in=ids).delete()[0],
                "embarazos": Embarazo.objects.filter(paciente_id__in=ids).delete()[0],
                "pacientes": Paciente.objects.filter(id__in=ids).delete()[0],
            }
            # Primero los usuarios: el cargo no se borra mientras alguien lo tenga.
            usuarios = list(Usuario.objects.filter(email__endswith="@e2e.test"))
            for usuario in usuarios:
                usuario.cargo, usuario.activo = None, False
                usuario.save()
            cuentas["usuarios desactivados"] = len(usuarios)
            cuentas["cargos"] = Cargo.objects.filter(nombre__startswith="E2E ").delete()[0]
        self.stdout.write(self.style.SUCCESS(f"Datos E2E borrados: {cuentas}"))
