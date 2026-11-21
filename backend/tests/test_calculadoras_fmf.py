"""Tests de los endpoints de riesgo FMF y análisis de laboratorio.

Por qué existe este archivo
---------------------------
`calculadoras/services/calculador_riesgos_fmf.py` (543 líneas) implementa el
modelo bayesiano de la Fetal Medicine Foundation para riesgo de preeclampsia y
trisomías, y `ia_medica/services/ml_laboratorio_service.py` (481 líneas) el
análisis de hemograma, glucosa, función hepática y renal.

Ambos estaban escritos, probados a mano y **sin una sola referencia en todo el
proyecto**: ningún módulo los importaba, así que ninguna pantalla los usaba.
Mil líneas de lógica clínica que no llegaban a la médica.

Estos tests cubren los endpoints que los exponen. Cada uno declara el
resultado ESPERADO y lo compara con el OBTENIDO.
"""

import datetime

from rest_framework.test import APITestCase

from usuarios.models import Usuario


class _ConMedica(APITestCase):
    """Base: una médica autenticada, que es quien usa estas calculadoras."""

    def setUp(self):
        self.medica = Usuario.objects.create_user(
            email="dra.fmf@test.bo",
            nombre="Elena",
            apellido_paterno="Choque",
            password="clave-de-prueba-123",
            rol="medico",
        )
        self.client.force_authenticate(user=self.medica)


class RiesgoPreeclampsiaFMFTest(_ConMedica):
    """POST /api/calculadoras-avanzadas/fmf/preeclampsia/"""

    URL = "/api/calculadoras-avanzadas/fmf/preeclampsia/"

    def test_calcula_riesgo_con_factores_e_indica_aspirina(self):
        """ESPERADO: 200, con riesgo, clasificación y si toca aspirina.

        Una gestante de 35 años con hipertensión crónica y arterias uterinas
        alteradas es el caso donde la aspirina profiláctica cambia el
        desenlace. El sistema tiene que decirlo, no dejarlo al ojo clínico.
        """
        r = self.client.post(self.URL, {
            "edad_materna": 35, "peso_kg": 72, "talla_cm": 158, "semanas": 12,
            "hipertension_cronica": True,
            "pas_mmhg": 140, "pad_mmhg": 90, "utap_ip_promedio": 1.8,
        }, format="json")

        assert r.status_code == 200, f"Esperado 200, obtenido {r.status_code}: {r.data}"
        assert "riesgo_final" in r.data
        assert "clasificacion_riesgo" in r.data
        assert r.data["requiere_aspirina"] is True, (
            "Con hipertensión crónica y Doppler alterado debe recomendar aspirina."
        )
        assert r.data["factores_riesgo_presentes"]

    def test_gestante_sin_factores_tiene_riesgo_menor(self):
        """ESPERADO: menor riesgo que el caso con factores.

        Comprueba que el modelo discrimina, no que devuelve siempre lo mismo.
        """
        sano = self.client.post(self.URL, {
            "edad_materna": 25, "peso_kg": 58, "talla_cm": 162, "semanas": 12,
        }, format="json").data
        riesgo = self.client.post(self.URL, {
            "edad_materna": 42, "peso_kg": 95, "talla_cm": 155, "semanas": 12,
            "hipertension_cronica": True, "diabetes_tipo2": True,
            "historia_preeclampsia": True,
        }, format="json").data

        assert sano["riesgo_final"] < riesgo["riesgo_final"], (
            f"Sin factores {sano['riesgo_final']} deberia ser menor que "
            f"con factores {riesgo['riesgo_final']}"
        )

    def test_faltan_datos_obligatorios_da_400(self):
        """ESPERADO: 400 con el detalle, no un 500."""
        r = self.client.post(self.URL, {"edad_materna": 30}, format="json")
        assert r.status_code == 400
        assert "error" in r.data or "detail" in r.data

    def test_recepcion_no_puede_calcular_riesgo(self):
        """ESPERADO: 403 — es una decisión clínica, no administrativa."""
        recepcion = Usuario.objects.create_user(
            email="recep.fmf@test.bo", nombre="Ana", apellido_paterno="Flores",
            password="clave-de-prueba-123", rol="recepcion",
        )
        self.client.force_authenticate(user=recepcion)
        r = self.client.post(self.URL, {
            "edad_materna": 30, "peso_kg": 60, "talla_cm": 160, "semanas": 12,
        }, format="json")
        assert r.status_code == 403


