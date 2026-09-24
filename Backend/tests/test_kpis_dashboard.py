"""Los KPIs del tablero salen de los datos reales y con la forma del frontend.

Fallo que previene: /reportes/dashboard-kpis/ devolvía la tabla de
definiciones cargadas a mano y las pantallas de Reportes y KPIs, que esperan
{kpis, tendencias, alertas}, se veían vacías.
"""
import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario

HOY = timezone.localdate()


class KpisDashboardTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(email="adm.kpi@test.bo", nombre="A", apellido_paterno="K",
                                                password="clave-segura-123", rol="administrador")
        for i, riesgo in enumerate(("alto", "bajo")):
            p = Paciente.objects.create(nombre="Kpi", apellido_paterno=f"P{i}", apellido_materno="X",
                                        fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino",
                                        ci=f"79330{i:02d}")
            Embarazo.objects.create(paciente=p, numero_gesta=1, riesgo_embarazo=riesgo,
                                    fecha_ultima_menstruacion=HOY - datetime.timedelta(weeks=20))

    def test_forma_y_valores(self):
        c = APIClient()
        c.force_authenticate(self.admin)
        r = c.get("/api/reportes/dashboard-kpis/resumen/")
        self.assertEqual(r.status_code, 200, r.content[:300])
        d = r.json()
        self.assertEqual(set(d), {"fecha_actualizacion", "kpis", "tendencias", "alertas"})
        self.assertEqual(d["kpis"]["pacientes_activos"]["valor"], 2)
        self.assertEqual(d["kpis"]["embarazos_activos"]["valor"], 2)
        self.assertEqual(d["alertas"]["embarazos_alto_riesgo"], 1)
        # 20 semanas y ningún control en 4 semanas: los dos están atrasados
        self.assertEqual(d["alertas"]["controles_atrasados"], 2)
        self.assertEqual(len(d["tendencias"]["partos_ultimo_anio"]), 12)
        self.assertEqual(len(d["tendencias"]["controles_ultimo_trimestre"]), 13)
        self.assertEqual(len(d["tendencias"]["citas_ultima_semana"]), 7)

    def test_la_lista_de_definiciones_sigue_funcionando(self):
        c = APIClient()
        c.force_authenticate(self.admin)
        self.assertEqual(c.get("/api/reportes/dashboard-kpis/").status_code, 200)
