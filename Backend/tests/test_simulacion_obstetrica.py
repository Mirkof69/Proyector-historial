"""El generador de datos tiene que producir señal, no ruido.

Por qué existe este archivo
---------------------------
Los datos sintéticos del proyecto eran inservibles para aprendizaje automático
por construcción:

  - `seed_carga.py:572` → `peso_nacimiento=random.randint(1800, 4200)`, dentro
    de una función que **recibía las semanas de gestación y no las usaba**.
    La correlación peso↔edad gestacional, que en la realidad es r≈0,8, valía
    exactamente **cero**.
  - `seed_carga.py:493-497` → biometría desacoplada de la edad gestacional.
    Un feto de 12 semanas podía tener un diámetro biparietal de 95 mm.
  - `seed_carga.py:537` → `if semanas_actuales >= 37`: **todos los partos a
    término**, así que ni siquiera había variación de semanas que aprender.
  - `seed_carga.py:573-576` → talla, perímetro y los dos Apgar independientes
    entre sí y del peso. Un bebé de 1.800 g podía medir 54 cm.

El test clave de este archivo es el de la correlación. Si vuelve a caer a cero,
cualquier modelo entrenado sobre estos datos es un ejercicio vacío y su métrica
no significa nada.

Van sobre `SimpleTestCase` porque no tocan la base de datos: corren en
milisegundos y se pueden ejecutar en cada cambio.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import random
import statistics

from django.test import SimpleTestCase

from core.simulacion.curvas_obstetricas import (
    biometria_esperada,
    clasificar_peso_nacimiento,
    peso_mediano_por_semana,
    simular_apgar,
    simular_biometria,
    simular_peso_nacimiento,
    simular_talla_y_perimetro,
    sortear_semanas_al_parto,
    sortear_z_tamano,
)


def _correlacion(xs, ys) -> float:
    """Pearson. Se calcula a mano para no depender de scipy en un test rápido."""
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx and dy else 0.0


class LaBiometriaCreceConLaEdadGestacionalTest(SimpleTestCase):
    """Un feto no puede medir lo mismo a las 12 semanas que a las 36."""

    def test_las_medias_crecen_semana_a_semana(self):
        """ESPERADO: cada medida sube de forma monótona entre 10 y 42 semanas."""
        anterior = biometria_esperada(10)
        for semana in range(11, 43):
            actual = biometria_esperada(semana)
            for clave in ("dbp", "cc", "ca", "lf"):
                assert actual[clave] >= anterior[clave], (
                    f"{clave} baja de la semana {semana - 1} a la {semana}: "
                    f"{anterior[clave]} -> {actual[clave]}"
                )
            anterior = actual

    def test_la_interpolacion_cae_entre_las_dos_semanas_de_la_tabla(self):
        """ESPERADO: la semana 13 queda entre la 12 y la 14."""
        doce, trece, catorce = (biometria_esperada(s) for s in (12, 13, 14))
        for clave in ("dbp", "cc", "ca", "lf"):
            assert doce[clave] < trece[clave] < catorce[clave]

    def test_un_feto_de_12_semanas_nunca_mide_como_uno_de_termino(self):
        """ESPERADO: el máximo DBP a las 12 semanas se queda por debajo de 32 mm.

        Fallo que previene: `_rango(20, 95)` en `seed_carga.py:493` daba 95 mm
        —el diámetro de un feto a término— a un feto del primer trimestre.
        """
        rng = random.Random(2026)
        maximo = max(
            float(simular_biometria(12, z_tamano=sortear_z_tamano(rng), rng=rng)["dbp"])
            for _ in range(2000)
        )
        assert maximo < 32, f"El DBP máximo a las 12 semanas fue {maximo} mm."

    def test_las_cuatro_medidas_del_mismo_feto_correlacionan(self):
        """ESPERADO: r(DBP, CA) > 0,6 en fetos de la misma semana.

        Es lo que aporta el factor latente `z_tamano`. Sin él, sorteando cada
        medida por separado, r sería ≈ 0 y no habría un feto: habría cuatro
        números sueltos.
        """
        rng = random.Random(7)
        dbps, cas = [], []
        for _ in range(2000):
            b = simular_biometria(32, z_tamano=sortear_z_tamano(rng), rng=rng)
            dbps.append(float(b["dbp"]))
            cas.append(float(b["ca"]))

        r = _correlacion(dbps, cas)
        assert r > 0.6, f"r(DBP, CA) = {r:.3f}; sin z_tamano compartido sería ~0."


class ElPesoAlNacerDependeDeLaEdadGestacionalTest(SimpleTestCase):
    """El test central de todo el arreglo."""

    def test_correlacion_peso_semanas(self):
        """ESPERADO: r > 0,6 sobre 2.000 partos entre 28 y 42 semanas.

        OBTENIDO con el generador anterior: r ≈ 0,00, porque el peso era
        `random.randint(1800, 4200)` y las semanas no entraban en el cálculo.

        Si este test falla, cualquier modelo entrenado con estos datos está
        aprendiendo ruido y su MAE no significa nada.
        """
        rng = random.Random(2026)
        semanas, pesos = [], []
        for _ in range(2000):
            s = rng.randint(28, 42)
            semanas.append(s)
            pesos.append(
                simular_peso_nacimiento(
                    semanas_parto=s, z_tamano=sortear_z_tamano(rng), rng=rng,
                ),
            )

        r = _correlacion(semanas, pesos)
        assert r > 0.6, f"r(semanas, peso) = {r:.3f}. Volvió el random suelto."

    def test_el_peso_correlaciona_con_la_biometria_del_mismo_embarazo(self):
        """ESPERADO: r(CA a las 34 semanas, peso al nacer) > 0,5.

        Es LA correlación que el modelo tiene que aprender: predecir el peso al
        nacer desde la biometría de una ecografía anterior. Sin ella, todo el
        ejercicio es ajustar ruido.
        """
        rng = random.Random(11)
        cas, pesos = [], []
        for _ in range(1500):
            z = sortear_z_tamano(rng)
            cas.append(float(simular_biometria(34, z_tamano=z, rng=rng)["ca"]))
            pesos.append(
                simular_peso_nacimiento(semanas_parto=39, z_tamano=z, rng=rng),
            )

        r = _correlacion(cas, pesos)
        assert r > 0.5, f"r(CA, peso al nacer) = {r:.3f}."

    def test_la_mediana_por_semana_sigue_la_tabla_publicada(self):
        """ESPERADO: la mediana simulada queda a menos del 8% del p50 de Hadlock."""
        rng = random.Random(3)
        for semana in (28, 32, 36, 40):
            pesos = [
                simular_peso_nacimiento(
                    semanas_parto=semana, z_tamano=sortear_z_tamano(rng), rng=rng,
                )
                for _ in range(600)
            ]
            esperado = peso_mediano_por_semana(semana)
            obtenido = statistics.median(pesos)
            desvio = abs(obtenido - esperado) / esperado
            assert desvio < 0.08, (
                f"Semana {semana}: mediana simulada {obtenido:.0f} g frente a "
                f"{esperado:.0f} g de la tabla ({desvio:.1%} de desvío)."
            )

    def test_la_diabetes_sube_el_peso_medio(self):
        """ESPERADO: entre +100 y +400 g de diferencia.

        Si no hubiera efecto, la columna `diabetes` del dataset sería ruido
        puro y el modelo aprendería —correctamente— a ignorarla. Eso dejaría
        inútil la mitad de las variables maternas.
        """
        rng = random.Random(5)
        sin_dm, con_dm = [], []
        for _ in range(1500):
            z = sortear_z_tamano(rng)
            sin_dm.append(simular_peso_nacimiento(
                semanas_parto=39, z_tamano=z, diabetes=False, rng=rng))
            con_dm.append(simular_peso_nacimiento(
                semanas_parto=39, z_tamano=z, diabetes=True, rng=rng))

        diferencia = statistics.mean(con_dm) - statistics.mean(sin_dm)
        assert 100 < diferencia < 400, f"La diabetes aportó {diferencia:.0f} g."

    def test_un_gemelar_pesa_menos(self):
        """ESPERADO: al menos 400 g menos de media."""
        rng = random.Random(13)
        unicos, gemelos = [], []
        for _ in range(1200):
            z = sortear_z_tamano(rng)
            unicos.append(simular_peso_nacimiento(
                semanas_parto=38, z_tamano=z, gemelar=False, rng=rng))
            gemelos.append(simular_peso_nacimiento(
                semanas_parto=38, z_tamano=z, gemelar=True, rng=rng))

        assert statistics.mean(unicos) - statistics.mean(gemelos) > 400


class LaBiometriaYElPesoCuentanLaMismaHistoriaTest(SimpleTestCase):
    """Un feto no puede tener medidas de 5 kg y nacer con 3,6."""

    def test_hadlock_sobre_la_biometria_coincide_con_el_peso_simulado(self):
        """ESPERADO: cociente Hadlock/peso entre 0,85 y 1,20 para z de −2 a +2.

        Es el test del error que más costó ver. La primera versión aplicaba el
        mismo 11% de dispersión a las medidas (mm) y al peso (g), pero el peso
        crece con el CUBO de las medidas. Medido, mismo feto, sin ruido:

            z = −2   Hadlock 1.626 g   nacía con 2.532 g   cociente 0,64
            z = +1   Hadlock 5.019 g   nacía con 3.603 g   cociente 1,39

        Y eso falseaba la comparación del modelo: Hadlock salía peor que
        predecir siempre la mediana, y el modelo lineal "ganaba por un 71%"
        sobre todo porque aprendía a deshacer el error del generador.

        Se prueba sin ruido (un generador que devuelve siempre la media) para
        aislar la coherencia estructural del azar.
        """
        from ecografias.peso_fetal import hadlock_1985_4p

        class SinRuido:
            def gauss(self, media, _desv):
                return media

        rng = SinRuido()
        for z in (-2.0, -1.0, 0.0, 1.0, 2.0):
            b = simular_biometria(39, z_tamano=z, rng=rng)
            hadlock = hadlock_1985_4p(b["dbp"], b["cc"], b["ca"], b["lf"])
            peso = simular_peso_nacimiento(semanas_parto=39, z_tamano=z, rng=rng)

            assert hadlock is not None, f"z={z}: Hadlock fuera de rango."
            cociente = hadlock / peso
            assert 0.85 <= cociente <= 1.20, (
                f"z={z:+}: la biometría dice {hadlock} g y el bebé nace con "
                f"{peso} g (cociente {cociente:.2f}). El generador vuelve a "
                f"fabricar fetos incoherentes: revisar DISPERSION_BIOMETRIA."
            )

    def test_la_dispersion_de_las_medidas_es_menor_que_la_del_peso(self):
        """ESPERADO: la biometría varía aproximadamente un tercio que el peso.

        Porque el peso va con el volumen, y el volumen con el cubo de la
        longitud. Si alguien vuelve a igualarlas, este test lo dice.
        """
        from core.simulacion.curvas_obstetricas import (
            DISPERSION_BIOMETRIA,
            DISPERSION_PESO,
        )

        assert DISPERSION_BIOMETRIA < DISPERSION_PESO / 2, (
            f"Biometría {DISPERSION_BIOMETRIA:.3f} frente a peso "
            f"{DISPERSION_PESO:.3f}: si se parecen, el peso crecería con la "
            f"longitud y no con su cubo."
        )


class LasMedidasDelRecienNacidoSonCoherentesTest(SimpleTestCase):
    """Talla, perímetro y Apgar tienen que salir del peso, no de un sorteo."""

    def test_la_talla_correlaciona_con_el_peso(self):
        """ESPERADO: r > 0,7.

        Fallo que previene: `_rango(42, 54)` para la talla, independiente del
        peso. Un recién nacido de 1.800 g podía medir 54 cm.
        """
        rng = random.Random(17)
        pesos, tallas = [], []
        for _ in range(1500):
            p = rng.randint(1200, 4500)
            talla, _perimetro = simular_talla_y_perimetro(p, rng)
            pesos.append(p)
            tallas.append(float(talla))

        r = _correlacion(pesos, tallas)
        assert r > 0.7, f"r(peso, talla) = {r:.3f}."

    def test_el_perimetro_cefalico_tambien(self):
        """ESPERADO: r > 0,6."""
        rng = random.Random(19)
        pesos, perimetros = [], []
        for _ in range(1500):
            p = rng.randint(1200, 4500)
            _talla, perimetro = simular_talla_y_perimetro(p, rng)
            pesos.append(p)
            perimetros.append(float(perimetro))

        assert _correlacion(pesos, perimetros) > 0.6

    def test_el_apgar_de_5_minutos_nunca_es_menor_que_el_de_1(self):
        """ESPERADO: en los 3.000 sorteos, ni uno.

        Fallo que previene: se sorteaban por separado y salía 9 al minuto y 7 a
        los cinco, que fisiológicamente es raro y clínicamente confuso.
        """
        rng = random.Random(23)
        for _ in range(3000):
            a1, a5 = simular_apgar(
                semanas_parto=rng.randint(28, 42),
                peso_g=rng.randint(900, 4500),
                rng=rng,
            )
            assert a5 >= a1, f"Apgar 1'={a1} y 5'={a5}: el de cinco bajó."

    def test_la_prematuridad_baja_el_apgar(self):
        """ESPERADO: el Apgar medio a las 30 semanas es menor que a las 39."""
        rng = random.Random(29)
        pretermino = [
            simular_apgar(semanas_parto=30, peso_g=1400, rng=rng)[0]
            for _ in range(800)
        ]
        termino = [
            simular_apgar(semanas_parto=39, peso_g=3300, rng=rng)[0]
            for _ in range(800)
        ]
        assert statistics.mean(pretermino) < statistics.mean(termino)


class LoGeneradoPasaLosValidadoresDelModeloTest(SimpleTestCase):
    """Si el simulador produce algo que el modelo rechaza, el seeder falla."""

    def test_todos_los_valores_caen_en_los_rangos_permitidos(self):
        """ESPERADO: peso [300,6000], talla [20,60], perímetro [20,50], Apgar [0,10].

        Son los validadores de `partos/models.py:1082,1087,1094,1104,1109`.
        """
        rng = random.Random(31)
        for _ in range(3000):
            semanas = sortear_semanas_al_parto(rng)
            z = sortear_z_tamano(rng)
            peso = simular_peso_nacimiento(
                semanas_parto=semanas, z_tamano=z,
                imc_materno=rng.uniform(17, 40),
                paridad=rng.randint(0, 5),
                diabetes=rng.random() < 0.1,
                hipertension=rng.random() < 0.1,
                gemelar=rng.random() < 0.05,
                rng=rng,
            )
            talla, perimetro = simular_talla_y_perimetro(peso, rng)
            a1, a5 = simular_apgar(semanas_parto=semanas, peso_g=peso, rng=rng)

            assert 300 <= peso <= 6000, f"peso {peso}"
            assert 20 <= float(talla) <= 60, f"talla {talla}"
            assert 20 <= float(perimetro) <= 50, f"perímetro {perimetro}"
            assert 0 <= a1 <= 10 and 0 <= a5 <= 10

    def test_la_biometria_nunca_es_negativa_ni_cero(self):
        rng = random.Random(37)
        for semana in range(10, 43):
            for _ in range(60):
                b = simular_biometria(semana, z_tamano=sortear_z_tamano(rng), rng=rng)
                for clave, valor in b.items():
                    assert float(valor) > 0, f"semana {semana}, {clave} = {valor}"


class LaDistribucionDeSemanasEsRealistaTest(SimpleTestCase):
    """Sin variación de edad gestacional no hay nada que aprender."""

    def test_hay_pretermino_de_verdad(self):
        """ESPERADO: entre 5% y 20% por debajo de las 37 semanas.

        Fallo que previene: `if semanas_actuales >= 37` en `seed_carga.py:537`
        generaba el 100% a término. La edad gestacional es el predictor más
        fuerte del peso, y sin variación su efecto no se puede aprender.
        """
        rng = random.Random(41)
        semanas = [sortear_semanas_al_parto(rng) for _ in range(5000)]
        proporcion = sum(1 for s in semanas if s < 37) / len(semanas)

        assert 0.05 < proporcion < 0.20, (
            f"{proporcion:.1%} de pretérminos. Con 0% no hay señal; "
            f"con 40% el dataset no representa una clínica."
        )

    def test_la_mayoria_es_a_termino(self):
        """ESPERADO: más del 75% entre 37 y 41 semanas."""
        rng = random.Random(43)
        semanas = [sortear_semanas_al_parto(rng) for _ in range(5000)]
        a_termino = sum(1 for s in semanas if 37 <= s <= 41) / len(semanas)
        assert a_termino > 0.75

    def test_nunca_sale_una_semana_imposible(self):
        rng = random.Random(47)
        for _ in range(3000):
            assert 20 <= sortear_semanas_al_parto(rng) <= 42


class LosCortesDePesoNoSeSeparanTest(SimpleTestCase):
    """Tres funciones distintas clasifican el peso; tienen que coincidir."""

    def test_coinciden_con_get_clasificacion_peso_del_modelo(self):
        """ESPERADO: la misma frontera en 2500 y en 4000 g.

        Hay tres sitios que clasifican el peso: esta función,
        `ecografias.peso_fetal` y `RecienNacido.get_clasificacion_peso()`
        (`partos/models.py:1191`). Si alguien cambia unos cortes y no los
        otros, el dataset y la ficha clínica empiezan a discrepar sin que nada
        falle.
        """
        assert clasificar_peso_nacimiento(2499) == "bajo_peso"
        assert clasificar_peso_nacimiento(2500) == "normal"
        assert clasificar_peso_nacimiento(4000) == "normal"
        assert clasificar_peso_nacimiento(4001) == "macrosomia"

    def test_las_tres_clases_aparecen_en_una_muestra_realista(self):
        """ESPERADO: las tres presentes, con macrosomía por encima del 1%.

        Si una clase no aparece, el clasificador no se puede entrenar ni
        evaluar sobre ella.
        """
        rng = random.Random(53)
        clases = [
            clasificar_peso_nacimiento(
                simular_peso_nacimiento(
                    semanas_parto=sortear_semanas_al_parto(rng),
                    z_tamano=sortear_z_tamano(rng),
                    imc_materno=rng.uniform(18, 38),
                    diabetes=rng.random() < 0.08,
                    rng=rng,
                ),
            )
            for _ in range(4000)
        ]
        for clase in ("bajo_peso", "normal", "macrosomia"):
            proporcion = clases.count(clase) / len(clases)
            assert proporcion > 0.01, f"{clase} solo aparece el {proporcion:.2%}."


class EsReproducibleTest(SimpleTestCase):
    """Con la misma semilla, los mismos datos. Sin esto no hay experimento."""

    def test_dos_corridas_con_la_misma_semilla_dan_lo_mismo(self):
        def corrida():
            rng = random.Random(2026)
            return [
                simular_peso_nacimiento(
                    semanas_parto=39, z_tamano=sortear_z_tamano(rng), rng=rng,
                )
                for _ in range(50)
            ]

        assert corrida() == corrida()
