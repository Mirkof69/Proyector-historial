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
            "archivo",  # URL (protegida: /media/ exige sesión); sin ella no se podía ver ni bajar
            "nombre_archivo",
            "tipo_archivo",
            "tamano_bytes",
            "fecha_subida",
            "subido_por_nombre",
            "descripcion",
        ]
        read_only_fields = fields


#: Formato detectado por el contenido → tipo guardado.
TIPO_POR_FORMATO = {"PNG": "imagen", "JPG": "imagen", "BMP": "imagen", "TIFF": "imagen",
                    "DICOM": "dicom", "PDF": "pdf", "MP4": "video", "AVI": "video"}


class EcografiaArchivoCreateSerializer(serializers.ModelSerializer):
    """Alta de un adjunto. El TIPO se deduce del contenido del archivo.

    Antes era imposible crear un adjunto: el modelo aceptaba «imagen/video/
    dicom/pd» y este serializer exigía «DICOM/JPG/PNG/PDF/VIDEO» en
    mayúsculas, así que ningún valor cumplía las dos reglas. Además el tipo lo
    declaraba el cliente; ahora sale de los primeros bytes del archivo.
    """

    class Meta:
        """Meta"""
        model = EcografiaArchivo
        fields = ["id", "ecografia", "archivo", "nombre_archivo", "tipo_archivo", "descripcion"]
        read_only_fields = ["id", "tipo_archivo"]
        extra_kwargs = {"nombre_archivo": {"required": False}}

    def validate_archivo(self, value):
        """Tamaño y formato REAL (por el contenido, no por la extensión)."""
        from django.core.exceptions import ValidationError as ErrorDjango

        from core.validacion_archivos import FIRMAS, validar_archivo

        try:
            self._formato = validar_archivo(value, permitidos=tuple(FIRMAS), max_mb=50)
        except ErrorDjango as e:
            raise serializers.ValidationError(e.messages[0]) from e
        return value

    def validate(self, attrs):
        archivo = attrs["archivo"]
        attrs["tipo_archivo"] = TIPO_POR_FORMATO[self._formato]
        attrs["tamano_bytes"] = archivo.size
        if not attrs.get("nombre_archivo"):
            attrs["nombre_archivo"] = (getattr(archivo, "name", "") or "archivo")[:200]
        return attrs
