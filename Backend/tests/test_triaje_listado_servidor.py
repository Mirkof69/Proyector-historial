"""La pantalla de triaje pagina, filtra, resume y exporta EN EL SERVIDOR.

Antes pedía la lista una vez (el servidor cortaba en 200) y filtraba y
contaba en el navegador. Además el formulario pedía la PRIORIDAD (campo
obligatorio) y la pantalla filtraba por prioridad y estado, pero el modelo
no tenía ninguno de los dos: DRF descartaba la prioridad sin avisar, las
tarjetas «Pendientes / Completados / Urgentes» daban 0 y «Completar» no
hacía nada.
"""
import datetime
from decimal import Decimal
from io import BytesIO

from django.test import TestCase
from django.utils import timezone
from openpyxl import load_workbook
from rest_framework.test import APIClient

from auditoria.models import RegistroAuditoria
from pacientes.models import Paciente
from triaje.models import TriajeEnfermeria
from usuarios.models import Usuario

URL = "/api/triaje/triajes/"

SIGNOS = {"peso_kg": Decimal("62.0"), "talla_cm": Decimal("158.0"), "presion_sistolica": 110,
          "presion_diastolica": 70, "temperatura": Decimal("36.6"), "frecuencia_cardiaca": 80,
          "frecuencia_respiratoria": 16, "motivo_visita": "Control prenatal"}


class ListadoTriajeServidorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.enfermera = Usuario.objects.create_user(email="tri.srv@test.bo", nombre="Tania", apellido_paterno="Tri",
                                                    password="clave-segura-123", rol="enfermera")
        cls.rosa = Paciente.objects.create(nombre="Rosa", apellido_paterno="Quispe", apellido_materno="Mamani",
                                           fecha_nacimiento=datetime.date(1995, 5, 5), genero="femenino", ci="7841101")
        luz = Paciente.objects.create(nombre="Luz", apellido_paterno="Condori", apellido_materno="Apaza",
                                      fecha_nacimiento=datetime.date(1993, 3, 3), genero="femenino", ci="7841102")
        # 205 triajes completados de Rosa (más que el tope de 200 por página)
        TriajeEnfermeria.objects.bulk_create([
            TriajeEnfermeria(paciente=cls.rosa, enfermera=cls.enfermera, prioridad="normal", estado="completado",
                             **SIGNOS)
            for _ in range(205)
        ])
        # Luz: uno urgente pendiente con PA alta y otro bajo pendiente.
        cls.urgente = TriajeEnfermeria.objects.create(paciente=luz, enfermera=cls.enfermera, prioridad="urgente",
                                                      **{**SIGNOS, "presion_sistolica": 150,
                                                         "motivo_visita": "Cefalea intensa"})
        TriajeEnfermeria.objects.create(paciente=luz, enfermera=cls.enfermera, prioridad="bajo", **SIGNOS)

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.enfermera)

    def _contar(self, **q):
        return self.c.get(URL, {"page_size": 1, **q}).json()["count"]

    def test_pagina_en_el_servidor_con_el_total_real(self):
        r = self.c.get(URL, {"page_size": 10}).json()
        self.assertEqual(r["count"], 207)
        self.assertEqual(len(r["results"]), 10)
        # ESPERADO: la tabla muestra el ID clínico bajo el nombre.
        self.assertIn("id_clinico", r["results"][0]["paciente_info"])

    def test_la_prioridad_del_formulario_se_guarda(self):
        """ESPERADO: 201 sin mandar `enfermera` (como hace el formulario; antes
        daba 400 «enfermera requerido») y la prioridad guardada (antes DRF la
        descartaba en silencio)."""
        r = self.c.post(URL, {"paciente": self.rosa.id, "prioridad": "alto", **{k: str(v) for k, v in SIGNOS.items()}})
        self.assertEqual(r.status_code, 201, r.content)
        t = TriajeEnfermeria.objects.get(pk=r.json()["id"])
        self.assertEqual(t.prioridad, "alto")
        self.assertEqual(t.estado, "pendiente")  # un triaje nuevo espera al médico

    def test_completar_con_patch(self):
        r = self.c.patch(f"{URL}{self.urgente.id}/", {"estado": "completado"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.urgente.refresh_from_db()
        self.assertEqual(self.urgente.estado, "completado")

    def test_filtros_de_la_pantalla(self):
        self.assertEqual(self._contar(estado="pendiente"), 2)
        self.assertEqual(self._contar(prioridad="urgente"), 1)
        self.assertEqual(self._contar(search="condori"), 2)
        self.assertEqual(self._contar(search="cefalea"), 1)
        hoy = timezone.localtime()
        self.assertEqual(self._contar(fecha_registro__gte=hoy.replace(hour=0, minute=0, second=0).isoformat(),
                                      fecha_registro__lte=hoy.replace(hour=23, minute=59, second=59).isoformat()), 207)
        ayer = hoy - datetime.timedelta(days=1)
        self.assertEqual(self._contar(fecha_registro__lte=ayer.isoformat()), 0)

    def test_resumen_cuenta_todo_con_los_mismos_filtros(self):
        r = self.c.get(f"{URL}resumen/").json()
        self.assertEqual(r["total"], 207)
        self.assertEqual(r["pendiente"], 2)
        self.assertEqual(r["completado"], 205)
        self.assertEqual(r["urgente"], 1)
        self.assertEqual(r["presion_alta"], 1)
        filtrado = self.c.get(f"{URL}resumen/", {"search": "condori"}).json()
        self.assertEqual(filtrado["total"], 2)
        self.assertEqual(filtrado["completado"], 0)

    def test_excel_respeta_filtros_y_queda_auditado(self):
        r = self.c.get(f"{URL}exportar-excel/", {"prioridad": "urgente"})
        self.assertEqual(r.status_code, 200)
        filas = list(load_workbook(BytesIO(r.content)).active.iter_rows(values_only=True))
        self.assertEqual(len(filas), 2, filas)  # encabezado + el urgente
        self.assertIn("Urgente", filas[1])
        self.assertIn("150/70 mmHg", filas[1])
        self.assertTrue(RegistroAuditoria.objects.filter(accion="EXPORTAR", modulo="triaje").exists())
