#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def _consola_tolerante():
    """La consola de Windows (cp850/cp1252) no puede imprimir emojis ni algunos
    símbolos: un `print("✅ …")` tumbaba el comando a mitad de trabajo con
    UnicodeEncodeError (p. ej. poblar_valores_referencia desde un .bat). Se
    imprime en UTF-8 y lo que no quepa se sustituye, nunca se cae."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main():
    """Run administrative tasks."""
    _consola_tolerante()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable Did you "
            "forget to activate a virtual environment",
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
