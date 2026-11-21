"""La pantalla de ecografías pagina, filtra, resume y exporta EN EL SERVIDOR.

Antes descargaba TODAS las ecografías (una petición por cada 200) y filtraba
y contaba trimestres en el navegador. Tenía además dos botones «Exportar
Excel»: uno armaba el archivo en el navegador con todo, ignorando los
filtros, y el otro usaba una vista hecha a mano que no quedaba auditada.
"""
import datetime
from io import BytesIO

from django.test import TestCase
from django.utils import timezone
from openpyxl import load_workbook
from rest_framework.test import APIClient

from auditoria.models import RegistroAuditoria
from ecografias.models import Ecografia
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario

URL = "/api/ecografias/"


class ListadoEcografiasServidorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="eco.srv@test.bo", nombre="Elsa", apellido_paterno="Eco",
                                                 password="clave-segura-123", rol="medico")
        hoy = timezone.localdate()
        cls.hoy = hoy
        rosa = Paciente.objects.create(nombre="Rosa", apellido_paterno="Quispe", apellido_materno="Mamani",
                                       fecha_nacimiento=datetime.date(1995, 5, 5), genero="femenino", ci="7821101")
        luz = Paciente.objects.create(nombre="Luz", apellido_paterno="Condori", apellido_materno="Apaza",
                                      fecha_nacimiento=datetime.date(1993, 3, 3), genero="femenino", ci="7821102")
        emb_rosa = Embarazo.objects.create(paciente=rosa, numero_gesta=1, numero_para=0, numero_abortos=0,
                                           numero_cesareas=0, fecha_ultima_menstruacion=hoy - datetime.timedelta(weeks=30))
        emb_luz = Embarazo.objects.create(paciente=luz, numero_gesta=1, numero_para=0, numero_abortos=0,
                                          numero_cesareas=0, fecha_ultima_menstruacion=hoy - datetime.timedelta(weeks=10))
        base = {"medico": cls.medico, "indicacion": "control_rutina", "diagnostico": "Normal"}
        # 205 ecografías de Rosa en el 2.º trimestre (más que el tope de 200 por página)
        Ecografia.objects.bulk_create([
            Ecografia(paciente=rosa, embarazo=emb_rosa, fecha_ecografia=hoy - datetime.timedelta(days=10 + i % 50),
                      tipo_ecografia="segundo_trimestre", edad_gestacional_semanas=20, **base)
            for i in range(205)
        ])
        # Luz: una de 1.er trimestre hace 3 días y una de 3.er trimestre hoy.
        Ecografia.objects.create(paciente=luz, embarazo=emb_luz, fecha_ecografia=hoy - datetime.timedelta(days=3),
                                 tipo_ecografia="primer_trimestre", edad_gestacional_semanas=13, **base)
        Ecografia.objects.create(paciente=luz, embarazo=emb_luz, fecha_ecografia=hoy,
                                 tipo_ecografia="doppler", edad_gestacional_semanas=28,
                                 vitalidad_fetal=False, medico=cls.medico, indicacion="control_rutina",
                                 diagnostico="Sin actividad cardiaca")

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.medico)

    def _contar(self, **q):
        return self.c.get(URL, {"page_size": 1, **q}).json()["count"]

    def test_pagina_en_el_servidor_con_el_total_real(self):
        """ESPERADO: 207 en total aunque pase del tope de 200, y solo 10 filas."""
        r = self.c.get(URL, {"page_size": 10}).json()
        self.assertEqual(r["count"], 207)
        self.assertEqual(len(r["results"]), 10)

    def test_paginas_sin_repetidos(self):
        """ESPERADO: recorrer todas las páginas da 207 ids distintos (orden estable con -id)."""
        ids = []
        for pagina in range(1, 4):
            ids += [e["id"] for e in self.c.get(URL, {"page_size": 100, "page": pagina}).json()["results"]]
        self.assertEqual(len(ids), 207)
        self.assertEqual(len(set(ids)), 207)

    def test_filtros_de_la_pantalla(self):
        self.assertEqual(self._contar(tipo_ecografia="primer_trimestre"), 1)
        # ESPERADO: el rango es por fecha local, inclusive en los dos extremos.
        self.assertEqual(self._contar(fecha_ecografia__gte=self.hoy - datetime.timedelta(days=3),
                                      fecha_ecografia__lte=self.hoy), 2)
        self.assertEqual(self._contar(search="condori"), 2)
        self.assertEqual(self._contar(search="quispe"), 205)
        # La búsqueda también mira el diagnóstico (texto en claro).
        self.assertEqual(self._contar(search="actividad cardiaca"), 1)

    def test_fecha_mal_escrita_da_400_en_vez_de_devolver_todo(self):
        self.assertEqual(self.c.get(URL, {"fecha_ecografia__gte": "ayer"}).status_code, 400)

    def test_resumen_cuenta_todo_con_los_mismos_filtros(self):
        r = self.c.get(f"{URL}resumen/").json()
        self.assertEqual(r["total"], 207)
        self.assertEqual(r["primer_trimestre"], 1)   # 13 semanas = 1.er trimestre
        self.assertEqual(r["segundo_trimestre"], 205)
        self.assertEqual(r["tercer_trimestre"], 1)   # 28 semanas = 3.er trimestre
        self.assertEqual(r["sin_vitalidad"], 1)
        filtrado = self.c.get(f"{URL}resumen/", {"search": "condori"}).json()
        self.assertEqual(filtrado["total"], 2)
        self.assertEqual(filtrado["segundo_trimestre"], 0)

    def test_excel_respeta_filtros_y_queda_auditado(self):
        r = self.c.get(f"{URL}exportar-excel/", {"search": "condori"})
        self.assertEqual(r.status_code, 200)
        filas = list(load_workbook(BytesIO(r.content)).active.iter_rows(values_only=True))
        self.assertEqual(filas[0][0], "Fecha")
        self.assertEqual(len(filas), 3, filas)  # encabezado + 2 de Luz
        self.assertIn("Doppler", filas[1])      # etiqueta, no el código
        self.assertTrue(RegistroAuditoria.objects.filter(accion="EXPORTAR", modulo="ecografias").exists())
