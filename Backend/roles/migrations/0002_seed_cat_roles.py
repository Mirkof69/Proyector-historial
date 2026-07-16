"""Siembra el catalogo de roles base. La tabla cat_roles nunca tuvo datos
reales (el modelo solo definia los choices), por lo que la pantalla de
Roles y Permisos siempre mostraba la lista vacia."""
from django.db import migrations


# El frontend (pages/Roles/Roles.tsx) espera permisos como lista plana de
# strings "modulo.accion" (hace permisos.slice(0,3)), no un objeto anidado.
ROLES_BASE = [
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
        "nombre": "administrativo",
        "descripcion": "Personal administrativo: agenda de citas, "
                        "consultorios y gestion de pacientes (sin datos clinicos).",
        "permisos": [
            "pacientes.ver", "pacientes.crear",
            "citas.ver", "citas.crear", "citas.editar",
            "consultorios.ver",
        ],
    },
]


def seed_roles(apps, schema_editor):
    CatRol = apps.get_model("roles", "CatRol")
    for rol in ROLES_BASE:
        CatRol.objects.get_or_create(
            nombre=rol["nombre"],
            defaults={
                "descripcion": rol["descripcion"],
                "permisos": rol["permisos"],
                "activo": True,
            },
        )


def unseed_roles(apps, schema_editor):
    CatRol = apps.get_model("roles", "CatRol")
    CatRol.objects.filter(
        nombre__in=[r["nombre"] for r in ROLES_BASE],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("roles", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles, unseed_roles),
    ]
