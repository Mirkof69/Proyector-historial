"""
Management command: python manage.py limpiar_datos
Elimina TODOS los datos de pacientes, ecografias, citas, embarazos, etc.
Conserva: Usuarios (admin, medicos, etc.), configuracion, roles, grupos.
"""
import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = "Elimina todos los datos de pacientes manteniendo usuarios"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== LIMPIAR DATOS - Fetal Medical Bolivia ==="))

        # -- 1. Eliminar archivos fisicos --
        self.stdout.write(self.style.NOTICE("\n[1/5] Eliminando archivos fisicos..."))
        media_dirs = [
            os.path.join(settings.MEDIA_ROOT, "ecografias"),
            os.path.join(settings.MEDIA_ROOT, "ia_medica"),
            os.path.join(settings.MEDIA_ROOT, "usuarios"),
            os.path.join(settings.MEDIA_ROOT, "ecografias_archivos"),
        ]
        for d in media_dirs:
            if os.path.exists(d):
                try:
                    shutil.rmtree(d)
                    self.stdout.write(f"  Eliminado: {d}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  Error eliminando {d}: {e}"))
            else:
                self.stdout.write(f"  No existe: {d} - omitido")

        # -- Obtener todos los tenants --
        from clientes.models import Client
        all_tenants = list(Client.objects.all())
        self.stdout.write(f"\nSe encontraron {len(all_tenants)} tenant(s).")

        # Modelos a limpiar en cada tenant (orden inverso a dependencias)
        tenant_models_to_clear = [
            ('ia_medica', ['PatologiaDetectadaCNN', 'AlertaCNNAnalisis', 'AnalisisCNN', 'ImagenEcografica']),
            ('ecografias_archivos', ['EcografiaArchivo']),
            ('ecografias', ['AnexosFetales', 'AnatomiaFetal', 'BiometriaFetal', 'ImagenEcografia', 'Ecografia']),
            ('citas', ['HistorialCita', 'Cita']),
            ('partos', ['Parto']),
            ('controles', ['ControlPrenatal']),
            ('embarazos', ['Embarazo']),
            ('laboratorio', ['ResultadoLaboratorio', 'ExamenLaboratorio']),
            ('vacunas', ['RegistroVacuna']),
            ('notas_evolucion', ['NotaEvolucion']),
            ('antecedentes', ['AntecedentePatologico', 'AntecedenteGinecoObstetrico']),
            ('triaje', ['TriajeEnfermeria']),
            ('pacientes', ['Paciente']),
        ]

        for tenant in all_tenants:
            self.stdout.write(self.style.NOTICE(f"\n--- Procesando tenant: {tenant.schema_name} ---"))
            with schema_context(tenant.schema_name):
                self._delete_tenant_data(tenant_models_to_clear)

        # -- Verificar que admin sigue vivo --
        from usuarios.models import Usuario
        admin_count = Usuario.objects.filter(is_superuser=True).count()
        total_usuarios = Usuario.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"\n*** DATOS LIMPIOS - {admin_count} superusuarios preservados "
            f"de {total_usuarios} usuarios totales."
        ))
        self.stdout.write(self.style.SUCCESS("*** Listo para reingresar datos desde 0."))

    def _delete_tenant_data(self, models_to_clear):
        from django.apps import apps
        for app_label, model_names in models_to_clear:
            for name in model_names:
                try:
                    model = apps.get_model(app_label, name)
                    if model is None:
                        self.stdout.write(f"  Modelo {app_label}.{name} no encontrado - omitido")
                        continue
                    model.objects.all().delete()
                    self.stdout.write(f"  {app_label}.{name}: eliminado")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  {app_label}.{name}: {e} - omitido"))
