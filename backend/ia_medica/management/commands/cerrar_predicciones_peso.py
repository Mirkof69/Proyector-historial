"""Cierra las predicciones de peso al nacer con el peso real (para partos ya registrados).

    python manage.py tenant_command cerrar_predicciones_peso --schema=clinica

El cierre normal es automático al registrar el recién nacido; esto recorre lo
que quedó abierto (por ejemplo, partos cargados antes de existir el cierre) e
imprime el error del modelo y de Hadlock sobre los nacimientos reales.
"""
from django.core.management.base import BaseCommand

from ia_medica.models import PrediccionPesoNacimiento
from ia_medica.signals import cerrar_predicciones
from partos.models import RecienNacido


class Command(BaseCommand):
    help = "Cierra las predicciones de peso con los recién nacidos ya registrados."

    def handle(self, *args, **opciones):
        embarazos = PrediccionPesoNacimiento.objects.filter(recien_nacido__isnull=True).values_list("embarazo_id", flat=True)
        cerradas = sum(cerrar_predicciones(rn) for rn in
                       RecienNacido.objects.filter(parto__embarazo_id__in=set(embarazos)).select_related("parto"))
        total = PrediccionPesoNacimiento.objects.filter(peso_real_g__isnull=False)
        n = total.count()
        self.stdout.write(f"Cerradas ahora: {cerradas}. Con nacimiento real: {n}.")
        if n:
            mae_m = sum(abs(p.error_modelo_g) for p in total) / n
            con_h = [p for p in total if p.error_hadlock_g is not None]
            linea = f"Error medio del modelo: {mae_m:.0f} g"
            if con_h:
                linea += f" · de Hadlock: {sum(abs(p.error_hadlock_g) for p in con_h) / len(con_h):.0f} g"
            self.stdout.write(linea)
