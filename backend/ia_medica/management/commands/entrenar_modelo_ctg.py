"""Entrena el clasificador de cardiotocografía con los 2.126 registros reales.

    python manage.py entrenar_modelo_ctg --simular   # mide e imprime, no guarda
    python manage.py entrenar_modelo_ctg             # guarda una versión nueva

Se niega a guardar si en la prueba no supera claramente al suelo (decir
siempre «normal») o si no detecta al menos el 80 % de los registros
patológicos: un clasificador así sería peor que no tenerlo.
"""
from django.core.management.base import BaseCommand, CommandError

from ia_medica.ml import cardiotocografia as ctg

SENSIBILIDAD_PATOLOGICA_MINIMA = 0.80


class Command(BaseCommand):
    help = "Entrena y evalúa el clasificador supervisado de cardiotocografía."

    def add_arguments(self, parser):
        parser.add_argument("--simular", action="store_true", help="Medir sin guardar el modelo.")

    def handle(self, *args, **opciones):
        modelo, ficha = ctg.entrenar(registro=self.stdout.write)
        prueba = ficha["prueba"]
        suelo = ficha["comparativa_validacion_cruzada"]["constante_normal"]["cv"]["exactitud"]
        if prueba["sensibilidad"]["patologica"] < SENSIBILIDAD_PATOLOGICA_MINIMA or prueba["exactitud"] <= suelo:
            raise CommandError(
                f"No se guarda: sensibilidad patológica {prueba['sensibilidad']['patologica']:.2f} "
                f"(mínimo {SENSIBILIDAD_PATOLOGICA_MINIMA}) o exactitud {prueba['exactitud']:.3f} "
                f"no mejor que decir siempre «normal» ({suelo:.3f}).")
        if opciones["simular"]:
            self.stdout.write(self.style.WARNING("--simular: no se guardó nada."))
            return
        carpeta = ctg.guardar(modelo, ficha)
        self.stdout.write(self.style.SUCCESS(f"Modelo guardado en {carpeta}"))
