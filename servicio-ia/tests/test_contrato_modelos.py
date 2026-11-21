"""Contrato de GET /api/modelos con el catálogo de Django y la Guía de IA.

El backend (ia_medica/services/catalogo_modelos.py) redacta la «fiabilidad
medida» de cada red leyendo claves concretas de `metricas_prueba`. Si un
reentrenamiento cambia la forma del JSON, la guía mostraría «sin cifra» sin que
nada fallara. Esta prueba fija las claves que se leen, red por red.

Ejecutar (necesita las redes en modelos-ia/redes/):
    C:/Users/Miscar/AppData/Local/Programs/Python/Python312/python.exe -m pytest test_contrato_modelos.py -v
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)

#: red → rutas de claves (separadas por «.») que lee el catálogo de Django.
CLAVES = {
    "plano_anatomico_fetal_planes": ["exactitud", "imagenes_prueba", "madres_prueba", "cabezas_primer_trimestre_reconocidas"],
    "segmentacion_cabeza": ["prueba_externa_hc18.imagenes", "prueba_externa_hc18.hc_error_medio_mm",
                            "prueba_externa_hc18.dentro_de_5_por_ciento"],
    "segmentacion_torax": ["dice_prueba_medio", "indice_cardiotoracico_prueba.ict_areas_error_medio", "imagenes_prueba"],
    "segmentacion_abdomen": ["dice_prueba_medio", "marcadores_plano_abdominal.estomago.sensibilidad",
                             "imagenes_prueba", "pacientes_prueba"],
    "biometria_femur": ["prueba.fl.error_medio_mm", "prueba.fl.error_mediano_mm", "prueba.fl.dentro_de_5_por_ciento",
                        "imagenes_prueba", "pacientes_prueba"],
    "biometria_abdomen": ["prueba.ca.error_relativo_medio", "prueba.ca.error_mediano_mm",
                          "prueba.ca.dentro_de_5_por_ciento", "prueba.ca.imagenes"],
    "segmentacion_intraparto": ["angulo_progresion_prueba.aop_error_medio_grados", "angulo_progresion_prueba.imagenes",
                                "angulo_progresion_prueba.sensibilidad_aop_120",
                                "angulo_progresion_prueba.especificidad_aop_120"],
    "anomalias_cerebrales_fetales": ["externa_falsos_positivos.fp", "externa_falsos_positivos.n"],
    "circunferencia_cefalica_hc18": ["r2", "error_medio_mm", "imagenes_prueba", "madres_prueba"],
    "segmentacion_ovario": ["dice_prueba_medio", "lesion_ovarica_prueba.lesion_encontrada_iou_0_5",
                            "imagenes_prueba", "pacientes_prueba"],
    "clasificador_ovario": ["prueba.exactitud", "prueba.exactitud_ic95", "prueba.imagenes",
                            "prueba.malignidad.sensibilidad", "prueba.malignidad.casos_malignos",
                            "prueba.malignidad.especificidad"],
    "segmentacion_mioma": ["mioma_prueba.mioma_encontrado_iou_0_5", "imagenes_prueba", "pacientes_prueba"],
    "clasificador_ovario_pco": ["prueba.exactitud", "prueba.exactitud_ic95", "prueba.imagenes"],
}


def _leer(d, ruta):
    for parte in ruta.split("."):
        d = d[parte]
    return d


@pytest.fixture(scope="module")
def estado():
    r = cliente.get("/api/modelos")
    assert r.status_code == 200
    return r.json()


def test_el_catalogo_conoce_todas_las_redes_que_se_sirven(estado):
    """Una red nueva en el microservicio tiene que entrar también en el catálogo (y en la guía)."""
    assert set(estado) == set(CLAVES)


@pytest.mark.parametrize("red", sorted(CLAVES))
def test_cada_red_trae_las_metricas_que_lee_la_guia(estado, red):
    info = estado[red]
    if not info["disponible"]:
        pytest.skip(f"falta {red}.pth en modelos-ia/redes/")
    for ruta in CLAVES[red]:
        valor = _leer(info["metricas_prueba"], ruta)
        assert valor is not None, f"{red}: {ruta} vacío"
