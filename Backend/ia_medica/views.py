"""=============================================================================
VIEWS — IA Médica CNN: Imágenes Ecográficas y Análisis por Red Neuronal
=============================================================================
"""

import logging
import os
import time
from datetime import date, datetime

import requests
from django.conf import settings
from django.db.models import Count
from django.http import HttpResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from core.permissions import FetalMedicalPermission
from rest_framework.response import Response

from .models import (
    AnalisisCNN,
    ConsultaIA,
    ImagenEcografica,
    ModeloCNNConfig,
)
from .serializers import (
    AnalisisCNNSerializer,
    ImagenEcograficaDetailSerializer,
    ImagenEcograficaListSerializer,
    ImagenEcograficaUploadSerializer,
    ModeloCNNConfigListSerializer,
    ModeloCNNConfigSerializer,
)
from .services.cnn_service import cnn_service

logger = logging.getLogger("ia_medica")

# URL del microservicio IA — leer de settings para permitir override via .env
MICROSERVICE_URL = getattr(settings, "AI_SERVICE_URL", "http://localhost:8001")


# =============================================================================
# VIEWSET: Imágenes Ecográficas CNN
# =============================================================================


class ImagenEcograficaViewSet(viewsets.ModelViewSet):
    """ViewSet completo para gestión de imágenes ecográficas.

    Endpoints:
        pass
    - GET    /api/ia/imagenes/           — Galería paginada
    - POST   /api/ia/imagenes/           — Subir imagen (multipart)
    - GET    /api/ia/imagenes/{id}/      — Detalle de imagen
    - DELETE /api/ia/imagenes/{id}/      — Eliminar imagen
    - POST   /api/ia/imagenes/{id}/analizar/  — Ejecutar análisis CNN
    - GET    /api/ia/imagenes/{id}/resultado/ — Ver resultado del análisis
    - GET    /api/ia/imagenes/estadisticas/   — Estadísticas del módulo
    - GET    /api/ia/imagenes/modelos/        — Modelos CNN disponibles
    - GET    /api/ia/imagenes/exportar/       — Exportar dataset JSON
    """

    permission_classes = [FetalMedicalPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "paciente__nombre",
        "paciente__apellido_paterno",
        "descripcion",
        "tipo_imagen",
    ]
    ordering_fields = ["fecha_subida", "tipo_imagen", "estado"]
    ordering = ["-fecha_subida"]

    def get_queryset(self):
        qs = ImagenEcografica.objects.select_related(
            "paciente", "subida_por", "analisis_cnn",
        )
        # Filtros opcionales
        paciente_id = self.request.query_params.get("paciente_id")
        if paciente_id:
            qs = qs.filter(paciente_id=paciente_id)

        tipo = self.request.query_params.get("tipo_imagen")
        if tipo:
            qs = qs.filter(tipo_imagen=tipo)

        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return ImagenEcograficaListSerializer
        if self.action in ("create", "update", "partial_update"):
            return ImagenEcograficaUploadSerializer
        return ImagenEcograficaDetailSerializer

    @extend_schema(
        summary="Subir imagen ecográfica",
        description="Sube una imagen ecográfica para análisis CNN. Formatos: JPG, PNG, TIFF, BMP.",
        responses={201: ImagenEcograficaDetailSerializer},
    )
    def create(self, request, *args, **kwargs):
        """Subir nueva imagen ecográfica."""
        serializer = ImagenEcograficaUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extraer metadatos de la imagen
        imagen_file = request.FILES.get("imagen")
        extra_data = {
            "subida_por": request.user,
            "nombre_original": imagen_file.name if imagen_file else "unknown",
            "tamanio_bytes": imagen_file.size if imagen_file else 0,
        }

        # Detectar formato
        if imagen_file:
            ext = (
                imagen_file.name.rsplit(".", 1)[-1].lower()
                if "." in imagen_file.name
                else "jpg"
            )
            extra_data["formato"] = ext

        # Guardar imagen
        instancia = serializer.save(**extra_data)

        # Intentar extraer dimensiones con Pillow
        try:
            from PIL import Image

            img = Image.open(instancia.imagen.path)
            instancia.resolucion_ancho, instancia.resolucion_alto = img.size
            instancia.save(update_fields=["resolucion_ancho", "resolucion_alto"])
        except Exception as e:
            logger.warning("No se pudieron extraer dimensiones: %s", e)

        logger.info(
            "Imagen subida: %s - %s por %s",
            instancia.id,
            instancia.nombre_original,
            request.user.email,
        )

        detail_serializer = ImagenEcograficaDetailSerializer(
            instancia, context={"request": request},
        )
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Eliminar imagen y su archivo físico. Solo admin o quien subió la imagen."""
        instancia = self.get_object()
        if request.user.rol != "administrador" and instancia.subida_por != request.user:
            return Response(
                {"error": "No tienes permiso para eliminar esta imagen."},
                status=status.HTTP_403_FORBIDDEN,
            )
        imagen_path = instancia.imagen.path if instancia.imagen else None

        instancia.delete()

        # Eliminar archivo físico
        if imagen_path and os.path.exists(imagen_path):
            try:
                os.remove(imagen_path)
                logger.info("Archivo físico eliminado: %s", imagen_path)
            except OSError as e:
                logger.warning("No se pudo eliminar archivo físico: %s", e)

        return Response(
            {"mensaje": "Imagen eliminada correctamente."}, status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Analizar imagen con CNN",
        description="Ejecuta análisis de Red Neuronal Convolucional sobre la imagen.",
        parameters=[
            OpenApiParameter(
                "modelo",
                description="Modelo CNN: resnet50, unet, efficientnet, yolo_fetal",
                required=False,
            ),
        ],
        responses={200: AnalisisCNNSerializer},
    )
    @action(detail=True, methods=["post"], url_path="analizar")
    def analizar(self, request, pk=None):
        """Ejecutar análisis CNN sobre una imagen."""
        instancia = self.get_object()

        if not instancia.imagen:
            return Response(
                {"error": "La imagen no tiene archivo asociado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        modelo = request.data.get("modelo", "resnet50")
        modelos_validos = (
            "resnet50",
            "unet",
            "efficientnet",
            "yolo_fetal",
            "custom_cnn",
        )
        if modelo not in modelos_validos:
            return Response(
                {"error": f"Modelo no válido. Opciones: {', '.join(modelos_validos)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Marcar como procesando
        instancia.estado = "procesando"
        instancia.save(update_fields=["estado"])

        try:
            # Importar la tarea asíncrona de Celery
            from .tasks import analizar_imagen_task

            # Encolar el análisis en Celery/RabbitMQ
            analizar_imagen_task.delay(
                imagen_id=instancia.id,
                modelo=modelo,
                user_id=request.user.id if request.user else None,
            )

            logger.info(
                "Análisis CNN asíncrono encolado para imagen=%s con modelo=%s",
                instancia.id,
                modelo,
            )

            return Response(
                {
                    "mensaje": f"Análisis encolado asíncronamente con {modelo.upper()}.",
                    "estado": "procesando",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except Exception as e:
            instancia.estado = "error"
            instancia.save(update_fields=["estado"])
            logger.error("Error en análisis CNN: %s", e)
            return Response(
                {"error": f"Error durante el análisis: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="resultado")
    def resultado(self, request, pk=None):
        """Obtener resultado del análisis CNN de una imagen."""
        instancia = self.get_object()
        if not hasattr(instancia, "analisis_cnn"):
            return Response(
                {
                    "error": "Esta imagen aún no ha sido analizada.",
                    "estado": instancia.estado,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AnalisisCNNSerializer(instancia.analisis_cnn)
        imagen_serializer = ImagenEcograficaListSerializer(
            instancia, context={"request": request},
        )
        return Response(
            {
                "imagen": imagen_serializer.data,
                "analisis": serializer.data,
            },
        )

    @action(detail=False, methods=["get"], url_path="estadisticas")
    def estadisticas(self, request):
        """Estadísticas del módulo CNN."""
        stats = cnn_service.estadisticas_servicio()

        # Estadísticas adicionales de la BD
        total_por_tipo = dict(
            ImagenEcografica.objects.values("tipo_imagen")
            .annotate(total=Count("id"))
            .values_list("tipo_imagen", "total"),
        )
        total_por_estado = dict(
            ImagenEcografica.objects.values("estado")
            .annotate(total=Count("id"))
            .values_list("estado", "total"),
        )
        total_por_resultado = dict(
            AnalisisCNN.objects.values("resultado")
            .annotate(total=Count("id"))
            .values_list("resultado", "total"),
        )

        return Response(
            {
                **stats,
                "por_tipo_imagen": total_por_tipo,
                "por_estado": total_por_estado,
                "por_resultado_cnn": total_por_resultado,
                "modelos_disponibles": cnn_service.obtener_modelos_disponibles(),
            },
        )

    @action(detail=False, methods=["get"], url_path="modelos")
    def modelos(self, _request):
        """Lista de modelos CNN disponibles."""
        modelos_dinamicos = cnn_service.obtener_modelos_disponibles()
        modelos_bd = ModeloCNNConfig.objects.filter(estado="activo")
        bd_serializer = ModeloCNNConfigListSerializer(modelos_bd, many=True)

        return Response(
            {
                "modelos_builtin": modelos_dinamicos,
                "modelos_personalizados": bd_serializer.data,
                "total": len(modelos_dinamicos) + modelos_bd.count(),
            },
        )

    @action(detail=False, methods=["get"], url_path="exportar")
    def exportar(self, request):
        """Exportar dataset de imágenes y análisis. Solo administradores."""
        if request.user.rol != "administrador":
            return Response(
                {"error": "Solo administradores pueden exportar datasets."},
                status=status.HTTP_403_FORBIDDEN,
            )
        import json

        paciente_id = request.query_params.get("paciente_id")
        qs = ImagenEcografica.objects.select_related("paciente", "analisis_cnn").all()
        if paciente_id:
            qs = qs.filter(paciente_id=paciente_id)

        dataset = []
        for img in qs:
            entry = {
                "id": img.id,
                "paciente_id": img.paciente_id,
                "tipo_imagen": img.tipo_imagen,
                "fecha_subida": img.fecha_subida.isoformat(),
                "semana_gestacional": img.semana_gestacional,
                "resolucion": f"{img.resolucion_ancho}x{img.resolucion_alto}",
            }
            if hasattr(img, "analisis_cnn"):
                a = img.analisis_cnn
                entry["analisis"] = {
                    "resultado": a.resultado,
                    "confianza": a.confianza,
                    "modelo": a.modelo_usado,
                    "anomalias": a.anomalias_detectadas,
                    "fecha_analisis": a.fecha_analisis.isoformat(),
                }
            dataset.append(entry)

        contenido = json.dumps(
            {
                "exportado_en": datetime.now().isoformat(),
                "total_imagenes": len(dataset),
                "dataset": dataset,
            },
            ensure_ascii=False,
            indent=2,
        )

        respuesta = HttpResponse(
            contenido, content_type="application/json; charset=utf-8",
        )
        respuesta["Content-Disposition"] = (
            f'attachment; filename="dataset_cnn_{date.today()}.json"'
        )
        return respuesta


# =============================================================================
# VIEWSET: Modelos CNN Config
# =============================================================================


class ModeloCNNConfigViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar configuraciones de modelos CNN."""

    queryset = ModeloCNNConfig.objects.all()
    permission_classes = [FetalMedicalPermission]

    def get_serializer_class(self):
        if self.action == "list":
            return ModeloCNNConfigListSerializer
        return ModeloCNNConfigSerializer

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)


