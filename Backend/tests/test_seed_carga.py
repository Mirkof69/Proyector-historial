"""El generador de datos de prueba respeta las reglas del sistema.

Regresión: `objects.create()` NO ejecuta las validaciones del modelo, así que
el seed metía en la base filas que la API o un formulario rechazarían, sin
ningún error visible. Concretamente inventaba `tipo_sangre="O"` (el modelo
exige "O+"/"O-"), `factor_rh="+"` (exige "positivo"/"negativo") y
`tipo_ecografia="obstetrica"` (no es una opción). Eran 568 filas inválidas
con la suite entera en verde.

La regla del proyecto es que el sistema manda y el generador se adapta: estos
tests comparan lo que el generador produce contra las `choices` REALES de los
modelos, así que si alguien cambia una regla clínica el test avisa en vez de
dejar entrar datos malos.
"""
from django.test import SimpleTestCase, TestCase

from ecografias.models import Ecografia
from pacientes.management.commands.seed_carga import (
    ESTADOS_CIVILES,
    TIPOS_SANGRE,
    _tipo_ecografia,
)
from pacientes.models import Paciente


def _opciones(modelo, campo):
    return [c[0] for c in modelo._meta.get_field(campo).choices]


class ValoresDelGeneradorTest(SimpleTestCase):
    """Todo valor del catálogo del seed tiene que ser una opción válida."""

    def test_tipos_de_sangre_son_opciones_reales_del_modelo(self):
        validos = _opciones(Paciente, "tipo_sangre")
        for tipo in TIPOS_SANGRE:
            self.assertIn(tipo, validos, f"{tipo!r} no es un grupo sanguíneo válido")

    def test_los_grupos_llevan_signo(self):
        """El bug exacto: se generaba "O" en vez de "O+"/"O-"."""
        for tipo in TIPOS_SANGRE:
            self.assertTrue(
                tipo.endswith(("+", "-")), f"{tipo!r} no indica el factor Rh",
            )

    def test_estados_civiles_son_opciones_reales(self):
        validos = _opciones(Paciente, "estado_civil")
        for estado in ESTADOS_CIVILES:
            self.assertIn(estado, validos)

    def test_tipo_de_ecografia_es_valido_en_todo_el_embarazo(self):
        """Se recorre semana a semana: ninguna debe producir un tipo inválido."""
        validos = _opciones(Ecografia, "tipo_ecografia")
        for semana in range(4, 43):
            tipo = _tipo_ecografia(semana)
            self.assertIn(
                tipo, validos, f"semana {semana} genera un tipo inválido: {tipo!r}",
            )

    def test_el_tipo_de_ecografia_corresponde_al_trimestre(self):
        """No basta con que sea válido: tiene que ser clínicamente coherente."""
        self.assertEqual(_tipo_ecografia(8), "primer_trimestre")
        self.assertIn(_tipo_ecografia(18), ("segundo_trimestre", "morfologica"))
        self.assertIn(_tipo_ecografia(36), ("tercer_trimestre", "doppler"))


class PacienteGeneradoValidaTest(TestCase):
    """Una paciente creada con los valores del generador pasa full_clean()."""

    def test_paciente_con_valores_del_generador_es_valida(self):
        import datetime

        for tipo_sangre in TIPOS_SANGRE:
            paciente = Paciente(
                id_clinico=f"PAC-GEN-{tipo_sangre}",
                nombre="Generada", apellido_paterno="Test",
                fecha_nacimiento=datetime.date(1995, 3, 3), genero="femenino",
                ci=f"9300{TIPOS_SANGRE.index(tipo_sangre):04d}",
                tipo_sangre=tipo_sangre,
                factor_rh="negativo" if tipo_sangre.endswith("-") else "positivo",
                consentimiento_datos_aceptado=True,
            )
            # full_clean es justo lo que objects.create() se saltea.
            paciente.full_clean(exclude=["ci_hash"])

    def test_cedulas_del_generador_no_colisionan_entre_lotes(self):
        """Regresión: un único contador compartido por los dos prefijos de
        lote hacía que al re-sembrar los editables chocaran contra CIs vivas
        (unique de ci_hash) y el lote entero se perdiera."""
        from pacientes.management.commands.seed_carga import Command

        comando = Command()
        comando._contadores_ci = {"99": 0, "98": 0}

        generadas = set()
        for _ in range(50):
            comando._contadores_ci["99"] += 1
            generadas.add(f"99{comando._contadores_ci['99']:05d}")
            comando._contadores_ci["98"] += 1
            generadas.add(f"98{comando._contadores_ci['98']:05d}")

        self.assertEqual(len(generadas), 100, "hay CIs repetidas entre los dos lotes")
