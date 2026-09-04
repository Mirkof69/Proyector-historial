"""Un solo vocabulario de acciones en la auditoría.

Por qué existe este archivo
---------------------------
Existían dos nombres para la misma cosa: `CREAR` y `crear`, `EDITAR` y
`actualizar`, `DESACTIVAR` y `eliminar`. Medido sobre la base real: 12.068
filas `CREAR` conviviendo con 5.199 `crear`, y 884 `actualizar` mientras el
canónico `EDITAR` tenía cero.

El problema no es estético. Filtrar la auditoría por `EDITAR` **no devolvía
las 884 ediciones** guardadas como `actualizar`. Una auditoría que no se puede
consultar de forma fiable no cumple su función legal: quien la revise concluye
que esas modificaciones nunca ocurrieron.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

from django.test import TestCase

from auditoria.acciones import (
    ACCIONES_LEGADAS,
    canonica,
    filtro_accion,
    nombres_equivalentes,
)


class AccionCanonicaTest(TestCase):
    """La normalización debe ser total, idempotente y no perder datos."""

    def test_las_minusculas_legadas_se_normalizan(self):
        """ESPERADO: el nombre canónico en mayúsculas."""
        casos = {"crear": "CREAR", "actualizar": "EDITAR", "eliminar": "DESACTIVAR"}
        for legada, esperada in casos.items():
            obtenida = canonica(legada)
            assert obtenida == esperada, (
                f"Para {legada!r} se esperaba {esperada!r}, se obtuvo {obtenida!r}"
            )

    def test_las_canonicas_se_dejan_igual(self):
        """ESPERADO: idempotente — normalizar dos veces da lo mismo."""
        assert canonica("CREAR") == "CREAR"
        assert canonica(canonica("crear")) == "CREAR"
        assert canonica(canonica("actualizar")) == "EDITAR"

    def test_una_accion_desconocida_se_conserva(self):
        """ESPERADO: se devuelve tal cual.

        Perder el registro es peor que guardarlo con un nombre inesperado: la
        auditoría prefiere un dato raro a un hueco.
        """
        assert canonica("ALGO_NUEVO") == "ALGO_NUEVO"
        assert canonica("DESACTIVAR_PACIENTE") == "DESACTIVAR_PACIENTE"

    def test_vacio_y_none_no_revientan(self):
        """ESPERADO: cadena vacía, sin excepción.

        La auditoría no puede tumbar la operación que está auditando.
        """
        assert canonica("") == ""
        assert canonica(None) == ""

    def test_el_mapa_de_legadas_no_apunta_a_si_mismo(self):
        """ESPERADO: ninguna clave legada es también un valor canónico.

        Si lo fuera, normalizar sería ambiguo y podría entrar en bucle.
        """
        canonicas = set(ACCIONES_LEGADAS.values())
        for legada in ACCIONES_LEGADAS:
            assert legada not in canonicas, (
                f"{legada!r} es a la vez nombre legado y canónico."
            )


class RegistrarNormalizaTest(TestCase):
    """Nada puede volver a entrar en la base con un nombre legado."""

    def test_registrar_guarda_el_nombre_canonico(self):
        """ESPERADO: se pide 'crear', queda guardado 'CREAR'."""
        from auditoria.models import RegistroAuditoria

        registro = RegistroAuditoria.registrar(
            usuario=None, accion="crear", modulo="Paciente", registro_id="1",
        )

        assert registro.accion == "CREAR", (
            f"Esperado 'CREAR' en la base, obtenido {registro.accion!r}"
        )

    def test_filtrar_por_el_canonico_encuentra_lo_guardado_como_legado(self):
        """ESPERADO: 1 resultado.

        Es exactamente el fallo que motivó todo esto: buscar `EDITAR` no
        devolvía las ediciones registradas como `actualizar`.
        """
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.registrar(
            usuario=None, accion="actualizar", modulo="Embarazo", registro_id="7",
        )

        encontrados = RegistroAuditoria.objects.filter(
            accion="EDITAR", registro_id="7",
        ).count()
        assert encontrados == 1, (
            f"Esperado 1 registro al filtrar por 'EDITAR', obtenido {encontrados}"
        )


class ConsultarHistoricoTest(TestCase):
    """Los registros viejos no se reescriben; la consulta los encuentra igual.

    La tabla de auditoría tiene un trigger `BEFORE UPDATE` que lanza excepción
    ante cualquier modificación, y eso es deliberado: un registro que se puede
    editar después no sirve como evidencia. Por eso las 884 filas `actualizar`
    se quedan como están y es el filtro el que aprende a encontrarlas.
    """

    def test_nombres_equivalentes_incluye_el_legado(self):
        """ESPERADO: ['EDITAR', 'actualizar'] — ambos nombres."""
        obtenido = sorted(nombres_equivalentes("EDITAR"))
        assert obtenido == ["EDITAR", "actualizar"], (
            f"Esperado ['EDITAR', 'actualizar'], obtenido {obtenido}"
        )

    def test_el_filtro_encuentra_registros_historicos(self):
        """ESPERADO: 2 — el nuevo canónico y el viejo legado.

        Se inserta la fila legada saltándose `registrar()` (que normaliza)
        para reproducir exactamente lo que hay en la base histórica.
        """
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.objects.create(
            accion="actualizar", modulo="Embarazo", registro_id="99",
        )
        RegistroAuditoria.objects.create(
            accion="EDITAR", modulo="Embarazo", registro_id="99",
        )

        encontrados = RegistroAuditoria.objects.filter(
            filtro_accion("EDITAR"), registro_id="99",
        ).count()
        assert encontrados == 2, (
            f"Esperado 2 registros (canónico + legado), obtenido {encontrados}. "
            f"Filtrar solo por 'EDITAR' perdía las 884 ediciones históricas."
        )

    def test_el_filtro_no_trae_otras_acciones(self):
        """ESPERADO: 0 — buscar EDITAR no puede devolver creaciones."""
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.objects.create(
            accion="CREAR", modulo="Paciente", registro_id="55",
        )

        encontrados = RegistroAuditoria.objects.filter(
            filtro_accion("EDITAR"), registro_id="55",
        ).count()
        assert encontrados == 0, f"Esperado 0, obtenido {encontrados}"
