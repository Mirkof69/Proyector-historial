"""Fase 0 - Inventario del sistema bajo prueba, leído del código real (no escrito a mano).

Genera en docs/inventario/:
  inventario_pantallas.md, inventario_formularios.md, inventario_endpoints.md,
  matriz_roles_permisos.md, requisitos.md e inventario.json (lo usan el explorador y las pruebas).

Se ejecuta con el intérprete del sistema bajo prueba, porque introspecciona Django:
    <repo_sistema>\\Backend\\.venv\\Scripts\\python.exe tools\\inventario.py --sistema "<repo_sistema>"
No escribe nada en la base de datos: solo lee permisos y la configuración de URLs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parents[1]
SALIDA = AQUI / "docs" / "inventario"


def leer_rutas(app_routes: Path) -> list[dict]:
    """Rutas de React Router con su componente y el permiso que exige ProtectedRoute."""
    rutas = []
    fuente = app_routes.read_text(encoding="utf-8")
    # componentes auxiliares definidos en el mismo archivo que solo redirigen (p. ej. PartogramaEnDetalle)
    auxiliares = {nombre: destino.replace("${id}", ":id") for nombre, destino in re.findall(
        r"const (\w+): React\.FC = \(\) => \{.*?<Navigate to=\{?[`\"]([^`\"]+)[`\"]", fuente, re.S)}
    for linea in fuente.splitlines():
        m = re.search(r'<Route\s+path="([^"]+)"\s+element=\{(.*)\}\s*/>', linea)
        if not m:
            continue
        ruta, elemento = m.groups()
        destino = re.search(r'<Navigate to="([^"]+)"', elemento)
        permiso = re.search(r'requiredPermission="([^"]+)"', elemento)
        solo_admin = "requireAdmin" in elemento
        comp = re.findall(r"<([A-Z][A-Za-z0-9]+)", elemento)
        comp = [c for c in comp if c not in ("ProtectedRoute", "Navigate")]
        if not destino and comp and comp[0] in auxiliares:
            destino = re.match(r"(.*)", auxiliares[comp[0]])
        rutas.append({
            "ruta": "/dashboard/" + ruta if not ruta.startswith("/") else ruta,
            "componente": comp[0] if comp else "",
            "permiso": permiso.group(1) if permiso else ("(solo administrador)" if solo_admin else ""),
            "redirige_a": destino.group(1) if destino else "",
            "parametros": re.findall(r":([a-z_]+)", ruta),
        })
    return rutas


ACCIONES = {
    "crear": r"\b(Nuevo|Nueva|Crear|Registrar|Agregar)\b",
    "editar": r"\b(Editar|Actualizar|Modificar)\b",
    "eliminar": r"\b(Eliminar|Desactivar|Borrar)\b",
    "buscar": r"\b(Buscar|Search|buscar)\b",
    "filtrar": r"\b(Filtrar|Filtro|filtros)\b",
    "exportar": r"\b(Exportar|exportar|Excel|CSV)\b",
    "subir archivo": r"<Upload|Dragger|type=\"file\"",
    "imprimir": r"\b(Imprimir|PDF|imprimir)\b",
}


def archivo_de_componente(src: Path, comp: str) -> Path | None:
    cands = [p for p in src.rglob(f"{comp}.tsx") if "node_modules" not in p.parts and ".test." not in p.name]
    return cands[0] if cands else None


def acciones_de(archivo: Path | None) -> list[str]:
    if not archivo:
        return []
    txt = archivo.read_text(encoding="utf-8", errors="ignore")
    # incluye los componentes hijos de la misma carpeta (listados, filtros, modales)
    for hijo in archivo.parent.glob("**/*.tsx"):
        if hijo != archivo and ".test." not in hijo.name:
            txt += hijo.read_text(encoding="utf-8", errors="ignore")
    return [a for a, rx in ACCIONES.items() if re.search(rx, txt)]


def leer_formularios(src: Path) -> list[dict]:
    """Cada <Form.Item name=...> con su etiqueta y sus reglas de validación del frontend."""
    forms = []
    for archivo in sorted(src.rglob("*.tsx")):
        if "node_modules" in archivo.parts or ".test." in archivo.name:
            continue
        txt = archivo.read_text(encoding="utf-8", errors="ignore")
        if "<Form.Item" not in txt:
            continue
        campos = []
        for m in re.finditer(r"<Form\.Item\b", txt):
            bloque = txt[m.start(): m.start() + 900]
            siguiente = bloque.find("<Form.Item", 10)   # sin esto, un campo sin reglas heredaba las del siguiente
            if siguiente > 0:
                bloque = bloque[:siguiente]
            fin = bloque.find(">\n")
            cab = bloque[: fin if fin > 0 else 600]
            nombre = re.search(r'name=\{?\[?["\']([^"\']+)["\']', cab)
            if not nombre:
                continue
            etiqueta = re.search(r'label=["\']([^"\']+)["\']', cab) or re.search(r'label=\{["\']([^"\']+)', cab)
            reglas = re.search(r"rules=\{\[(.*?)\]\}", bloque, re.S)
            r = reglas.group(1) if reglas else ""
            campos.append({
                "campo": nombre.group(1),
                "etiqueta": etiqueta.group(1) if etiqueta else "",
                "obligatorio": "required: true" in r or "required:true" in r,
                "min": (re.search(r"\bmin:\s*([\d.]+)", r) or [None, ""])[1],
                "max": (re.search(r"\bmax:\s*([\d.]+)", r) or [None, ""])[1],
                "tipo": (re.search(r"type:\s*['\"](\w+)", r) or [None, ""])[1],
                "patron": bool(re.search(r"pattern:", r)),
                "mensajes": re.findall(r"message:\s*['\"]([^'\"]+)", r)[:2],
            })
        if campos:
            forms.append({"archivo": str(archivo.relative_to(src)).replace("\\", "/"), "campos": campos})
    return forms


def leer_endpoints() -> list[dict]:
    from django.urls import URLPattern, URLResolver, get_resolver

    salida = []

    def recorrer(patrones, prefijo=""):
        for p in patrones:
            patron = str(p.pattern)
            if isinstance(p, URLResolver):
                recorrer(p.url_patterns, prefijo + patron)
                continue
            if not isinstance(p, URLPattern):
                continue
            ruta = prefijo + patron
            if "<format>" in ruta or "<drf_format_suffix" in ruta:
                continue
            ruta = re.sub(r"\(\?P<(\w+)>[^)]*\)", r"{\1}", ruta)
            ruta = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", ruta)
            ruta = ruta.replace("^", "").replace("$", "").replace("\\", "")
            cb = p.callback
            cls = getattr(cb, "cls", None) or getattr(cb, "view_class", None)
            if cls is None:
                metodos = ["GET"]
                nombre = getattr(cb, "__name__", str(cb))
                permisos, autent = [], []
            else:
                acciones = getattr(cb, "actions", None)
                if acciones:
                    metodos = sorted(m.upper() for m in acciones)
                else:
                    metodos = sorted(m.upper() for m in getattr(cls, "http_method_names", [])
                                     if hasattr(cls, m) and m not in ("options", "head"))
                nombre = f"{cls.__module__}.{cls.__name__}"
                permisos = [getattr(c, "__name__", type(c).__name__) for c in getattr(cls, "permission_classes", [])]
                autent = [getattr(c, "__name__", type(c).__name__) for c in getattr(cls, "authentication_classes", [])]
            salida.append({"ruta": "/" + ruta.lstrip("/"), "metodos": metodos, "vista": nombre,
                           "permisos": permisos, "autenticacion": autent, "nombre": p.name or ""})

    recorrer(get_resolver().url_patterns)
    vistos, unicos = set(), []
    for e in salida:
        k = (e["ruta"], tuple(e["metodos"]))
        if k not in vistos and e["ruta"].startswith("/api"):
            vistos.add(k)
            unicos.append(e)
    return unicos


def leer_requisitos(docs: Path) -> dict:
    rf, rnf = [], []
    for l in (docs / "02_requisitos_funcionales.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (RF-\d+) \| (.*?) \| (Alta|Media|Baja) \| (.*?) \|$", l)
        if m:
            rf.append({"id": m.group(1), "descripcion": m.group(2), "prioridad": m.group(3), "verificado_por": m.group(4)})
    for l in (docs / "03_requisitos_no_funcionales.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (RNF-\d+) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|$", l)
        if m:
            rnf.append({"id": m.group(1), "categoria": m.group(2), "descripcion": m.group(3), "criterio": m.group(4),
                        "medicion": m.group(5), "verificado_por": m.group(6)})
    return {"rf": rf, "rnf": rnf}


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sistema", required=True, help="raíz del repositorio del sistema bajo prueba")
    a = ap.parse_args()
    raiz = Path(a.sistema)
    back = raiz / "Backend"
    src = back / "frontend" / "src"
    sys.path.insert(0, str(back))
    os.chdir(back)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    import django
    django.setup()
    from django.contrib.auth.models import Permission
    from django_tenants.utils import schema_context
    from usuarios import permisos_por_rol as P

    SALIDA.mkdir(parents=True, exist_ok=True)
    rutas = leer_rutas(src / "routes" / "AppRoutes.tsx")
    with schema_context("clinica"):
        todos = set(Permission.objects.values_list("codename", flat=True))
        por_rol = {rol: set(P.permisos_del_rol(rol).values_list("codename", flat=True)) for rol in P.PERMISOS_POR_ROL}
    por_rol["administrador"] = todos
    roles = ["administrador", "medico", "enfermera", "laboratorista", "recepcion"]
    for r in rutas:
        arch = archivo_de_componente(src, r["componente"]) if r["componente"] else None
        r["archivo"] = str(arch.relative_to(src)).replace("\\", "/") if arch else ""
        r["acciones"] = acciones_de(arch)
        if r["permiso"] == "(solo administrador)":
            r["roles"] = ["administrador"]
        else:
            r["roles"] = [rol for rol in roles if not r["permiso"] or r["permiso"] in por_rol[rol]]
    formularios = leer_formularios(src)
    endpoints = leer_endpoints()
    req = leer_requisitos(raiz / "docs" / "sistema")

    # ---------------------------------------------------------------- pantallas
    navegables = [r for r in rutas if not r["redirige_a"]]
    L = ["# Inventario de pantallas", "",
         f"Fuente: `Backend/frontend/src/routes/AppRoutes.tsx` (leído por `tools/inventario.py`). "
         f"{len(navegables)} rutas navegables y {len(rutas) - len(navegables)} redirecciones. "
         "El permiso es el que exige `ProtectedRoute`; los roles salen de `usuarios/permisos_por_rol.py`.", "",
         "| # | Ruta | Componente | Permiso | Roles con acceso | Acciones detectadas |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(navegables, 1):
        L.append(f"| {i} | `{r['ruta']}` | {r['componente']} | {r['permiso'] or '(sesión)'} | {', '.join(r['roles'])} | "
                 f"{', '.join(r['acciones']) or '-'} |")
    L += ["", "## Redirecciones", "", "| Ruta | Redirige a |", "|---|---|"]
    L += [f"| `{r['ruta']}` | `{r['redirige_a']}` |" for r in rutas if r["redirige_a"]]
    (SALIDA / "inventario_pantallas.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- formularios
    total_campos = sum(len(f["campos"]) for f in formularios)
    L = ["# Inventario de formularios", "",
         f"{len(formularios)} archivos con formulario y {total_campos} campos (`<Form.Item>` de Ant Design). "
         "Las reglas son las del frontend; el backend valida además en sus serializers y modelos, "
         "lo que se prueba en las suites de API.", ""]
    for f in formularios:
        L += [f"## `{f['archivo']}`", "", "| Campo | Etiqueta | Obligatorio | Mín | Máx | Tipo | Patrón | Mensaje |",
              "|---|---|---|---|---|---|---|---|"]
        for c in f["campos"]:
            L.append(f"| {c['campo']} | {c['etiqueta']} | {'Sí' if c['obligatorio'] else 'No'} | {c['min']} | {c['max']} | "
                     f"{c['tipo']} | {'Sí' if c['patron'] else 'No'} | {' / '.join(c['mensajes'])} |")
        L.append("")
    (SALIDA / "inventario_formularios.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- endpoints
    L = ["# Inventario de endpoints", "",
         f"{len(endpoints)} rutas de la API leídas del resolvedor de URLs de Django. "
         "Autenticación por defecto: cookie httpOnly con JWT (`CookieJWTAuthentication`) y CSRF en métodos de escritura. "
         "Los permisos por rol los decide `core.permissions.FetalMedicalPermission` según la tabla de roles.", "",
         "| # | Ruta | Métodos | Vista | Permisos |", "|---|---|---|---|---|"]
    for i, e in enumerate(endpoints, 1):
        L.append(f"| {i} | `{e['ruta']}` | {', '.join(e['metodos'])} | {e['vista'].split('.')[-1]} | "
                 f"{', '.join(e['permisos']) or '(por defecto)'} |")
    (SALIDA / "inventario_endpoints.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- roles
    L = ["# Matriz de roles y permisos", "",
         "Fuente: `Backend/usuarios/permisos_por_rol.py` (la misma tabla que aplica la API). "
         "El administrador tiene todos los permisos. «V» = ver, «C» = crear, «E» = editar; el borrado solo lo tiene "
         "el administrador.", ""]
    apps = sorted({a for d in P.PERMISOS_POR_ROL.values() for a in d})
    L += ["| Módulo | " + " | ".join(roles) + " |", "|---" * (len(roles) + 1) + "|"]
    for app in apps:
        fila = [app, "V C E B"]
        for rol in roles[1:]:
            acc = P.PERMISOS_POR_ROL.get(rol, {}).get(app, ())
            fila.append(" ".join({"view": "V", "add": "C", "change": "E"}[x] for x in acc) or "-")
        L.append("| " + " | ".join(fila) + " |")
    L += ["", "## Pantallas por rol", "", "| Rol | Pantallas con acceso | Pantallas sin acceso |", "|---|---|---|"]
    for rol in roles:
        si = sum(rol in r["roles"] for r in navegables)
        L.append(f"| {rol} | {si} | {len(navegables) - si} |")
    L += ["", "Solo el administrador ve: " + ", ".join(f"`{x}`" for x in P.SOLO_ADMINISTRADOR) + "."]
    (SALIDA / "matriz_roles_permisos.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- requisitos
    L = ["# Requisitos", "",
         "Fuente: `docs/sistema/02_requisitos_funcionales.md` y `03_requisitos_no_funcionales.md` del sistema. "
         "Se conservan los ID originales (RF-XX, RNF-XX) para mantener la trazabilidad con el informe.", "",
         "## Funcionales", "", "| ID | Requisito | Prioridad | Casos que lo verifican |", "|---|---|---|---|"]
    L += [f"| {r['id']} | {r['descripcion']} | {r['prioridad']} | {r['verificado_por']} |" for r in req["rf"]]
    L += ["", "## No funcionales", "", "| ID | Categoría | Requisito | Criterio | Casos |", "|---|---|---|---|---|"]
    L += [f"| {r['id']} | {r['categoria']} | {r['descripcion']} | {r['criterio']} | {r['verificado_por']} |" for r in req["rnf"]]
    (SALIDA / "requisitos.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    json.dump({"rutas": rutas, "formularios": formularios, "endpoints": endpoints, "requisitos": req,
               "roles": roles, "permisos_por_rol": {k: sorted(v) for k, v in por_rol.items() if k != "administrador"},
               "todos_los_permisos": sorted(todos)},
              open(SALIDA / "inventario.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"pantallas={len(navegables)} redirecciones={len(rutas) - len(navegables)} formularios={len(formularios)} "
          f"campos={total_campos} endpoints={len(endpoints)} roles={len(roles)} RF={len(req['rf'])} RNF={len(req['rnf'])}")
    for rol in roles:
        print(f"  {rol}: {sum(rol in r['roles'] for r in navegables)} pantallas")


if __name__ == "__main__":
    principal()
