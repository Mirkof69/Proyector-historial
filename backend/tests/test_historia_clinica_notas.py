"""Notas de evolución y tratamientos que se registran desde la Historia Clínica.

Regresión (21/11/2026): la Historia Clínica no guardaba la nota ni el tratamiento (solo los mostraba hasta recargar)
y el listado de notas no traía examen físico, plan ni indicaciones, así que la pestaña SOAP salía incompleta.
"""
from datetime import date

from django.utils import timezone
from rest_framework.test import APITestCase

from pacientes.models import Paciente
from usuarios.models import Usuario


class NotasDesdeLaHistoriaClinicaTest(APITestCase):
    def setUp(self):
        self.paciente = Paciente.objects.create(
            id_clinico="PAC-HC-NOTA", nombre="Lucía", apellido_paterno="Mamani",
            fecha_nacimiento=date(1995, 3, 3), genero="femenino", ci="7700001",
        )
        self.medico = Usuario.objects.create_user(
            email="medico-hc@notas.test", nombre="Ana", apellido_paterno="Rojas",
            password="Clave-de-prueba-123!", rol="medico",
        )
        self.client.force_authenticate(self.medico)

    def _crear(self, **campos):
        datos = {"paciente": self.paciente.id, "medico": self.medico.id, "fecha_consulta": timezone.now().isoformat(),
                 "tipo_consulta": "control_prenatal", "motivo_consulta": "Cefalea leve",
                 "examen_fisico": "PA 118/76, sin edemas", "diagnosticos": "Embarazo de bajo riesgo",
                 "plan_tratamiento": "Control en 4 semanas", **campos}
        return self.client.post("/api/notas-evolucion/", datos, format="json")

    def test_la_nota_soap_se_guarda_y_vuelve_completa_en_el_listado(self):
        r = self._crear(indicaciones="Hidratación")
        self.assertEqual(r.status_code, 201, r.content)
        fila = self.client.get(f"/api/notas-evolucion/?paciente={self.paciente.id}").json()["results"][0]
        for campo, valor in (("motivo_consulta", "Cefalea leve"), ("examen_fisico", "PA 118/76, sin edemas"),
                             ("diagnosticos", "Embarazo de bajo riesgo"), ("plan_tratamiento", "Control en 4 semanas"),
                             ("indicaciones", "Hidratación"), ("medico", self.medico.id)):
            with self.subTest(campo=campo):
                self.assertEqual(fila[campo], valor)

    def test_la_prescripcion_se_guarda_con_el_formato_que_lee_la_pestana_tratamientos(self):
        plan = "Medicamento: Sulfato ferroso | Dosis: 300 mg | Frecuencia: cada 24 h | Duración: 30 días"
        r = self._crear(tipo_consulta="seguimiento", motivo_consulta="Prescripción: Sulfato ferroso",
                        examen_fisico="Registro de prescripción (sin examen físico en esta nota)",
                        diagnosticos="Prescripción de Sulfato ferroso", plan_tratamiento=plan)
        self.assertEqual(r.status_code, 201, r.content)
        fila = self.client.get(f"/api/notas-evolucion/?paciente={self.paciente.id}").json()["results"][0]
        self.assertEqual(fila["plan_tratamiento"], plan)

    def test_una_nota_sin_motivo_no_se_guarda(self):
        r = self._crear(motivo_consulta="")
        self.assertEqual(r.status_code, 400)
