"""Cargos del hospital: solo el administrador los crea y cambia.

GET    /api/roles/cargos/                 lista (con cuántos usuarios tiene cada uno)
POST   /api/roles/cargos/                 {nombre, rol_base, modulos, descripcion, activo}
GET    /api/roles/cargos/modulos/         módulos que puede usar un cargo de cada rol
DELETE /api/roles/cargos/{id}/            409 si tiene usuarios: se desactiva en su lugar
Cada alta, cambio y baja queda en la auditoría.
"""
import logging

from django.db.models import Count, ProtectedError
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import EsSoloAdministrador
from usuarios.permisos_por_rol import modulos_elegibles

from .models import ROLES_BASE, Cargo
from .serializers import CargoSerializer

logger = logging.getLogger(__name__)


def _auditar(request, accion: str, cargo: Cargo, detalle: str) -> None:
    try:
        from auditoria.models import RegistroAuditoria

        RegistroAuditoria.registrar(usuario=request.user, accion=accion, modulo="Cargos",
                                    registro_id=str(cargo.pk), detalle=detalle, request=request)
    except Exception:
        logger.warning("No se pudo auditar el cargo %s", cargo.pk, exc_info=True)


def _resumen(cargo: Cargo) -> str:
    return f"{cargo.nombre} (rol base {cargo.rol_base}; módulos: {', '.join(cargo.modulos)}; activo={cargo.activo})"


class CargoViewSet(viewsets.ModelViewSet):
    serializer_class = CargoSerializer
    permission_classes = [EsSoloAdministrador]
    filterset_fields = ["rol_base", "activo"]
    search_fields = ["nombre", "descripcion"]
    pagination_class = None

    def get_queryset(self):
        return Cargo.objects.annotate(n_usuarios=Count("usuarios")).order_by("nombre")

    def perform_create(self, serializer):
        cargo = serializer.save()
        _auditar(self.request, "CREAR", cargo, f"Cargo creado: {_resumen(cargo)}")

    def perform_update(self, serializer):
        antes = _resumen(serializer.instance)
        cargo = serializer.save()
        _auditar(self.request, "EDITAR", cargo, f"Cargo modificado. Antes: {antes}. Ahora: {_resumen(cargo)}")

    def destroy(self, request, *args, **kwargs):
        cargo = self.get_object()
        try:
            cargo.delete()
        except ProtectedError:
            n = cargo.usuarios.count()
            return Response({"error": f"El cargo «{cargo.nombre}» lo tienen {n} usuario(s). "
                                      "Desactívelo o cámbieles el cargo antes de borrarlo."},
                            status=status.HTTP_409_CONFLICT)
        _auditar(request, "ELIMINAR", cargo, f"Cargo eliminado: {cargo.nombre}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Módulos que puede incluir un cargo según su rol base")
    @action(detail=False, methods=["get"])
    def modulos(self, request):
        return Response([{"rol": rol, "nombre": nombre, "modulos": modulos_elegibles(rol)}
                         for rol, nombre in ROLES_BASE])
