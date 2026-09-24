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
    salida["gradcam_url"] = guardar_gradcam(base64_gradcam, prefijo="eco")
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
        - ecografia_id: ID de la ecografía (opcional)

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

        # Ajuste de riesgo de preeclampsia por altitud (ver Microservicio_IA
        # app/models.py ALTITUDE_PREECLAMPSIA_FACTOR): se resuelve por la
        # ciudad del paciente cuando esta disponible.
        data = {"ciudad": ciudad_paciente} if ciudad_paciente else {}

        # Llamar al microservicio de IA
        ai_response = requests.post(
            f"{obtener_url_ia()}/api/analyze", files=files, data=data, timeout=30,
        )

        if ai_response.status_code == 200:
            ai_results = ai_response.json()

            # Guardar resultados en la imagen ecográfica (si se provee ID)
            if ecografia_id:
                try:
                    from .models import ImagenEcografia

                    imagen = (
                        ImagenEcografia.objects.filter(ecografia_id=ecografia_id)
                        .order_by("-fecha_captura")
                        .first()
                    )
                    if imagen:
                        imagen.analisis_ia = ai_results
                        imagen.save(update_fields=["analisis_ia"])
                except Exception as ex:
                    logger.exception(
                        "Error al guardar resultados IA en AnalisisCNN para ia_medica.ImagenEcografica id=%s: %s",
                        ecografia_id, ex,
                    )

            # Guardar resultados en ia_medica.ImagenEcografica / AnalisisCNN
            if ecografia_id:
                try:
                    from ia_medica.models import AnalisisCNN
                    from ia_medica.models import ImagenEcografica as IaImagen

                    imagen_ia = IaImagen.objects.get(id=ecografia_id)

                    from ia_medica.services.result_mapping import (
                        mapear_resultado_microservicio,
                    )

                    score_global = ai_results.get("score_global", 0)

                    mapeo = mapear_resultado_microservicio(ai_results)
                    pathologies = mapeo["pathologies"]
                    resultado = mapeo["resultado"]
                    confianza = mapeo["confianza"]

                    # "detected" = patologias reales distintas de normal/baja_confianza,
                    # ya filtradas por el microservicio con los umbrales calibrados por
                    # clase (no se vuelve a aplicar un umbral plano aqui).
                    detected = [
                        p for p in pathologies
                        if p.get("name") not in ("normal", "baja_confianza")
                    ]

                    biometry_raw = ai_results.get("biometry", {})
                    measurements = biometry_raw if isinstance(biometry_raw, dict) else {}

                    preds = [{"clase": p.get("name", ""), "confianza": p.get("probability", 0)} for p in pathologies]
                    anomalias = [
                        {"tipo": p.get("name", ""), "confianza": p.get("probability", 0),
                         "severidad": "alta" if p.get("probability", 0) >= 0.8 else "media"}
                        for p in detected
                    ]
                    alertas = biometry_raw.get("alerts", []) if isinstance(biometry_raw, dict) else []
                    recs = []
                    for p in detected:
                        name = p.get("name", "").replace("_", " ")
                        prob = p.get("probability", 0)
                        if prob >= 0.8:
                            recs.append(f"Remisión urgente: {name} ({prob*100:.0f}%)")
                        elif prob >= 0.5:
                            recs.append(f"Evaluar: {name} ({prob*100:.0f}%) - requiere confirmación")
                    if not recs:
                        recs.append("Control prenatal de rutina")

                    shap = ai_results.get("shap_risk_scores", {})

                    sugerencia = ai_results.get("sugerencia_diagnostica", {})
                    sugerencia_val = sugerencia if isinstance(sugerencia, dict) else None
                    analisis, _created = AnalisisCNN.objects.update_or_create(
                        imagen=imagen_ia,
                        defaults={
                            "modelo_usado": "efficientnet",
                            "version_modelo": ai_results.get("modelo_version", "EfficientNet-B4"),
                            "resultado": resultado,
                            "confianza": round(float(confianza), 4),
                            "score_general": round(float(score_global) * 100, 1),
                            "predicciones": preds,
                            "clases_detectadas": [p.get("name", "") for p in pathologies],
                            "estructuras_detectadas": {
                                p.get("name", ""): {"confianza": p.get("probability", 0)}
                                for p in pathologies
                            },
                            "medidas_estimadas": measurements if measurements else None,
                            "anomalias_detectadas": anomalias,
                            "alertas": alertas,
                            "recomendaciones": recs,
                            "mapa_calor": ai_results.get("gradcam_base64"),
                            "bpd_mm": measurements.get("BPD_mm"),
                            "hc_mm": measurements.get("HC_mm"),
                            "ac_mm": measurements.get("AC_mm"),
                            "fl_mm": measurements.get("FL_mm"),
                            "riesgo_preeclampsia": shap.get("riesgo_preeclampsia"),
                            "riesgo_parto_prematuro": shap.get("riesgo_parto_prematuro"),
                            "nivel_riesgo": "ALTO" if score_global >= 0.7
                                        else "MODERADO" if score_global >= 0.4
                                        else "BAJO",
                            "shap_valores": shap if shap else None,
                            "patologias": [p.get("name", "") for p in detected],
                            "sugerencia_diagnostica": sugerencia_val,
                            "tiempo_inferencia_ms": ai_results.get("inference_time_ms"),
                            "realizado_por": request.user if request.user.is_authenticated else None,
                        },
                    )

                    imagen_ia.estado = "analizada"
                    imagen_ia.save(update_fields=["estado"])

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
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "error": "Error en el microservicio de IA",
                "details": ai_response.text,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

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
        "classify_ultrasound_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["POST"])
