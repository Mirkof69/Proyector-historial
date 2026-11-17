"""Roles y pantallas por la interfaz: menú por rol, URL prohibidas y carga sana de las pantallas principales.

El menú se compara con la matriz de roles del inventario (docs/inventario/inventario.json, generada del código):
un ítem del menú que lleva a una pantalla que el rol no puede abrir es un defecto de navegación.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from selenium.webdriver.common.by import By

from components.menu_lateral import MenuLateral
from conftest import cliente
from pages.pantalla_page import PantallaPage
from utils import config

pytestmark = [pytest.mark.ui, pytest.mark.roles]

INVENTARIO = json.loads((Path(__file__).resolve().parents[2] / "docs" / "inventario" / "inventario.json")
                        .read_text(encoding="utf-8"))
ROLES = list(config.ROLES)


def _permitidas(rol: str) -> set[str]:
    """Rutas que el rol puede abrir; una redirección vale si su destino es abrible."""
    directas = {r["ruta"] for r in INVENTARIO["rutas"] if rol in r["roles"] and not r["redirige_a"]}
    for r in INVENTARIO["rutas"]:
        if r["redirige_a"] and r["redirige_a"].split("?")[0] in directas:
            directas.add(r["ruta"])
    return directas


@pytest.mark.smoke
@pytest.mark.tc("TC-014")
@pytest.mark.parametrize("rol", ROLES)
def test_tc014_menu_segun_rol(navegador, rol):
    """Cada rol ve en el menú solo los módulos que puede abrir."""
    d = navegador(rol)
    PantallaPage(d).abrir("/dashboard/home")
    menu = MenuLateral(d).rutas_visibles()
    PantallaPage(d).evidencia(f"menu-{rol}", f"Menú lateral del rol {rol}")
    assert menu, f"El menú de {rol} está vacío"
    sin_acceso = sorted(r for r in menu if r.split("?")[0] not in _permitidas(rol))
    assert not sin_acceso, f"El menú de {rol} ofrece pantallas que su rol no puede abrir: {sin_acceso}"
    clinicos = {"/dashboard/controles", "/dashboard/embarazos", "/dashboard/partos", "/dashboard/ecografias"}
    if rol == "recepcion":
        assert not (menu & clinicos), f"Recepción ve módulos clínicos: {sorted(menu & clinicos)}"
    if rol == "enfermera":
        assert not (menu & {"/dashboard/partos", "/dashboard/reportes"}), "Enfermería ve Partos o Reportes"


PROHIBIDAS = [("recepcion", "/dashboard/controles"), ("recepcion", "/dashboard/partos"),
              ("recepcion", "/dashboard/auditoria"), ("enfermera", "/dashboard/partos"),
              ("enfermera", "/dashboard/reportes"), ("laboratorista", "/dashboard/notas-evolucion"),
              ("laboratorista", "/dashboard/vacunas"), ("medico", "/dashboard/auditoria"),
              ("medico", "/dashboard/usuarios")]


@pytest.mark.tc("TC-015")
@pytest.mark.parametrize("rol,ruta", PROHIBIDAS, ids=[f"{r}-{u.rsplit('/', 1)[-1]}" for r, u in PROHIBIDAS])
def test_tc015_url_prohibida_muestra_acceso_denegado(navegador, rol, ruta):
    """Escribir la URL de un módulo no permitido muestra acceso denegado y ningún dato."""
    d = navegador(rol)
    pag = PantallaPage(d)
    salud = pag.abrir_y_medir(ruta)
    pag.evidencia(f"denegada-{rol}", f"{rol} escribe {ruta}")
    assert salud.denegada, f"{rol} abrió {ruta} (terminó en {salud.url_final})"
    assert not pag.filas_tabla(3), f"{rol} ve filas de datos en {ruta}"


def _sana(salud, que: str):
    assert not salud.problemas(), f"{que}: {'; '.join(salud.problemas())}"


@pytest.mark.citas
@pytest.mark.tc("TC-048")
@pytest.mark.parametrize("ruta", ["/dashboard/citas", "/dashboard/citas/hoy", "/dashboard/citas/calendario"])
def test_tc048_agenda_de_citas(navegador, ruta):
    """Agenda de citas, citas de hoy y calendario cargan sin errores (recepción)."""
    d = navegador("recepcion")
    pag = PantallaPage(d)
    salud = pag.abrir_y_medir(ruta)
    pag.evidencia(ruta.rsplit("/", 1)[-1], f"Recepción abre {ruta}")
    _sana(salud, ruta)


@pytest.mark.laboratorio
@pytest.mark.tc("TC-058")
def test_tc058_laboratorio_para_el_laboratorista(navegador):
    """El laboratorista abre el listado de laboratorio sin errores."""
    d = navegador("laboratorista")
    pag = PantallaPage(d)
    salud = pag.abrir_y_medir("/dashboard/laboratorio")
    pag.evidencia("laboratorio", "Listado de laboratorio")
    _sana(salud, "Laboratorio")
    assert pag.filas_tabla() or pag.tabla_vacia(), "El listado no muestra filas ni el aviso de vacío"


@pytest.mark.ecografia_ia
@pytest.mark.tc("TC-078")
def test_tc078_guia_de_ia_con_fiabilidad(navegador):
    """La Guía de IA lista los modelos con la cifra medida de cada uno."""
    d = navegador("medico")
    pag = PantallaPage(d)
    salud = pag.abrir_y_medir("/dashboard/ia-guia")
    pag.evidencia("guia", "Guía de IA")
    _sana(salud, "Guía de IA")
    texto = d.find_element(*pag.CONTENIDO).text
    usar = d.find_elements(By.XPATH, "//button[normalize-space(.)='Usar ahora']")
    assert len(usar) >= 10, f"La guía lista {len(usar)} modelos utilizables"
    assert "%" in texto, "La guía no muestra la cifra medida de los modelos"


@pytest.mark.tc("TC-090")
def test_tc090_partos_listado_y_detalle(navegador):
    """El médico abre el listado de partos y el detalle de uno."""
    d = navegador("medico")
    pag = PantallaPage(d)
    _sana(pag.abrir_y_medir("/dashboard/partos"), "Listado de partos")
    assert pag.filas_tabla(), "El listado de partos está vacío"
    pid = cliente("medico").lista("/partos/", page_size=1)[0]["id"]
    salud = pag.abrir_y_medir(f"/dashboard/partos/{pid}")
    pag.evidencia("detalle", f"Detalle del parto {pid}")
    _sana(salud, f"Detalle del parto {pid}")


@pytest.mark.reportes
@pytest.mark.tc("TC-099")
def test_tc099_centro_de_reportes(navegador):
    """El Centro de reportes abre cada pestaña sin errores."""
    d = navegador("administrador")
    pag = PantallaPage(d)
    _sana(pag.abrir_y_medir("/dashboard/reportes"), "Centro de reportes")
    nombres = pag.pestanas()
    assert len(nombres) >= 5, f"El Centro de reportes muestra {len(nombres)} pestañas"
    malas = {}
    for nombre in nombres:
        salud = pag.abrir_pestana(nombre)
        pag.evidencia(f"pestana-{nombres.index(nombre) + 1}", f"Pestaña «{nombre}»")
        if salud.problemas():
            malas[nombre] = salud.problemas()
    assert not malas, f"Pestañas con errores: {malas}"
