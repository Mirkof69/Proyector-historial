"""ECOGRAFÍAS ARCHIVOS - Model Definition
"""

from django.db import models


# MODEL
class EcografiaArchivo(models.Model):
    """Gestión de archivos multimedia de ecografías"""

    ecografia = models.ForeignKey(
        "ecografias.Ecografia", on_delete=models.CASCADE, related_name="archivos",
    )
    archivo = models.FileField(upload_to="ecografias/archivos/%Y/%m/%d/")
    tipo_archivo = models.CharField(
        max_length=20,
        choices=[
            ("imagen", "Imagen"),
            ("video", "Video"),
            ("dicom", "DICOM"),
            ("pd", "PDF"),
        ],
    )
    nombre_archivo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tamano_bytes = models.BigIntegerField(null=True, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(
        "usuarios.Usuario", on_delete=models.SET_NULL, null=True,
    )

    class Meta:
        """Meta"""
        db_table = "ecografias_archivos"
        ordering = ["-fecha_subida"]
        verbose_name = "Archivo de Ecografía"
        verbose_name_plural = "Archivos de Ecografías"

    def __str__(self):
        """Str"""
        return f"{self.nombre_archivo} - {self.ecografia}"
