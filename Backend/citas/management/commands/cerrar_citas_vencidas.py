"""Pasa a «No asistió» las citas pendientes de días ya pasados, en cada clínica.

    python manage.py cerrar_citas_vencidas

INICIAR.bat lo corre al arrancar; la API de citas lo repite una vez al día por
si el sistema queda encendido varios días seguidos. Ver citas/vencimiento.py.
"""
from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, schema_context

from citas.vencimiento import cerrar_citas_vencidas


class Command(BaseCommand):
    help = "Cierra como «No asistió» las citas agendadas o confirmadas de días anteriores."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default=None, help="Esquema concreto. Por defecto, todas las clínicas.")

    def handle(self, *args, **options):
        esquemas = [options["tenant"]] if options["tenant"] else [
            t.schema_name for t in get_tenant_model().objects.exclude(schema_name="public")]
        for esquema in esquemas:
            with schema_context(esquema):
                n = cerrar_citas_vencidas()
            self.stdout.write(f"{esquema}: {n} citas vencidas pasaron a «No asistió»")
