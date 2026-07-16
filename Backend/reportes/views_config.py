"""=============================================================================
VIEWS PARA CONFIGURACIÓN DEL SISTEMA
=============================================================================
"""

import logging

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models_config import ConfiguracionAlertas, HorarioAtencion, SistemaConfiguracion
from .serializers_config import (
    ConfiguracionAlertasSerializer,
    HorarioAtencionSerializer,
    SistemaConfiguracionSerializer,
)
from .services import DatabaseBackupService

logger = logging.getLogger(__name__)


# ==========================================================================================
# CONFIGURACIÓN GENERAL
# ==========================================================================================


@extend_schema(
    request=inline_serializer(
        "configuracion_general_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET", "POST"])
@extend_schema(request=None, responses={200: dict})
@permission_classes([IsAuthenticated, IsAdminUser])
@parser_classes([MultiPartParser, FormParser])
def configuracion_general(request):
    """GET: Obtener configuración actual del sistema
    POST: Actualizar configuración (acepta multipart/form-data para logo)
    """
    # Obtener o crear configuración
    config = SistemaConfiguracion.get_configuracion()

    if request.method == "GET":
        serializer = SistemaConfiguracionSerializer(config)
        return Response(serializer.data)

    serializer = SistemaConfiguracionSerializer(
        config, data=request.data, partial=True,
    )
    if serializer.is_valid():
        serializer.save(actualizado_por=request.user)
        logger.info("Configuración actualizada por %s", request.user.email)
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================================================================
# CONFIGURACIÓN DE ALERTAS
# ==========================================================================================


@extend_schema(request=None, responses={200: dict})
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def configuracion_alertas(request):
    """GET: Obtener configuración actual de umbrales y notificaciones de alertas.
    POST: Actualizar configuración de alertas.
    """
    config = ConfiguracionAlertas.get_configuracion()

    if request.method == "GET":
        serializer = ConfiguracionAlertasSerializer(config)
        return Response(serializer.data)

    serializer = ConfiguracionAlertasSerializer(
        config, data=request.data, partial=True,
    )
    if serializer.is_valid():
        serializer.save(actualizado_por=request.user)
        logger.info("Configuración de alertas actualizada por %s", request.user.email)
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================================================================
# HORARIOS DE ATENCIÓN
# ==========================================================================================


@extend_schema(
    request=inline_serializer(
        "horarios_atencion_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def horarios_atencion(request):
    """GET: Obtener todos los horarios de atención
    POST: Actualizar todos los horarios (batch update)
    """
    if request.method == "GET":
        horarios = HorarioAtencion.objects.all().order_by("id")
        serializer = HorarioAtencionSerializer(horarios, many=True)
        return Response(serializer.data)

    # Espera lista de horarios en request.data
    if not isinstance(request.data, list):
        return Response(
            {"error": "Se esperaba una lista de horarios"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    resultados = []
    errores = []

    for horario_data in request.data:
        dia = horario_data.get("dia")
        if not dia:
            errores.append({"error": "Falta campo dia", "data": horario_data})
            continue

        try:
            horario = HorarioAtencion.objects.get(dia=dia)
            serializer = HorarioAtencionSerializer(
                horario, data=horario_data, partial=True,
            )
            if serializer.is_valid():
                serializer.save()
                resultados.append(serializer.data)
            else:
                errores.append({"dia": dia, "errors": serializer.errors})
        except HorarioAtencion.DoesNotExist:
            # Crear nuevo horario
            serializer = HorarioAtencionSerializer(data=horario_data)
            if serializer.is_valid():
                serializer.save()
                resultados.append(serializer.data)
            else:
                errores.append({"dia": dia, "errors": serializer.errors})

    if errores:
        return Response(
            {"resultados": resultados, "errores": errores},
            status=status.HTTP_207_MULTI_STATUS,
        )

    logger.info("Horarios actualizados por %s", request.user.email)
    return Response(resultados)


# ==========================================================================================
# BACKUPS DE BASE DE DATOS
# ==========================================================================================


@extend_schema(
    request=inline_serializer(
        "crear_backup_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def crear_backup(request):
    """Crear un backup manual de la base de datos"""
    try:
        service = DatabaseBackupService()
        result = service.create_backup("manual")

        if result["success"]:
            logger.info("Backup creado por %s: %s", request.user.email, result["filename"])
            return Response(result, status=status.HTTP_201_CREATED)
        logger.error("Error al crear backup: %s", result["message"])
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error("Excepción al crear backup: %s", str(e))
        return Response(
            {"success": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    operation_id="reportes_configuracion_listar_backups",
    request=inline_serializer(
        "listar_backups_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def listar_backups(_request):
    """Listar todos los backups disponibles"""
    try:
        service = DatabaseBackupService()
        backups = service.get_backups()
        return Response(backups)

    except Exception as e:
        logger.error("Error al listar backups: %s", str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    operation_id="reportes_configuracion_descargar_backup",
    request=inline_serializer(
        "descargar_backup_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def descargar_backup(request, filename):
    """Descargar un archivo de backup específico"""
    try:
        service = DatabaseBackupService()
        file_response = service.download_backup(filename)

        if file_response:
            logger.info("Backup descargado por %s: %s", request.user.email, filename)
            return file_response
        return Response(
            {"error": "Archivo no encontrado"}, status=status.HTTP_404_NOT_FOUND,
        )

    except Exception as e:
        logger.error("Error al descargar backup: %s", str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    request=inline_serializer(
        "eliminar_backup_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsAdminUser])
def eliminar_backup(request, filename):
    """Eliminar un archivo de backup"""
    try:
        service = DatabaseBackupService()
        success = service.delete_backup(filename)

        if success:
            logger.info("Backup eliminado por %s: %s", request.user.email, filename)
            return Response({"message": "Backup eliminado correctamente"})
        return Response(
            {"error": "No se pudo eliminar el backup"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        logger.error("Error al eliminar backup: %s", str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    request=inline_serializer(
        "restaurar_backup_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def restaurar_backup(request, filename):
    """Restaura la base de datos completa desde un backup.

    Operacion destructiva: sobrescribe toda la base de datos actual. El
    servicio crea automaticamente un backup de seguridad de la base actual
    antes de ejecutar el restore.
    """
    try:
        service = DatabaseBackupService()
        result = service.restore_backup(filename)
        logger.warning(
            "Base de datos restaurada por %s desde %s", request.user.email, filename,
        )
        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error("Error al restaurar backup: %s", str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
