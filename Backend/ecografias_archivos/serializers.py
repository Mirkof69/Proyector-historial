"""Ecografias Archivos Serializers"""

from rest_framework import serializers

from .models import EcografiaArchivo


class EcografiaArchivoSerializer(serializers.ModelSerializer):
    """Serializer for EcografiaArchivo model"""

    subido_por_nombre = serializers.CharField(
        source="subido_por.get_full_name", read_only=True,
    )
    ecografia_info = serializers.SerializerMethodField()
    url_archivo = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = EcografiaArchivo
        fields = "__all__"
        read_only_fields = ("fecha_subida", "tamano_bytes", "subido_por")

    def get_ecografia_info(self, obj):
        """Get basic ecografia information"""
        if obj.ecografia:
            return {
                "id": obj.ecografia.id,
                "tipo": obj.ecografia.tipo_ecografia,
                "fecha": obj.ecografia.fecha_ecografia,
            }
        return None

    def get_url_archivo(self, obj):
        """Get file URL"""
        if obj.archivo:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.archivo.url)
        return None


class EcografiaArchivoListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing"""

    subido_por_nombre = serializers.CharField(
        source="subido_por.get_full_name", read_only=True,
    )

    class Meta:
        """Meta"""
        model = EcografiaArchivo
        fields = [
            "id",
            "nombre_archivo",
            "tipo_archivo",
            "tamano_bytes",
            "fecha_subida",
            "subido_por_nombre",
            "descripcion",
        ]
        read_only_fields = fields


class EcografiaArchivoCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new files"""

    class Meta:
        """Meta"""
        model = EcografiaArchivo
        fields = [
            "ecografia",
            "archivo",
            "nombre_archivo",
            "tipo_archivo",
            "descripcion",
        ]

    def validate_tipo_archivo(self, value):
        """Validate file type"""
        allowed_types = ["DICOM", "JPG", "PNG", "PDF", "VIDEO"]
        if value not in allowed_types:
            raise serializers.ValidationError(
                f"Tipo de archivo no válido. Permitidos: {', '.join(allowed_types)}",
            )
        return value

    def validate_archivo(self, value):
        """Validate file size"""
        if value.size > 50 * 1024 * 1024:  # 50MB
            raise serializers.ValidationError("El archivo no debe superar los 50MB")
        return value
