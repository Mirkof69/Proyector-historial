"""=============================================================================
SERVICIO ORTHANC — Integración con PACS (Picture Archiving and Communication System)
=============================================================================
Este servicio permite la comunicación bidireccional entre el Backend de Django
y el servidor DICOM Orthanc, habilitando el almacenamiento estandarizado de
imágenes médicas y la conexión con visores como OHIF.
"""

import logging
import os

import requests
from django.conf import settings

logger = logging.getLogger("ia_medica")


class OrthancService:
    """Orthancservice"""
    def __init__(self):
        """Init"""
        # Configuración desde variables de entorno
        self.url = getattr(settings, "ORTHANC_URL", "http://localhost:8042")
        self.username = getattr(settings, "ORTHANC_USERNAME", "orthanc")
        self.password = getattr(settings, "ORTHANC_PASSWORD", "orthanc")
        self.auth = (
            (self.username, self.password) if self.username and self.password else None
        )

    def verificar_conexion(self) -> bool:
        """Verifica si el servidor Orthanc está respondiendo."""
        try:
            response = requests.get(f"{self.url}/system", auth=self.auth, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            logger.warning("No se pudo conectar al servidor Orthanc.")
            return False

    def subir_dicom(self, file_path: str) -> dict:
        """Sube un archivo DICOM al servidor Orthanc."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    f"{self.url}/instances",
                    data=f,
                    headers={"Content-Type": "application/dicom"},
                    auth=self.auth,
                    timeout=30,
                )

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    "DICOM subido exitosamente. ID Instancia: %s", data.get("ID"),
                )
                return {
                    "status": "success",
                    "orthanc_id": data.get("ID"),
                    "parent_patient": data.get("ParentPatient"),
                    "parent_study": data.get("ParentStudy"),
                    "parent_series": data.get("ParentSeries"),
                }
            logger.error(
                "Error subiendo DICOM a Orthanc. HTTP %s: %s",
                response.status_code,
                response.text,
            )
            return {"status": "error", "message": f"HTTP {response.status_code}"}

        except requests.RequestException as e:
            logger.error("Error de conexión con Orthanc al subir archivo: %s", e)
            return {"status": "error", "message": str(e)}

    def obtener_visor_url(self, study_id: str) -> str:
        """Retorna la URL del visor OHIF embebido apuntando al estudio en Orthanc.
        Se requiere que OHIF esté configurado para apuntar a Orthanc (por ejemplo, vía WADO).
        """
        # Suponiendo que OHIF está en /viewer/ y acepta query params para el study_uid
        ohif_base = getattr(settings, "OHIF_VIEWER_URL", "http://localhost:3000/viewer")
        return f"{ohif_base}url={self.url}/dicom-web/studies/{study_id}"


orthanc_service = OrthancService()
