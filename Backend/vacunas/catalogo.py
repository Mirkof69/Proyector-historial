"""Vacunas del embarazo (esquema del MSP de Bolivia): el catálogo inicial.

Antes solo las creaban los comandos de demostración (`seed_carga`): una base
nueva quedaba sin ningún tipo de vacuna y no se podía registrar ninguna. El
administrador puede agregar otras desde la pantalla de Vacunas.
"""
from __future__ import annotations

#: nombre -> (dosis, días entre dosis, obligatoria en el embarazo)
VACUNAS_EMBARAZO: dict[str, tuple[int, int, bool]] = {
    "Antitetánica (dT)": (2, 28, True),
    "Influenza estacional": (1, 0, True),
    "Hepatitis B": (3, 30, False),
}


def asegurar_vacunas() -> int:
    """Crea las vacunas que falten (idempotente). Devuelve cuántas creó."""
    from .models import TipoVacuna

    nuevas = 0
    for nombre, (dosis, intervalo, obligatoria) in VACUNAS_EMBARAZO.items():
        _, creada = TipoVacuna.objects.get_or_create(nombre=nombre, defaults={
            "descripcion": f"{nombre} — esquema del embarazo (MSP Bolivia)",
            "dosis_requeridas": dosis, "intervalo_dosis_dias": intervalo, "edad_minima_aplicacion": 12,
            "contraindicaciones": "Reacción alérgica severa a dosis previa",
            "efectos_secundarios": "Dolor local, febrícula", "obligatoria_embarazo": obligatoria, "activo": True,
        })
        nuevas += creada
    return nuevas
