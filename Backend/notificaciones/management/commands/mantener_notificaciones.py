"""Archiva y limpia la tabla de notificaciones, tenant por tenant.

    python manage.py mantener_notificaciones --simular    # ver que haria
    python manage.py mantener_notificaciones              # aplicarlo

Existe como comando y no solo como tarea de Celery porque el proyecto ya no usa
Docker ni tiene un `celery beat` corriendo de forma permanente: esto se puede
poner en el Programador de tareas de Windows y funciona igual.

Empezar SIEMPRE por `--simular`. La primera pasada sobre una base que lleva
tiempo sin mantenimiento archiva miles de filas de golpe, y conviene ver el
número antes de aplicarlo.
"""
from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, schema_context

from notificaciones.mantenimiento import mantener


class Command(BaseCommand):
    help = "Archiva las notificaciones viejas y borra las rutinarias ya archivadas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--simular",
            action="store_true",
            help="Cuenta lo que haria sin modificar nada.",
        )
        parser.add_argument(
            "--tenant",
            default=None,
            help="Esquema concreto. Por defecto recorre todos los de clientes.",
        )

    def handle(self, *args, **options):
        simular = options["simular"]
        uno = options["tenant"]

        if uno:
            esquemas = [uno]
        else:
            # `public` queda fuera a proposito: ahi vive la tabla de tenants,
            # no notificaciones de nadie.
            esquemas = [
                t.schema_name
                for t in get_tenant_model().objects.exclude(schema_name="public")
            ]

        if not esquemas:
            self.stdout.write(self.style.WARNING("No hay tenants que mantener."))
            return

        for esquema in esquemas:
            with schema_context(esquema):
                r = mantener(simular=simular)

            antes, despues = r["antes"], r["despues"]
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{esquema}"))
            self.stdout.write(
                f"  antes:    {antes['total']} en total, "
                f"{antes['pendientes']} pendientes "
                f"({antes['urgentes_pendientes']} urgentes o criticas)",
            )
            self.stdout.write(f"  archivadas: {r['archivadas']['total']}")
            self.stdout.write(f"  borradas:   {r['borradas']}")

            if simular:
                self.stdout.write(self.style.WARNING("  (simulado: no se toco nada)"))
            else:
                self.stdout.write(
                    f"  despues:  {despues['total']} en total, "
                    f"{despues['pendientes']} pendientes "
                    f"({despues['urgentes_pendientes']} urgentes o criticas)",
                )

        self.stdout.write(self.style.SUCCESS("\nMantenimiento terminado."))
