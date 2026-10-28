"""completar_demo reparte las fechas que la carga masiva dejó en un solo día.

seed_carga ponía el último control de todos los embarazos en curso el día de la
carga y los exámenes de laboratorio también (auto_now_add): el Panel mostraba
un único punto. Ver pacientes/management/commands/completar_demo.py.
"""
import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from controles.models import ControlPrenatal
from embarazos.models import Embarazo
from laboratorio.models import ExamenLaboratorio, TipoExamen
from pacientes.management.commands import completar_demo
from pacientes.models import Paciente


class RepartoDeFechasDeCargaTest(TestCase):
    def setUp(self):
        hoy = timezone.localdate()
        self.paciente = Paciente.objects.create(nombre="Ca", apellido_paterno="Rga", apellido_materno="X",
                                                fecha_nacimiento=datetime.date(1995, 5, 5), genero="femenino",
                                                ci="7866601")
        # Id fijo para que el atraso determinista ((id * 7919) % 28) no sea 0.
        self.embarazo = Embarazo.objects.create(id=5, paciente=self.paciente, numero_gesta=1, estado="activo",
                                                fecha_ultima_menstruacion=hoy - datetime.timedelta(weeks=20),
                                                notas="[SEED-CARGA] completo")
        self.controles = [
            ControlPrenatal.objects.create(embarazo=self.embarazo, paciente=self.paciente, numero_control=n + 1,
                                           fecha_control=hoy - datetime.timedelta(weeks=4 * (1 - n)),
                                           semanas_gestacion=16 + 4 * n, peso_actual=60, talla=158,
                                           presion_arterial_sistolica=110, presion_arterial_diastolica=70)
            for n in range(2)
        ]
        tipo = TipoExamen.objects.create(nombre="Rep", codigo="REP1", categoria="hematologia", tiempo_resultado=1)
        self.examen = ExamenLaboratorio.objects.create(paciente=self.paciente, tipo_examen=tipo,
                                                       control_prenatal=self.controles[0], estado="completado",
                                                       fecha_resultado=timezone.now())

    def _correr(self):
        cmd = completar_demo.Command()
        with patch.object(completar_demo, "UMBRAL_DIA_DE_CARGA", 1):
            return cmd._repartir_embarazos_de_carga(), cmd._fechas_de_laboratorio()

    def test_mueve_todo_el_embarazo_junto_y_una_sola_vez(self):
        fum_antes = self.embarazo.fecha_ultima_menstruacion
        self._correr()
        self.embarazo.refresh_from_db()
        atraso = (fum_antes - self.embarazo.fecha_ultima_menstruacion).days
        self.assertEqual(atraso, (5 * 7919) % 28)
        for c in self.controles:
            antes = c.fecha_control
            c.refresh_from_db()
            # La edad gestacional de cada control sigue siendo la misma.
            self.assertEqual((antes - c.fecha_control).days, atraso)
        self.assertIn("[fechas-repartidas]", self.embarazo.notas)

        r, _ = self._correr()
        self.assertEqual(r["embarazos_de_carga_repartidos"], 0)

    def test_el_examen_cae_en_la_fecha_de_su_control(self):
        self._correr()
        self.examen.refresh_from_db()
        self.controles[0].refresh_from_db()
        self.assertEqual(timezone.localtime(self.examen.fecha_solicitud).date(), self.controles[0].fecha_control)
        self.assertGreaterEqual(self.examen.fecha_resultado, self.examen.fecha_solicitud)
