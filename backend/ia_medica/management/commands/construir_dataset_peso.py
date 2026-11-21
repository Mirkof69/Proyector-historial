"""Construye la tabla de entrenamiento del modelo de peso al nacer.

    python manage.py construir_dataset_peso --simular
    python manage.py construir_dataset_peso --salida ../redes-neuronales/datos/tabulares/peso.csv

Empezar por `--simular`: cuenta las filas, imprime por qué se descartó cada una
y calcula la correlación peso-edad gestacional **sin escribir nada**.

Esa correlación es el semáforo del proyecto. Si sale cerca de cero, el
generador de datos volvió a producir ruido y cualquier modelo entrenado sobre
esta tabla sería un ejercicio vacío: mejor parar ahí que entrenar y presentar
una métrica que no significa nada.
"""
import statistics
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from ia_medica.ml.dataset_peso import DIAS_MAXIMOS, a_dataframe, construir_todos


def _correlacion(xs, ys) -> float:
    """Pearson. A mano, para no arrastrar scipy en un comando de gestión."""
    if len(xs) < 3:
        return 0.0
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx and dy else 0.0


class Command(BaseCommand):
    help = "Construye el dataset para predecir el peso al nacer."

    def add_arguments(self, parser):
        parser.add_argument("--simular", action="store_true",
                            help="Solo informa; no escribe ningún archivo.")
        parser.add_argument("--salida", default=str(settings.DATASETS_DIR / "peso_nacimiento.csv"))
        parser.add_argument("--tenant", default=None)
        parser.add_argument("--incluir-multiples", action="store_true",
                            help="Incluye gemelares (la biometría es ambigua).")
        parser.add_argument("--max-dias", type=int, default=None,
                            help="Días máximos entre la ecografía y el parto "
                                 "(120 por defecto; 7 = ecografía de ingreso).")
        parser.add_argument("--solo-reales", action="store_true",
                            help="Excluye las filas generadas por el seeder.")

    def handle(self, *args, **options):
        filas, descartes = construir_todos(
            options["tenant"], incluir_multiples=options["incluir_multiples"],
            dias_maximos=options["max_dias"] or DIAS_MAXIMOS,
        )

        if options["solo_reales"]:
            antes = len(filas)
            filas = [f for f in filas if not f["es_sintetico"]]
            self.stdout.write(
                f"--solo-reales: {antes - len(filas)} filas sintéticas fuera",
            )

        for esquema, d in descartes.items():
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{esquema}"))
            self.stdout.write(f"  descartados: {d.total()}")
            for motivo, cantidad in d.como_lineas():
                if cantidad:
                    self.stdout.write(f"     {motivo:<30} {cantidad:>5}")

        if not filas:
            self.stdout.write(self.style.ERROR(
                "\nNo quedó ninguna fila utilizable. Revisa los descartes.",
            ))
            return

        self.stdout.write(self.style.SUCCESS(f"\nfilas útiles: {len(filas)}"))

        sinteticas = sum(f["es_sintetico"] for f in filas)
        self.stdout.write(
            f"  sintéticas: {sinteticas} ({sinteticas / len(filas):.1%})",
        )

        pesos = [f["peso_nacimiento_g"] for f in filas]
        self.stdout.write(
            f"  peso: mediana {statistics.median(pesos):.0f} g, "
            f"rango {min(pesos)}-{max(pesos)} g",
        )

        self.stdout.write("\n  clases:")
        for clase in ("bajo_peso", "normal", "macrosomia"):
            n = sum(1 for f in filas if f["clase_peso"] == clase)
            self.stdout.write(f"     {clase:<12} {n:>5}  ({n / len(filas):.1%})")

        # El semáforo.
        egs = [f["eg_al_nacer_semanas"] for f in filas]
        r = _correlacion(egs, pesos)
        estilo = self.style.SUCCESS if r > 0.4 else self.style.ERROR
        self.stdout.write(estilo(
            f"\n  correlación peso-edad gestacional: r = {r:.3f}",
        ))
        if r <= 0.4:
            self.stdout.write(self.style.ERROR(
                "  Con esta correlación no hay nada que aprender. "
                "Revisa core/simulacion/curvas_obstetricas.py antes de entrenar.",
            ))

        # El número que el modelo tiene que batir. Se imprimen los dos para que
        # quede a la vista por qué el crudo no es un rival justo.
        crudo = [(f["peso_hadlock_g"], f["peso_nacimiento_g"])
                 for f in filas if f["peso_hadlock_g"]]
        proyectado = [(f["peso_hadlock_proyectado_g"], f["peso_nacimiento_g"])
                      for f in filas if f["peso_hadlock_proyectado_g"]]
        if crudo:
            mae = statistics.mean(abs(h - r) for h, r in crudo)
            self.stdout.write(
                f"  MAE de Hadlock crudo (peso el día de la eco): {mae:.0f} g  "
                f"<- NO es un rival justo: responde otra pregunta",
            )
        if proyectado:
            mae = statistics.mean(abs(h - r) for h, r in proyectado)
            self.stdout.write(self.style.WARNING(
                f"  MAE de Hadlock proyectado al parto:          {mae:.0f} g  "
                f"<- ESTE es el número a batir (n={len(proyectado)})",
            ))

        if options["simular"]:
            self.stdout.write(self.style.WARNING(
                "\n(simulado: no se escribió ningún archivo)",
            ))
            return

        salida = Path(options["salida"])
        salida.parent.mkdir(parents=True, exist_ok=True)
        marco = a_dataframe(filas)
        if salida.suffix == ".parquet":
            marco.to_parquet(salida, index=False)
        else:
            marco.to_csv(salida, index=False, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(
            f"\nEscrito: {salida}  ({len(marco)} filas x {len(marco.columns)} columnas)",
        ))
