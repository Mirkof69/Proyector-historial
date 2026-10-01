"""Laboratorio, citas, vacunas, notas y auditoría se exportan a Excel.

Antes no tenían exportación (y el frontend de auditoría llamaba a
/auditoria/exportar-csv/, que no existía). El Excel respeta los filtros del
listado y cada exportación queda auditada.
"""
import datetime
from io import BytesIO

from django.test import TestCase
from openpyxl import load_workbook
from rest_framework.test import APIClient

from auditoria.models import RegistroAuditoria
from citas.models import Cita
from pacientes.models import Paciente
from usuarios.models import Usuario

RUTAS = [
    "/api/laboratorios/examenes/exportar-excel/",
    "/api/citas/citas/exportar-excel/",
    "/api/vacunas/registros/exportar-excel/",
    "/api/notas-evolucion/exportar-excel/",
    "/api/auditoria/exportar-excel/",
    "/api/partos/exportar-excel/",
]


class ExportacionesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(email="adm.exp@test.bo", nombre="Ana", apellido_paterno="Exp",
                                                password="clave-segura-123", rol="administrador")
        p = Paciente.objects.create(nombre="Paz", apellido_paterno="Excel", apellido_materno="X",
                                    fecha_nacimiento=datetime.date(1991, 1, 1), genero="femenino", ci="7955501")
        medico = Usuario.objects.create_user(email="med.exp@test.bo", nombre="Mia", apellido_paterno="Exp",
                                             password="clave-segura-123", rol="medico")
        manana = datetime.date.today() + datetime.timedelta(days=1)
        for hora, estado in ((9, "agendada"), (10, "cancelada")):
            Cita.objects.create(paciente=p, medico=medico, fecha_cita=manana,
                                hora_cita=datetime.time(hora, 0), estado=estado, motivo="Control")

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.admin)

    def test_todas_devuelven_un_xlsx(self):
        for ruta in RUTAS:
            r = self.c.get(ruta)
            self.assertEqual(r.status_code, 200, (ruta, r.content[:200]))
            self.assertTrue(r.content.startswith(b"PK"), ruta)

    def test_el_excel_respeta_el_filtro_y_usa_etiquetas(self):
        r = self.c.get("/api/citas/citas/exportar-excel/", {"estado": "cancelada"})
        hoja = load_workbook(BytesIO(r.content)).active
        filas = list(hoja.iter_rows(values_only=True))
        self.assertEqual(filas[0][0], "Fecha")
        self.assertEqual(len(filas), 2, filas)  # encabezado + 1 cita cancelada
        self.assertIn("Cancelada", filas[1])
        self.assertIn("Paz Excel X", " ".join(str(v) for v in filas[1]))

    def test_la_exportacion_queda_auditada(self):
        self.c.get("/api/citas/citas/exportar-excel/")
        self.assertTrue(RegistroAuditoria.objects.filter(accion="EXPORTAR", modulo="citas").exists())
