"""Cada vista guarda la autoría en campos que su modelo SÍ tiene.

`serializer.save(created_by=...)` sobre un modelo sin `created_by` hace que el
alta responda 500 (Cita, Hemograma, Bioquímica, ReporteGenerado) y, en una
edición, DRF lo pone como atributo suelto y no lo guarda (ControlPrenatal
perdía quién lo editó). Hallado el 28/10/2026 por la prueba E2E de módulos.
"""
import importlib
import inspect
import re

from django.test import SimpleTestCase

APPS = [
    "antecedentes", "calculadoras", "citas", "consultorios", "controles", "ecografias",
    "embarazos", "ia_medica", "laboratorio", "notas_evolucion", "pacientes", "partos",
    "triaje", "vacunas", "usuarios", "roles", "reportes", "soporte", "notificaciones",
]


class CamposDeTrazabilidadTest(SimpleTestCase):
    def test_save_solo_usa_campos_del_modelo(self):
        ausentes = []
        for app in APPS:
            vistas = importlib.import_module(f"{app}.views")
            for nombre, clase in inspect.getmembers(vistas, inspect.isclass):
                modelo = getattr(getattr(clase, "queryset", None), "model", None)
                if clase.__module__ != vistas.__name__ or modelo is None:
                    continue
                campos = {f.name for f in modelo._meta.get_fields()}
                for metodo in ("perform_create", "perform_update"):
                    funcion = clase.__dict__.get(metodo)
                    if not funcion:
                        continue
                    for argumentos in re.findall(r"serializer\.save\(([^)]*)\)", inspect.getsource(funcion)):
                        for campo in re.findall(r"(\w+)\s*=", argumentos):
                            if campo not in campos:
                                ausentes.append(f"{app}.{nombre}.{metodo}: {modelo.__name__}.{campo}")
        # ESPERADO: ninguno.
        self.assertEqual(ausentes, [])


class CreacionesConCamposDelModeloTest(SimpleTestCase):
    """`Modelo.objects.create(campo=...)` solo con campos que el modelo tiene.

    «Registrar resultados» de laboratorio pasaba `unidad` a ResultadoLaboratorio:
    cada resultado fallaba dentro de un try/except y la respuesta era 201 con 0
    guardados. La calculadora de preeclampsia guardaba la presión en
    DopplerMaterno, que no tiene esos campos (500). Hallados el 28/10/2026.
    """

    def test_create_solo_usa_campos_del_modelo(self):
        import ast
        import pathlib

        from django.apps import apps
        from django.conf import settings

        campos = {}
        for modelo in apps.get_models():
            nombres = {"pk", "defaults", "create_defaults"}
            for f in modelo._meta.get_fields():
                nombres.add(f.name)
                nombres.add(getattr(f, "attname", f.name))
            campos.setdefault(modelo.__name__, []).append(nombres)
        ausentes = []
        raiz = pathlib.Path(settings.BASE_DIR)
        for app in APPS:
            for archivo in (raiz / app).rglob("*.py"):
                if archivo.name.startswith("test") or any(p in archivo.parts for p in ("migrations", "tests", "management")):
                    continue
                for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8-sig"))):
                    f = getattr(nodo, "func", None)
                    if not (isinstance(nodo, ast.Call) and isinstance(f, ast.Attribute)
                            and f.attr in ("create", "get_or_create", "update_or_create")
                            and isinstance(f.value, ast.Attribute) and f.value.attr == "objects"
                            and isinstance(f.value.value, ast.Name) and f.value.value.id in campos):
                        continue
                    usados = {k.arg.split("__")[0] for k in nodo.keywords if k.arg}
                    if all(usados - posibles for posibles in campos[f.value.value.id]):
                        sobran = min((usados - p for p in campos[f.value.value.id]), key=len)
                        ausentes.append(f"{archivo.relative_to(raiz)}:{nodo.lineno} {f.value.value.id}: {sorted(sobran)}")
        # ESPERADO: ninguno.
        self.assertEqual(ausentes, [])
