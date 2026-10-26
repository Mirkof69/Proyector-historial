"""«Generar reporte PDF» produce de verdad el archivo y se puede descargar.

Antes la solicitud quedaba «pendiente» para siempre (nada la procesaba) y no
había tipos de reporte configurados (reportes/services/generador_reportes.py).
"""
import datetime
import tempfile

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from pacientes.models import Paciente
from reportes.models import TipoReporte
from usuarios.models import Usuario

URL = "/api/reportes/reportes-generados/"


@override_settings(REPORTES_DIR=tempfile.mkdtemp(prefix="reportes_test_"))
class GenerarReporteTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.rep@test.bo", nombre="Ana", apellido_paterno="Rep",
                                                 password="clave-segura-123", rol="medico")
        p = Paciente.objects.create(nombre="Ema", apellido_paterno="Rep", ci="7744551",
                                    fecha_nacimiento=datetime.date(1994, 2, 2), genero="femenino")
        Embarazo.objects.create(paciente=p, numero_gesta=1, tipo_embarazo="simple",
                                fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=20))

    def setUp(self):
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.medico)

    def test_hay_ocho_tipos_configurados(self):
        self.assertEqual(TipoReporte.objects.filter(codigo__startswith="RPT-", activo=True).count(), 8)

    def test_cada_tipo_se_genera_y_descarga(self):
        hoy = timezone.localdate()
        for tipo in TipoReporte.objects.filter(codigo__startswith="RPT-"):
            for formato in ("pd", "excel", "csv"):
                r = self.cliente.post(f"{URL}solicitar/", {
                    "tipo_reporte": tipo.pk, "formato": formato,
                    "fecha_inicio": str(hoy - datetime.timedelta(days=365)), "fecha_fin": str(hoy),
                }, format="json")
                self.assertEqual(r.status_code, 201, r.content[:300])
                self.assertEqual(r.json()["estado"], "completado", f"{tipo.codigo} {formato}: {r.json().get('mensaje_error')}")
                descarga = self.cliente.get(f"{URL}{r.json()['id']}/descargar/")
                self.assertEqual(descarga.status_code, 200, f"{tipo.codigo} {formato}")
                contenido = b"".join(descarga.streaming_content)
                if formato == "pd":
                    self.assertTrue(contenido.startswith(b"%PDF"), tipo.codigo)
