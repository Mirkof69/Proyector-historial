"""Views para integración con Microservicio de IA

Incluye (el antiguo `ai_result_callback`, AllowAny y sin llamador, se eliminó:
cualquiera en la red podía sobrescribir el análisis de cualquier ecografía):
  - analyze_ultrasound_with_ai:  análisis síncrono (directo al microservicio FastAPI)

El análisis asíncrono NO pasa por RabbitMQ directo: el flujo productivo es
Celery (tasks en ecografias/) → cnn_service (HTTP con circuit breaker) →
microservicio FastAPI. El antiguo publisher a la cola "dicom.analysis" se
eliminó porque ningún consumer la atendía y ninguna vista lo invocaba.
"""

import logging
import mimetypes
import os

import requests
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes

from core.permissions import FetalMedicalPermission
from rest_framework.response import Response

logger = logging.getLogger(__name__)

def obtener_url_ia() -> str:
    """URL base del microservicio de IA, leída desde `settings`.

    Antes esto era una constante de módulo que leía `os.environ` directamente.
    Eso creó dos mecanismos distintos para la misma configuración —
    `ia_medica/services/cnn_service.py` sí usa `settings`— y el resultado fue
    que `.env` apuntaba al puerto 8002, donde no escucha nada, mientras el
    microservicio corría en el 8001. El análisis de ecografías devolvía 503 y
    nada lo detectaba, porque ningún test podía sobrescribir una constante ya
    evaluada al importar el módulo.

    Se resuelve en cada llamada para que `override_settings` funcione en los
    tests, y se quita la barra final para no construir rutas con `//`.
    """
    from django.conf import settings

    return str(getattr(settings, "AI_SERVICE_URL", "http://localhost:8001")).rstrip("/")


def respuesta_de_error_ia(respuesta) -> Response:
    """Traduce una respuesta no-200 del microservicio a la del backend.

    Un 400/404/422 (extensión no permitida, tamaño de píxel absurdo, imagen
    ilegible) y el 503 (red sin instalar) son información para quien usa la
    pantalla y se reenvían con su motivo. Antes el análisis completo los
    convertía en un 500 «Error en el microservicio de IA» con el JSON crudo, y
    la médica veía un fallo del servidor por haber elegido mal el archivo.
    Un 5xx del microservicio es un fallo río arriba: 502.
    """
    try:
        cuerpo = respuesta.json()
        detalle = cuerpo.get("detail") or cuerpo.get("error") if isinstance(cuerpo, dict) else None
    except ValueError:
        detalle = None
    detalle = detalle if isinstance(detalle, str) else (str(detalle) if detalle else (respuesta.text or "")[:300])
    codigo = respuesta.status_code
    if 400 <= codigo < 500 or codigo == 503:
        return Response({"error": detalle or "El servicio de IA rechazó la imagen."}, status=codigo)
    return Response({"error": "El servicio de IA falló al procesar la imagen.", "details": detalle},
                    status=status.HTTP_502_BAD_GATEWAY)


def preparar_respuesta_ia(resultado: dict) -> dict:
    """Deja el resultado del microservicio listo para viajar por la red.

    Saca `gradcam_base64` del JSON y lo reemplaza por `gradcam_url`. Medido
    sobre una ecografía real: la respuesta pesaba 252 KB, de los cuales 249 KB
    (el 98%) eran ese base64; todos los datos clínicos juntos —patologías,
    biometría, recomendaciones— suman menos de 2 KB.

    En la red 3G de una clínica eso son unos 5 segundos por ecografía para
    leer un resultado que cabe en dos kilobytes. Con la imagen como archivo
    aparte, el navegador la pide cuando la necesita, se cachea y se sirve
    comprimida.
    """
    from .gradcam import guardar_gradcam

    salida = dict(resultado)
    base64_gradcam = salida.pop("gradcam_base64", "")
    if base64_gradcam:
        salida["gradcam_url"] = guardar_gradcam(base64_gradcam, prefijo="eco")
    # Análisis con las redes medidas: la imagen con las estructuras dibujadas
    # viaja igual, como archivo aparte.
    superposicion = salida.pop("superposicion_png", "")
    if superposicion:
        salida["superposicion_url"] = guardar_gradcam(superposicion, prefijo="seg")
    return salida


