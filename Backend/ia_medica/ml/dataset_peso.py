"""Construye la tabla de entrenamiento: una fila por recién nacido.

Qué hace
--------
Recorre los recién nacidos, y para cada uno busca la ecografía con biometría
más cercana ANTERIOR al parto. Esa es la pregunta clínica real: *con la
ecografía de hoy, ¿cuánto va a pesar?*

    RecienNacido ──> Parto ──> Embarazo ──> Paciente
                                   └──> Ecografía ──> BiometríaFetal
                                   └──> ControlPrenatal
                       Paciente ──> AntecedentePatologico (tipo="personal")

Lo que se descarta, y por qué
-----------------------------
Cada exclusión se cuenta y se imprime. Un dataset del que no se sabe qué se
tiró es un dataset en el que no se puede confiar.
"""
from __future__ import annotations

import logging
from contextlib import nullcontext
from dataclasses import dataclass

from ia_medica.ml.caracteristicas_peso import COLUMNAS_DATASET

logger = logging.getLogger(__name__)

#: Ventana entre la ecografía y el parto, en días.
#:
#: Menos de 0 significa que la ecografía es posterior al parto: error de
#: captura. Más de 120 días son 17 semanas de distancia, y una biometría de
#: hace cuatro meses no dice gran cosa del peso al nacer.
DIAS_MINIMOS = 0
DIAS_MAXIMOS = 120

#: La ventana de los estudios de peso al nacer por ecografía: la biometría de
#: la última semana. Se pide con `construir_dataset_peso --max-dias 7`.
DIAS_ECOGRAFIA_DE_INGRESO = 7

#: Edad gestacional mínima de la ecografía utilizable.
#: Hadlock está validado desde las 20 semanas; por debajo la biometría no
#: proyecta peso al término de forma fiable.
EG_ECO_MINIMA = 20


@dataclass
class Descartes:
    """Cuenta por qué se perdió cada fila. Se imprime siempre."""

    no_vivos: int = 0
    multiples: int = 0
    sin_embarazo: int = 0
    sin_biometria: int = 0
    eco_fuera_de_ventana: int = 0
    peso_invalido: int = 0
    sin_fecha_parto: int = 0

    def total(self) -> int:
        return sum(cantidad for _, cantidad in self.como_lineas())

    def como_lineas(self) -> list[tuple[str, int]]:
        return [
            ("no vivos", self.no_vivos),
            ("múltiples", self.multiples),
            ("sin embarazo resoluble", self.sin_embarazo),
            ("sin biometría utilizable", self.sin_biometria),
            ("ecografía fuera de ventana", self.eco_fuera_de_ventana),
            ("peso fuera de rango", self.peso_invalido),
            ("sin fecha de parto", self.sin_fecha_parto),
        ]


def esquemas_a_recorrer(tenant: str | None = None) -> list[str | None]:
    """Los esquemas a recorrer, o `[None]` si no hay multi-tenancy.

    `None` significa «el esquema actual» y se combina con `nullcontext()`.

    Hace falta porque la suite de tests corre sobre SQLite **sin
    django_tenants** (ver `settings.py`): llamar ahí a `get_tenant_model()`
    lanzaría, y todo el módulo dejaría de ser testeable.
    """
    from django.conf import settings

    if "django_tenants" not in settings.INSTALLED_APPS:
        return [None]

    from django_tenants.utils import get_tenant_model

    if tenant:
        return [tenant]
    return [
        t.schema_name
        for t in get_tenant_model().objects.exclude(schema_name="public")
    ]


def contexto_de_esquema(esquema: str | None):
    """`schema_context(esquema)`, o un contexto vacío si no hay tenants."""
    if esquema is None:
        return nullcontext()
    from django_tenants.utils import schema_context

    return schema_context(esquema)


def _semanas_al_parto(parto) -> float | None:
    """Edad gestacional del parto, en semanas con decimales.

    `Parto.edad_gestacional_parto` es un `CharField` con formato `"39+2"`, no
    un número. El modelo ya trae el parser.
    """
    try:
        semanas, dias = parto.obtener_semanas_dias_gestacion()
    except Exception:  # noqa: BLE001 - un dato mal formado no puede tumbar el ETL
        return None
    if semanas is None:
        return None
    return float(semanas) + float(dias or 0) / 7.0


def _edad_a_fecha(fecha_nacimiento, fecha_referencia) -> int | None:
    """Edad en años en una fecha concreta.

    **No usar `Paciente.edad`**: esa property compara contra `hoy`, así que un
    parto de hace tres años quedaría etiquetado con la edad actual de la madre.
    Es una fuga temporal que no lanza ninguna excepción y envenena el dataset
    entero.
    """
    if not fecha_nacimiento or not fecha_referencia:
        return None
    años = fecha_referencia.year - fecha_nacimiento.year
    if (fecha_referencia.month, fecha_referencia.day) < (
        fecha_nacimiento.month, fecha_nacimiento.day
    ):
        años -= 1
    return años


