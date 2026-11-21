"""Todo permiso que pide el frontend existe en Django.

Fallo que previene (encontrado el 01/10/2026 en el navegador): las pantallas
preguntaban `canAdd('examen')` y `canAdd('control')`, pero los permisos se
llaman `add_examenlaboratorio` y `add_controlprenatal`. `hasPermission`
devolvía falso sin error y los médicos y enfermeras NO veían «Nuevo examen»,
«Importar», «Nuevo control», editar ni borrar; solo el administrador.
"""
import re
from pathlib import Path

from django.contrib.auth.models import Permission
from django.test import TestCase

SRC = Path(__file__).resolve().parents[2] / "frontend" / "src"
PATRONES = [
    re.compile(r"can(Add|Change|Delete|View)\('([a-z_]+)'\)"),
    re.compile(r"(?:requiredPermission|permiso|permission)[=:]\s*['\"]((?:view|add|change|delete)_[a-z_]+)['\"]"),
    re.compile(r"hasPermission\('((?:view|add|change|delete)_[a-z_]+)'\)"),
]


def permisos_pedidos() -> dict[str, set[str]]:
    pedidos: dict[str, set[str]] = {}
    for archivo in SRC.rglob("*.ts*"):
        if ".test." in archivo.name:
            continue
        texto = archivo.read_text(encoding="utf-8", errors="ignore")
        for m in PATRONES[0].finditer(texto):
            pedidos.setdefault(f"{m.group(1).lower()}_{m.group(2)}", set()).add(archivo.name)
        for patron in PATRONES[1:]:
            for m in patron.finditer(texto):
                pedidos.setdefault(m.group(1), set()).add(archivo.name)
    return pedidos


class PermisosFrontendTest(TestCase):
    def test_cada_permiso_pedido_existe(self):
        existentes = set(Permission.objects.values_list("codename", flat=True))
        pedidos = permisos_pedidos()
        self.assertGreater(len(pedidos), 30, "el escaneo no encontró los permisos del frontend")
        faltan = {p: sorted(a) for p, a in pedidos.items() if p not in existentes}
        self.assertEqual(faltan, {}, f"El frontend pide permisos que no existen: {faltan}")
