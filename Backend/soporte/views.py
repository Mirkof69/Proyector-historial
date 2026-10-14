"""Views module."""
from rest_framework import permissions, viewsets

from .models import TicketSoporte
from .serializers import TicketSoporteSerializer


class TicketSoporteViewSet(viewsets.ModelViewSet):
    """Gestion de tickets de soporte tecnico.

    Cualquier usuario autenticado puede crear un ticket y ver los suyos.
    Solo administradores (is_staff) pueden ver/editar todos los tickets
    (para responder y cambiar el estado).
    """

    serializer_class = TicketSoporteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get queryset"""
        qs = TicketSoporte.objects.select_related("usuario").all()
        u = self.request.user
        if u.is_staff or u.is_superuser or getattr(u, "rol", "") == "administrador":
            return qs
        return qs.filter(usuario=self.request.user)

    def get_permissions(self):
        """Solo administradores pueden actualizar/eliminar tickets."""
        if self.action in ["update", "partial_update", "destroy"]:
            from core.permissions import EsSoloAdministrador

            return [permissions.IsAuthenticated(), EsSoloAdministrador]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Asignar automaticamente el usuario solicitante."""
        serializer.save(usuario=self.request.user)
