"""La fórmula de Hadlock consume MILÍMETROS y nunca devuelve cero.

Por qué existe este archivo
---------------------------
La estimación del peso fetal estaba rota y fallaba en silencio. Los
coeficientes de Hadlock 1985 están publicados en **centímetros**; la base de
datos guarda **milímetros** (`verbose_name="DBP (mm)"`) y nadie convertía.

Medido contra las 280 biometrías reales del tenant `clinica_demo` el 23 de
septiembre de 2026:

    calcular_peso_fetal_hadlock() devolvía 0 g en 174 de 280 (62%)

Y en el 38% restante devolvía disparates que además quedaban **guardados en la
base y visibles en pantalla**:

    | guardado  | biometría real          | lo correcto |
    |-----------|-------------------------|-------------|
    | 13.118 g  | DBP 20,6 mm (~12 sem)   |      93 g   |
    |    382 g  | DBP 35,0 mm             |     183 g   |
    |      0 g  | DBP 77,8 mm (~31 sem)   |   1.569 g   |

Un feto de doce semanas registrado con trece kilos.

Lo peor es que fallaba **al revés** de como haría falta. El término
`-0,00386·CA·LF` crece con el cuadrado de las medidas: con un feto grande en
milímetros se dispara y el resultado se va a 10⁻⁴¹ → 0; con uno pequeño no
alcanza a compensar los términos lineales y sale una sobreestimación enorme.
O sea que daba cero justo en el tercer trimestre, que es cuando el peso decide
la vía de parto.

Y los tests que existían **codificaban el fallo**: le pasaban centímetros con
el comentario «The Hadlock formula works with cm values, not mm», y la
aserción era `if peso is not None: assertTrue(peso > 0)` — un test que no podía
fallar nunca, porque si el peso venía `None` no comprobaba nada.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

from decimal import Decimal

from django.test import SimpleTestCase

from ecografias.peso_fetal import (
    CORTE_BAJO_PESO_G,
    CORTE_MACROSOMIA_G,
    PESO_FETAL_MAXIMO_G,
    PESO_FETAL_MINIMO_G,
    TABLA_HADLOCK_1991,
    clasificar_crecimiento,
    estimar_peso_fetal,
    hadlock_1985_3p,
    hadlock_1985_4p,
    percentil_peso_fetal,
)


class LaFormulaConsumeMilimetrosTest(SimpleTestCase):
    """El contrato de unidades, fijado en las dos direcciones."""

    def test_un_feto_a_termino_en_milimetros_da_un_peso_a_termino(self):
        """ESPERADO: entre 2.500 y 3.500 g.

        DBP 90 / CC 320 / CA 330 / LF 70 mm es un feto de unas 39 semanas.
        OBTENIDO antes del arreglo: 0 g (log10 = −41,44).
        """
        peso = hadlock_1985_4p(90.0, 320.0, 330.0, 70.0)

        assert peso is not None, "Devolvió None con las cuatro medidas puestas."
        assert 2500 <= peso <= 3500, (
            f"Un feto de ~39 semanas pesa unos 3.000 g; la fórmula dio {peso} g. "
            f"Si dio 0, volvió el bug de unidades."
        )

    def test_nunca_devuelve_cero_en_el_tercer_trimestre(self):
        """ESPERADO: ningún 0 entre las semanas 28 y 40.

        Es el tramo donde el bug pegaba más fuerte y donde el peso decide
        decisiones clínicas. Se recorre con biometría realista por semana.
        """
        # (semana, DBP, CC, CA, LF) en milímetros, valores típicos.
        biometrias = [
            (28, 71.0, 262.0, 240.0, 53.0),
            (30, 76.0, 278.0, 258.0, 57.0),
            (32, 81.0, 292.0, 276.0, 61.0),
            (34, 86.0, 305.0, 295.0, 65.0),
            (36, 89.0, 315.0, 313.0, 68.0),
            (38, 92.0, 325.0, 330.0, 71.0),
            (40, 95.0, 333.0, 348.0, 74.0),
        ]
        for semana, dbp, cc, ca, lf in biometrias:
            peso = hadlock_1985_4p(dbp, cc, ca, lf)
            assert peso is not None, f"Semana {semana}: devolvió None."
            assert peso != 0, f"Semana {semana}: devolvió 0 g. Volvió el bug."
            assert 800 <= peso <= 5000, (
                f"Semana {semana}: {peso} g está fuera de lo fisiológico."
            )

    def test_centimetros_pasados_como_milimetros_se_rechazan(self):
        """ESPERADO: None, no un número pequeño y plausible.

        Es la red de seguridad. Si alguien pasa 9,0 / 32,0 / 33,0 / 7,0
        creyendo que son milímetros, la conversión los deja en 0,9 / 3,2 / 3,3
        / 0,7 cm y sale un peso de unos 4 g. Devolver ese número sería peor que
        no devolver nada: parece un dato.
        """
        assert hadlock_1985_4p(9.0, 32.0, 33.0, 7.0) is None

    def test_falta_una_medida_devuelve_none_no_excepcion(self):
        """ESPERADO: None. Una biometría incompleta es lo normal, no un error."""
        assert hadlock_1985_4p(None, 320.0, 330.0, 70.0) is None
        assert hadlock_1985_4p(90.0, None, 330.0, 70.0) is None
        assert hadlock_1985_4p(90.0, 320.0, None, 70.0) is None
        assert hadlock_1985_4p(90.0, 320.0, 330.0, None) is None

    def test_acepta_decimal_que_es_lo_que_da_el_modelo(self):
        """ESPERADO: funciona con Decimal.

        Los campos de `BiometriaFetal` son `DecimalField`. Si la función solo
        aceptara float, fallaría al recibir lo que le da el ORM.
        """
        peso = hadlock_1985_4p(
            Decimal("90.0"), Decimal("320.0"), Decimal("330.0"), Decimal("70.0"),
        )
        assert peso is not None
        assert 2500 <= peso <= 3500

    def test_el_resultado_nunca_sale_del_rango_fisiologico(self):
        """ESPERADO: o None, o dentro de los límites declarados."""
        casos = [
            (90.0, 320.0, 330.0, 70.0),
            (20.0, 78.0, 73.0, 16.0),      # el caso real que daba 13.118 g
            (200.0, 600.0, 600.0, 150.0),  # absurdo por arriba
            (1.0, 1.0, 1.0, 1.0),          # absurdo por abajo
        ]
        for dbp, cc, ca, lf in casos:
            peso = hadlock_1985_4p(dbp, cc, ca, lf)
            if peso is not None:
                assert PESO_FETAL_MINIMO_G <= peso <= PESO_FETAL_MAXIMO_G

    def test_el_caso_real_que_daba_trece_kilos(self):
        """ESPERADO: un peso de primer trimestre, no 13.118 g.

        Biometría sacada tal cual de la base: DBP 20,6 / CC 78,0 / CA 73,5 /
        LF 16,3 mm, un feto de unas 12 semanas. La función rota devolvía
        13.118 g y ese valor quedó guardado.
        """
        peso = hadlock_1985_4p(20.6, 78.0, 73.5, 16.3)

        assert peso != 13118, "Volvió exactamente el bug original."
        if peso is not None:
            assert peso < 300, (
                f"Un feto de ~12 semanas pesa unos 15-90 g; dio {peso} g."
            )


class LaVarianteDeTresParametrosTest(SimpleTestCase):
    """Existe para las ecografías sin circunferencia cefálica medible."""

    def test_da_un_peso_parecido_al_de_cuatro_parametros(self):
        """ESPERADO: menos de 20% de diferencia a las 34 semanas.

        Hadlock declara ±15% de error. Si las dos variantes se separan mucho
        más que eso, una de las dos está mal transcrita.
        """
        cuatro = hadlock_1985_4p(86.0, 305.0, 295.0, 65.0)
        tres = hadlock_1985_3p(86.0, 295.0, 65.0)

        assert cuatro is not None and tres is not None
        diferencia = abs(cuatro - tres) / cuatro
        assert diferencia < 0.20, (
            f"4p dio {cuatro} g y 3p dio {tres} g: {diferencia:.0%} de diferencia."
        )

    def test_estimar_peso_fetal_usa_tres_parametros_si_falta_la_cefalica(self):
        """ESPERADO: devuelve un peso aunque CC sea None.

        Es el caso real: con el feto encajado la cabeza queda fuera de plano.
        """
        peso = estimar_peso_fetal(86.0, None, 295.0, 65.0)

        assert peso is not None, "Sin CC debería usar la fórmula de 3 parámetros."
        assert 1800 <= peso <= 3200


class LosPercentilesSalenDeUnaTablaPublicadaTest(SimpleTestCase):
    """Antes el 'percentil' solo podía valer 10, 50 o 90."""

    def test_la_tabla_es_monotona_dentro_de_cada_semana(self):
        """ESPERADO: p10 < p50 < p90 en las 33 semanas de la tabla."""
        for semana, (p10, p50, p90) in TABLA_HADLOCK_1991.items():
            assert p10 < p50 < p90, f"Semana {semana}: {p10}/{p50}/{p90} desordenado."

    def test_la_tabla_crece_semana_a_semana(self):
        """ESPERADO: el p50 sube siempre. Un feto no adelgaza."""
        semanas = sorted(TABLA_HADLOCK_1991)
        for anterior, actual in zip(semanas, semanas[1:]):
            assert TABLA_HADLOCK_1991[actual][1] > TABLA_HADLOCK_1991[anterior][1], (
                f"El p50 baja de la semana {anterior} a la {actual}."
            )

    def test_el_peso_mediano_da_percentil_cincuenta(self):
        """ESPERADO: 50 (±2) al pasarle exactamente el p50 de la tabla."""
        for semana in (24, 32, 40):
            p50 = TABLA_HADLOCK_1991[semana][1]
            assert abs(percentil_peso_fetal(p50, semana) - 50) <= 2

    def test_devuelve_valores_intermedios_no_solo_10_50_y_90(self):
        """ESPERADO: un peso entre p50 y p90 da algo estrictamente entre 50 y 90.

        La implementación anterior solo podía devolver 10, 50 o 90, así que
        dos fetos muy distintos salían con el mismo 'percentil'.
        """
        p50, p90 = TABLA_HADLOCK_1991[32][1], TABLA_HADLOCK_1991[32][2]
        percentil = percentil_peso_fetal((p50 + p90) // 2, 32)

        assert 50 < percentil < 90, f"Dio {percentil}, esperaba algo intermedio."

    def test_fuera_del_rango_de_la_tabla_devuelve_none(self):
        """ESPERADO: None para semana 5 o 50, no un número inventado."""
        assert percentil_peso_fetal(3000, 5) is None
        assert percentil_peso_fetal(3000, 50) is None
        assert percentil_peso_fetal(None, 32) is None
        assert percentil_peso_fetal(3000, None) is None


class LaClasificacionDelCrecimientoTest(SimpleTestCase):
    """Los cortes en p10 y p90 son los de la práctica obstétrica."""

    def test_por_debajo_del_percentil_diez_es_pequeno(self):
        assert clasificar_crecimiento(5)[0] == "pequeno"

    def test_por_encima_del_noventa_es_grande(self):
        assert clasificar_crecimiento(95)[0] == "grande"

    def test_en_medio_es_adecuado(self):
        assert clasificar_crecimiento(50)[0] == "adecuado"

    def test_los_bordes_exactos(self):
        """ESPERADO: 10 y 90 son adecuados; 9 y 91 no.

        Los bordes son donde se equivocan las comparaciones.
        """
        assert clasificar_crecimiento(10)[0] == "adecuado"
        assert clasificar_crecimiento(90)[0] == "adecuado"
        assert clasificar_crecimiento(9)[0] == "pequeno"
        assert clasificar_crecimiento(91)[0] == "grande"

    def test_sin_percentil_lo_dice_en_vez_de_inventar(self):
        codigo, texto = clasificar_crecimiento(None)
        assert codigo == "desconocido"
        assert texto


class LosCortesDePesoCoincidenConElModeloTest(SimpleTestCase):
    """Si estos cortes se separan, el dataset y la ficha clínica discrepan."""

    def test_coinciden_con_get_clasificacion_peso(self):
        """ESPERADO: los mismos límites que `RecienNacido.get_clasificacion_peso()`.

        Esa función (`partos/models.py:1191`) devuelve cadenas con emoji y seis
        categorías, así que no sirve como etiqueta — pero sus cortes sí son los
        correctos, y son los que se replican aquí. Este test impide que alguien
        cambie unos y no los otros.

        Nota sobre `fecha_nacimiento`: se pasa a propósito aunque no haga falta
        para clasificar. `RecienNacido.__init__` (`partos/models.py:1037-1039`)
        accede a `self.parto` cuando la fecha viene vacía, y en una instancia
        sin guardar eso lanza `RelatedObjectDoesNotExist`. Es decir, hoy **no
        se puede construir un RecienNacido en memoria sin parto**, ni para una
        comprobación tan simple como ésta. Debería usar `self.parto_id`; queda
        anotado como fragilidad aparte.
        """
        import datetime

        from partos.models import RecienNacido

        for peso, esperado in [
            (2499, "Bajo peso"), (2500, "normal"),
            (4000, "normal"), (4001, "Macrosomía"),
        ]:
            recien_nacido = RecienNacido(
                peso_nacimiento=peso, fecha_nacimiento=datetime.date(2026, 1, 1),
            )
            texto = recien_nacido.get_clasificacion_peso()
            assert esperado in texto, f"{peso} g dio «{texto}»"

        assert CORTE_BAJO_PESO_G == 2500
        assert CORTE_MACROSOMIA_G == 4000
