"""Corrige el catalogo cat_roles para que coincida con los roles reales que
usuarios.models.Usuario.ROLES permite asignar a un usuario.

La migracion 0002 sembro un conjunto distinto e incompleto: tenia
"administrativo" (que ningun usuario real tiene) y le faltaban
"laboratorista", "administrador" y "recepcion" (roles que si existen en
usuarios reales del sistema, por eso la pantalla de Roles y Permisos no
los mostraba)."""
from django.db import migrations


ROLES_REALES = [
    {
        "nombre": "medico",
        "descripcion": "Personal medico: acceso a historiales clinicos, "
                        "ecografias, diagnosticos y prescripciones.",
        "permisos": [
            "pacientes.ver", "pacientes.crear", "pacientes.editar",
            "ecografias.ver", "ecografias.crear", "ecografias.editar", "ecografias.analizar",
            "laboratorio.ver", "laboratorio.crear",
            "recetas.ver", "recetas.crear",
        ],
    },
    {
        "nombre": "enfermera",
        "descripcion": "Personal de enfermeria: triaje, signos vitales, "
                        "vacunas y seguimiento de controles.",
        "permisos": [
            "pacientes.ver", "pacientes.editar",
            "triaje.ver", "triaje.crear", "triaje.editar",
            "vacunas.ver", "vacunas.crear",
            "controles.ver",
        ],
    },
    {
        "nombre": "laboratorista",
        "descripcion": "Personal de laboratorio: registro y validacion de "
                        "resultados de examenes clinicos.",
        "permisos": [
            "laboratorio.ver", "laboratorio.crear", "laboratorio.editar",
            "pacientes.ver",
        ],
    },
    {
        "nombre": "administrador",
        "descripcion": "Administrador del sistema: gestion de usuarios, "
                        "roles, consultorios y configuracion general.",
        "permisos": [
            "usuarios.ver", "usuarios.crear", "usuarios.editar", "usuarios.eliminar",
            "roles.ver", "roles.crear", "roles.editar",
            "consultorios.ver", "consultorios.crear", "consultorios.editar",
            "pacientes.ver", "reportes.ver",
        ],
    },
    {
        "nombre": "recepcion",
        "descripcion": "Personal de recepcion: agenda de citas y registro "
                        "inicial de pacientes (sin datos clinicos).",
        "permisos": [
            "pacientes.ver", "pacientes.crear",
            "citas.ver", "citas.crear", "citas.editar",
            "consultorios.ver",
        ],
    },
]

ROLES_OBSOLETOS = ["administrativo"]


def fix_roles(apps, schema_editor):
    CatRol = apps.get_model("roles", "CatRol")
    CatRol.objects.filter(nombre__in=ROLES_OBSOLETOS).delete()
    for rol in ROLES_REALES:
        CatRol.objects.update_or_create(
            nombre=rol["nombre"],
            defaults={
                "descripcion": rol["descripcion"],
                "permisos": rol["permisos"],
                "activo": True,
            },
        )


def revert_roles(apps, schema_editor):
    CatRol = apps.get_model("roles", "CatRol")
    CatRol.objects.filter(
        nombre__in=[r["nombre"] for r in ROLES_REALES if r["nombre"] not in ("medico", "enfermera")],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("roles", "0003_alter_catrol_nombre"),
    ]

    operations = [
        migrations.RunPython(fix_roles, revert_roles),
    ]
