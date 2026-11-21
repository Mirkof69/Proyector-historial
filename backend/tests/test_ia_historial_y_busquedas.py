"""IA médica: cada análisis queda en el historial de su paciente y se puede reabrir.

Regresión (07/11/2026): «Ver resultado» de un análisis guardado no mostraba la
imagen ni las medidas, y el listado cargaba por cada fila la imagen del análisis
(cerca de 1 MB en base64). Alertas y notificaciones solo buscaban en las primeras
200: una paciente con alertas fuera de esas 200 no aparecía.
"""
import datetime

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from ia_medica.models import AnalisisCNN, ImagenEcografica
from ia_medica.services.result_mapping import defaults_analisis_medido
from notificaciones.models import Notificacion
from pacientes.models import Paciente
from reportes.models import AlertaMedica
from usuarios.models import Usuario

INFORME = {
    "version_flujo": "2.1",
    "plano": {"plano": "cerebro fetal", "confianza": 0.91, "probabilidades": {"cerebro fetal": 0.91, "otro": 0.09}},
    "medidas": {"circunferencia_cefalica_mm": 251.0, "margen_hc_mm": 4.9},
    "estructuras_vistas": {"Cráneo": True, "Cerebelo": False},
    "anomalias_cerebrales": {"aplicable": True, "alarma_anomalia": True, "probabilidad_anomalia": 0.8, "umbral": 0.5,
                             "familia_sospechada": "fosa_posterior", "familia_sospechada_nombre": "Fosa posterior"},
    "hallazgos": ["Posible anomalía de fosa posterior."],
    "avisos": ["Revise el corte."],
    "requiere_revision": False,
    "superposicion_png": "QUJD",
    "modelos_usados": [{"archivo": "plano.pt", "dataset": "FETAL_PLANES_DB", "sha256": "abc123456789"}],
    "informe_texto": "Plano detectado: cerebro fetal.",
    "tiempo_ms": 800,
}


def _paciente(nombre, apellido, ci):
    return Paciente.objects.create(nombre=nombre, apellido_paterno=apellido, ci=ci, genero="femenino",
                                   fecha_nacimiento=datetime.date(1993, 4, 5))


class HistorialDeAnalisisTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.ia@hospital.bo", nombre="Ana", apellido_paterno="Ia",
                                                 password="clave-segura-123", rol="medico")
        cls.paciente = _paciente("Rosa", "Quispe", "7700101")
        cls.otra = _paciente("Elena", "Mamani", "7700102")
        cls.imagen = cls._imagen(cls.paciente, "a.png")
        cls.analisis = AnalisisCNN.objects.create(imagen=cls.imagen, **defaults_analisis_medido(INFORME, cls.medico))
        cls.sin_analizar = cls._imagen(cls.otra, "b.png")

    @classmethod
    def _imagen(cls, paciente, nombre):
        return ImagenEcografica.objects.create(paciente=paciente, subida_por=cls.medico, imagen=f"pruebas/{nombre}",
                                               nombre_original=nombre, tipo_imagen="eco_2d", semana_gestacional=22)

    def setUp(self):
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.medico)

    def test_el_informe_guardado_trae_imagen_medidas_y_paciente(self):
        r = self.cliente.get(f"/api/ia/imagenes/{self.imagen.id}/informe/")
        self.assertEqual(r.status_code, 200)
        d = r.data
        self.assertEqual(d["plano"]["plano"], "cerebro fetal")
        self.assertEqual(d["plano"]["probabilidades"]["otro"], 0.09)
        self.assertEqual(d["medidas"]["circunferencia_cefalica_mm"], 251.0)
        self.assertEqual(d["estructuras_vistas"], {"Cráneo": True, "Cerebelo": False})
        self.assertEqual(d["superposicion_url"], "data:image/png;base64,QUJD")
        self.assertTrue(d["anomalias_cerebrales"]["alarma_anomalia"])
        self.assertEqual(d["anomalias_cerebrales"]["umbral"], 0.5)
        self.assertEqual(d["hallazgos"], ["Posible anomalía de fosa posterior."])
        self.assertEqual(d["avisos"], ["Revise el corte."])
        self.assertEqual(d["paciente"]["id"], self.paciente.id)
        self.assertIn("Quispe", d["paciente"]["nombre"])
        self.assertEqual(d["paciente"]["ci"], "7700101")
        self.assertEqual(d["semana_gestacional"], 22)
        self.assertEqual(d["resultado"], self.analisis.resultado)
        self.assertTrue(d["realizado_por"])

    def test_analisis_anterior_sin_detalle_en_la_sugerencia_tambien_abre(self):
        AnalisisCNN.objects.filter(pk=self.analisis.pk).update(sugerencia_diagnostica={"informe": "viejo"})
        d = self.cliente.get(f"/api/ia/imagenes/{self.imagen.id}/informe/").data
        self.assertTrue(d["anomalias_cerebrales"]["alarma_anomalia"])
        self.assertEqual(d["hallazgos"], ["Posible anomalía de fosa posterior."])

    def test_imagen_sin_analizar_responde_404_con_motivo(self):
        r = self.cliente.get(f"/api/ia/imagenes/{self.sin_analizar.id}/informe/")
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", r.data)

    def test_el_listado_no_carga_la_imagen_del_analisis(self):
        with CaptureQueriesContext(connection) as consultas:
            r = self.cliente.get("/api/ia/imagenes/")
        self.assertEqual(r.status_code, 200)
        self.assertFalse([q for q in consultas if "mapa_calor" in q["sql"]])
        fila = next(f for f in r.data["results"] if f["id"] == self.imagen.id)
        self.assertEqual(fila["analisis_resultado"]["plano"], "cerebro fetal")
        self.assertTrue(fila["analisis_resultado"]["fecha"])

    def test_la_imagen_subida_toma_la_semana_del_embarazo_activo(self):
        from embarazos.models import Embarazo
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        import io

        Embarazo.objects.create(paciente=self.otra, numero_gesta=1, numero_para=0, tipo_embarazo="simple",
                                riesgo_embarazo="bajo", medico_responsable=self.medico,
                                fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=24))
        buffer = io.BytesIO()
        Image.new("L", (32, 32)).save(buffer, "PNG")
        archivo = SimpleUploadedFile("eco.png", buffer.getvalue(), content_type="image/png")
        r = self.cliente.post("/api/ia/imagenes/", {"imagen": archivo, "paciente": self.otra.id, "tipo_imagen": "eco_2d"},
                              format="multipart")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["semana_gestacional"], 24)

    def test_filtros_por_paciente_resultado_y_busqueda(self):
        def ids(**q):
            return {f["id"] for f in self.cliente.get("/api/ia/imagenes/", q).data["results"]}

        self.assertEqual(ids(paciente_id=self.otra.id), {self.sin_analizar.id})
        self.assertEqual(ids(resultado=self.analisis.resultado), {self.imagen.id})
        self.assertEqual(ids(analizadas="1"), {self.imagen.id})
        self.assertEqual(ids(search="Quispe"), {self.imagen.id})
        self.assertEqual(ids(search="7700102"), {self.sin_analizar.id})
        r = self.cliente.get("/api/ia/imagenes/", {"page_size": 1})
        self.assertEqual((r.data["count"], len(r.data["results"])), (2, 1))


class BusquedaEnTodosLosRegistrosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.bus@hospital.bo", nombre="Bea", apellido_paterno="Bus",
                                                 password="clave-segura-123", rol="medico")
        cls.buscada = _paciente("Julia", "Condori", "7700201")
        cls.otra = _paciente("Marta", "Flores", "7700202")
        cls.alerta = AlertaMedica.objects.create(titulo="Hipertensión", descripcion="PA alta", tipo="clinica",
                                                 prioridad="alta", paciente=cls.buscada)
        cls.ajena = AlertaMedica.objects.create(titulo="Otra", descripcion="x", tipo="clinica", prioridad="media",
                                                paciente=cls.otra)
        AlertaMedica.objects.filter(pk=cls.ajena.pk).update(
            fecha_creacion=timezone.now() - datetime.timedelta(days=40))

    def setUp(self):
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.medico)

    def _alertas(self, **q):
        return {f["id"] for f in self.cliente.get("/api/reportes/alertas-medicas/", q).data["results"]}

    def test_alertas_se_buscan_por_nombre_y_ci_de_la_paciente(self):
        self.assertEqual(self._alertas(search="Condori"), {self.alerta.id})
        self.assertEqual(self._alertas(search="7700201"), {self.alerta.id})
        self.assertEqual(self._alertas(search="Hipertensión"), {self.alerta.id})

    def test_alertas_se_filtran_por_fecha_en_el_servidor(self):
        desde = (timezone.localdate() - datetime.timedelta(days=5)).isoformat()
        self.assertEqual(self._alertas(fecha_desde=desde), {self.alerta.id})
        hasta = (timezone.localdate() - datetime.timedelta(days=30)).isoformat()
        self.assertEqual(self._alertas(fecha_hasta=hasta), {self.ajena.id})

    def test_notificaciones_buscan_filtran_y_paginan_en_el_servidor(self):
        for i in range(3):
            Notificacion.objects.create(usuario=self.medico, tipo="alerta_informacion", titulo=f"Aviso {i}",
                                        mensaje="Control de Julia Condori")
        vieja = Notificacion.objects.create(usuario=self.medico, tipo="alerta_informacion", titulo="Aviso viejo",
                                            mensaje="Otra paciente", leida=True)
        Notificacion.objects.filter(pk=vieja.pk).update(fecha_creacion=timezone.now() - datetime.timedelta(days=40))
        base = "/api/notificaciones/"
        self.assertEqual(self.cliente.get(base, {"search": "Condori"}).data["count"], 3)
        self.assertEqual(self.cliente.get(base, {"leida": "true"}).data["count"], 1)
        r = self.cliente.get(base, {"page_size": 2})
        self.assertEqual((r.data["count"], len(r.data["results"])), (4, 2))
        hasta = (timezone.localdate() - datetime.timedelta(days=30)).isoformat()
        self.assertEqual(self.cliente.get(base, {"fecha_hasta": hasta}).data["count"], 1)

    def test_antecedentes_buscan_por_paciente_y_paginan_en_el_servidor(self):
        from antecedentes.models import AntecedenteGinecoObstetrico, AntecedentePatologico

        AntecedenteGinecoObstetrico.objects.create(paciente=self.buscada, gestas=2, partos=1, abortos=0, cesareas=0)
        AntecedenteGinecoObstetrico.objects.create(paciente=self.otra, gestas=0, partos=0, abortos=0, cesareas=0)
        AntecedentePatologico.objects.create(paciente=self.buscada, tipo="personal")
        base = "/api/antecedentes/"
        r = self.cliente.get(f"{base}gineco-obstetricos/", {"search": "Condori"}).data
        self.assertEqual((r["count"], r["results"][0]["paciente"]), (1, self.buscada.id))
        self.assertEqual(self.cliente.get(f"{base}patologicos/", {"search": "7700201"}).data["count"], 1)
        self.assertEqual(self.cliente.get(f"{base}patologicos/", {"search": "Flores"}).data["count"], 0)
        self.assertEqual(len(self.cliente.get(f"{base}gineco-obstetricos/", {"page_size": 1}).data["results"]), 1)
        resumen = self.cliente.get(f"{base}gineco-obstetricos/resumen/").data
        self.assertEqual(resumen, {"total": 2, "con_gestas": 1, "con_partos": 1, "con_abortos": 0})
