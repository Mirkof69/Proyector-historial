"""Setup groups module."""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command"""
    help = "Configures user groups and permissions"

    def __init__(self, *args, **kwargs):
        """Initialize command attributes."""
        super().__init__(*args, **kwargs)
        self.models_dict = {}

    def handle(self, *args, **options):
        """Handle"""
        # ✅ Lazy imports - Import only when command runs
        from citas.models import Cita
        from controles.models import ControlPrenatal
        from ecografias.models import Ecografia
        from embarazos.models import Embarazo
        from laboratorio.models import ExamenLaboratorio
        from pacientes.models import Paciente
        from partos.models import Parto
        from reportes.models import ReporteGenerado
        from triaje.models import TriajeEnfermeria

        self.models_dict = {
            "medicos": [
                Paciente,
                Embarazo,
                ControlPrenatal,
                Parto,
                Ecografia,
                ExamenLaboratorio,
                Cita,
                ReporteGenerado,
            ],
            "enfermeros": [
                Paciente,
                Embarazo,
                ControlPrenatal,
                Parto,
                Cita,
                TriajeEnfermeria,
            ],
        }

        self.setup_medicos()
        self.setup_enfermeros()
        self.stdout.write(
            self.style.SUCCESS("Successfully setup groups and permissions"),
        )

    def setup_medicos(self):
        """Setup medicos"""
        group, _created = Group.objects.get_or_create(name="Medicos")

        # Modules: Pacientes, Embarazos, Controles, Partos, Ecografias, Laboratorio, Citas, Reportes
        models = self.models_dict["medicos"]

        permissions = []
        for model in models:
            ct = ContentType.objects.get_for_model(model)
            # Medicos: View, Add, Change (No Delete)
            perms = Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f"view_{model._meta.model_name}",
                    f"add_{model._meta.model_name}",
                    f"change_{model._meta.model_name}",
                ],
            )
            permissions.extend(perms)

        group.permissions.set(permissions)
        self.stdout.write(
            f"Configured Medicos group with {len(permissions)} permissions",
        )

    def setup_enfermeros(self):
        """Setup enfermeros"""
        group, _created = Group.objects.get_or_create(name="Enfermeros")

        # Modules: Pacientes, Embarazos, Controles, Partos, Citas, Triaje
        # Nurses: View, Add (No Edit, No Delete)
        # Note: Triaje might need Change if they edit their own forms, but strict request says "No Edit".
        # Assuming they can Add and View.
        models = self.models_dict["enfermeros"]

        permissions = []
        for model in models:
            ct = ContentType.objects.get_for_model(model)
            # Enfermeros: View, Add ONLY
            perms = Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f"view_{model._meta.model_name}",
                    f"add_{model._meta.model_name}",
                ],
            )
            permissions.extend(perms)

        group.permissions.set(permissions)
        self.stdout.write(
            f"Configured Enfermeros group with {len(permissions)} permissions",
        )
