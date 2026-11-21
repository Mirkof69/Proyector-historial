"""Lo que la API deja hacer a quien tiene un cargo.

El rol base ya decide qué puede hacer el usuario (core/permissions.py). El
cargo solo quita módulos: si la vista pertenece a un módulo del rol base que
el cargo no incluye, se responde 403. Lo demás sigue igual.

Se comprueba al autenticar (usuarios/auth_cookies.py) y no con una clase de
permiso, porque cerca de 40 vistas declaran sus propias `permission_classes` y
saltarían una clase por defecto. A los usuarios sin cargo no les cuesta nada:
ni siquiera se consulta la base.
"""
from __future__ import annotations

from rest_framework.exceptions import PermissionDenied

from usuarios.permisos_por_rol import NOMBRES_MODULO, modulos_del_rol


def modulo_de_vista(vista) -> str:
    """App de Django a la que pertenece la vista (`laboratorio.views` → `laboratorio`)."""
    return type(vista).__module__.split(".")[0]


def comprobar_cargo(usuario, vista) -> None:
    if vista is None or not getattr(usuario, "cargo_id", None):
        return
    cargo = usuario.cargo
    modulo = modulo_de_vista(vista)
    if modulo in modulos_del_rol(cargo.rol_base) and modulo not in cargo.modulos:
        raise PermissionDenied(
            f"Su cargo «{cargo.nombre}» no incluye el módulo {NOMBRES_MODULO.get(modulo, modulo)}. "
            "Pida al administrador que lo agregue si lo necesita.")
