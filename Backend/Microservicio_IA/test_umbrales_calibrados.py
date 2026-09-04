"""Tests de los umbrales de decision de la red neuronal.

Por que existe este archivo
---------------------------
Los umbrales de `CLASS_THRESHOLDS` deciden si una patologia se reporta o no.
Un umbral demasiado bajo llena la consulta de falsas alarmas y el medico deja
de creerle al sistema; uno demasiado alto pierde casos reales. Ninguno de los
dos errores es visible desde el codigo: solo se ven midiendo.

Medido el 2026-09-04 sobre `datasets_pathology_v2` (calibrado en `valid/`,
reportado en `test/`, 2.911 imagenes):

    clase                umbral viejo -> nuevo    F1 viejo -> nuevo
    polihidramnios              0.18 -> 0.49        0.268 -> 0.430
    macrosomia_fetal            0.22 -> 0.37        0.305 -> 0.429

Con 0.18, `polihidramnios` acertaba 15 de cada 100 alertas. Su AUC es 0.959
—la senal SI esta— asi que era puro problema de umbral.

`macrosomia_fetal` es distinto: AUC 0.838, la mas baja de las 14 clases. Ahi
el limite es el modelo, no el umbral. Recalibrar lo mejora de 0.305 a 0.429 y
no mas; llegar a valores clinicamente comodos necesita mas datos de
entrenamiento.

Estos tests no vuelven a medir el modelo (necesitaria GPU y el dataset): fijan
que los valores calibrados no se pierdan en un refactor, y que ninguno quede
en un rango absurdo.
"""

import pytest

from app.config import CLASS_THRESHOLDS, PATHOLOGY_THRESHOLD

#: Valores calibrados el 2026-09-04. Cambiarlos exige volver a medir.
CALIBRADOS = {
    "polihidramnios": 0.49,
    "macrosomia_fetal": 0.37,
}


class TestUmbralesCalibrados:
    """Los umbrales medidos deben mantenerse."""

    @pytest.mark.parametrize(("clase", "esperado"), CALIBRADOS.items())
    def test_conserva_el_umbral_calibrado(self, clase, esperado):
        """ESPERADO: el valor medido en la calibracion de 2026-09-04."""
        obtenido = CLASS_THRESHOLDS[clase]
        assert obtenido == pytest.approx(esperado), (
            f"{clase}: esperado {esperado}, obtenido {obtenido}. "
            f"Si se cambia a proposito, hay que volver a medir F1 sobre "
            f"datasets_pathology_v2/test y actualizar este test."
        )

    def test_ningun_umbral_de_patologia_esta_en_un_extremo_absurdo(self):
        """ESPERADO: las patologias, entre 0.05 y 0.95.

        Por debajo de 0.05 la clase dispara con cualquier cosa; por encima de
        0.95 practicamente no dispara nunca. Ambos extremos convierten al
        detector en ruido o en silencio.

        `no_ecografia` queda fuera a proposito: no es una patologia sino la
        clase de RECHAZO, la que dice "esto no es una ecografia obstetrica".
        Ahi un umbral altisimo es lo correcto — solo se rechaza una imagen
        cuando la certeza es casi total, porque negarse a analizar una
        ecografia valida es peor que analizar una imagen dudosa.
        """
        for clase, umbral in CLASS_THRESHOLDS.items():
            if clase == "no_ecografia":
                continue
            assert 0.05 <= umbral <= 0.95, (
                f"{clase} tiene umbral {umbral}, fuera del rango util."
            )

    def test_la_clase_de_rechazo_es_deliberadamente_estricta(self):
        """ESPERADO: >= 0.95 — rechazar una ecografia valida es el peor error."""
        assert CLASS_THRESHOLDS.get("no_ecografia", 0) >= 0.95

    def test_estan_las_14_clases_con_umbral_propio(self):
        """ESPERADO: cada patologia tiene su umbral, no el generico."""
        esperadas = {
            "hidrocefalia", "anencefalia", "espina_bifida", "labio_leporino",
            "atresia_duodenal", "oligohidramnios", "polihidramnios",
            "restriccion_crecimiento", "macrosomia_fetal", "placenta_previa",
            "preeclampsia_signos", "muerte_fetal", "embarazo_multiple",
        }
        faltan = esperadas - set(CLASS_THRESHOLDS)
        assert not faltan, f"Sin umbral propio (usarian el generico): {faltan}"

    def test_el_umbral_generico_sigue_siendo_conservador(self):
        """ESPERADO: >= 0.5 — quien no tiene umbral propio no debe ser laxo."""
        assert PATHOLOGY_THRESHOLD >= 0.5


class TestUmbralesPorEntorno:
    """Los umbrales se pueden ajustar por variable de entorno sin tocar codigo."""

    def test_se_puede_sobrescribir_por_entorno(self, monkeypatch):
        """ESPERADO: THRESHOLD_<CLASE> manda sobre el valor por defecto.

        Permite a una clinica ajustar su punto de operacion —mas sensible o
        mas especifico— sin modificar el codigo ni redesplegar.
        """
        import importlib

        monkeypatch.setenv("THRESHOLD_POLIHIDRAMNIOS", "0.33")
        from app import config

        importlib.reload(config)
        try:
            assert config.CLASS_THRESHOLDS["polihidramnios"] == pytest.approx(0.33)
        finally:
            monkeypatch.delenv("THRESHOLD_POLIHIDRAMNIOS", raising=False)
            importlib.reload(config)
