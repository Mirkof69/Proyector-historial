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

Cargos (`roles.Cargo`)
----------------------
Para otros funcionarios (obstetriz, nutricionista, trabajadora social…) el
administrador crea un cargo sobre uno de estos roles y elige qué módulos usa.
Un cargo solo puede QUITAR módulos al rol, nunca agregar: lo que la API deja
hacer sigue siendo lo del rol base, menos lo que el cargo excluye
(`roles/acceso.py`). Así un cargo nuevo no abre ningún hueco de seguridad.

Quien tiene cargo sigue en el grupo de su rol; el cargo se aplica filtrando
los permisos que recibe el frontend (`permisos_de_usuario`). No se crean
grupos por cargo: los usuarios viven en el esquema `public` y los grupos en el
de cada clínica, enlazados por id. Los grupos por rol coinciden en todos los
esquemas porque se crean en el mismo orden; uno creado desde una clínica no
existía en `public` y el alta del usuario fallaba (visto el 02/10/2026).
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

#: Nombre de cada módulo tal como lo ve el administrador al armar un cargo.
NOMBRES_MODULO = {
    "pacientes": "Pacientes", "embarazos": "Embarazos", "controles": "Controles prenatales",
    "ecografias": "Ecografías", "ecografias_archivos": "Archivos de ecografía",
    "partos": "Partos y recién nacidos", "laboratorio": "Laboratorio", "citas": "Citas",
    "triaje": "Triaje", "antecedentes": "Antecedentes", "evoluciones": "Evoluciones",
    "notas_evolucion": "Notas de evolución", "vacunas": "Vacunas", "calculadoras": "Calculadoras",
    "calculadoras_avanzadas": "Calculadoras avanzadas", "reportes": "Reportes",
    "ia_medica": "Inteligencia artificial", "consultorios": "Consultorios",
    "notificaciones": "Notificaciones",
}

#: Todo cargo los conserva: sin pacientes no se puede elegir a quién se atiende,
#: y sin notificaciones no llegan las alertas.
MODULOS_OBLIGATORIOS = ("pacientes", "notificaciones")


def nombre_grupo(rol: str) -> str:
    return f"{PREFIJO_GRUPO}{rol}"


def modulos_del_rol(rol: str) -> list[str]:
    return list(PERMISOS_POR_ROL.get(rol, {}))


def modulos_elegibles(rol: str) -> list[dict]:
    """Módulos que un cargo sobre `rol` puede incluir, con su nombre y si son fijos."""
    return [{"modulo": m, "nombre": NOMBRES_MODULO.get(m, m), "obligatorio": m in MODULOS_OBLIGATORIOS,
             "acciones": list(PERMISOS_POR_ROL[rol][m])} for m in modulos_del_rol(rol)]


def validar_cargo(rol_base: str, modulos) -> dict[str, str]:
    """Errores {campo: mensaje} de un cargo; vacío si es válido."""
    if rol_base not in PERMISOS_POR_ROL:
        return {"rol_base": "Elija el rol en que se basa el cargo (médico, enfermería, laboratorio o recepción)."}
    if not isinstance(modulos, list) or not all(isinstance(m, str) for m in modulos):
        return {"modulos": "Los módulos deben ser una lista."}
    ajenos = sorted(set(modulos) - set(modulos_del_rol(rol_base)))
    if ajenos:
        nombres = ", ".join(NOMBRES_MODULO.get(m, m) for m in ajenos)
        return {"modulos": f"El rol base no incluye: {nombres}. Un cargo solo puede quitar módulos a su rol."}
    return {}


def modulos_del_cargo(rol_base: str, modulos) -> list[str]:
    """Los módulos elegidos más los obligatorios, en el orden de la tabla."""
    elegidos = set(modulos or []) | set(MODULOS_OBLIGATORIOS)
    return [m for m in modulos_del_rol(rol_base) if m in elegidos]


def permisos_del_rol(rol: str, modulos=None):
    """QuerySet de `Permission` que corresponde al rol (vacío si no está en la tabla).

    Con `modulos`, solo los de esos módulos (los de un cargo).
    """
    from django.contrib.auth.models import Permission
    from django.db.models import Q

    filtro = Q(pk__in=[])
    for app, acciones in PERMISOS_POR_ROL.get(rol, {}).items():
        if modulos is not None and app not in modulos:
            continue
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


def modulos_excluidos(usuario) -> set[str]:
    """Módulos del rol que el cargo del usuario quita (vacío sin cargo)."""
    if not getattr(usuario, "cargo_id", None):
        return set()
    cargo = usuario.cargo
    return set(modulos_del_rol(cargo.rol_base)) - set(cargo.modulos)


def permisos_de_usuario(usuario) -> list[str]:
    """Codenames que recibe el frontend: directos y de grupos, menos los del
    cargo. Una sola definición para el login y la verificación MFA."""
    from django.contrib.auth.models import Permission
    from django.db.models import Q

    permisos = Permission.objects.filter(Q(usuario=usuario) | Q(group__usuario=usuario))
    excluidos = modulos_excluidos(usuario)
    if excluidos:
        permisos = permisos.exclude(content_type__app_label__in=excluidos)
    return sorted(set(permisos.values_list("codename", flat=True)))
