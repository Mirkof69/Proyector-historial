"""El modelo de peso al nacer: sus garantías de honestidad, fijadas.

Por qué existe este archivo
---------------------------
Un modelo de aprendizaje automático puede dar números plausibles y equivocados
sin lanzar ninguna excepción. Las cosas que se protegen aquí son justo ésas:
las que fallan en silencio.

Tres de ellas se descubrieron construyendo este modelo:

1. **Un generador que fabricaba fetos incoherentes.** Aplicaba la misma
   dispersión a las medidas y al peso, cuando el peso crece con el cubo de las
   medidas. Hadlock salía con un error de 598 g —peor que predecir siempre la
   mediana— y el modelo lineal «ganaba por un 71%» sobre todo porque aprendía
   a deshacer ese error. Corregido, Hadlock baja a 223 g y la «ventaja» del
   modelo se reduce a 11 g.

2. **Un rival de paja.** Comparar el modelo con Hadlock SIN proyectar daba un
   error de 1.473 g para la fórmula, porque ésta estima el peso el día de la
   ecografía, no al nacer. Cualquier modelo habría parecido un prodigio.

3. **Una regla de decisión que desplegaba empates.** «Gana quien tenga menos
   error medio» declaraba ganador a un modelo con 11 g de ventaja y ±14 g de
   ruido. Ahora se compara partición a partición.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import datetime
import math

import numpy as np
from django.test import SimpleTestCase, TestCase

from ia_medica.ml.caracteristicas_peso import (
    BIOMETRIA_OBLIGATORIA,
    CARACTERISTICAS,
    COLUMNAS_DATASET,
    COMPARADOR,
    construir_vector,
)
from ia_medica.ml.entrenamiento_peso import Resultado, clase_de, comparar_pareado


class ElContratoDeColumnasTest(SimpleTestCase):
    """El orden de las columnas es un contrato: romperlo no lanza nada."""

    def test_construir_vector_respeta_el_orden_declarado(self):
        """ESPERADO: la posición i del vector es la característica i.

        Fallo que previene: recibir las columnas en otro orden al servir y
        predecir números plausibles y equivocados sin ninguna excepción.
        """
        datos = {c: float(i + 1) for i, c in enumerate(CARACTERISTICAS)}
        vector = construir_vector(datos)

        assert len(vector) == len(CARACTERISTICAS)
        for i, valor in enumerate(vector):
            assert valor == float(i + 1), (
                f"Posición {i} ({CARACTERISTICAS[i]}) tiene {valor}."
            )

    def test_falta_una_medida_obligatoria_y_lanza_en_vez_de_inventar(self):
        """ESPERADO: KeyError que nombra la medida.

        Un error claro es preferible a una predicción silenciosamente
        equivocada sobre una biometría incompleta.
        """
        datos = {c: 1.0 for c in CARACTERISTICAS}
        del datos["ca_mm"]

        with self.assertRaises(KeyError) as ctx:
            construir_vector(datos)
        assert "ca_mm" in str(ctx.exception)

    def test_las_opcionales_que_faltan_van_como_nan_no_como_cero(self):
        """ESPERADO: NaN.

        Un cero no es «desconocido»: un IMC de 0 es un dato, y absurdo. Los
        modelos de árboles manejan NaN de forma nativa; con un 0 aprenderían
        de un valor inventado.
        """
        datos = {c: 90.0 for c in BIOMETRIA_OBLIGATORIA}
        vector = construir_vector(datos)
        indice_imc = CARACTERISTICAS.index("imc_pregestacional")

        assert math.isnan(vector[indice_imc])

    def test_numero_gesta_no_es_una_caracteristica(self):
        """ESPERADO: ausente.

        `Embarazo.clean()` obliga a G = P + A + 1, así que `numero_gesta` es
        combinación lineal exacta de dos columnas que ya están. No aporta nada
        y hace singular la matriz de los modelos lineales.
        """
        assert "numero_gesta" not in CARACTERISTICAS

    def test_el_comparador_no_entra_como_caracteristica(self):
        """ESPERADO: Hadlock proyectado es columna del dataset pero NO variable.

        Si entrara, el modelo podría limitarse a copiarla y la comparación
        dejaría de significar nada.
        """
        assert COMPARADOR in COLUMNAS_DATASET
        assert COMPARADOR not in CARACTERISTICAS


class LaDecisionDeDesplegarTest(SimpleTestCase):
    """Un empate no puede desplegarse como si fuera una mejora."""

    def _resultado(self, maes):
        r = Resultado("x", "x")
        r.mae = list(maes)
        return r

    def test_una_ventaja_dentro_del_ruido_es_un_empate(self):
        """ESPERADO: mejora_significativa = False.

        Es el caso real medido: 11 g de ventaja media con ±28 g entre
        particiones, ganando en 3 de 5. La regla ingenua lo habría desplegado.
        """
        hadlock = self._resultado([210, 235, 220, 240, 210])
        modelo = self._resultado([220, 200, 225, 205, 210 - 1])

        r = comparar_pareado(modelo, hadlock)

        assert r["mejora_significativa"] is False, (
            f"Declaró mejora con {r['mejora_media_g']:.0f} g de media y "
            f"{r['gana_en_particiones']}/5 particiones ganadas."
        )

    def test_una_mejora_clara_y_consistente_si_cuenta(self):
        """ESPERADO: mejora_significativa = True.

        Si el modelo gana por ~100 g en las cinco particiones, eso no es azar.
        """
        hadlock = self._resultado([300, 310, 295, 305, 300])
        modelo = self._resultado([200, 205, 198, 210, 202])

        assert comparar_pareado(modelo, hadlock)["mejora_significativa"] is True

    def test_ganar_en_cuatro_de_cinco_no_basta(self):
        """ESPERADO: False aunque la media mejore.

        Perder en una partición significa que en parte de los casos el modelo
        es peor que la fórmula que ya existía.
        """
        hadlock = self._resultado([300, 300, 300, 300, 300])
        modelo = self._resultado([200, 200, 200, 200, 320])

        assert comparar_pareado(modelo, hadlock)["mejora_significativa"] is False


class LosCortesDeClaseTest(SimpleTestCase):
    """Los mismos cortes que el resto del sistema."""

    def test_bordes_exactos(self):
        assert clase_de(2499) == "bajo_peso"
        assert clase_de(2500) == "normal"
        assert clase_de(4000) == "normal"
        assert clase_de(4001) == "macrosomia"


class ElDatasetNoFiltraFugasTest(TestCase):
    """Las fugas temporales y los joins ambiguos, comprobados sobre la base."""

    @classmethod
    def setUpTestData(cls):
        from antecedentes.models import AntecedentePatologico
        from ecografias.models import BiometriaFetal, Ecografia
        from embarazos.models import Embarazo
        from pacientes.models import Paciente
        from partos.models import Parto, RecienNacido
        from usuarios.models import Usuario

        cls.medico = Usuario.objects.create_user(
            email="dr.dataset@test.bo", nombre="Ana",
            apellido_paterno="Test", password="clave-de-prueba-123", rol="medico",
        )

        def crear(ci, tipo_embarazo="simple", antecedente=None):
            paciente = Paciente.objects.create(
                nombre="Madre", apellido_paterno="Dataset", apellido_materno="Test",
                fecha_nacimiento=datetime.date(1990, 6, 15),
                genero="femenino", ci=ci,
            )
            fum = datetime.date(2020, 1, 1)
            embarazo = Embarazo.objects.create(
                paciente=paciente, numero_gesta=1, numero_para=0,
                numero_abortos=0, fecha_ultima_menstruacion=fum,
                tipo_embarazo=tipo_embarazo, medico_responsable=cls.medico,
                peso_pregestacional=60, talla_materna=160,
            )
            eco = Ecografia.objects.create(
                paciente=paciente, embarazo=embarazo,
                fecha_ecografia=fum + datetime.timedelta(weeks=36),
                edad_gestacional_semanas=36, edad_gestacional_dias=0,
            )
            BiometriaFetal.objects.create(
                ecografia=eco, diametro_biparietal=89, circunferencia_cefalica=315,
                circunferencia_abdominal=313, longitud_femur=68,
            )
            parto = Parto.objects.create(
                paciente=paciente, embarazo=embarazo,
                medico_responsable=cls.medico, numero_parto=f"P-{ci}",
                fecha_parto=datetime.datetime(2020, 9, 30, 10, 0,
                                              tzinfo=datetime.timezone.utc),
                edad_gestacional_parto="39+0",
            )
            RecienNacido.objects.create(
                parto=parto, numero_gemelo=1, sexo="femenino",
                fecha_nacimiento=parto.fecha_parto, peso_nacimiento=3300,
                talla_nacimiento=50, apgar_1_minuto=8, apgar_5_minutos=9,
            )
            if antecedente:
                AntecedentePatologico.objects.create(
                    paciente=paciente, **antecedente,
                )
            return paciente

        cls.normal = crear("7000001")
        cls.gemelar = crear("7000002", tipo_embarazo="gemelar")
        cls.familiar = crear("7000003", antecedente={
            "tipo": "heredofamiliar", "diabetes": True,
        })
        cls.propia = crear("7000004", antecedente={
            "tipo": "personal", "diabetes": True,
        })

    def _filas(self):
        from ia_medica.ml.dataset_peso import construir

        filas, descartes = construir(None)
        return {f["paciente_id"]: f for f in filas}, descartes

    def test_los_gemelares_se_excluyen(self):
        """ESPERADO: fuera.

        `BiometriaFetal` es OneToOne con `Ecografia`: en un gemelar no se sabe
        a cuál de los dos fetos corresponde la medida.
        """
        filas, descartes = self._filas()

        assert self.gemelar.id not in filas
        assert descartes.multiples >= 1

    def test_la_edad_materna_es_la_de_la_fecha_de_la_ecografia(self):
        """ESPERADO: 30 años.

        Nacida el 15 de junio de 1990; ecografía el 9 de septiembre de 2020
        (FUM 1-ene-2020 + 36 semanas). Ya había cumplido: 30.

        Fallo que previene: usar `Paciente.edad`, que compara contra HOY. Un
        parto de 2020 quedaría con la edad actual de la madre, y eso envenena
        el dataset entero sin lanzar nada.
        """
        filas, _ = self._filas()
        edad = filas[self.normal.id]["edad_materna"]

        assert edad == 30, (
            f"Edad {edad}; esperaba 30. Si coincide con "
            f"{datetime.date.today().year - 1990}, se está calculando a hoy."
        )

    def test_los_antecedentes_de_familiares_no_cuentan_como_propios(self):
        """ESPERADO: diabetes = 0 para quien solo tiene un familiar diabético.

        Fallo que previene: olvidar el filtro `tipo="personal"` y que
        «diabetes» pase a significar «alguien de su familia tuvo diabetes».
        """
        filas, _ = self._filas()

        assert filas[self.familiar.id]["diabetes"] == 0
        assert filas[self.propia.id]["diabetes"] == 1

    def test_la_ventana_de_7_dias_deja_fuera_una_eco_de_3_semanas_antes(self):
        """ESPERADO: con `dias_maximos=7` la ecografía de 21 días antes no entra.

        La eco es del 9-sep-2020 y el parto del 30-sep: 21 días. Con la ventana
        por defecto (120) entra; con la de ingreso (7) cuenta como fuera de
        ventana y no se sustituye por nada.
        """
        from ia_medica.ml.dataset_peso import DIAS_ECOGRAFIA_DE_INGRESO, construir

        filas_120, _ = construir(None)
        filas_7, descartes_7 = construir(None, dias_maximos=DIAS_ECOGRAFIA_DE_INGRESO)

        assert self.normal.id in {f["paciente_id"] for f in filas_120}
        assert self.normal.id not in {f["paciente_id"] for f in filas_7}
        assert descartes_7.eco_fuera_de_ventana >= 1

    def test_el_imc_sale_del_control_si_el_embarazo_no_lo_tiene(self):
        """ESPERADO: 60 kg / 1,60 m² = 23,44, tomado del primer control.

        Fallo que previene: el constructor cargaba los controles y no los usaba;
        con el peso previo anotado solo en el control, el IMC quedaba vacío en
        todas las filas y el modelo perdía la variable sin avisar.
        """
        from controles.models import ControlPrenatal
        from embarazos.models import Embarazo

        embarazo = Embarazo.objects.get(paciente=self.normal)
        Embarazo.objects.filter(pk=embarazo.pk).update(peso_pregestacional=None, talla_materna=None)
        ControlPrenatal.objects.create(
            embarazo=embarazo, paciente=self.normal, medico=self.medico,
            numero_control=1, fecha_control=datetime.date(2020, 3, 1),
            semanas_gestacion=8, peso_actual=61, peso_pregestacional=60, talla=160,
            presion_arterial_sistolica=110, presion_arterial_diastolica=70,
        )
        filas, _ = self._filas()

        assert filas[self.normal.id]["imc_pregestacional"] == 23.44

    def test_hadlock_proyectado_esta_y_es_plausible(self):
        """ESPERADO: entre 2.800 y 4.200 g para un feto medio proyectado a 39 sem."""
        filas, _ = self._filas()
        proyectado = filas[self.normal.id][COMPARADOR]

        assert proyectado is not None
        assert 2800 <= proyectado <= 4200, f"Proyectó {proyectado} g."


class ElModeloAprendeAlgoTest(SimpleTestCase):
    """Que el pipeline corre y aprende, sobre datos del simulador."""

    def test_bate_a_predecir_siempre_la_mediana(self):
        """ESPERADO: el mejor modelo tiene menos error que la constante.

        No es un listón alto, y a propósito: si un modelo no bate a la mediana,
        el pipeline está roto, no el modelo.
        """
        import random

        import pandas as pd

        from core.simulacion.curvas_obstetricas import (
            simular_biometria,
            simular_peso_nacimiento,
            sortear_semanas_al_parto,
            sortear_z_tamano,
        )
        from ecografias.peso_fetal import hadlock_1985_4p, proyectar_peso
        from ia_medica.ml.entrenamiento_peso import evaluar

        rng = random.Random(2026)
        filas = []
        for i in range(250):
            z = sortear_z_tamano(rng)
            eg_eco = rng.uniform(30, 37)
            eg_parto = max(eg_eco + 0.5, sortear_semanas_al_parto(rng))
            b = simular_biometria(eg_eco, z_tamano=z, rng=rng)
            dbp, cc, ca, lf = (float(b[k]) for k in ("dbp", "cc", "ca", "lf"))
            h = hadlock_1985_4p(dbp, cc, ca, lf)
            fila = {c: np.nan for c in CARACTERISTICAS}
            fila.update({
                "grupo": f"g{i}", "es_sintetico": 1,
                "dbp_mm": dbp, "cc_mm": cc, "ca_mm": ca, "lf_mm": lf,
                "relacion_cc_ca": cc / ca, "relacion_lf_ca": lf / ca,
                "peso_hadlock_g": h, "eg_eco_semanas": eg_eco,
                "eg_al_nacer_semanas": eg_parto,
                COMPARADOR: proyectar_peso(h, eg_eco, eg_parto),
                "peso_nacimiento_g": simular_peso_nacimiento(
                    semanas_parto=eg_parto, z_tamano=z, rng=rng),
            })
            filas.append(fila)

        resultados, _ = evaluar(pd.DataFrame(filas))
        mediana = resultados["mediana"].resumen()["mae_g"]["media"]
        mejor = min(
            resultados[k].resumen()["mae_g"]["media"]
            for k in ("ridge", "random_forest", "gradient_boosting")
        )

        assert mejor < mediana, (
            f"El mejor modelo ({mejor:.0f} g) no bate a la mediana "
            f"({mediana:.0f} g): el pipeline está roto."
        )
