"""«Evolución del embarazo» se unifica en «Notas de evolución» sin perder datos.

La evolución era una línea de tiempo escrita a mano que duplicaba controles y
ecografías ya registrados; su texto clínico pasa a ser una nota de evolución.
"""
import datetime
import importlib

from django.apps import apps
from django.test import TestCase
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from evoluciones.models import EvolucionEmbarazo
from notas_evolucion.models import NotaEvolucion
from pacientes.models import Paciente
from usuarios.models import Usuario

migracion = importlib.import_module("notas_evolucion.migrations.0004_importar_evoluciones_embarazo")


class UnificarEvolucionesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(email="adm.evo@test.bo", nombre="Ada", apellido_paterno="Evo",
                                                password="clave-segura-123", rol="administrador")
        cls.medico = Usuario.objects.create_user(email="med.evo@test.bo", nombre="Mar", apellido_paterno="Evo",
                                                 password="clave-segura-123", rol="medico")
        p = Paciente.objects.create(nombre="Eva", apellido_paterno="Luna", apellido_materno="Sol",
                                    fecha_nacimiento=datetime.date(1994, 2, 2), genero="femenino", ci="7922201")
        e = Embarazo.objects.create(paciente=p, fecha_ultima_menstruacion=datetime.date.today() - datetime.timedelta(weeks=20),
                                    numero_gesta=1, numero_para=0, numero_abortos=0)
        cls.ev_con_medico = EvolucionEmbarazo.objects.create(
            embarazo=e, paciente=p, fecha_evento=datetime.date(2026, 5, 10), tipo_evento="urgencia",
            descripcion="Dolor abdominal, se indica reposo.", medico=cls.medico)
        cls.ev_sin_medico = EvolucionEmbarazo.objects.create(
            embarazo=e, paciente=p, fecha_evento=datetime.date(2026, 6, 1), tipo_evento="ecografia",
            descripcion="Ecografía sin hallazgos.")

    def test_cada_evolucion_pasa_a_ser_una_nota_y_no_se_duplica(self):
        """ESPERADO: 2 notas con el texto original; repetir no crea más."""
        NotaEvolucion.objects.all().delete()
        migracion.importar(apps, None)
        migracion.importar(apps, None)
        notas = NotaEvolucion.objects.order_by("fecha_consulta")
        self.assertEqual(notas.count(), 2)
        urgencia, eco = notas
        self.assertEqual(urgencia.motivo_consulta, "Dolor abdominal, se indica reposo.")
        self.assertEqual(urgencia.tipo_consulta, "urgencia")
        self.assertEqual(urgencia.medico, self.medico)
        self.assertEqual(eco.tipo_consulta, "seguimiento")
        self.assertEqual(eco.medico, self.admin)            # sin médico: al administrador…
        self.assertIn("atribuida al administrador", eco.observaciones)  # …y queda dicho
        self.assertEqual(EvolucionEmbarazo.objects.count(), 2)  # no se borra nada

    def test_la_api_vieja_queda_de_solo_lectura(self):
        c = APIClient()
        c.force_authenticate(self.medico)
        self.assertEqual(c.get("/api/evoluciones/evoluciones/").status_code, 200)
        r = c.post("/api/evoluciones/evoluciones/", {"descripcion": "x"})
        self.assertEqual(r.status_code, 405)