@permission_classes([FetalMedicalPermission])
def classify_ultrasound(request):
    """Clasifica el tipo de ecografía usando IA

    Endpoint: POST /api/ecografias/classify/
    """
    try:
        if "file" not in request.FILES:
            return Response(
                {"error": "No se proporcionó archivo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_file = request.FILES["file"]
        files = {"file": (image_file.name, image_file.read(), image_file.content_type)}

        ai_response = requests.post(
            f"{obtener_url_ia()}/api/classify", files=files, timeout=15,
        )

        if ai_response.status_code == 200:
            return Response(ai_response.json(), status=status.HTTP_200_OK)
        return Response(
            {"error": "Error en clasificación"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    request=inline_serializer(
        "detect_anomalies_request",
        fields={}
    ),
    responses={200: dict}
)
@api_view(["POST"])
@permission_classes([FetalMedicalPermission])
def detect_anomalies(request):
    """Detecta anomalías fetales usando IA

    Endpoint: POST /api/ecografias/detect-anomalies/
    """
    try:
        if "file" not in request.FILES:
            return Response(
                {"error": "No se proporcionó archivo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_file = request.FILES["file"]
        files = {"file": (image_file.name, image_file.read(), image_file.content_type)}

        ai_response = requests.post(
            f"{obtener_url_ia()}/api/detect-anomalies", files=files, timeout=15,
        )

        if ai_response.status_code == 200:
            return Response(ai_response.json(), status=status.HTTP_200_OK)
        return Response(
            {"error": "Error en detección de anomalías"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
def crear_ecografia_desde_ia(request):
    """Crea una Ecografía en el módulo de ecografias desde una imagen del módulo IA.

    Endpoint: POST /api/ecografias/crear-desde-ia/

    Request:
        - imagen_ia_id: ID de ia_medica.ImagenEcografica
        - paciente_id: ID del paciente

    Crea:
        1. Embarazo (si no hay activo)
        2. Ecografia con los datos disponibles
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

    # 1. Buscar o crear embarazo activo
    embarazo = Embarazo.objects.filter(
        paciente=paciente, estado="activo"
    ).first()
    if not embarazo:
        from datetime import timedelta
        embarazo = Embarazo.objects.create(
            paciente=paciente,
            numero_gesta=1,
            numero_para=0,
            numero_abortos=0,
            numero_cesareas=0,
            fecha_ultima_menstruacion=timezone.localdate() - timedelta(days=280),
            estado="activo",
            created_by=request.user,
            updated_by=request.user,
        )

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
        fecha_ecografia=imagen_ia.fecha_captura or timezone.localdate(),
        tipo_ecografia=tipo_ecografia,
        edad_gestacional_semanas=imagen_ia.semana_gestacional or 12,
        edad_gestacional_dias=0,
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
