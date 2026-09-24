"""Recalcula el peso fetal estimado de las biometrías ya guardadas.

    python manage.py recalcular_peso_fetal --simular    # ver que haria
    python manage.py recalcular_peso_fetal              # aplicarlo

Por qué hace falta
------------------
La fórmula de Hadlock estaba rota: consumía milímetros con coeficientes
calibrados en centímetros. Ya está arreglada, pero **los valores que escribió
mientras estuvo rota siguen en la base**, y `BiometriaFetal.save()` no los toca
porque solo rellena el campo cuando está vacío.

Medido sobre las 280 biometrías del tenant `clinica_demo` el 23 de septiembre
de 2026:

    | guardado  | biometría real          | lo correcto |
    |-----------|-------------------------|-------------|
    | 13.118 g  | DBP 20,6 mm (~12 sem)   |      93 g   |
    |    382 g  | DBP 35,0 mm             |     183 g   |
    |      0 g  | DBP 77,8 mm (~31 sem)   |   1.569 g   |

Un feto de doce semanas registrado con trece kilos, y 174 registros en cero.
Esos números se muestran hoy en la ficha de la ecografía, en dos pestañas de la
historia clínica, en el panel y en el PDF.

Empezar SIEMPRE por `--simular`: imprime cuántos cambiarían y cuánto, sin tocar
nada. Conviene mirar la lista antes de reescribir datos clínicos.

Qué NO hace
-----------
No toca el peso que escribió una persona. Solo reescribe los valores que puede
demostrar que salieron de la fórmula rota, es decir, los que coinciden
exactamente con lo que ésta devolvía. Si el ecografista midió el peso a mano,
ese dato manda sobre cualquier fórmula.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from ecografias.models import BiometriaFetal
from ecografias.peso_fetal import hadlock_1985_4p, percentil_peso_fetal

#: Tamaño del lote para `bulk_update`. Ni tan pequeño que haga mil viajes ni
#: tan grande que mantenga una transacción abierta demasiado tiempo.
TAMANO_LOTE = 500


def _formula_rota(dbp, cc, ca, lf) -> int | None:
    """Lo que devolvía la fórmula ANTES del arreglo, para reconocer sus huellas.

    Se conserva a propósito, aunque duela: es la única forma de distinguir un
    peso escrito por una persona de uno que escribió el bug. Sin esto habría
    que reescribirlos todos, incluidos los medidos a mano.
    """
    if None in (dbp, cc, ca, lf):
        return None
    dbp, cc, ca, lf = float(dbp), float(cc), float(ca), float(lf)
    log_peso = (
        1.3596
        - 0.00386 * ca * lf
        + 0.0064 * cc
        + 0.00061 * dbp * ca
        + 0.0425 * ca
        + 0.174 * lf
    )
    try:
        return int(10**log_peso)
    except (OverflowError, ValueError):
        return None


class Command(BaseCommand):
    help = "Recalcula el peso fetal de las biometrías afectadas por el bug de unidades."

    def add_arguments(self, parser):
        parser.add_argument(
            "--simular", action="store_true",
            help="Muestra qué cambiaría sin modificar nada.",
        )
        parser.add_argument(
            "--tenant", default=None,
            help="Esquema concreto. Por defecto, todos los de clientes.",
        )

    def handle(self, *args, **options):
        simular = options["simular"]

        for esquema, contexto in self._esquemas(options["tenant"]):
            with contexto:
                self._procesar(esquema, simular)

        if simular:
            self.stdout.write(self.style.WARNING(
                "\n(simulado: no se modificó nada. Quita --simular para aplicarlo)",
            ))
        else:
            self.stdout.write(self.style.SUCCESS("\nRecálculo terminado."))

    def _esquemas(self, uno):
        """Los esquemas a recorrer, con su gestor de contexto.

        Devuelve `nullcontext()` cuando django_tenants no está activo: la suite
        de tests corre sobre SQLite de esquema único (ver `settings.py`), y ahí
        `schema_context()` lanzaría.
        """
        from contextlib import nullcontext

        try:
            from django_tenants.utils import get_tenant_model, schema_context
        except ImportError:
            return [("(esquema único)", nullcontext())]

        from django.conf import settings

        if "django_tenants" not in settings.INSTALLED_APPS:
            return [("(esquema único)", nullcontext())]

        nombres = [uno] if uno else [
            t.schema_name
            for t in get_tenant_model().objects.exclude(schema_name="public")
        ]
        return [(n, schema_context(n)) for n in nombres]

    def _procesar(self, esquema, simular):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{esquema}"))

        biometrias = BiometriaFetal.objects.select_related("ecografia").all()
        total = biometrias.count()
        if not total:
            self.stdout.write("  sin biometrías")
            return

        a_corregir, intocables, sin_medidas, ya_bien = [], 0, 0, 0
        ejemplos = []

        for b in biometrias:
            medidas = (
                b.diametro_biparietal, b.circunferencia_cefalica,
                b.circunferencia_abdominal, b.longitud_femur,
            )
            correcto = hadlock_1985_4p(*medidas)
            if correcto is None:
                sin_medidas += 1
                continue

            guardado = b.peso_fetal_estimado
            if guardado == correcto:
                ya_bien += 1
                continue

            # ¿El valor guardado es huella de la fórmula rota, o lo puso alguien?
            roto = _formula_rota(*medidas)
            if guardado is not None and guardado != roto:
                intocables += 1
                continue

            if len(ejemplos) < 5:
                ejemplos.append((guardado, correcto, b.diametro_biparietal))
            b.peso_fetal_estimado = correcto
            b.percentil_peso = percentil_peso_fetal(
                correcto,
                getattr(b.ecografia, "edad_gestacional_semanas", None),
            )
            a_corregir.append(b)

        self.stdout.write(f"  biometrías                        {total:>6}")
        self.stdout.write(f"  ya correctas                      {ya_bien:>6}")
        self.stdout.write(f"  sin las 4 medidas                 {sin_medidas:>6}")
        self.stdout.write(f"  peso puesto a mano (no se toca)   {intocables:>6}")
        self.stdout.write(self.style.WARNING(
            f"  a corregir                        {len(a_corregir):>6}",
        ))

        if ejemplos:
            self.stdout.write("\n  ejemplos:")
            for guardado, correcto, dbp in ejemplos:
                self.stdout.write(
                    f"    {str(guardado):>8} g  ->  {correcto:>6} g   (DBP {dbp} mm)",
                )

        if not simular and a_corregir:
            with transaction.atomic():
                for i in range(0, len(a_corregir), TAMANO_LOTE):
                    BiometriaFetal.objects.bulk_update(
                        a_corregir[i:i + TAMANO_LOTE],
                        ["peso_fetal_estimado", "percentil_peso"],
                    )
            self.stdout.write(self.style.SUCCESS(f"  corregidas {len(a_corregir)}"))
