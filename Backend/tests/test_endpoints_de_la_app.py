"""Los endpoints que la aplicación llama de verdad devuelven LISTAS filtradas.

Regresión de una familia de bugs que se repitió tres veces en la ronda de
carga: el frontend pedía `/vacunas/`, `/laboratorios/` o `/citas/`, que son la
RAÍZ del router de DRF. Esa raíz responde **200** con el índice de rutas
(`{"tipos-vacunas": "...", "registros": "..."}`), así que el código hacía
`data.results || data`, obtenía un objeto en vez de un array y dejaba la
sección vacía. Sin error, sin 404, sin nada en consola: tabs en blanco.

Estos tests fijan el contrato de las rutas REALES que consume la app, y que
lo devuelto sea una lista filtrada por paciente — no un objeto, no la lista
completa.
"""
import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from laboratorio.models import ExamenLaboratorio, TipoExamen
from pacientes.models import Paciente
from usuarios.models import Usuario
from vacunas.models import RegistroVacuna, TipoVacuna


def _lista(respuesta):
    """Extrae la lista de resultados como lo hace el frontend."""
    datos = respuesta.data
    if isinstance(datos, dict) and "results" in datos:
        return datos["results"]
    return datos


class EndpointsDeListaClinicaTest(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_superuser(
            email="app@test.bo", nombre="App", apellido_paterno="Test",
            password="clave12345",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)

        self.ana = Paciente.objects.create(
            id_clinico="PAC-APP-1", nombre="Ana", apellido_paterno="Torrez",
            fecha_nacimiento=datetime.date(1993, 2, 2), genero="femenino", ci="95000001",
        )
        self.otra = Paciente.objects.create(
            id_clinico="PAC-APP-2", nombre="Bea", apellido_paterno="Mamani",
            fecha_nacimiento=datetime.date(1991, 6, 6), genero="femenino", ci="95000002",
        )

        self.tipo_vacuna = TipoVacuna.objects.create(
            nombre="Antitetánica (dT)", dosis_requeridas=2, intervalo_dosis_dias=28,
            edad_minima_aplicacion=12, obligatoria_embarazo=True, activo=True,
        )
        for paciente in (self.ana, self.otra):
            RegistroVacuna.objects.create(
                paciente=paciente, tipo_vacuna=self.tipo_vacuna,
                fecha_aplicacion=datetime.datetime(2026, 5, 1, 10, 0),
                numero_dosis=1, via_administracion="intramuscular",
                aplicado_por=self.usuario,
            )

        self.tipo_examen = TipoExamen.objects.create(
            nombre="Hemograma completo", codigo="HEM-T1", categoria="hematologia",
            tiempo_resultado=24, precio=35, activo=True,
        )
        for paciente in (self.ana, self.otra):
            ExamenLaboratorio.objects.create(
                paciente=paciente, tipo_examen=self.tipo_examen,
                medico_solicitante=self.usuario,
                fecha_solicitud=datetime.datetime(2026, 5, 2, 9, 0),
                estado="completado", prioridad="normal",
            )

    # ── Vacunas ───────────────────────────────────────────────────────────
    def test_registros_de_vacunas_devuelve_lista_filtrada(self):
        respuesta = self.client.get("/api/vacunas/registros/", {"paciente": self.ana.id})
        self.assertEqual(respuesta.status_code, 200)
        datos = _lista(respuesta)
        self.assertIsInstance(datos, list, "debe ser una LISTA, no el índice del router")
        self.assertEqual(len(datos), 1, "solo las dosis de esa paciente")

    def test_catalogo_de_tipos_de_vacuna_responde(self):
        """La ruta es `tipos-vacunas`; el servicio pedía `/tipos` y daba 404
        que el `catch` se tragaba devolviendo lista vacía: el catálogo nunca
        cargaba y el error pasaba desapercibido."""
        respuesta = self.client.get("/api/vacunas/tipos-vacunas/")
        self.assertEqual(respuesta.status_code, 200)
        nombres = [t["nombre"] for t in _lista(respuesta)]
        self.assertIn("Antitetánica (dT)", nombres)

    # ── Laboratorio ───────────────────────────────────────────────────────
    def test_examenes_de_laboratorio_devuelve_lista_filtrada(self):
        respuesta = self.client.get(
            "/api/laboratorios/examenes/", {"paciente": self.ana.id},
        )
        self.assertEqual(respuesta.status_code, 200)
        datos = _lista(respuesta)
        self.assertIsInstance(datos, list)
        self.assertEqual(len(datos), 1)

    def test_examen_expone_el_nombre_del_tipo_no_solo_el_id(self):
        """`tipo_examen` viaja como PK numérica. La historia clínica mostraba
        "1" en la columna Examen y reventaba al hacer `.toLowerCase()` sobre
        un número, tumbando TODA la vista al branch de error."""
        respuesta = self.client.get(
            "/api/laboratorios/examenes/", {"paciente": self.ana.id},
        )
        examen = _lista(respuesta)[0]
        self.assertIn("tipo_examen_nombre", examen)
        self.assertEqual(examen["tipo_examen_nombre"], "Hemograma completo")

    # ── La raíz del router NO es una lista ────────────────────────────────
    def test_la_raiz_del_router_no_devuelve_una_lista(self):
        """Deja constancia de POR QUÉ hay que usar las rutas hijas: la raíz
        responde 200 con un objeto, y por eso el bug era invisible."""
        for raiz in ("/api/vacunas/", "/api/laboratorios/"):
            respuesta = self.client.get(raiz)
            self.assertEqual(respuesta.status_code, 200, raiz)
            self.assertNotIsInstance(
                _lista(respuesta), list,
                f"{raiz} es el índice del router; la app debe usar la ruta hija",
            )
