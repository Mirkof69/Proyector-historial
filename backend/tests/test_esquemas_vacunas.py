"""Un esquema de vacunación es de una paciente y una vacuna.

Fallo que previene: cada registro se evaluaba suelto, así que la dosis 1 de
un esquema ya completado (dosis 1 y 2 aplicadas) salía como «incompleta».
"""
import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from pacientes.models import Paciente
from usuarios.models import Usuario
from vacunas.models import RegistroVacuna, TipoVacuna


class EsquemasVacunasTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(email="adm.vac@test.bo", nombre="A", apellido_paterno="V",
                                                password="clave-segura-123", rol="administrador")
        tipo = TipoVacuna.objects.create(nombre="dT prueba", dosis_requeridas=2, intervalo_dosis_dias=30)
        from django.utils import timezone

        hoy = timezone.now()
        for ci, dosis in (("7966601", (1, 2)), ("7966602", (1,))):
            p = Paciente.objects.create(nombre="Vac", apellido_paterno=ci, apellido_materno="X",
                                        fecha_nacimiento=datetime.date(1992, 1, 1), genero="femenino", ci=ci)
            for d in dosis:
                RegistroVacuna.objects.create(paciente=p, tipo_vacuna=tipo, numero_dosis=d,
                                              fecha_aplicacion=hoy - datetime.timedelta(days=40 * (3 - d)))

    def test_solo_el_esquema_sin_terminar_es_incompleto(self):
        c = APIClient()
        c.force_authenticate(self.admin)
        r = c.get("/api/vacunas/registros/esquemas_incompletos/")
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertEqual(r.json()["total_esquemas_incompletos"], 1)
        stats = c.get("/api/vacunas/registros/estadisticas/").json()["resumen"]
        self.assertEqual((stats["esquemas_completos"], stats["esquemas_incompletos"]), (1, 1))
