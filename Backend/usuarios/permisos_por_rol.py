"""Qué puede ver y hacer cada rol: una sola tabla para todo el sistema.

Por qué existe
--------------
El frontend muestra cada pantalla solo si el usuario tiene el permiso de Django
correspondiente (`view_parto`, `add_ecografia`…). Esos permisos llegan por los
grupos del usuario. Pero en la base no había ningún grupo y ningún usuario tenía
permisos: un médico entraba y casi no veía nada; solo el administrador usaba el
sistema completo. El comando `setup_groups` que debía hacerlo cubría dos roles,
pocos módulos, y no asignaba los grupos a nadie.

Esta tabla está alineada con `core.permissions.FetalMedicalPermission`, que es
lo que el BACKEND deja hacer a cada rol: la pantalla no puede ofrecer lo que la
API va a rechazar, ni esconder lo que la API permite.

El grupo de cada usuario se asigna solo al crearlo o cambiarle el rol
(`usuarios/signals.py`), y los grupos se sincronizan tras cada migración.
"""
from __future__ import annotations

VER = ("view",)
VER_CREAR_EDITAR = ("view", "add", "change")

#: rol -> {app_label: acciones}. El borrado no se da a ningún rol clínico:
#: lo hace el administrador (que en el frontend tiene todo).
PERMISOS_POR_ROL: dict[str, dict[str, tuple[str, ...]]] = {
    "medico": {
        app: VER_CREAR_EDITAR for app in (
            "pacientes", "embarazos", "controles", "ecografias", "ecografias_archivos",
            "partos", "laboratorio", "citas", "triaje", "antecedentes", "evoluciones",
            "notas_evolucion", "vacunas", "calculadoras", "calculadoras_avanzadas",
            "reportes", "ia_medica",
        )
    } | {"consultorios": VER, "notificaciones": VER_CREAR_EDITAR},
    # Enfermería: el backend le bloquea partos, reportes y calculadoras avanzadas.
    "enfermera": {
        "pacientes": VER_CREAR_EDITAR, "controles": VER_CREAR_EDITAR, "citas": VER_CREAR_EDITAR,
        "triaje": VER_CREAR_EDITAR, "vacunas": VER_CREAR_EDITAR, "notas_evolucion": VER_CREAR_EDITAR,
        "embarazos": VER, "ecografias": VER, "laboratorio": VER, "antecedentes": VER,
        "calculadoras": VER, "evoluciones": VER, "consultorios": VER, "notificaciones": VER_CREAR_EDITAR,
    },
    "laboratorista": {
        "laboratorio": VER_CREAR_EDITAR, "calculadoras": VER_CREAR_EDITAR,
        "pacientes": VER, "embarazos": VER, "controles": VER, "ecografias": VER,
        "citas": VER, "antecedentes": VER, "notificaciones": VER_CREAR_EDITAR,
    },
    # Recepción: el backend le bloquea todo lo clínico.
    "recepcion": {
        "pacientes": VER_CREAR_EDITAR, "citas": VER_CREAR_EDITAR,
        "consultorios": VER, "notificaciones": VER_CREAR_EDITAR,
    },
}

#: Modelos de configuración que solo toca el administrador, aunque su app esté
#: en la tabla (la configuración del sistema vive dentro de `reportes`, y la de
#: los modelos de IA dentro de `ia_medica`).
SOLO_ADMINISTRADOR = (
    "sistemaconfiguracion", "auditoriareporte", "configuracionmodeloia",
    "modelocnnconfig", "datasetentrenamientoia", "campoadicionalepicrisis",
)

PREFIJO_GRUPO = "Rol: "


def nombre_grupo(rol: str) -> str:
    return f"{PREFIJO_GRUPO}{rol}"


def permisos_del_rol(rol: str):
    """QuerySet de `Permission` que corresponde al rol (vacío si no está en la tabla)."""
    from django.contrib.auth.models import Permission
    from django.db.models import Q

    filtro = Q(pk__in=[])
    for app, acciones in PERMISOS_POR_ROL.get(rol, {}).items():
        for accion in acciones:
            filtro |= Q(content_type__app_label=app, codename__startswith=f"{accion}_")
    excluir = Q(pk__in=[])
    for modelo in SOLO_ADMINISTRADOR:
        excluir |= Q(codename__endswith=f"_{modelo}")
    return Permission.objects.filter(filtro).exclude(excluir)


def sincronizar_grupos() -> dict[str, int]:
    """Crea o actualiza un grupo por rol con sus permisos. Devuelve {grupo: n}."""
    from django.contrib.auth.models import Group

    resultado = {}
    for rol in PERMISOS_POR_ROL:
        grupo, _ = Group.objects.get_or_create(name=nombre_grupo(rol))
        permisos = list(permisos_del_rol(rol))
        grupo.permissions.set(permisos)
        resultado[grupo.name] = len(permisos)
    return resultado


def asignar_grupo_de_rol(usuario) -> None:
    """Deja al usuario en el grupo de su rol y lo saca de los de otros roles."""
    from django.contrib.auth.models import Group

    otros = usuario.groups.filter(name__startswith=PREFIJO_GRUPO).exclude(name=nombre_grupo(usuario.rol))
    if otros.exists():
        usuario.groups.remove(*otros)
    if usuario.rol not in PERMISOS_POR_ROL:
        return
    grupo = Group.objects.filter(name=nombre_grupo(usuario.rol)).first()
    if grupo is None:
        sincronizar_grupos()
        grupo = Group.objects.get(name=nombre_grupo(usuario.rol))
    usuario.groups.add(grupo)
