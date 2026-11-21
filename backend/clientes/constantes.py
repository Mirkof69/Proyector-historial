"""La clínica del hospital: un solo esquema con todos sus datos.

Desde el 29/10/2026 la base tiene una sola clínica, `clinica`. Antes los datos
vivían en `clinica_demo` (pacientes ficticias) y `clinica` estaba vacía.
"""
ESQUEMA_PRINCIPAL = "clinica"


def negar_datos_ficticios(esquema: str | None = None) -> None:
    """Los comandos de demostración no cargan pacientes ficticias en la clínica real.

    `esquema` es el que recibe el comando; sin él se mira la conexión actual
    (cuando se corre con `tenant_command --schema=...`).
    """
    from django.core.management.base import CommandError
    from django.db import connection

    destino = esquema or getattr(connection, "schema_name", None)
    if destino == ESQUEMA_PRINCIPAL:
        raise CommandError(
            f"«{ESQUEMA_PRINCIPAL}» es la clínica real del hospital: este comando carga datos "
            "ficticios y no se ejecuta ahí.",
        )
