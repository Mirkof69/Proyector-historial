"""Comparación fonética de nombres para el castellano boliviano.

Por qué existe este módulo
--------------------------
La búsqueda de pacientes comparaba subcadenas exactas sobre el nombre
descifrado. Medido contra los 450 pacientes del tenant de demostración, las
15 variantes de transcripción más habituales del castellano-aymara fallaban
**las 15**, perdiendo entre 11 y 36 pacientes reales cada una:

    Mamani → Mamany    0 resultados   (25 pacientes perdidas)
    Huanca → Guanca    0 resultados   (22)
    Choque → Chuque    0 resultados   (30)
    Quispe → Kispe     0 resultados   (22)
    Poma   → Puma      0 resultados   (36)

En recepción eso significa abrir una historia clínica nueva a una paciente
que ya existe: el mismo embarazo queda partido en dos expedientes.

Por qué no se usa soundex
-------------------------
Es la solución obvia y es la equivocada. Está diseñado para el inglés y
separa justo los pares que aquí hay que unir: PostgreSQL da
`soundex('Huanca') = H520` y `soundex('Guanca') = G520`. Comprobado.

Cómo funciona
-------------
Dos capas. Primero `clave_fonetica()` reduce el nombre a las equivalencias que
de verdad ocurren al escribir en Bolivia — la H aspirada que se escribe G o W,
la K/Q/C dura, la B y la V que suenan igual, la O y la U átonas—. Después se
compara con `SequenceMatcher`, que tolera además letras de más o de menos.

Medido sobre esas 15 variantes: **15 de 15** se encuentran. Con
`SequenceMatcher` a solas serían 11; la capa fonética aporta las 4 restantes,
que son sustituciones de la primera letra en palabras cortas.

Y no afloja de más: nombres realmente distintos se quedan lejos del umbral —
Mamani/Mamerto 0.46, Choque/Chávez 0.44, Poma/Pérez 0.22.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

#: Similitud mínima para considerar que dos nombres son el mismo.
#: En una clínica un falso positivo es peor que un cero resultado: lleva a
#: abrir la historia equivocada. 0.80 se eligió porque deja las 15 variantes
#: reales por encima y los nombres distintos por debajo de 0.50.
UMBRAL_SIMILITUD = 0.80


def normalizar(texto: str | None) -> str:
    """Minúsculas y sin tildes: "López" se encuentra escribiendo "lopez"."""
    descompuesto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower()


def clave_fonetica(texto: str | None) -> str:
    """Reduce un nombre a las letras que de verdad lo distinguen al oírlo.

    Cada regla corresponde a una confusión observada al transcribir apellidos
    aymaras y quechuas al castellano escrito. El orden importa: los dígrafos
    (`hu`, `qu`) se resuelven antes que las letras sueltas.
    """
    s = normalizar(texto)
    # H aspirada inicial: Huanca = Guanca = Wanca
    s = re.sub(r"^(hu|gu|w)", "W", s)
    # Oclusiva velar sorda: Cusi = Kusi, Quispe = Kispe, Choque = Choqe
    s = re.sub(r"qu|k|c(?=[aou])|q", "K", s)
    # Sibilante: Cespedes = Sespedes, Zarate = Sarate
    s = re.sub(r"c(?=[ei])|z|s", "S", s)
    # B y V son el mismo sonido: Vargas = Bargas
    s = re.sub(r"b|v", "B", s)
    # Jota y G ante e/i: Yujra = Yugra
    s = re.sub(r"j|g(?=[ei])|x", "J", s)
    # Vocal final átona: Mamani = Mamany
    s = re.sub(r"[yi]$", "I", s)
    # O y U átonas se confunden: Poma = Puma
    s = re.sub(r"[ou]", "O", s)
    # H muda ya no aporta nada
    s = s.replace("h", "")
    # Letras dobles: Mamanni = Mamani
    return re.sub(r"(.)\1+", r"\1", s)


def similitud(a: str | None, b: str | None) -> float:
    """Parecido entre dos nombres, de 0 a 1, comparando su clave fonética.

    Exige además que coincida la INICIAL de la clave fonética. En un nombre la
    primera letra es la que más información aporta, y quien se equivoca al
    escribir un apellido raramente se equivoca en ella. Sin esta condición,
    "Fernada" traía también a las 12 pacientes llamadas "Bernarda": se parecen
    0.80 —justo el umbral— porque solo difieren en la inicial y una erre.

    No estrecha la búsqueda real, porque la capa fonética ya unificó las
    iniciales que sí se confunden: Huanca/Guanca/Wanca comparten W, Cusi/Kusi
    comparten K, Vargas/Bargas comparten B. Verificado: las 15 variantes
    reales siguen encontrándose.
    """
    ka, kb = clave_fonetica(a), clave_fonetica(b)
    if not ka or not kb or ka[0] != kb[0]:
        return 0.0
    return SequenceMatcher(None, ka, kb).ratio()


def coincide(termino: str | None, nombre_completo: str | None) -> float:
    """Puntúa cuánto se parece `termino` a `nombre_completo`.

    Devuelve 0.0 si no llega al umbral. Un término de varias palabras
    ("rosa mamani") tiene que casar TODAS: quien escribe dos apellidos está
    acotando, y devolverle las pacientes que solo cumplen uno sería ruido.

    Cada palabra del término se busca contra cada palabra del nombre, así que
    el orden no importa: "mamani rosa" encuentra a "Rosa Mamani".
    """
    palabras_termino = normalizar(termino).split()
    palabras_nombre = normalizar(nombre_completo).split()
    if not palabras_termino or not palabras_nombre:
        return 0.0

    puntajes = []
    for palabra in palabras_termino:
        mejor = max(
            (similitud(palabra, candidata) for candidata in palabras_nombre),
            default=0.0,
        )
        if mejor < UMBRAL_SIMILITUD:
            return 0.0
        puntajes.append(mejor)

    return sum(puntajes) / len(puntajes)
