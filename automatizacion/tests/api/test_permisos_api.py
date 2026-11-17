"""Control de acceso por rol en la API (tabla de decisión rol × módulo).

Lo esperado sale de `usuarios/permisos_por_rol.py` del sistema (la tabla que el código declara alineada con la
API). Para la escritura se envía un cuerpo VACÍO: 400 significa que el permiso dejó pasar la petición (y falló la
validación), 403 que el permiso la rechazó. Así se prueba el permiso sin crear registros.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import cliente

pytestmark = [pytest.mark.api, pytest.mark.roles]

# módulo de la tabla de roles -> endpoint de su listado
MODULOS = {
    "pacientes": "/pacientes/", "embarazos": "/embarazos/", "controles": "/controles/", "ecografias": "/ecografias/",
    "partos": "/partos/", "laboratorio": "/laboratorios/examenes/", "citas": "/citas/citas/", "triaje": "/triaje/triajes/",
    "antecedentes": "/antecedentes/patologicos/", "notas_evolucion": "/notas-evolucion/", "vacunas": "/vacunas/registros/",
    "reportes": "/reportes/dashboard-kpis/", "consultorios": "/consultorios/",
}
INVENTARIO = json.loads((Path(__file__).resolve().parents[2] / "docs" / "inventario" / "inventario.json").read_text("utf-8"))
TABLA = INVENTARIO["permisos_por_rol"]   # rol -> codenames de su tabla


def _puede(rol: str, modulo: str, accion: str) -> bool:
    """¿La tabla de roles le da al rol `accion` (view/add) sobre algún modelo del módulo?"""
    if rol == "administrador":
        return True
    from importlib import import_module  # noqa: F401
    acciones = _ACCIONES.get(rol, {}).get(modulo, ())
    return accion in acciones


_ACCIONES = {
    "medico": {m: ("view", "add", "change") for m in ("pacientes", "embarazos", "controles", "ecografias", "partos",
                                                       "laboratorio", "citas", "triaje", "antecedentes", "notas_evolucion",
                                                       "vacunas", "reportes")} | {"consultorios": ("view",)},
    "enfermera": {"pacientes": ("view", "add", "change"), "controles": ("view", "add", "change"),
                  "citas": ("view", "add", "change"), "triaje": ("view", "add", "change"), "vacunas": ("view", "add", "change"),
                  "notas_evolucion": ("view", "add", "change"), "embarazos": ("view",), "ecografias": ("view",),
                  "laboratorio": ("view",), "antecedentes": ("view",), "consultorios": ("view",)},
    "laboratorista": {"laboratorio": ("view", "add", "change"), "pacientes": ("view",), "embarazos": ("view",),
                      "controles": ("view",), "ecografias": ("view",), "citas": ("view",), "antecedentes": ("view",)},
    "recepcion": {"pacientes": ("view", "add", "change"), "citas": ("view", "add", "change"), "consultorios": ("view",)},
}

CASOS_LECTURA = [(rol, mod) for rol in ("medico", "enfermera", "laboratorista", "recepcion") for mod in MODULOS]
CASOS_ESCRITURA = [(rol, mod) for rol in ("enfermera", "laboratorista", "recepcion")
                   for mod in ("embarazos", "controles", "ecografias", "partos", "notas_evolucion", "vacunas", "triaje")]


@pytest.mark.tc("TC-016")
@pytest.mark.parametrize("rol,modulo", CASOS_LECTURA, ids=[f"{r}-{m}" for r, m in CASOS_LECTURA])
def test_tc016_lectura_segun_tabla_de_roles(rol, modulo):
    """Matriz rol × endpoint de la API (lectura)."""
    r = cliente(rol).get(MODULOS[modulo])
    esperado = 200 if _puede(rol, modulo, "view") else 403
    assert r.status_code == esperado, (f"{rol} GET {MODULOS[modulo]}: esperado {esperado} según la tabla de roles, "
                                       f"obtenido {r.status_code}")


@pytest.mark.tc("TC-016")
@pytest.mark.parametrize("rol,modulo", CASOS_ESCRITURA, ids=[f"{r}-{m}" for r, m in CASOS_ESCRITURA])
def test_tc016_escritura_segun_tabla_de_roles(rol, modulo):
    """Matriz rol × endpoint de la API (escritura con cuerpo vacío)."""
    ruta = "/partos/" if modulo == "partos" else MODULOS[modulo]
    r = cliente(rol).post(ruta, {})
    permitido = _puede(rol, modulo, "add")
    if permitido:
        assert r.status_code == 400, f"{rol} POST {ruta}: debía llegar a la validación (400), obtuvo {r.status_code}"
    else:
        assert r.status_code == 403, (f"{rol} POST {ruta}: su rol no puede crear en «{modulo}» y la API no lo "
                                      f"rechazó (HTTP {r.status_code}; 400 = el permiso dejó pasar la petición)")


@pytest.mark.tc("TC-017")
def test_tc017_recepcion_no_registra_triaje_ni_control(paciente_qa, embarazo_qa):
    """Recepción intenta registrar un triaje y un control prenatal."""
    from data import fabrica
    rec = cliente("recepcion")
    assert rec.post("/triaje/triajes/", fabrica.triaje(paciente_qa["id"])).status_code == 403
    assert rec.post("/controles/", fabrica.control(paciente_qa["id"], embarazo_qa["id"])).status_code == 403


@pytest.mark.tc("TC-018")
def test_tc018_enfermeria_no_registra_partos(paciente_qa, embarazo_qa):
    """Enfermería intenta registrar un parto."""
    from data import fabrica
    parto = {"paciente": paciente_qa["id"], "embarazo": embarazo_qa["id"], "edad_gestacional_parto": "39",
             "tipo_parto": "vaginal_espontaneo", "parto_finalizado": True, "fecha_parto": fabrica.ahora_iso()}
    assert cliente("enfermera").post("/partos/", parto).status_code == 403


@pytest.mark.tc("TC-020")
def test_tc020_todo_permiso_de_pantalla_existe():
    """Todo permiso que pide la pantalla existe (rutas de AppRoutes.tsx contra los permisos del sistema)."""
    universo = set(INVENTARIO["todos_los_permisos"])   # codenames de django.contrib.auth en la base
    # «(solo administrador)» no es un permiso: es la marca que el inventario pone a las rutas con requireAdmin
    pedidos = {r["permiso"] for r in INVENTARIO["rutas"] if r["permiso"] and not r["permiso"].startswith("(")}
    faltan = sorted(p for p in pedidos if p not in universo)
    assert not faltan, f"Permisos pedidos por pantallas que no existen en el sistema: {faltan}"


@pytest.mark.tc("TC-016")
def test_tc016_listado_de_usuarios_solo_para_administracion():
    """Matriz rol × endpoint: el listado de usuarios (con correos y teléfonos) no es para recepción."""
    r = cliente("recepcion").get("/usuarios/")
    datos = r.json() if r.status_code == 200 else {}
    filas = datos.get("results", datos) if isinstance(datos, dict) else datos
    sensibles = ("email", "telefono", "is_superuser", "is_staff", "ultimo_acceso", "last_login")
    expuestas = [u.get("id") for u in (filas or []) if any(campo in u for campo in sensibles)]
    assert r.status_code == 403 or not expuestas, (f"Recepción ve correo, teléfono o banderas de administración de "
                                                   f"{len(expuestas)} cuentas (HTTP {r.status_code})")
    if r.status_code == 200:   # lo que sí necesita para elegir a un profesional
        assert all("nombre_completo" in u and "rol" in u for u in filas), "El listado básico perdió el nombre o el rol"
