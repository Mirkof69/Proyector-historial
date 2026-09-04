"""Tests de la búsqueda fonética de pacientes.

Por qué existe este archivo
---------------------------
Buscar una paciente escribiendo su apellido como suena —que es como lo escribe
recepción— no encontraba a nadie. Medido contra los 450 pacientes del tenant
de demostración: las 15 variantes de transcripción más habituales del
castellano-aymara fallaban las 15, perdiendo entre 11 y 36 pacientes cada una.

El riesgo no es la incomodidad: es abrir una historia clínica nueva a una
paciente que ya existe y partir su embarazo en dos expedientes.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import pytest

from pacientes.fonetica import (
    UMBRAL_SIMILITUD,
    clave_fonetica,
    coincide,
    normalizar,
    similitud,
)

#: Las 15 variantes reales medidas en producción. Antes fallaban las 15.
VARIANTES_REALES = [
    ("Mamani", "Mamany"),
    ("Mamani", "Mamanni"),
    ("Huanca", "Guanca"),
    ("Huanca", "Wanca"),
    ("Choque", "Choqe"),
    ("Choque", "Chuque"),
    ("Cusi", "Kusi"),
    ("Quispe", "Kispe"),
    ("Poma", "Puma"),
    ("Yujra", "Yugra"),
    ("Vargas", "Bargas"),
    ("Cespedes", "Sespedes"),
    ("Salvatierra", "Salvatiera"),
    ("Avila", "Abila"),
    ("Fernanda", "Fernada"),
]

#: Nombres realmente distintos. Un falso positivo aquí lleva a abrir la
#: historia clínica equivocada, que es peor que no encontrar nada.
NOMBRES_DISTINTOS = [
    ("Mamani", "Mamerto"),
    ("Choque", "Chavez"),
    ("Poma", "Perez"),
    ("Quispe", "Quiroga"),
    ("Vargas", "Vera"),
    ("Rosa", "Rodrigo"),
]


class TestNormalizar:
    """Las tildes y las mayúsculas no pueden impedir encontrar a nadie."""

    def test_quita_tildes(self):
        """ESPERADO: 'lopez' — en Bolivia se escribe López y Lopez."""
        assert normalizar("López") == "lopez"

    def test_baja_a_minusculas(self):
        """ESPERADO: 'mamani'."""
        assert normalizar("MAMANI") == "mamani"

    def test_vacio_y_none_no_revientan(self):
        """ESPERADO: cadena vacía, sin excepción."""
        assert normalizar(None) == ""
        assert normalizar("") == ""


class TestClaveFonetica:
    """Las equivalencias del castellano boliviano escrito."""

    @pytest.mark.parametrize(("a", "b"), [
        ("Huanca", "Guanca"),
        ("Huanca", "Wanca"),
        ("Cusi", "Kusi"),
        ("Quispe", "Kispe"),
        ("Vargas", "Bargas"),
        ("Cespedes", "Sespedes"),
        ("Poma", "Puma"),
        ("Mamani", "Mamany"),
        ("Mamanni", "Mamani"),
    ])
    def test_las_variantes_comparten_clave(self, a, b):
        """ESPERADO: la misma clave fonética para ambas grafías."""
        ka, kb = clave_fonetica(a), clave_fonetica(b)
        assert ka == kb, f"{a}→{ka} y {b}→{kb} deberían coincidir"

    def test_apellidos_distintos_no_comparten_clave(self):
        """ESPERADO: claves distintas; si no, se confundirían dos personas."""
        assert clave_fonetica("Mamani") != clave_fonetica("Mamerto")
        assert clave_fonetica("Choque") != clave_fonetica("Chavez")


class TestSimilitud:
    """El punto de todo: encontrar las 15, sin traer a quien no es."""

    @pytest.mark.parametrize(("correcto", "tipeado"), VARIANTES_REALES)
    def test_encuentra_las_variantes_reales(self, correcto, tipeado):
        """ESPERADO: >= 0.80. OBTENIDO antes del arreglo: 0 resultados."""
        s = similitud(correcto, tipeado)
        assert s >= UMBRAL_SIMILITUD, (
            f"'{tipeado}' no encuentra a '{correcto}' (similitud {s:.3f}). "
            f"En recepción eso crea un expediente duplicado."
        )

    @pytest.mark.parametrize(("a", "b"), NOMBRES_DISTINTOS)
    def test_no_confunde_nombres_distintos(self, a, b):
        """ESPERADO: < 0.80 — abrir la historia equivocada es lo peor."""
        s = similitud(a, b)
        assert s < UMBRAL_SIMILITUD, (
            f"'{a}' y '{b}' se parecen {s:.3f}: se confundirían dos pacientes."
        )

    def test_identico_es_uno(self):
        """ESPERADO: 1.0 exacto."""
        assert similitud("Mamani", "Mamani") == 1.0

    def test_vacio_es_cero(self):
        """ESPERADO: 0.0 — sin texto no hay parecido que medir."""
        assert similitud("", "Mamani") == 0.0
        assert similitud(None, None) == 0.0


class TestCoincide:
    """Búsqueda sobre el nombre completo, como la usa recepción."""

    NOMBRE = "Rosa Mamani Choque"

    def test_encuentra_por_apellido_mal_escrito(self):
        """ESPERADO: > 0 — buscar 'mamany' encuentra a Rosa Mamani."""
        assert coincide("mamany", self.NOMBRE) > 0

    def test_encuentra_por_nombre_de_pila(self):
        """ESPERADO: > 0."""
        assert coincide("rosa", self.NOMBRE) > 0

    def test_el_orden_de_las_palabras_no_importa(self):
        """ESPERADO: > 0 — recepción escribe el apellido primero a menudo."""
        assert coincide("mamani rosa", self.NOMBRE) > 0

    def test_dos_apellidos_deben_casar_ambos(self):
        """ESPERADO: 0 — quien escribe dos apellidos está acotando.

        'mamani perez' NO puede devolver a Rosa Mamani Choque: el segundo
        apellido no casa, y devolverla sería ruido justo cuando la usuaria
        está intentando desambiguar.
        """
        assert coincide("mamani perez", self.NOMBRE) == 0

    def test_un_nombre_ajeno_no_coincide(self):
        """ESPERADO: 0."""
        assert coincide("gutierrez", self.NOMBRE) == 0

    def test_termino_vacio_no_coincide(self):
        """ESPERADO: 0 — quien llama decide qué hacer con un término vacío."""
        assert coincide("", self.NOMBRE) == 0
        assert coincide(None, self.NOMBRE) == 0

    def test_devuelve_puntaje_no_solo_booleano(self):
        """ESPERADO: la coincidencia exacta puntúa más que la aproximada.

        Es lo que permite ordenar los resultados por relevancia en vez de
        devolverlos en un orden arbitrario.
        """
        exacta = coincide("mamani", self.NOMBRE)
        aproximada = coincide("mamany", self.NOMBRE)
        assert exacta >= aproximada > 0


class TestInicialFonetica:
    """La inicial debe coincidir: es la letra que más distingue un nombre.

    Sin esta condición, buscar "Fernada" devolvía también a las 12 pacientes
    llamadas "Bernarda" — se parecen 0.80, justo el umbral, porque solo
    difieren en la inicial y una erre.
    """

    def test_rechaza_nombres_que_solo_difieren_en_la_inicial(self):
        """ESPERADO: 0.0 — Fernanda y Bernarda son personas distintas."""
        assert similitud("Fernada", "Bernarda") == 0.0

    @pytest.mark.parametrize(("a", "b"), [
        ("Huanca", "Guanca"),
        ("Huanca", "Wanca"),
        ("Cusi", "Kusi"),
        ("Quispe", "Kispe"),
        ("Vargas", "Bargas"),
    ])
    def test_no_estorba_a_las_variantes_reales(self, a, b):
        """ESPERADO: > 0 — la capa fonética ya unificó esas iniciales.

        Huanca/Guanca/Wanca comparten la W; Cusi/Kusi y Quispe/Kispe la K;
        Vargas/Bargas la B. La condición solo corta lo que de verdad empieza
        distinto.
        """
        assert similitud(a, b) >= UMBRAL_SIMILITUD
