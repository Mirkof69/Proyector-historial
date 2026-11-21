"""El frontend y el backend tienen que llamar igual a los mismos roles.

Por qué existe este archivo
---------------------------
`Usuario.ROLES` define cinco roles. El frontend tenía su propia copia del mapa
—repetida en tres archivos— que conocía tres, y uno con otra grafía:
`enfermero` donde el backend guarda `enfermera`.

No daba ningún error. Daba una pantalla que mentía:

  - Filtrar por enfermera mandaba `rol=enfermero`: cero resultados, siempre.
  - La tarjeta «Enfermeros» contaba `rol === 'enfermero'`: cero, siempre.
  - `laboratorista` y `recepcion` no estaban en el desplegable.
  - En el detalle, la etiqueta del rol salía en blanco para esos tres roles.

El test del frontend (`src/config/__tests__/roles.test.tsx`) fija la lista
desde su lado. Este la fija desde el lado que manda: si alguien añade un rol
en el modelo y no lo añade al catálogo del frontend, falla aquí y dice cuál.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import pathlib
import re

from django.test import TestCase

from usuarios.models import Usuario

#: `frontend/src/config/roles.tsx`, el catálogo único del frontend.
CATALOGO_FRONTEND = (
    pathlib.Path(__file__).resolve().parents[2]
    / "frontend" / "src" / "config" / "roles.tsx"
)


def _roles_declarados_en_el_frontend() -> set[str]:
    """Las claves del objeto `ROLES` del catálogo del frontend.

    Se leen del archivo en vez de ejecutarlo porque es TypeScript con JSX
    dentro: no hay forma de importarlo desde Python. La expresión regular
    busca las claves del literal, que van todas al principio de línea con
    dos espacios de sangría y un `{` detrás.
    """
    fuente = CATALOGO_FRONTEND.read_text(encoding="utf-8")
    bloque = fuente.split("export const ROLES", 1)[1].split("};", 1)[0]
    return set(re.findall(r"^\s{2}(\w+):\s*\{", bloque, re.MULTILINE))


class VocabularioDeRolesTest(TestCase):
    """Las dos mitades del sistema tienen que usar las mismas palabras."""

    def test_el_catalogo_del_frontend_existe(self):
        """ESPERADO: el archivo está donde se espera.

        Si alguien lo mueve o lo borra, los tests de abajo darían un falso
        aprobado silencioso en vez de un fallo claro.
        """
        assert CATALOGO_FRONTEND.exists(), (
            f"No está {CATALOGO_FRONTEND}. Es el catálogo único de roles del "
            f"frontend; sin él vuelven las tres copias desincronizadas."
        )

    def test_el_frontend_conoce_todos_los_roles_del_modelo(self):
        """ESPERADO: ningún rol del backend falta en el frontend.

        Un rol que el backend guarda y el frontend no conoce se muestra sin
        nombre traducido y no se puede filtrar.
        """
        del_backend = {clave for clave, _ in Usuario.ROLES}
        del_frontend = _roles_declarados_en_el_frontend()

        faltan = del_backend - del_frontend
        assert not faltan, (
            f"El frontend no conoce estos roles del modelo: {sorted(faltan)}. "
            f"No se pueden filtrar y su etiqueta sale sin nombre. "
            f"Añadirlos en frontend/src/config/roles.tsx."
        )

    def test_el_frontend_no_inventa_roles_que_el_backend_no_guarda(self):
        """ESPERADO: ningún rol de más.

        Este es el fallo exacto que hubo: el frontend ofrecía `enfermero`, que
        el backend nunca guarda, así que ese filtro devolvía cero siempre.
        """
        del_backend = {clave for clave, _ in Usuario.ROLES}
        del_frontend = _roles_declarados_en_el_frontend()

        sobran = del_frontend - del_backend
        assert not sobran, (
            f"El frontend ofrece roles que el backend no guarda: "
            f"{sorted(sobran)}. Filtrar por ellos devuelve cero resultados "
            f"siempre, sin dar ningún error."
        )

    def test_enfermera_se_escribe_en_femenino_en_los_dos_lados(self):
        """ESPERADO: 'enfermera' en ambos; 'enfermero' en ninguno.

        Se comprueba aparte porque es la grafía concreta que se desincronizó
        y la que más cuesta ver leyendo el código.
        """
        del_backend = {clave for clave, _ in Usuario.ROLES}
        del_frontend = _roles_declarados_en_el_frontend()

        assert "enfermera" in del_backend
        assert "enfermera" in del_frontend
        assert "enfermero" not in del_frontend, (
            "El frontend volvió a escribir 'enfermero'. El backend guarda "
            "'enfermera': el filtro no encontraría a ninguna."
        )
