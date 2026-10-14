"""Los .bat de arranque llaman a comandos de Django con opciones que existen.

Regresión: los lanzadores de entonces (hoy un solo INICIAR.bat) y MIGRAR_Y_SEED usaban
`migrate_schemas --no-input`, opción que ese comando NO tiene (es
`--noinput`). Los tres lanzadores fallaban en el paso de migraciones y se
cerraban: el sistema no arrancaba con doble clic.
"""
import re
import shlex
from pathlib import Path

from django.core.management import get_commands, load_command_class
from django.test import SimpleTestCase

RAIZ = Path(__file__).resolve().parents[2]
LLAMADA = re.compile(r"manage\.py\s+([a-z_]+)([^>&|\r\n]*)")


def _llamadas():
    for bat in sorted(RAIZ.glob("*.bat")):
        for numero, linea in enumerate(bat.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if linea.lstrip().startswith(("::", "rem ", "REM ", "echo ")):
                continue
            for comando, resto in LLAMADA.findall(linea):
                yield bat.name, numero, comando, resto


class LanzadoresTest(SimpleTestCase):
    def test_hay_lanzadores_que_revisar(self):
        self.assertTrue(list(_llamadas()))

    def test_cada_comando_y_opcion_existen(self):
        # La suite corre sin django_tenants en INSTALLED_APPS: sus comandos
        # (migrate_schemas, tenant_command) se cargan de su propio paquete.
        comandos = {**{c: "django_tenants" for c in ("migrate_schemas", "tenant_command")}, **get_commands()}
        for bat, numero, comando, resto in _llamadas():
            with self.subTest(bat=bat, linea=numero, comando=comando):
                self.assertIn(comando, comandos, f"{bat}:{numero} llama a «{comando}», que no existe")
                parser = load_command_class(comandos[comando], comando).create_parser("manage.py", comando)
                validas = {o for a in parser._actions for o in a.option_strings}
                try:
                    partes = shlex.split(resto, posix=False)
                except ValueError:
                    partes = resto.split()
                for opcion in (p.split("=")[0] for p in partes if p.startswith("--")):
                    self.assertIn(opcion, validas, f"{bat}:{numero}: «{comando} {opcion}» no es una opción válida")