def _antecedentes_personales(paciente_id, cache: dict) -> dict[str, int]:
    """Los cuatro antecedentes patológicos, como 0/1.

    Se filtra por `tipo="personal"`. **Sin ese filtro se mezclarían los
    antecedentes de familiares** (`antecedentes/models.py:150`) y «diabetes»
    pasaría a significar «alguien de su familia tuvo diabetes».

    Si la paciente no tiene ningún registro, se devuelve 0 en todo. Conviene
    saber que en este sistema «no registrado» y «no tiene» son
    indistinguibles: es una limitación de los datos, no una decisión de
    modelado.
    """
    return cache.get(paciente_id, {
        "diabetes": 0, "hipertension": 0,
        "preeclampsia_previa": 0, "diabetes_gestacional_previa": 0,
    })


def construir(esquema: str | None = None, *, incluir_multiples: bool = False,
              dias_maximos: int = DIAS_MAXIMOS):
    """Construye el dataset de un esquema. Devuelve `(filas, descartes)`.

    `filas` es una lista de dicts con las claves de `COLUMNAS_DATASET`.
    """
    from antecedentes.models import AntecedentePatologico
    from controles.models import ControlPrenatal
    from ecografias.models import Ecografia
    from ecografias.peso_fetal import hadlock_1985_4p, proyectar_peso
    from partos.models import RecienNacido

    from core.simulacion.curvas_obstetricas import clasificar_peso_nacimiento

    descartes = Descartes()
    filas: list[dict] = []

    recien_nacidos = list(
        RecienNacido.objects
        .select_related("parto", "parto__embarazo", "parto__paciente")
        .all(),
    )
    if not recien_nacidos:
        return filas, descartes

    # --- Precarga en bloque. Sin esto son N+1 consultas por cada uno de los
    # --- cinco joins: con 400 recién nacidos, unas 3.000 consultas.
    ids_pacientes = {rn.parto.paciente_id for rn in recien_nacidos if rn.parto}

    antecedentes_por_paciente: dict[int, dict[str, int]] = {}
    for a in AntecedentePatologico.objects.filter(
        paciente_id__in=ids_pacientes, tipo="personal",
    ):
        actual = antecedentes_por_paciente.setdefault(a.paciente_id, {
            "diabetes": 0, "hipertension": 0,
            "preeclampsia_previa": 0, "diabetes_gestacional_previa": 0,
        })
        # OR sobre todos los registros personales de esa paciente.
        for campo in actual:
            if getattr(a, campo, False):
                actual[campo] = 1

    ecos_por_embarazo: dict[int, list] = {}
    for eco in Ecografia.objects.select_related("biometria").filter(
        embarazo__paciente_id__in=ids_pacientes,
    ):
        if getattr(eco, "biometria", None) is None:
            continue
        ecos_por_embarazo.setdefault(eco.embarazo_id, []).append(eco)

    controles_por_embarazo: dict[int, list] = {}
    for c in ControlPrenatal.objects.filter(paciente_id__in=ids_pacientes):
        controles_por_embarazo.setdefault(c.embarazo_id, []).append(c)

    for rn in recien_nacidos:
        parto = rn.parto
        if parto is None:
            descartes.sin_embarazo += 1
            continue

        if rn.estado_nacimiento != "vivo":
            # Un mortinato tiene otra distribución de peso, y muchas veces el
            # bajo peso es consecuencia y no predicción.
            descartes.no_vivos += 1
            continue

        embarazo = parto.embarazo
        if embarazo is None:
            # `Parto.embarazo` es nullable (`partos/models.py:100`). Inventar
            # un join por proximidad de fechas metería biometría de otro
            # embarazo: el peor error posible aquí, y silencioso.
            descartes.sin_embarazo += 1
            continue

        es_multiple = (
            embarazo.tipo_embarazo != "simple" or (rn.numero_gemelo or 1) > 1
        )
        if es_multiple and not incluir_multiples:
            # `BiometriaFetal` es OneToOne con `Ecografia`, así que en un
            # gemelar NO se puede saber a cuál de los dos fetos corresponde la
            # medida. Es ruido de etiqueta irreducible, no una decisión de
            # modelado.
            descartes.multiples += 1
            continue

        if not parto.fecha_parto:
            descartes.sin_fecha_parto += 1
            continue

        if not (300 <= (rn.peso_nacimiento or 0) <= 6000):
            descartes.peso_invalido += 1
            continue

        fecha_parto = parto.fecha_parto.date() if hasattr(
            parto.fecha_parto, "date") else parto.fecha_parto

        # --- La ecografía: la más cercana ANTERIOR al parto, con las 4 medidas
        mejor_eco, mejor_dias = None, None
        for eco in ecos_por_embarazo.get(embarazo.id, []):
            b = eco.biometria
            if None in (b.diametro_biparietal, b.circunferencia_cefalica,
                        b.circunferencia_abdominal, b.longitud_femur):
                continue
            if (eco.edad_gestacional_semanas or 0) < EG_ECO_MINIMA:
                continue
            dias = (fecha_parto - eco.fecha_ecografia).days
            if not (DIAS_MINIMOS <= dias <= dias_maximos):
                continue
            if mejor_dias is None or dias < mejor_dias:
                mejor_eco, mejor_dias = eco, dias

        if mejor_eco is None:
            # Distinguir "no tenía biometría" de "la tenía pero fuera de
            # ventana" cuesta poco y dice mucho sobre la calidad del registro.
            hubo_alguna = bool(ecos_por_embarazo.get(embarazo.id))
            if hubo_alguna:
                descartes.eco_fuera_de_ventana += 1
            else:
                descartes.sin_biometria += 1
            continue

        b = mejor_eco.biometria
        dbp = float(b.diametro_biparietal)
        cc = float(b.circunferencia_cefalica)
        ca = float(b.circunferencia_abdominal)
        lf = float(b.longitud_femur)

        semanas_parto = _semanas_al_parto(parto)
        if semanas_parto is None:
            descartes.sin_fecha_parto += 1
            continue

        paciente = parto.paciente

        # IMC pregestacional; si falta, se deja NaN y el modelo lo maneja.
        imc = None
        peso_pre, talla_cm = embarazo.peso_pregestacional, embarazo.talla_materna
        if not (peso_pre and talla_cm):
            # Muchas veces el peso previo y la talla se anotan en el primer
            # control prenatal y no en el embarazo. Antes los controles se
            # cargaban aquí y no se usaban: el IMC salía vacío en el 100 %.
            for c in sorted(controles_por_embarazo.get(embarazo.id, []),
                            key=lambda c: c.fecha_control):
                if c.peso_pregestacional and c.talla:
                    peso_pre, talla_cm = c.peso_pregestacional, c.talla
                    break
        if peso_pre and talla_cm:
            talla_m = float(talla_cm) / 100.0
            if talla_m > 0:
                imc = float(peso_pre) / (talla_m**2)

        antecedentes = _antecedentes_personales(
            paciente.id, antecedentes_por_paciente,
        )

        eg_eco = float(mejor_eco.edad_gestacional_semanas or 0) + float(
            mejor_eco.edad_gestacional_dias or 0) / 7.0
        peso_hadlock = hadlock_1985_4p(dbp, cc, ca, lf)

        filas.append({
            "tenant": esquema or "unico",
            # La clave del split: todas las filas de la misma paciente tienen
            # que caer del mismo lado. Los IDs se repiten entre esquemas.
            "grupo": f"{esquema or 'unico'}:{paciente.id}",
            "recien_nacido_id": rn.id,
            "paciente_id": paciente.id,
            "ecografia_id": mejor_eco.id,
            "es_sintetico": int("[SEED-CARGA]" in (rn.observaciones_rn or "")),
            "fecha_parto": fecha_parto.isoformat(),

            "dbp_mm": dbp,
            "cc_mm": cc,
            "ca_mm": ca,
            "lf_mm": lf,
            "relacion_cc_ca": round(cc / ca, 4) if ca else None,
            "relacion_lf_ca": round(lf / ca, 4) if ca else None,
            "peso_hadlock_g": peso_hadlock,

            "eg_eco_semanas": round(eg_eco, 2),
            "eg_al_nacer_semanas": round(semanas_parto, 2),

            "edad_materna": _edad_a_fecha(
                paciente.fecha_nacimiento, mejor_eco.fecha_ecografia,
            ),
            "imc_pregestacional": round(imc, 2) if imc else None,
            "numero_para": embarazo.numero_para,
            "numero_abortos": embarazo.numero_abortos,
            "numero_cesareas": embarazo.numero_cesareas,

            **antecedentes,

            # El comparador: lo que diria la practica clinica proyectando
            # Hadlock desde el dia de la eco hasta la semana del parto.
            "peso_hadlock_proyectado_g": proyectar_peso(
                peso_hadlock, eg_eco, semanas_parto,
            ),

            "peso_nacimiento_g": rn.peso_nacimiento,
            "clase_peso": clasificar_peso_nacimiento(rn.peso_nacimiento),
        })

    return filas, descartes


def construir_todos(tenant: str | None = None, *, incluir_multiples: bool = False,
                    dias_maximos: int = DIAS_MAXIMOS):
    """Recorre los esquemas y concatena. Devuelve `(filas, {esquema: descartes})`."""
    todas: list[dict] = []
    por_esquema: dict[str, Descartes] = {}

    for esquema in esquemas_a_recorrer(tenant):
        with contexto_de_esquema(esquema):
            filas, descartes = construir(
                esquema, incluir_multiples=incluir_multiples, dias_maximos=dias_maximos,
            )
        todas.extend(filas)
        por_esquema[esquema or "unico"] = descartes

    return todas, por_esquema


def a_dataframe(filas: list[dict]):
    """Las filas como `DataFrame`, con las columnas en el orden del contrato."""
    import pandas as pd

    if not filas:
        return pd.DataFrame(columns=list(COLUMNAS_DATASET))
    return pd.DataFrame(filas)[list(COLUMNAS_DATASET)]