# =============================================================================
# VIEW ORIGINAL: Consulta IA (mantener compatibilidad)
# =============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def consultar_ia(request):
    """Gateway: Proxy al microservicio IA con inyección de contexto del sistema
    """
    try:
        from embarazos.models import Embarazo
        from notificaciones.models import Notificacion
        from pacientes.models import Paciente

        consulta = request.data.get("consulta", "")
        paciente_id = request.data.get("paciente_id")

        if not consulta:
            return Response(
                {"error": "La consulta no puede estar vacía"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contexto = {
            "total_pacientes": Paciente.objects.count(),
            "total_embarazos_activos": Embarazo.objects.filter(estado="activo").count(),
            "total_notificaciones_pendientes": Notificacion.objects.filter(
                leida=False,
            ).count(),
            "usuario_rol": request.user.rol
            if hasattr(request.user, "rol")
            else "usuario",
            "fecha_sistema": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        if paciente_id:
            try:
                paciente = Paciente.objects.get(id=paciente_id)
                nombre_completo = f"{paciente.nombre} {paciente.apellido_paterno}"
                if paciente.apellido_materno:
                    nombre_completo += f" {paciente.apellido_materno}"
                today = date.today()
                edad = (
                    today.year
                    - paciente.fecha_nacimiento.year
                    - (
                        (today.month, today.day)
                        < (
                            paciente.fecha_nacimiento.month,
                            paciente.fecha_nacimiento.day,
                        )
                    )
                )
                contexto["paciente_actual"] = {
                    "nombre": nombre_completo,
                    "edad": edad,
                    "grupo_sanguineo": f"{paciente.tipo_sangre}{paciente.factor_rh}"
                    if paciente.tipo_sangre
                    else "No registrado",
                    "embarazo_activo": paciente.embarazos.filter(
                        estado="activo",
                    ).exists(),
                }
            except Paciente.DoesNotExist:
                pass

        try:
            start_time = time.time()
            response = requests.post(
                f"{MICROSERVICE_URL}/api/consultar",
                json={
                    "consulta": consulta,
                    "user_id": request.user.id,
                    "contexto": contexto,
                },
                timeout=10,
            )
            if response.status_code == 200:
                ms_data = response.json()
                tiempo_ms = int((time.time() - start_time) * 1000)
                _VALID_CATS = {
                    "preeclampsia",
                    "diabetes",
                    "rciu",
                    "laboratorio",
                    "edad_gestacional",
                    "general",
                    "emergencia",
                }
                categoria = ms_data.get("categoria", "general")
                if categoria not in _VALID_CATS:
                    categoria = "general"
                consulta_obj = ConsultaIA.objects.create(
                    usuario=request.user,
                    paciente_id=paciente_id,
                    consulta_original=consulta,
                    consulta_procesada=consulta,
                    idioma_detectado="es",
                    categoria=categoria,
                    respuesta_ia=ms_data.get("respuesta", ""),
                    confianza=float(ms_data.get("confianza", 50)),
                    requiere_ml=False,
                    tiempo_respuesta_ms=ms_data.get("tiempo_respuesta_ms", tiempo_ms),
                )
                return Response(
                    {
                        "consulta": {
                            "id": consulta_obj.id,
                            "usuario": request.user.id,
                            "paciente": paciente_id,
                            "consulta_original": consulta,
                            "consulta_procesada": consulta,
                            "idioma_detectado": "es",
                            "categoria": categoria,
                            "respuesta_ia": ms_data.get("respuesta", ""),
                            "confianza": ms_data.get("confianza", 50),
                            "requiere_ml": False,
                            "resultado_ml": None,
                            "util": None,
                            "rating": None,
                            "comentario_feedback": None,
                            "fecha_consulta": consulta_obj.fecha_consulta.strftime(
                                "%Y-%m-%d %H:%M:%S",
                            ),
                            "tiempo_respuesta_ms": ms_data.get(
                                "tiempo_respuesta_ms", tiempo_ms,
                            ),
                        },
                        "nlp_info": {
                            "texto_corregido": consulta,
                            "idioma": "es",
                            "keywords": [w for w in consulta.split() if len(w) > 3],
                            "confianza": ms_data.get("confianza", 50),
                        },
                        "tiempo_total_ms": tiempo_ms,
                        "contexto_inyectado": True,
                    },
                )
            return Response(
                {"error": "Error en microservicio IA"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        except requests.exceptions.ConnectionError:
            return Response(
                {
                    "consulta": {
                        "id": 0,
                        "usuario": request.user.id,
                        "paciente": paciente_id,
                        "consulta_original": consulta,
                        "consulta_procesada": consulta,
                        "idioma_detectado": "es",
                        "categoria": "error",
                        "respuesta_ia": f'Microservicio IA no disponible. Consulta: "{consulta}"',
                        "confianza": 0,
                        "requiere_ml": False,
                        "resultado_ml": None,
                        "util": None,
                        "rating": None,
                        "comentario_feedback": None,
                        "fecha_consulta": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "tiempo_respuesta_ms": 0,
                    },
                    "nlp_info": {
                        "texto_corregido": consulta,
                        "idioma": "es",
                        "keywords": [w for w in consulta.split() if len(w) > 3],
                        "confianza": 0,
                    },
                    "fallback": True,
                },
            )
        except requests.exceptions.Timeout:
            return Response(
                {"error": "Timeout en microservicio"},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )

    except Exception as e:
        logger.error("Error en consultar_ia: %s", e)
        return Response(
            {"error": f"Error procesando la consulta: {e!s}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# =============================================================================
# VIEWSET: Historial de Consultas IA (ConsultaIA)
# =============================================================================


class ConsultaIAViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar el historial de consultas al chatbot IA.

    Endpoints:
        pass
    - GET    /api/ia/consultas/           — Historial del usuario actual (paginado)
    - GET    /api/ia/consultas/{id}/      — Detalle de una consulta
    - DELETE /api/ia/consultas/{id}/      — Eliminar del historial propio
    - POST   /api/ia/consultas/{id}/calificar/ — Registrar feedback médico
    """

    permission_classes = [FetalMedicalPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["consulta_original", "categoria", "respuesta_ia"]
    ordering = ["-fecha_consulta"]
    ordering_fields = ["fecha_consulta", "confianza", "categoria"]
    http_method_names = [
        "get",
        "delete",
        "head",
        "options",
    ]  # No permitir POST/PUT directo

    def get_queryset(self):
        """Solo muestra el historial del usuario autenticado (médicos/admin ven todo)."""
        qs = ConsultaIA.objects.select_related("usuario", "paciente")
        if self.request.user.rol in ("administrador",):
            return qs
        return qs.filter(usuario=self.request.user)

    def get_serializer_class(self):
        from .serializers import ConsultaIASerializer

        return ConsultaIASerializer

    @action(detail=True, methods=["post"], url_path="calificar")
    def calificar(self, request, _pk=None):
        """Registrar feedback médico sobre la respuesta del chatbot IA."""
        consulta = self.get_object()

        # Solo el usuario dueño o admin puede calificar
        if consulta.usuario != request.user and request.user.rol != "administrador":
            return Response(
                {"error": "Solo puedes calificar tus propias consultas."},
                status=status.HTTP_403_FORBIDDEN,
            )

        util = request.data.get("util")
        rating = request.data.get("rating")
        comentario = request.data.get("comentario_feedback", "")

        if rating is not None:
            try:
                rating = int(rating)
                if not 1 <= rating <= 5:
                    raise ValueError("Valor fuera de rango")
            except (ValueError, TypeError):
                return Response(
                    {"error": "El rating debe ser un número entre 1 y 5."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            consulta.rating = rating

        if util is not None:
            consulta.util = bool(util)

        consulta.comentario_feedback = comentario
        consulta.save(update_fields=["util", "rating", "comentario_feedback"])

        return Response(
            {
                "mensaje": "Feedback registrado correctamente.",
                "util": consulta.util,
                "rating": consulta.rating,
            },
        )
