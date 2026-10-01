"""Las predicciones de peso al nacer se cierran solas con el peso real.

Esperado vs obtenido. Fallo que previene: un modelo que solo se mide con
partos simulados para siempre; con esto acumula su error real en el hospital.
"""
import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from ecografias.models import Ecografia
from embarazos.models import Embarazo
from ia_medica.models import PrediccionPesoNacimiento
from pacientes.models import Paciente
from usuarios.models import Usuario


class CierrePrediccionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.cierre@test.bo", nombre="M", apellido_paterno="C",
                                                 password="clave-segura-123", rol="medico")

    def _embarazo(self, ci, tipo="simple"):
        p = Paciente.objects.create(nombre="Cierre", apellido_paterno="Peso", apellido_materno="X", ci=ci,
                                    fecha_nacimiento=datetime.date(1991, 1, 1), genero="femenino")
        emb = Embarazo.objects.create(paciente=p, numero_gesta=1, tipo_embarazo=tipo,
                                      fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=39))
        eco = Ecografia.objects.create(paciente=p, embarazo=emb, fecha_ecografia=timezone.localdate() - datetime.timedelta(days=5),
                                       edad_gestacional_semanas=38, edad_gestacional_dias=2)
        pred = PrediccionPesoNacimiento.objects.create(ecografia=eco, embarazo=emb, semanas_objetivo=39,
                                                       peso_previsto_g=3300, peso_hadlock_proyectado_g=3450)
        return emb, pred

    def _parto(self, emb, pesos):
        c = APIClient()
        c.force_authenticate(self.medico)
        datos = {"embarazo": emb.id, "paciente": emb.paciente_id, "tipo_parto": "vaginal_espontaneo",
                 "fecha_parto": timezone.now().isoformat(), "edad_gestacional_parto": "39+0", "parto_finalizado": True,
                 "sexo_bebe": "femenino", "peso_bebe": pesos[0], "talla_bebe": 50, "apgar_1min": 8, "apgar_5min": 9}
        if len(pesos) > 1:
            datos["otros_recien_nacidos"] = [{"sexo": "masculino", "peso_nacimiento": pesos[1], "talla_nacimiento": 47,
                                              "apgar_1_minuto": 8, "apgar_5_minutos": 9}]
        r = c.post("/api/partos/", datos, format="json")
        assert r.status_code == 201, r.content[:300]

    def test_se_cierra_con_el_peso_real(self):
        """ESPERADO: real 3200 g → error del modelo +100 g, de Hadlock +250 g."""
        emb, pred = self._embarazo("7811001")
        self._parto(emb, [3200])
        pred.refresh_from_db()
        self.assertEqual((pred.peso_real_g, pred.error_modelo_g, pred.error_hadlock_g), (3200, 100, 250))
        self.assertIsNotNone(pred.fecha_cierre)

    def test_gemelos_no_se_cierra(self):
        emb, pred = self._embarazo("7811002", tipo="gemelar")
        self._parto(emb, [2400, 2300])
        pred.refresh_from_db()
        self.assertIsNone(pred.peso_real_g)

    def test_desempeno_con_nacimientos_reales(self):
        emb, _ = self._embarazo("7811003")
        self._parto(emb, [3200])
        c = APIClient()
        c.force_authenticate(self.medico)
        d = c.get("/api/ia/prediccion-peso/desempeno/").json()
        self.assertEqual((d["cerradas_con_nacimiento"], d["error_medio_modelo_g"], d["error_medio_hadlock_g"]), (1, 100, 250))