class RiesgoTrisomiasFMFTest(_ConMedica):
    """POST /api/calculadoras-avanzadas/fmf/trisomias/"""

    URL = "/api/calculadoras-avanzadas/fmf/trisomias/"

    def test_calcula_las_tres_trisomias(self):
        """ESPERADO: 200 con riesgo para T21, T18 y T13."""
        r = self.client.post(self.URL, {
            "edad_materna": 38, "semanas": 12, "translucencia_nucal_mm": 3.2,
            "papp_a_mom": 0.4, "free_bhcg_mom": 2.5, "hueso_nasal_presente": False,
        }, format="json")

        assert r.status_code == 200, f"Obtenido {r.status_code}: {r.data}"
        for clave in ("riesgo_t21_ajustado", "riesgo_t18_ajustado", "riesgo_t13_ajustado"):
            assert clave in r.data, f"Falta {clave}"
        assert "clasificacion_t21" in r.data

    def test_la_edad_materna_sube_el_riesgo_basal(self):
        """ESPERADO: a mayor edad, mayor riesgo basal de T21.

        Es la relación mejor establecida en cribado prenatal; si no se
        cumpliera, el modelo estaria mal cableado.
        """
        joven = self.client.post(self.URL, {
            "edad_materna": 25, "semanas": 12, "translucencia_nucal_mm": 1.5,
        }, format="json").data
        mayor = self.client.post(self.URL, {
            "edad_materna": 42, "semanas": 12, "translucencia_nucal_mm": 1.5,
        }, format="json").data

        assert mayor["riesgo_t21_basal"] > joven["riesgo_t21_basal"]

    def test_translucencia_nucal_obligatoria(self):
        """ESPERADO: 400 — sin TN no hay cribado del primer trimestre."""
        r = self.client.post(self.URL, {"edad_materna": 30, "semanas": 12}, format="json")
        assert r.status_code == 400


class AnalisisLaboratorioMLTest(_ConMedica):
    """POST /api/ia/laboratorio/analizar/"""

    URL = "/api/ia/laboratorio/analizar/"

    def test_detecta_anemia_y_trombocitopenia(self):
        """ESPERADO: 200 y alertas por los valores alterados.

        Hemoglobina 9.2 con plaquetas 95.000 en una gestante es un cuadro que
        no puede pasar desapercibido.
        """
        r = self.client.post(self.URL, {
            "hemograma": {
                "hemoglobina": 9.2, "hematocrito": 28,
                "plaquetas": 95000, "leucocitos": 14000,
            },
        }, format="json")

        assert r.status_code == 200, f"Obtenido {r.status_code}: {r.data}"
        assert r.data["hemograma"]["valores_anormales"], (
            "No detectó ningún valor anormal con hemoglobina 9.2 y plaquetas 95.000"
        )
        assert r.data["hemograma"]["alertas"]

    def test_valores_normales_no_generan_alerta(self):
        """ESPERADO: sin alertas — un falso positivo aquí genera ansiedad."""
        r = self.client.post(self.URL, {
            "hemograma": {
                "hemoglobina": 12.5, "hematocrito": 38,
                "plaquetas": 250000, "leucocitos": 8000,
            },
        }, format="json")

        assert r.status_code == 200
        assert not r.data["hemograma"]["alertas"]

    def test_sin_datos_da_400(self):
        """ESPERADO: 400 — no hay nada que analizar."""
        r = self.client.post(self.URL, {}, format="json")
        assert r.status_code == 400

    def test_analiza_varios_paneles_a_la_vez(self):
        """ESPERADO: 200 con un bloque por cada panel enviado."""
        r = self.client.post(self.URL, {
            "hemograma": {"hemoglobina": 11.0, "plaquetas": 200000},
            "glucosa": {"glucosa_ayunas": 105},
        }, format="json")

        assert r.status_code == 200
        assert "hemograma" in r.data
        assert "glucosa" in r.data


class QuedanRegistradosEnAuditoriaTest(_ConMedica):
    """Un cálculo de riesgo es una decisión clínica: tiene que quedar."""

    def test_el_calculo_de_preeclampsia_se_audita(self):
        """ESPERADO: 1 registro nuevo con quién lo calculó."""
        from auditoria.models import RegistroAuditoria

        antes = RegistroAuditoria.objects.filter(modulo="CalculadoraFMF").count()
        self.client.post("/api/calculadoras-avanzadas/fmf/preeclampsia/", {
            "edad_materna": 35, "peso_kg": 72, "talla_cm": 158, "semanas": 12,
        }, format="json")
        despues = RegistroAuditoria.objects.filter(modulo="CalculadoraFMF")

        assert despues.count() == antes + 1
        assert despues.order_by("-id").first().usuario_id == self.medica.id


def _fecha_prueba():
    """Fecha fija para que los tests no dependan del día en que corran."""
    return datetime.date(2026, 1, 15)
