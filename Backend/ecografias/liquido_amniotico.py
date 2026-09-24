"""Una sola clasificación del índice de líquido amniótico (ILA, en cm).

Antes había cuatro reglas distintas: el modelo llamaba «oligohidramnios» a un
ILA de 7 cm y «polihidramnios» a uno de 22, la calculadora usaba 5 y 25, y el
frontend tenía otras dos. La misma ecografía salía normal en una pantalla y
patológica en otra. Todo el sistema clasifica ahora con esta función.

Criterios (método de los cuatro cuadrantes, Phelan 1987; ACOG):
  ILA ≤ 5          oligohidramnios
  5 < ILA < 8      límite bajo (vigilancia, no es oligohidramnios)
  8 ≤ ILA < 25     normal
  ILA ≥ 25         polihidramnios: leve < 30, moderado < 35, severo ≥ 35
"""
OLIGOHIDRAMNIOS_MAX = 5.0
LIMITE_BAJO_MAX = 8.0
POLIHIDRAMNIOS_MIN = 25.0


def clasificar_ila(ila_cm):
    """Clasifica un ILA en cm. Devuelve None si no hay valor.

    `codigo` es estable (oligohidramnios, limite_bajo, normal, polihidramnios);
    `severidad` es normal / alerta / critica, para colores y alertas.
    """
    if ila_cm is None or ila_cm == "":
        return None
    ila = float(ila_cm)
    if ila <= OLIGOHIDRAMNIOS_MAX:
        return {"codigo": "oligohidramnios", "grado": None, "severidad": "critica",
                "texto": "Oligohidramnios"}
    if ila < LIMITE_BAJO_MAX:
        return {"codigo": "limite_bajo", "grado": None, "severidad": "alerta",
                "texto": "ILA en límite bajo"}
    if ila < POLIHIDRAMNIOS_MIN:
        return {"codigo": "normal", "grado": None, "severidad": "normal", "texto": "Normal"}
    if ila < 30:
        grado, severidad = "leve", "alerta"
    elif ila < 35:
        grado, severidad = "moderado", "critica"
    else:
        grado, severidad = "severo", "critica"
    return {"codigo": "polihidramnios", "grado": grado, "severidad": severidad,
            "texto": f"Polihidramnios {grado}"}
