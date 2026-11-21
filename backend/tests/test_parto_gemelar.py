"""Un parto múltiple registra a todos los recién nacidos.

Fallo que previene: el formulario y el alta solo admitían un recién nacido;
en un parto de gemelos el segundo bebé no quedaba registrado.
"""
import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from pacientes.models import Paciente
from partos.models import Parto, RecienNacido
from usuarios.models import Usuario


class PartoGemelarTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.gem@test.bo", nombre="M", apellido_paterno="G",
                                                 password="clave-segura-123", rol="medico")
        p = Paciente.objects.create(nombre="Gem", apellido_paterno="Elar", apellido_materno="X", ci="7911222",
                                    fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino")
        cls.embarazo = Embarazo.objects.create(paciente=p, numero_gesta=1, tipo_embarazo="gemelar",
                                               fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=37))

    def _parto(self, segundo_peso):
        c = APIClient()
        c.force_authenticate(self.medico)
        return c.post("/api/partos/", {
            "embarazo": self.embarazo.id, "tipo_parto": "vaginal_espontaneo", "fecha_parto": timezone.now().isoformat(),
            "paciente": self.embarazo.paciente_id, "edad_gestacional_parto": "37+0", "parto_finalizado": True,
            "sexo_bebe": "femenino", "peso_bebe": 2450, "talla_bebe": 46, "apgar_1min": 8, "apgar_5min": 9,
            "otros_recien_nacidos": [{"sexo": "masculino", "peso_nacimiento": segundo_peso, "talla_nacimiento": 45,
                                      "apgar_1_minuto": 7, "apgar_5_minutos": 9}],
        }, format="json")

    def test_se_registran_los_dos_gemelos(self):
        r = self._parto(2300)
        self.assertEqual(r.status_code, 201, r.content[:300])
        rns = RecienNacido.objects.filter(parto_id=r.json()["id"]).order_by("numero_gemelo")
        self.assertEqual([(x.numero_gemelo, x.sexo, x.peso_nacimiento) for x in rns],
                         [(1, "femenino", 2450), (2, "masculino", 2300)])

    def test_un_gemelo_invalido_no_deja_un_parto_a_medias(self):
        antes = Parto.objects.count()
        try:
            r = self._parto(50)  # 50 g: físicamente imposible (validador 300-6000)
            codigo = r.status_code
        except Exception:
            codigo = 500
        self.assertNotEqual(codigo, 201)
        self.assertEqual(Parto.objects.count(), antes)
