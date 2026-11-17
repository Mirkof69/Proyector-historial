r"""Sonda de DOM: inicia sesión con un rol y vuelca, por pantalla, los campos, botones y pestañas que se ven.

Sirve para escribir los Page Objects con los localizadores reales (no se adivinan). Uso:
    .venv\Scripts\python tools\sonda_dom.py --rol medico /dashboard/embarazos/nuevo /dashboard/triaje/nuevo
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402

from pages.base_page import BasePage  # noqa: E402
from pages.login_page import LoginPage  # noqa: E402
from utils import config  # noqa: E402
from utils.driver_factory import crear_driver  # noqa: E402

JS = r"""
const vis = e => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length);
const txt = e => (e.innerText || e.value || e.getAttribute('aria-label') || '').trim().replace(/\s+/g,' ').slice(0,60);
return {
  titulo: [...document.querySelectorAll('h1,h2,h3,h4,.ant-page-header-heading-title,.ant-card-head-title')].filter(vis).map(txt).slice(0,15),
  campos: [...document.querySelectorAll('input,textarea,select')].filter(e=>e.id||e.name).map(e=>({id:e.id,name:e.name,tipo:e.type,
           rol:e.getAttribute('role'),ph:e.placeholder,visible:vis(e),
           etiqueta:(document.querySelector('label[for="'+e.id+'"]')||{}).innerText||''})).slice(0,90),
  botones: [...document.querySelectorAll('button')].filter(vis).map(txt).filter(Boolean).slice(0,60),
  pestanas: [...document.querySelectorAll('.ant-tabs-tab')].map(txt),
  pasos: [...document.querySelectorAll('.ant-steps-item-title')].map(txt),
  buscadores: [...document.querySelectorAll('input[placeholder]')].filter(vis).filter(e=>e.type==='text'||e.type==='search')
               .map(e=>({ph:e.placeholder,id:e.id,name:e.name})),
  filtros: [...document.querySelectorAll('.ant-select')].filter(vis).map(e=>(e.querySelector('.ant-select-selection-placeholder, .ant-select-selection-item')||{}).innerText||'').slice(0,8),
  filas: document.querySelectorAll('.ant-table-tbody tr.ant-table-row').length,
  columnas: [...document.querySelectorAll('.ant-table-thead th')].filter(vis).map(txt).filter(Boolean).slice(0,10),
  con_name: [...document.querySelectorAll('[name]')].filter(e=>e.tagName!=='META').map(e=>e.tagName.toLowerCase()+'[name='+e.getAttribute('name')+']').slice(0,12),
};
"""


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rol", default="medico")
    ap.add_argument("--salida", default="")
    ap.add_argument("rutas", nargs="+")
    a = ap.parse_args()
    d = crear_driver()
    try:
        assert LoginPage(d).iniciar_sesion(config.ROLES[a.rol]) == "panel"
        res = {}
        for ruta in a.rutas:
            BasePage(d).abrir(ruta)
            WebDriverWait(d, 20).until(lambda x: "Cargando" not in x.find_element("tag name", "body").text)
            res[ruta] = d.execute_script(JS)
            res[ruta]["url_final"] = d.current_url.replace(config.SUT_URL, "")
        texto = json.dumps(res, ensure_ascii=False, indent=1)
        if a.salida:
            Path(a.salida).write_text(texto, encoding="utf-8")
        else:
            print(texto)
    finally:
        d.quit()


if __name__ == "__main__":
    principal()