@extend_schema(
    request=inline_serializer(
        "analyze_ultrasound_with_ai_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["POST"])
@extend_schema(request=None, responses={200: dict})
@permission_classes([FetalMedicalPermission])
def analyze_ultrasound_with_ai(request):
    """Analiza una ecografía usando el microservicio de IA

    Endpoint: POST /api/ecografias/analyze-with-ai/

    Request:
        - file: Archivo de imagen (DICOM, JPG, PNG)
        - ecografia_id: ID de la imagen del módulo IA (ia_medica.ImagenEcografica),
          no de una ecografía clínica; el nombre se mantiene por compatibilidad.

    Returns:
        - Análisis completo de IA
        - Clasificación, segmentación, anomalías
        - Recomendaciones médicas

    """
    try:
        ecografia_id = request.data.get("ecografia_id")
        ciudad_paciente = None

        # Si no se envió archivo pero hay ecografia_id, leer desde disco
        if "file" not in request.FILES:
            if not ecografia_id:
                return Response(
                    {"error": "No se proporcionó archivo de imagen ni ecografia_id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            from ia_medica.models import ImagenEcografica as IaImagen
            try:
                imagen_ia = IaImagen.objects.get(id=ecografia_id)
            except IaImagen.DoesNotExist:
                return Response(
                    {"error": "Imagen no encontrada"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            ruta = imagen_ia.imagen.path
            nombre = os.path.basename(ruta)
            mime = mimetypes.guess_type(ruta)[0] or "application/octet-stream"
            with open(ruta, "rb") as f:
                file_bytes = f.read()
            image_file_name = nombre
            image_file_bytes = file_bytes
            image_file_type = mime
            ciudad_paciente = getattr(imagen_ia.paciente, "ciudad", None)
        else:
            image_file = request.FILES["file"]
            image_file_name = image_file.name
            image_file_bytes = image_file.read()
            image_file_type = image_file.content_type

        files = {"file": (image_file_name, image_file_bytes, image_file_type)}

        # Ajuste de riesgo de preeclampsia por altitud (ver servicio-ia
        # app/models.py ALTITUDE_PREECLAMPSIA_FACTOR): se resuelve por la
        # ciudad del paciente cuando esta disponible.
        data = {"ciudad": ciudad_paciente} if ciudad_paciente else {}
        # Con el tamaño del píxel (del ecógrafo o del DICOM) la red da HC y DBP en mm.
        if request.data.get("tamano_pixel_mm"):
            data["tamano_pixel_mm"] = request.data["tamano_pixel_mm"]

        # Llamar al microservicio de IA
        ai_response = requests.post(
            f"{obtener_url_ia()}/api/analyze", files=files, data=data, timeout=30,
        )

        if ai_response.status_code == 200:
            ai_results = ai_response.json()
            if ai_results.get("status") != "success":
                # Sin modelo cargado no hay análisis: antes se entregaba un
                # resultado vacío con 200, como si la imagen fuera normal.
                return Response(
                    {"success": False,
                     "error": ai_results.get("advertencia") or "El servicio de IA no tiene el modelo cargado."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # `ecografia_id` es el id de una ia_medica.ImagenEcografica (así lo
            # envía la pantalla de IA Médica, la única que llama aquí). Antes se
            # usaba ADEMÁS como id de ecografias.Ecografia para escribir
            # `analisis_ia` en sus imágenes: con ids coincidentes, el análisis
            # acababa en la ecografía de otra paciente. Ese guardado se quitó.

            # Guardar resultados en ia_medica.ImagenEcografica / AnalisisCNN
            guardado = False
            if ecografia_id:
                try:
                    from ia_medica.models import AnalisisCNN
                    from ia_medica.models import ImagenEcografica as IaImagen

                    imagen_ia = IaImagen.objects.get(id=ecografia_id)

                    from ia_medica.services.result_mapping import defaults_analisis_cnn

                    defaults = defaults_analisis_cnn(ai_results, request.user, "efficientnet")
                    resultado = defaults["resultado"]
                    analisis, _created = AnalisisCNN.objects.update_or_create(
                        imagen=imagen_ia, defaults=defaults,
                    )

                    imagen_ia.estado = "analizada"
                    imagen_ia.save(update_fields=["estado"])
                    guardado = True

                    logger.info(
                        "IA analysis saved to AnalisisCNN id=%s (resultado=%s, %s) "
                        "for ia_medica.ImagenEcografica id=%s",
                        analisis.id, resultado,
                        "actualizado" if not _created else "creado",
                        ecografia_id,
                    )

                except IaImagen.DoesNotExist:
                    logger.warning(
                        "ia_medica.ImagenEcografica %s not found", ecografia_id,
                    )
                except Exception as ex:
                    logger.exception(
                        "Error saving AI analysis to ia_medica.AnalisisCNN: %s", ex
                    )

            # `ANALISIS_CNN` estaba declarada en RegistroAuditoria.ACCIONES
            # pero nunca se emitía: no quedaba constancia de que una imagen de
            # una paciente hubiera pasado por la red neuronal, ni de quién lo
            # pidió. En un sistema que apoya decisiones clínicas eso es
            # justamente lo que hay que poder reconstruir.
            try:
                from auditoria.models import RegistroAuditoria

                RegistroAuditoria.registrar(
                    usuario=request.user
                    if getattr(request.user, "is_authenticated", False)
                    else None,
                    accion="ANALISIS_CNN",
                    modulo="Ecografia",
                    registro_id=str(ecografia_id or ""),
                    detalle="Análisis de imagen con red neuronal",
                    request=request,
                )
            except Exception:  # auditar no puede impedir entregar el análisis
                logger.warning("No se pudo auditar el análisis CNN", exc_info=True)

            # El Grad-CAM se guarda como archivo y viaja como URL: incrustado
            # en base64 era el 98% del peso de esta respuesta (249 KB de 252).
            # Se hace DESPUÉS de persistir `ai_results`, para que el análisis
            # guardado en la base conserve el mapa de calor original.
            return Response(
                {
                    "status": "success",
                    "ai_analysis": preparar_respuesta_ia(ai_results),
                    "message": "Análisis de IA completado exitosamente",
                    "guardado": guardado,
                },
                status=status.HTTP_200_OK,
            )
        return respuesta_de_error_ia(ai_response)

    except requests.exceptions.ConnectionError:
        return Response(
            {
                "error": "No se pudo conectar al microservicio de IA",
                "details": "Verifique que el microservicio esté corriendo en puerto 8001",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except requests.exceptions.Timeout:
        return Response(
            {
                "error": "Timeout al procesar la imagen",
                "details": "El análisis tomó demasiado tiempo",
            },
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )

    except Exception as e:
        return Response(
            {"error": "Error inesperado", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    request=inline_serializer(
        "ai_service_health_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["GET"])
@permission_classes([FetalMedicalPermission])
def ai_service_health(_request):
    """Verifica el estado del microservicio de IA

    Endpoint: GET /api/ecografias/ai/health/
    """
    try:
        # El microservicio expone /health en la RAIZ, no /api/health: verificado
        # contra el servicio corriendo (/health -> 200, /api/health -> 404).
        health_response = requests.get(f"{obtener_url_ia()}/health", timeout=5)

        if health_response.status_code == 200:
            return Response(
                {"status": "online", "ai_service": health_response.json()},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "status": "error",
                "message": "Microservicio no responde correctamente",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except requests.exceptions.ConnectionError:
        return Response(
            {"status": "offline", "message": "Microservicio de IA no disponible"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    request=inline_serializer(
        "crear_ecografia_desde_ia_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["POST"])
@permission_classes([FetalMedicalPermission])
@transaction.atomic
def crear_ecografia_desde_ia(request):
    """Crea una Ecografía en el módulo de ecografias desde una imagen del módulo IA.

    Endpoint: POST /api/ecografias/crear-desde-ia/

    Request:
        - imagen_ia_id: ID de ia_medica.ImagenEcografica
        - paciente_id: ID del paciente

    Crea:
        1. Ecografia con los datos disponibles, en el embarazo ACTIVO de la
           paciente (si no tiene, responde 409: antes se inventaba uno con
           FUM = hoy - 280 días, G1P0, y 12 semanas por defecto, lo que
           descuadraba la edad gestacional y la fecha de parto)
        2. (ver arriba)
        3. ImagenEcografia (ecografias) con la misma imagen
        4. Copia el análisis IA al campo analisis_ia de la nueva imagen
    """

    from django.core.files.base import ContentFile

    from embarazos.models import Embarazo
    from ia_medica.models import ImagenEcografica as IaImagen

    from .models import Ecografia as EcoModel
    from .models import ImagenEcografia as EcoImagen

    imagen_ia_id = request.data.get("imagen_ia_id")
    paciente_id = request.data.get("paciente_id")

    if not all([imagen_ia_id, paciente_id]):
        return Response(
            {"error": "Se requieren imagen_ia_id y paciente_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from pacientes.models import Paciente
        paciente = Paciente.objects.get(id=paciente_id)
    except Paciente.DoesNotExist:
        return Response(
            {"error": "Paciente no encontrado"},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        imagen_ia = IaImagen.objects.select_related(
            "paciente", "analisis_cnn"
        ).get(id=imagen_ia_id)
    except IaImagen.DoesNotExist:
        return Response(
            {"error": "Imagen IA no encontrada"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # La imagen tiene que ser de esta paciente: si no, el análisis quedaba en
    # la historia de otra persona.
    if imagen_ia.paciente_id and imagen_ia.paciente_id != paciente.id:
        return Response(
            {"error": "La imagen pertenece a otra paciente."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 1. El embarazo activo real; nunca uno inventado.
    embarazo = Embarazo.objects.filter(
        paciente=paciente, estado="activo"
    ).first()
    if not embarazo:
        return Response(
            {"error": "La paciente no tiene un embarazo activo. Regístrelo primero "
                      "con su fecha de última menstruación."},
            status=status.HTTP_409_CONFLICT,
        )
    fecha_eco = imagen_ia.fecha_captura or timezone.localdate()
    if hasattr(fecha_eco, "date"):
        fecha_eco = fecha_eco.date()
    if imagen_ia.semana_gestacional:
        semanas, dias = int(imagen_ia.semana_gestacional), 0
    else:
        dias_totales = max(0, (fecha_eco - embarazo.fecha_ultima_menstruacion).days)
        semanas, dias = divmod(dias_totales, 7)

    # 2. Crear ecografía
    tipo_eco_map = {
        "eco_2d": "primer_trimestre",
        "eco_3d": "segundo_trimestre",
        "eco_4d": "tercer_trimestre",
        "doppler": "doppler",
        "morfologica": "morfologica",
    }
    tipo_ecografia = tipo_eco_map.get(
        imagen_ia.tipo_imagen, "primer_trimestre"
    )

    ecografia = EcoModel.objects.create(
        embarazo=embarazo,
        paciente=paciente,
        medico=request.user if request.user.rol == "medico" else None,
        fecha_ecografia=fecha_eco,
        tipo_ecografia=tipo_ecografia,
        edad_gestacional_semanas=semanas,
        edad_gestacional_dias=dias,
        diagnostico="Pendiente de diagnóstico",
        created_by=request.user,
        updated_by=request.user,
    )

    # 3. Copiar la imagen física a la ecografía
    eco_imagen = None
    if imagen_ia.imagen:
        try:
            img_path = imagen_ia.imagen.path
            with open(img_path, "rb") as f:
                img_bytes = f.read()
            img_name = os.path.basename(imagen_ia.imagen.name)
            eco_imagen = EcoImagen.objects.create(
                ecografia=ecografia,
                imagen=ContentFile(img_bytes, name=img_name),
                tipo_imagen="general",
                titulo=f"Imagen desde IA — {imagen_ia.nombre_original}",
                descripcion=imagen_ia.descripcion,
                created_by=request.user,
                updated_by=request.user,
            )
        except Exception as e:
            logger.warning(
                "No se pudo copiar la imagen física: %s", e
            )

    # 4. Copiar análisis IA si existe
    analisis_data = {}
    if hasattr(imagen_ia, "analisis_cnn") and imagen_ia.analisis_cnn:
        cnn = imagen_ia.analisis_cnn
        analisis_data = {
            "procesado": True,
            "fecha_analisis": str(cnn.fecha_analisis),
            "confianza": cnn.confianza,
            "resultado": cnn.resultado,
            "hallazgos": cnn.anomalias_detectadas,
            "mediciones_detectadas": cnn.medidas_estimadas or {},
            "anomalias_detectadas": cnn.anomalias_detectadas,
            "alertas": cnn.alertas,
            "modelo_usado": cnn.modelo_usado,
            "shap_valores": cnn.shap_valores,
            "score_general": cnn.score_general,
            "fuente": "ia_medica",
        }
    elif imagen_ia.estado == "analizada" and not analisis_data:
        analisis_data = {
            "procesado": True,
            "fuente": "ia_medica",
            "resultado": "analizada",
        }

    if eco_imagen and analisis_data:
        eco_imagen.analisis_ia = analisis_data
        eco_imagen.save(update_fields=["analisis_ia"])

    logger.info(
        "Ecografía %s creada desde IA imagen %s para paciente %s",
        ecografia.id, imagen_ia_id, paciente_id,
    )

    return Response(
        {
            "status": "success",
            "ecografia_id": ecografia.id,
            "mensaje": "Ecografía creada desde imagen IA correctamente",
            "tiene_analisis_ia": bool(analisis_data),
        },
        status=status.HTTP_201_CREATED,
    )



def _reenviar_a_red_real(request, ruta: str, datos: dict) -> Response:
    """Pasa la imagen al microservicio y devuelve su respuesta tal cual.

    Los 400 (imagen ilegible, tamaño de píxel absurdo) y el 503 (modelo sin
    entrenar) se reenvían con su mensaje: son información para quien usa la
    pantalla, no fallos del servidor.
    """
    if "file" not in request.FILES:
        return Response({"error": "No se proporcionó archivo"}, status=status.HTTP_400_BAD_REQUEST)
    archivo = request.FILES["file"]
    try:
        respuesta = requests.post(
            f"{obtener_url_ia()}{ruta}",
            files={"file": (archivo.name, archivo.read(), archivo.content_type)},
            data=datos,
            timeout=30,
        )
    except requests.RequestException:
        logger.exception("Microservicio de IA inalcanzable en %s", ruta)
        return Response(
            {"error": "El servicio de IA no responde. Compruebe que está en marcha (puerto 8001)."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    try:
        cuerpo = respuesta.json()
    except ValueError:
        cuerpo = {"error": respuesta.text[:300]}
    if respuesta.status_code != 200 and "detail" in cuerpo:
        cuerpo = {"error": cuerpo["detail"]}
    return Response(cuerpo, status=respuesta.status_code)


@extend_schema(request=None, responses={200: dict})
@api_view(["POST"])
@permission_classes([FetalMedicalPermission])
def plano_anatomico(request):
    """Qué plano muestra la ecografía (red entrenada con FETAL_PLANES_DB real).

    Endpoint: POST /api/ecografias/plano-anatomico/  — file
    """
    return _reenviar_a_red_real(request, "/api/plano-anatomico", {})


@extend_schema(request=None, responses={200: dict})
@api_view(["POST"])
@permission_classes([FetalMedicalPermission])
def circunferencia_cefalica(request):
    """Circunferencia cefálica y edad gestacional (red entrenada con HC18 real).

    Endpoint: POST /api/ecografias/circunferencia-cefalica/  — file, tamano_pixel_mm
    """
    tamano = request.data.get("tamano_pixel_mm")
    if not tamano:
        return Response(
            {"error": "Falta tamano_pixel_mm: los milímetros que mide un píxel, "
                      "los da el ecógrafo o la cabecera DICOM."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return _reenviar_a_red_real(
        request, "/api/biometria/circunferencia-cefalica", {"tamano_pixel_mm": tamano},
    )


@extend_schema(request=None, responses={200: dict})
@api_view(["POST"])
@permission_classes([FetalMedicalPermission])
def anomalias_cerebrales(request):
    """Cribado de anomalías cerebrales fetales (red entrenada con ecografías reales).

    Endpoint: POST /api/ecografias/anomalias-cerebrales/  — file
    """
    return _reenviar_a_red_real(request, "/api/anomalias-cerebrales", {})
