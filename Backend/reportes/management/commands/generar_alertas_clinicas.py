"""Genera las alertas médicas de los controles y resultados ya guardados.

    python manage.py generar_alertas_clinicas --schema=clinica_demo

Los nuevos controles y resultados críticos generan su alerta solos (signals);
este comando hace lo mismo con los que ya existían. Es idempotente: se puede
correr varias veces sin duplicar alertas.
"""
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = "Crea las alertas médicas de los hallazgos críticos ya registrados"

    def add_arguments(self, parser):
        parser.add_argument("--schema", default="clinica_demo")

    def handle(self, *args, **opciones):
        from controles.models import ControlPrenatal
        from laboratorio.models import ResultadoLaboratorio
        from reportes.alertas_clinicas import desde_control, desde_resultado
        from reportes.models import AlertaMedica

        with schema_context(opciones["schema"]):
            antes = AlertaMedica.objects.count()
            controles = ControlPrenatal.objects.select_related("embarazo", "paciente")
            de_controles = sum(desde_control(c) for c in controles.iterator(chunk_size=500))
            resultados = ResultadoLaboratorio.objects.filter(es_critico=True).select_related(
                "examen__control_prenatal__embarazo", "valor_referencia")
            de_laboratorio = sum(desde_resultado(r) for r in resultados.iterator(chunk_size=500))
            activas = AlertaMedica.objects.filter(estado="activa").count()
        self.stdout.write(self.style.SUCCESS(
            f"Alertas creadas: {de_controles} de controles, {de_laboratorio} de laboratorio "
            f"(antes {antes}; ahora {antes + de_controles + de_laboratorio}, {activas} activas)."))
