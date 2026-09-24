"""Entrena el modelo de peso al nacer y lo compara contra sus rivales.

    python manage.py entrenar_modelo_peso --simular
    python manage.py entrenar_modelo_peso --version-modelo 1.0.0

Con `--simular` entrena, mide e imprime todo, pero **no guarda ningún
archivo**. Empezar siempre por ahí: la decisión de desplegar se toma mirando la
tabla comparativa, no antes.

Si el mejor modelo no bate a Hadlock proyectado, el comando lo dice y **se
niega a guardarlo**. Desplegar un modelo peor que la fórmula que ya existía
sería añadir complejidad a cambio de nada.
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ia_medica.ml import entrenamiento_peso as ep


def _fmt(d, clave="media", decimales=0, pct=False):
    if not d:
        return "—"
    v = d[clave]
    if pct:
        return f"{v * 100:.{decimales}f}%"
    return f"{v:,.{decimales}f}".replace(",", ".")


class Command(BaseCommand):
    help = "Entrena y evalúa el modelo supervisado de peso al nacer."

    def add_arguments(self, parser):
        parser.add_argument("--dataset", default="datasets/peso_nacimiento.csv")
        parser.add_argument("--version-modelo", default="1.0.0",
                            help="Versión con la que se guarda. (--version lo reserva Django.)")
        parser.add_argument("--simular", action="store_true",
                            help="Mide todo pero no guarda ningún archivo.")
        parser.add_argument("--forzar", action="store_true",
                            help="Guarda aunque no mejore significativamente "
                                 "a Hadlock. Queda registrado en la ficha.")

    def handle(self, *args, **options):
        ruta = Path(options["dataset"])
        if not ruta.exists():
            raise CommandError(
                f"No existe {ruta}. Genéralo antes con:\n"
                f"  python manage.py construir_dataset_peso --salida {ruta}",
            )

        marco = pd.read_csv(ruta)
        self.stdout.write(self.style.MIGRATE_HEADING("Dataset"))
        self.stdout.write(f"  {ruta}  ({len(marco)} filas)")

        resultados, info = ep.evaluar(marco)
        self.stdout.write(
            f"  {info['pacientes']} pacientes, {info['particiones']} particiones "
            f"agrupadas por paciente",
        )
        self.stdout.write(
            f"  {info['sinteticas']} de {info['filas']} filas son sintéticas "
            f"({info['sinteticas'] / info['filas']:.0%})",
        )

        # ---- Tabla comparativa -------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\nRegresión — validación cruzada, media ± desviación",
        ))
        self.stdout.write(
            f"  {'modelo':<38} {'MAE (g)':>14} {'R²':>12} {'±15%':>8}",
        )
        self.stdout.write("  " + "-" * 76)
        for r in resultados.values():
            s = r.resumen()
            self.stdout.write(
                f"  {s['descripcion']:<38} "
                f"{_fmt(s['mae_g']):>7} ± {_fmt(s['mae_g'], 'desv'):>4} "
                f"{_fmt(s['r2'], decimales=3):>7} ± {_fmt(s['r2'], 'desv', 2):>4} "
                f"{_fmt(s['dentro_15pct'], pct=True):>8}",
            )

        # ---- ¿Quién gana? ------------------------------------------------
        aprendibles = ("ridge", "random_forest", "gradient_boosting")
        ganador = min(aprendibles, key=lambda k: resultados[k].resumen()["mae_g"]["media"])
        mae_ganador = resultados[ganador].resumen()["mae_g"]["media"]
        mae_hadlock = resultados["hadlock"].resumen()["mae_g"]["media"]
        mejora = (mae_hadlock - mae_ganador) / mae_hadlock

        # La decision no se toma comparando medias: se compara particion a
        # particion. Ver `comparar_pareado` para el porque.
        pareado = ep.comparar_pareado(resultados[ganador], resultados["hadlock"])
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n¿Mejora de verdad o es ruido? (comparación pareada)",
        ))
        self.stdout.write(
            f"  mejor modelo:        {resultados[ganador].descripcion}",
        )
        self.stdout.write(
            f"  mejora media:        {pareado['mejora_media_g']:+.0f} g "
            f"(± {pareado['desv_g']:.0f} g entre particiones)",
        )
        self.stdout.write(
            f"  gana en:             {pareado['gana_en_particiones']} de "
            f"{pareado['particiones']} particiones",
        )
        self.stdout.write(
            f"  umbral (2 err. est): {2 * pareado['error_estandar_g']:.0f} g",
        )
        self.stdout.write("")
        if pareado["mejora_significativa"]:
            self.stdout.write(self.style.SUCCESS(
                f"  MEJORA REAL: {mae_ganador:.0f} g frente a {mae_hadlock:.0f} g "
                f"de Hadlock proyectado, consistente en todas las particiones.",
            ))
        elif mae_ganador < mae_hadlock:
            self.stdout.write(self.style.WARNING(
                f"  EMPATE: {mae_ganador:.0f} g frente a {mae_hadlock:.0f} g. La "
                f"diferencia ({mejora:.0%}) cabe dentro del ruido. No hay "
                f"evidencia de que el modelo mejore la fórmula.",
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"  PIERDE: ningún modelo bate a Hadlock proyectado "
                f"({mae_ganador:.0f} g frente a {mae_hadlock:.0f} g).",
            ))

        # ---- Clasificación -----------------------------------------------
        conf = ep.matriz_confusion(resultados[ganador])
        conf_hadlock = ep.matriz_confusion(resultados["hadlock"])
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\nClasificación derivada del peso previsto",
        ))
        self.stdout.write(
            f"  {'clase':<12} {'casos':>6}   {'sensib. modelo':>15} "
            f"{'sensib. Hadlock':>16}",
        )
        for c in ("bajo_peso", "normal", "macrosomia"):
            m, h = conf["por_clase"][c], conf_hadlock["por_clase"][c]
            sm = f"{m['sensibilidad']:.0%}" if m["sensibilidad"] is not None else "—"
            sh = f"{h['sensibilidad']:.0%}" if h["sensibilidad"] is not None else "—"
            self.stdout.write(f"  {c:<12} {m['casos']:>6}   {sm:>15} {sh:>16}")
        self.stdout.write(
            f"  F1 macro: modelo {conf['f1_macro']:.3f}  ·  "
            f"Hadlock {conf_hadlock['f1_macro']:.3f}",
        )

        self.stdout.write("\n  Matriz de confusión del modelo (filas = real):")
        clases = ("bajo_peso", "normal", "macrosomia")
        self.stdout.write("  " + " " * 12 + "".join(f"{c:>12}" for c in clases))
        for real in clases:
            fila = "".join(f"{conf['matriz'][real][p]:>12}" for p in clases)
            self.stdout.write(f"  {real:<12}{fila}")

        # ---- Importancia -------------------------------------------------
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\nQué variables pesan más (permutación, cuánto empeora el MAE)",
        ))
        importancia = ep.importancia_variables(marco, ganador)
        for f in importancia[:8]:
            barra = "#" * max(0, int(f["aumento_mae_g"] / 15))
            self.stdout.write(
                f"  {f['etiqueta']:<30} {f['aumento_mae_g']:>+7.0f} g  {barra}",
            )

        # ---- Guardar -----------------------------------------------------
        if options["simular"]:
            self.stdout.write(self.style.WARNING("\n(simulado: no se guardó nada)"))
            return

        # Antes esto era `if mae_ganador >= mae_hadlock`, y con 212 g frente a
        # 223 g habria guardado y desplegado un EMPATE como si fuera una
        # mejora. Ahora exige una mejora consistente en todas las particiones.
        if not pareado["mejora_significativa"] and not options["forzar"]:
            raise CommandError(
                "No se guarda: no hay evidencia de que el modelo mejore la "
                "fórmula que ya existía. Desplegarlo añadiría complejidad a "
                "cambio de nada. Usa --forzar si aun así quieres guardarlo "
                "(por ejemplo, para la demostración), sabiendo que es un empate.",
            )

        modelo, ms = ep.entrenar_final(marco, ganador)
        directorio = (
            Path(getattr(settings, "ML_MODELOS_DIR", settings.BASE_DIR / "ml_modelos"))
            / "peso_nacimiento" / options["version_modelo"]
        )
        ficha = {
            "nombre": "peso_nacimiento",
            "version": options["version_modelo"],
            "algoritmo": ganador,
            "descripcion": resultados[ganador].descripcion,
            "entrenado": datetime.now().isoformat(timespec="seconds"),
            "filas": info["filas"],
            "pacientes": info["pacientes"],
            "porcentaje_sintetico": info["sinteticas"] / info["filas"],
            "entrenado_con_datos_sinteticos": info["sinteticas"] == info["filas"],
            "tiempo_entrenamiento_ms": round(ms, 1),
            "comparativa": {k: r.resumen() for k, r in resultados.items()},
            "comparacion_pareada": pareado,
            "guardado_forzado": bool(options["forzar"]) and not pareado["mejora_significativa"],
            "clasificacion": conf,
            "clasificacion_hadlock": conf_hadlock,
            "importancia": importancia,
        }
        ep.guardar(directorio, modelo, ficha)
        self.stdout.write(self.style.SUCCESS(f"\nGuardado en {directorio}"))
        self.stdout.write(json.dumps(
            {"mae_g": round(mae_ganador), "mejora_vs_hadlock": f"{mejora:.0%}"},
            ensure_ascii=False,
        ))
