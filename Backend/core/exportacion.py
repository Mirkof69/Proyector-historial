"""Exportar a Excel exactamente lo que el usuario está viendo.

Mixin para ViewSets: añade GET <prefijo>/exportar-excel/ que aplica los
mismos filtros, búsqueda y orden que el listado, así el Excel coincide con la
pantalla. Cada exportación queda auditada (EXPORTAR), porque sacar datos de
pacientes del sistema es una acción que hay que poder rastrear.

Uso:
    class CitaViewSet(ExportarExcelMixin, viewsets.ModelViewSet):
        excel_nombre = "citas"
        excel_columnas = [("Fecha", "fecha_cita"), ("Paciente", "paciente"), ("Estado", "estado")]

Cada columna es (encabezado, ruta): la ruta admite puntos
(«paciente.id_clinico»); si el campo tiene choices se exporta la etiqueta.
"""
import logging
from datetime import date, datetime

from django.utils import timezone
from rest_framework.decorators import action

from reportes.excel_clinico import escribir_tabla, libro_clinico, respuesta_excel

logger = logging.getLogger(__name__)

MAX_FILAS_EXCEL = 20000


def _resolver(objeto, ruta: str):
    valor = objeto
    partes = ruta.split(".")
    for i, parte in enumerate(partes):
        if valor is None:
            return ""
        display = getattr(valor, f"get_{parte}_display", None)
        if i == len(partes) - 1 and callable(display):
            return display()
        valor = getattr(valor, parte, None)
        if callable(valor):
            valor = valor()
    if isinstance(valor, datetime):
        return timezone.localtime(valor).strftime("%d/%m/%Y %H:%M") if timezone.is_aware(valor) else valor.strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    return "" if valor is None else str(valor)


class ExportarExcelMixin:
    excel_nombre = "exportacion"
    excel_columnas: list[tuple[str, str]] = []

    @action(detail=False, methods=["get"], url_path="exportar-excel")
    def exportar_excel(self, request):
        """Excel del listado actual (mismos filtros y búsqueda que la pantalla)."""
        qs = self.filter_queryset(self.get_queryset())[:MAX_FILAS_EXCEL]
        filas = [[_resolver(obj, ruta) for _, ruta in self.excel_columnas] for obj in qs]
        wb, ws = libro_clinico(self.excel_nombre.replace("_", " ").title())
        escribir_tabla(ws, [enc for enc, _ in self.excel_columnas], filas)
        try:
            from auditoria.models import RegistroAuditoria

            RegistroAuditoria.registrar(
                usuario=request.user, accion="EXPORTAR", modulo=self.excel_nombre,
                detalle=f"Exportación Excel de {len(filas)} filas "
                        f"(filtros: {dict(request.query_params) or 'ninguno'})",
                request=request,
            )
        except Exception:
            logger.exception("No se pudo auditar la exportación de %s", self.excel_nombre)
        return respuesta_excel(wb, self.excel_nombre)
