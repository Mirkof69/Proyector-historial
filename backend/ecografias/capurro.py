def evaluar_capurro(datos):
    """Evaluar edad gestacional por método de Capurro

    Basado en 5 parámetros somáticos del recién nacido:
    - Formación del pezón
    - Pliegues plantares
    - Formación del pabellón auricular
    - Textura de la piel
    - Lanugo
    """
    puntajes = {
        "formacion_pezón": {
            "apenas_visible_sin_areola": 0,
            "areola_visible_menor_5mm": 5,
            "areola_mayor_5mm": 10,
            "boton_areolar_mayor_5mm": 15,
        },
        "pliegues_plantares": {
            "sin_pliegues": 0,
            "pliegues_escasos_tercio_anterior": 5,
            "pliegues_hasta_2_3_tercios": 10,
            "pliegues_toda_planta": 15,
        },
        "formacion_pabellon_auricular": {
            "plano_sin_curvatura": 0,
            "curvatura_parcial_borde": 8,
            "curvatura_completa_tercio_superior": 16,
            "curvatura_completa": 24,
        },
        "textura_piel": {
            "muy_fina_gelatinosa": 0,
            "fina_lisa": 5,
            "gruesa_descamacion_superficial": 10,
            "gruesa_agrietada": 15,
        },
        "lanugo": {
            "sin_lanugo": 0,
            "lanugo_abundante": 4,
            "lanugo_escaso": 8,
            "lanugo_solo_en_dorso": 12,
        },
    }

    puntaje_total = 0
    detalles = []

    for parametro, opciones in puntajes.items():
        valor = datos.get(parametro)
        if valor and valor in opciones:
            p = opciones[valor]
            puntaje_total += p
            detalles.append({parametro: {"seleccion": valor, "puntaje": p}})
        else:
            detalles.append({parametro: {"seleccion": valor or "no_evaluado", "puntaje": 0}})

    semanas = 24 + (puntaje_total // 7)
    dias_extra = puntaje_total % 7

    return {
        "semanas": semanas,
        "dias": dias_extra,
        "puntaje_total": puntaje_total,
        "texto": f"{semanas} semanas + {dias_extra} días",
        "detalles": detalles,
        "parametros_evaluados": list(puntajes.keys()),
        "metodo": "capurro_somatico",
    }
