"""La pantalla de controles prenatales pagina, filtra, resume y exporta EN EL SERVIDOR.

Antes descargaba TODOS los controles, TODOS los embarazos y TODAS las
pacientes (una petición por cada 200 de cada uno) solo para mostrar nombres,
filtraba en el navegador y ofrecía «Mostrar TODOS» (10.000 filas de golpe).
El filtro «Con/Sin alertas» usaba `tiene_alertas`; el servidor tiene que
aplicar EXACTAMENTE el mismo criterio (`tiene_alertas_criticas`).
"""
import datetime
from decimal import Decimal
from io import BytesIO

from django.test import TestCase
from django.utils import timezone
from openpyxl import load_workbook
from rest_framework.test import APIClient

from auditoria.models import RegistroAuditoria
from controles.models import ControlPrenatal
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario

URL = "/api/controles/"


class ListadoControlesServidorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="ctl.srv@test.bo", nombre="Celia", apellido_paterno="Ctl",
                                                 password="clave-segura-123", rol="medico")
        hoy = timezone.localdate()
        cls.hoy = hoy
        rosa = Paciente.objects.create(nombre="Rosa", apellido_paterno="Quispe", apellido_materno="Mamani",
                                       fecha_nacimiento=datetime.date(1995, 5, 5), genero="femenino", ci="7831101")
        luz = Paciente.objects.create(nombre="Luz", apellido_paterno="Condori", apellido_materno="Apaza",
                                      fecha_nacimiento=datetime.date(1993, 3, 3), genero="femenino", ci="7831102")
        emb_rosa = Embarazo.objects.create(paciente=rosa, numero_gesta=1, numero_para=0, numero_abortos=0,
                                           numero_cesareas=0, fecha_ultima_menstruacion=hoy - datetime.timedelta(weeks=20))
        emb_luz = Embarazo.objects.create(paciente=luz, numero_gesta=1, numero_para=0, numero_abortos=0,
                                          numero_cesareas=0, fecha_ultima_menstruacion=hoy - datetime.timedelta(weeks=34))
        base = {"medico": cls.medico, "peso_actual": Decimal("65.0"), "talla": Decimal("160.0"),
                "presion_arterial_sistolica": 110, "presion_arterial_diastolica": 70}
        # 205 controles normales de Rosa, todos el mismo número y en pocas
        # fechas: obliga a que el orden tenga desempate para paginar bien.
        ControlPrenatal.objects.bulk_create([
            ControlPrenatal(embarazo=emb_rosa, paciente=rosa, numero_control=1, semanas_gestacion=20,
                            fecha_control=hoy - datetime.timedelta(days=10 + i % 5), **base)
            for i in range(205)
        ])
        luz_base = {**base, "embarazo": emb_luz, "paciente": luz, "semanas_gestacion": 34}
        # Hipertensión (alerta crítica)
        ControlPrenatal.objects.create(numero_control=1, fecha_control=hoy - datetime.timedelta(days=2),
                                       **{**luz_base, "presion_arterial_sistolica": 150})
        # Bradicardia fetal (alerta crítica)
        ControlPrenatal.objects.create(numero_control=2, fecha_control=hoy, frecuencia_cardiaca_fetal=100, **luz_base)
        # Proteinuria en trazas: NO es alerta crítica (sí lo sería con ?con_alertas=true)
        ControlPrenatal.objects.create(numero_control=3, fecha_control=hoy - datetime.timedelta(days=1),
                                       proteinuria="trazas", **luz_base)

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.medico)

    def _contar(self, **q):
        return self.c.get(URL, {"page_size": 1, **q}).json()["count"]

    def test_pagina_en_el_servidor_con_el_total_real(self):
        r = self.c.get(URL, {"page_size": 20}).json()
        self.assertEqual(r["count"], 208)
        self.assertEqual(len(r["results"]), 20)
        # ESPERADO: el nombre y el ID clínico vienen en la lista; la pantalla
        # ya no necesita bajar embarazos ni pacientes para mostrarlos.
        fila = r["results"][0]
        self.assertTrue(fila["paciente_nombre"])
        self.assertIn("id_clinico", fila)
        self.assertIn("fecha_ultima_menstruacion", fila["embarazo_info"])

    def test_paginas_sin_repetidos(self):
        ids = []
        for pagina in range(1, 4):
            ids += [c["id"] for c in self.c.get(URL, {"page_size": 100, "page": pagina}).json()["results"]]
        self.assertEqual(len(ids), 208)
        self.assertEqual(len(set(ids)), 208)

    def test_no_se_puede_pedir_mas_de_200_por_pagina(self):
        """«Mostrar TODOS» pedía 10.000: el servidor corta en 200."""
        r = self.c.get(URL, {"page_size": 10000}).json()
        self.assertEqual(len(r["results"]), 200)

    def test_alerta_critica_coincide_con_tiene_alertas(self):
        """ESPERADO: el filtro del servidor da lo mismo que `tiene_alertas` fila por fila."""
        con = self.c.get(URL, {"page_size": 200, "alerta_critica": "true"}).json()
        self.assertEqual(con["count"], 2)
        self.assertTrue(all(c["tiene_alertas"] for c in con["results"]))
        sin = self.c.get(URL, {"page_size": 200, "alerta_critica": "false"}).json()
        self.assertEqual(sin["count"], 206)
        self.assertFalse(any(c["tiene_alertas"] for c in sin["results"]))

    def test_filtros_de_la_pantalla(self):
        self.assertEqual(self._contar(search="condori"), 3)
        self.assertEqual(self._contar(fecha_control__gte=self.hoy - datetime.timedelta(days=2),
                                      fecha_control__lte=self.hoy), 3)
        self.assertEqual(self._contar(trimestre=2), 205)
        self.assertEqual(self._contar(trimestre=3), 3)
        self.assertEqual(self.c.get(URL, {"fecha_control__gte": "ayer"}).status_code, 400)

    def test_resumen_y_panel_de_alertas_con_los_mismos_filtros(self):
        r = self.c.get(f"{URL}resumen/").json()
        self.assertEqual(r["total"], 208)
        self.assertEqual(r["con_alertas"], 2)
        self.assertEqual(r["sin_alertas"], 206)
        # Las más recientes primero: hoy (FCF 100) y luego hace 2 días (PA 150).
        self.assertEqual([c["numero_control"] for c in r["alertas_recientes"]], [2, 1])
        filtrado = self.c.get(f"{URL}resumen/", {"search": "quispe"}).json()
        self.assertEqual(filtrado["total"], 205)
        self.assertEqual(filtrado["con_alertas"], 0)
        self.assertEqual(filtrado["alertas_recientes"], [])

    def test_excel_respeta_filtros_y_queda_auditado(self):
        r = self.c.get(f"{URL}exportar-excel/", {"search": "condori", "alerta_critica": "true"})
        self.assertEqual(r.status_code, 200)
        filas = list(load_workbook(BytesIO(r.content)).active.iter_rows(values_only=True))
        self.assertEqual(filas[0][0], "Fecha")
        self.assertEqual(len(filas), 3, filas)  # encabezado + 2 controles con alerta
        self.assertTrue(RegistroAuditoria.objects.filter(accion="EXPORTAR", modulo="controles_prenatales").exists())
