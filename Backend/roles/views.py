"""CAT_ROLES - Full Stack"""

from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAdminUser

from .models import CatRol


# Serializer
class CatRolSerializer(serializers.ModelSerializer):
    """Catrolserializer"""
    class Meta:
        """Meta"""
        model = CatRol
        fields = "__all__"
        read_only_fields = ["fecha_creacion"]


# ViewSet
class CatRolViewSet(viewsets.ModelViewSet):
    """Catrolviewset"""
    queryset = CatRol.objects.all()
    serializer_class = CatRolSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["nombre", "activo"]
    ordering = ["nombre"]
