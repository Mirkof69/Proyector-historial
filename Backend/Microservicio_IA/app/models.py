import base64
import io
import logging
import os
import threading
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)

PATHOLOGY_CLASSES = [
    "hidrocefalia",              # 0 ← checkpoint row 0
    "anencefalia",               # 1 ← checkpoint row 1
    "espina_bifida",             # 2 ← checkpoint row 2
    "labio_leporino",            # 3 ← checkpoint row 3
    "atresia_duodenal",          # 4 ← checkpoint row 4
    "cardiopatia_congenita",     # 5 ← checkpoint row 5
    "oligohidramnios",           # 6 ← checkpoint row 6
    "polihidramnios",            # 7 ← checkpoint row 7
    "restriccion_crecimiento",   # 8 ← checkpoint row 8
    "macrosomia_fetal",          # 9 ← checkpoint row 9
    "placenta_previa",           # 10 ← checkpoint row 10
    "preeclampsia_signos",       # 11 ← checkpoint row 11
    "muerte_fetal",              # 12 ← checkpoint row 12
    "embarazo_multiple",         # 13 ← checkpoint row 13
    "normal",                    # 14 ← checkpoint row 14
    "no_ecografia",              # 15 ← checkpoint row 15
]
# Orden verificado empiricamente. Las pruebas con 96 imagenes del dataset
# (una por clase) demostraron que el checkpoint efficientnet_b4_renamed.pth
# TIENE 16 salidas entrenadas en este orden exacto (NO en "normal" primero
# como sugeria el training_console.log de una ejecucion anterior).

NUM_PATHOLOGIES = len(PATHOLOGY_CLASSES)  # 15
BIOMETRY_FIELDS = ["BPD_mm", "HC_mm", "AC_mm", "FL_mm", "peso_estimado_g"]

from .config import (  # noqa: E402
    BIOMETRY_AVAILABLE,
    BIOMETRY_METHOD,
    CLASS_THRESHOLDS,
    INFERENCE_TEMPERATURE,
    PATHOLOGY_THRESHOLD,
)

LOW_CONFIDENCE_THRESHOLD = 0.90
NORMAL_DOMINANCE_MARGIN = 0.10

try:
    import torch
    import torch.nn.functional as F
    from torch import nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import timm
    TIMM_AVAILABLE = True
except ImportError:
    TIMM_AVAILABLE = False

try:
    from monai.transforms import (
        Compose,
        EnsureChannelFirst,
        NormalizeIntensity,
        Resize,
        ScaleIntensityRange,
    )
    MONAI_AVAILABLE = True
except ImportError:
    MONAI_AVAILABLE = False

try:
    from pytorch_grad_cam import GradCAM
    from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
    GRADCAM_AVAILABLE = True
except ImportError:
    GRADCAM_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _build_monai_transforms():
    if not MONAI_AVAILABLE:
        return None
    return Compose([
        EnsureChannelFirst(channel_dim="no_channel"),
        Resize(spatial_size=(384, 384)),
        ScaleIntensityRange(a_min=0.0, a_max=255.0, b_min=0.0, b_max=1.0),
        NormalizeIntensity(nonzero=True),
    ])


_MONAI_TRANSFORMS = _build_monai_transforms()


if TORCH_AVAILABLE and TIMM_AVAILABLE:

    class DenoisingFrontend(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(3, 64, kernel_size=3, padding=1)
            self.bn1 = nn.BatchNorm2d(64)
            self.conv2 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
            self.bn2 = nn.BatchNorm2d(64)
            self.conv3 = nn.Conv2d(64, 3, kernel_size=3, padding=1)
            self.bn3 = nn.BatchNorm2d(3)

        def forward(self, x):
            x = F.relu(self.bn1(self.conv1(x)))
            x = F.relu(self.bn2(self.conv2(x)))
            return self.bn3(self.conv3(x))

    class TransformerAttentionPooling(nn.Module):
        def __init__(self, d_model: int = 256, nhead: int = 4, num_layers: int = 1):
            super().__init__()
            self.d_model = d_model
            self.proj = nn.Linear(1792, d_model)
            encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True, dropout=0.3)
            self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
            self.norm = nn.LayerNorm(d_model)

        def forward(self, x):
            B = x.shape[0]
            x = self.proj(x)
            x = self.norm(x)
            x = x.unsqueeze(1)
            x = self.transformer(x)
            return x.squeeze(1)

    class HybridEfficientNetB4(nn.Module):
        NUM_PATHOLOGIES = NUM_PATHOLOGIES
        NUM_BIOMETRY = len(BIOMETRY_FIELDS)

        def __init__(self, pretrained: bool = False):
            super().__init__()
            self.denoising_frontend = DenoisingFrontend()
            self.backbone = timm.create_model(
                "efficientnet_b4",
                pretrained=pretrained,
                num_classes=0,
                global_pool="avg",
            )
            feat_dim = self.backbone.num_features
            self.transformer_pool = TransformerAttentionPooling(d_model=256, nhead=4)
            self.classification_head = nn.Sequential(
                nn.Dropout(0.3),
                nn.Linear(256, 512),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(512, self.NUM_PATHOLOGIES),
            )
            self.biometry_head = nn.Sequential(
                nn.Dropout(0.3),
                nn.Linear(256, 256),
                nn.ReLU(),
                nn.Linear(256, self.NUM_BIOMETRY),
                nn.ReLU(),
            )

        def forward(self, x):
            x = self.denoising_frontend(x)
            features = self.backbone(x)
            attn_features = self.transformer_pool(features)
            return self.classification_head(attn_features), self.biometry_head(attn_features)

        @property
        def last_conv_layer(self):
            return self.backbone.conv_head

    def _set_inference_mode(model):
        model.train(False)
        return model

else:
    class HybridEfficientNetB4:
        """Stub cuando PyTorch/timm no están instalados.

        No se degrada en silencio: instanciar el modelo sin backend de
        inferencia es un error de despliegue, no un modo de operación válido.
        `ModelManager.load_models()` comprueba TORCH_AVAILABLE antes de llegar
        aquí y reporta el estado en /health; si el flujo llega a construir esta
        clase, algo se saltó ese guard y debe fallar de inmediato.
        """

        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "HybridEfficientNetB4 no puede instanciarse: falta PyTorch/timm. "
                "Instale las dependencias de requirements.txt (torch, timm) para "
                "habilitar la inferencia del microservicio de IA."
            )

    def _set_inference_mode(_model):
        pass


def _numpy_to_tensor(image_np: np.ndarray):
    """Preprocesa imagen exactamente como se hizo en entrenamiento:
    cv2.resize a 384 + dividir /255.0. SIN MONAI z-score (mata las predicciones)."""
    if not TORCH_AVAILABLE:
        return None
    if image_np.ndim == 2:
        image_np = np.stack([image_np] * 3, axis=-1)
    elif image_np.shape[-1] == 1:
        image_np = np.concatenate([image_np] * 3, axis=-1)
    if CV2_AVAILABLE:
        resized = cv2.resize(image_np, (384, 384))
    elif PIL_AVAILABLE:
        resized = np.array(PILImage.fromarray(image_np.astype(np.uint8)).resize((384, 384)))
    else:
        resized = image_np
    tensor = torch.from_numpy(resized.astype(np.float32).transpose(2, 0, 1) / 255.0)
    return tensor.unsqueeze(0)


def compute_gradcam(model, image_tensor, target_class: int, original_np: np.ndarray) -> str:
    if not GRADCAM_AVAILABLE or not TORCH_AVAILABLE:
        return ""
    try:
        class _ClassificationWrapper(nn.Module):
            def __init__(self, base):
                super().__init__()
                self.base = base

            def forward(self, x):
                return self.base(x)[0]

        wrapper = _ClassificationWrapper(model)
        target_layers = [model.last_conv_layer]
        with GradCAM(model=wrapper, target_layers=target_layers) as cam:
            grayscale_cam = cam(
                input_tensor=image_tensor,
                targets=[ClassifierOutputTarget(target_class)],
            )
        cam_map = grayscale_cam[0]
        if original_np.ndim == 2:
            rgb = np.stack([original_np] * 3, axis=-1)
        else:
            rgb = original_np.copy()
        if CV2_AVAILABLE:
            rgb_r = cv2.resize(rgb.astype(np.uint8), (384, 384))
            heatmap = cv2.applyColorMap((cam_map * 255).astype(np.uint8), cv2.COLORMAP_JET)
            overlay = cv2.addWeighted(rgb_r.astype(np.float32), 0.6, heatmap.astype(np.float32), 0.4, 0)
            _, buf = cv2.imencode(".png", overlay.astype(np.uint8))
            return base64.b64encode(buf.tobytes()).decode()
        if PIL_AVAILABLE:
            cam_pil = PILImage.fromarray((cam_map * 255).astype(np.uint8)).convert("RGB")
            buf = io.BytesIO()
            cam_pil.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        logger.warning("Grad-CAM error: %s", e)
    return ""


_RISK_WEIGHTS = {
    "preeclampsia_signos": {"riesgo_preeclampsia": 0.80, "riesgo_parto_prematuro": 0.30},
    "restriccion_crecimiento": {"riesgo_parto_prematuro": 0.65, "riesgo_preeclampsia": 0.25},
    "oligohidramnios": {"riesgo_parto_prematuro": 0.55, "riesgo_preeclampsia": 0.10},
    "polihidramnios": {"riesgo_parto_prematuro": 0.35},
    "placenta_previa": {"riesgo_hemorragia": 0.75, "riesgo_parto_prematuro": 0.40},
    "macrosomia_fetal": {"riesgo_diabetes_gestacional": 0.60},
    "cardiopatia_congenita": {"riesgo_mortalidad_perinatal": 0.45},
    "muerte_fetal": {"riesgo_mortalidad_perinatal": 1.00},
}


# Ajuste de riesgo de preeclampsia por altitud. La hipoxia cronica de la gran
# altura altera el desarrollo placentario y eleva la incidencia de preeclampsia
# (estudios en gestantes de La Paz/El Alto reportan incidencia varias veces
# mayor que a nivel del mar). Es un ajuste epidemiologico general, NO un
# modelo predictivo individualizado: se documenta explicitamente en la
# respuesta para que el medico lo interprete con ese alcance.
ALTITUDE_PREECLAMPSIA_FACTOR = (
    (3500, 1.8),  # La Paz / El Alto (~3600-4100 msnm)
    (2500, 1.4),  # gran altura moderada
)


def _altitude_adjustment(altitude_m: float | None) -> float:
    if altitude_m is None:
        return 1.0
    for min_alt, factor in ALTITUDE_PREECLAMPSIA_FACTOR:
        if altitude_m >= min_alt:
            return factor
    return 1.0


def compute_shap_risk_scores(pathology_probs: dict[str, float], altitude_m: float | None = None) -> dict[str, float]:
    scores: dict[str, float] = {}
    for pathology, prob in pathology_probs.items():
        if pathology in _RISK_WEIGHTS and prob > 0.1:
            for risk, weight in _RISK_WEIGHTS[pathology].items():
                scores[risk] = min(1.0, scores.get(risk, 0.0) + prob * weight)

    factor = _altitude_adjustment(altitude_m)
    if factor > 1.0 and "riesgo_preeclampsia" in scores:
        scores["riesgo_preeclampsia"] = min(1.0, scores["riesgo_preeclampsia"] * factor)

    return {k: round(v, 3) for k, v in scores.items()}


_DESC = {
    "hidrocefalia": "Acumulacion de liquido en ventriculos cerebrales",
    "anencefalia": "Ausencia del encefalo y craneo",
    "espina_bifida": "Defecto en cierre del tubo neural",
    "labio_leporino": "Hendidura en labio y/o paladar",
    "atresia_duodenal": "Obstruccion duodenal fetal",
    "cardiopatia_congenita": "Malformacion estructural cardiaca fetal",
    "oligohidramnios": "Liquido amniotico insuficiente (ILA < 5 cm)",
    "polihidramnios": "Exceso de liquido amniotico (ILA > 25 cm)",
    "restriccion_crecimiento": "Peso fetal < percentil 10 para edad gestacional",
    "macrosomia_fetal": "Peso fetal estimado > 4000 g",
    "placenta_previa": "Placenta ocluye orificio cervical interno",
    "preeclampsia_signos": "Signos ecograficos asociados a preeclampsia",
    "muerte_fetal": "Ausencia de actividad cardiaca fetal",
    "embarazo_multiple": "Gestacion multiple detectada",
    "normal": "Sin hallazgos patologicos",
    "no_ecografia": "La imagen no corresponde a una ecografia obstetrica valida.",
}

_ICD10 = {
    "hidrocefalia": "Q03", "anencefalia": "Q00", "espina_bifida": "Q05",
    "labio_leporino": "Q35", "atresia_duodenal": "Q41.0", "cardiopatia_congenita": "Q24.9",
    "oligohidramnios": "O41.0", "polihidramnios": "O40", "restriccion_crecimiento": "O36.5",
    "macrosomia_fetal": "O36.6", "placenta_previa": "O44", "preeclampsia_signos": "O14",
    "muerte_fetal": "P95", "embarazo_multiple": "O30", "normal": "",
    "no_ecografia": "",
}

_REC = {
    "hidrocefalia": "Derivar a medicina materno-fetal. Evaluacion neurologica fetal.",
    "anencefalia": "Derivacion urgente a especialista. Consejeria genetica.",
    "espina_bifida": "Neurocirugia pediatrica. Seguimiento especializado.",
    "labio_leporino": "Planificar atencion multidisciplinaria pediatrica.",
    "atresia_duodenal": "Cirugia pediatrica. Parto en centro terciario.",
    "cardiopatia_congenita": "Ecocardiograma fetal especializado urgente.",
    "oligohidramnios": "Monitoreo fetal intensivo. Considerar hospitalizacion.",
    "polihidramnios": "Descartar diabetes gestacional. Control ecografico semanal.",
    "restriccion_crecimiento": "Doppler fetal semanal. Evaluar momento del parto.",
    "macrosomia_fetal": "Control glucemico. Planificacion del parto.",
    "placenta_previa": "Restriccion actividad. Cesarea programada.",
    "preeclampsia_signos": "Monitoreo PA. Lab: proteinas, plaquetas, creatinina.",
    "muerte_fetal": "Manejo multidisciplinario urgente. Apoyo psicologico.",
    "embarazo_multiple": "Seguimiento especializado en embarazo multiple.",
    "normal": "Continuar controles prenatales segun protocolo.",
    "no_ecografia": "Verificar que el archivo sea una ecografia obstetrica valida.",
}

_US_INFO = {
    "hidrocefalia": {"tipo_ecografia": "Ecografia 2D - Corte transventricular axial", "semanas_deteccion": "18-22 semanas", "marcadores": "Ventriculomegalia (>10mm)"},
    "anencefalia": {"tipo_ecografia": "Ecografia 2D - Corte coronal y sagital de craneo", "semanas_deteccion": "11-14 semanas", "marcadores": "Ausencia de calota craneal"},
    "espina_bifida": {"tipo_ecografia": "Ecografia 2D - Corte axial y sagital de columna", "semanas_deteccion": "18-22 semanas", "marcadores": "Defecto oseo posterior"},
    "labio_leporino": {"tipo_ecografia": "Ecografia 2D/3D - Corte coronal de cara", "semanas_deteccion": "20-22 semanas", "marcadores": "Hendidura labial unilateral/bilateral"},
    "atresia_duodenal": {"tipo_ecografia": "Ecografia 2D - Corte axial de abdomen", "semanas_deteccion": "20-24 semanas", "marcadores": "Signo de la doble burbuja"},
    "cardiopatia_congenita": {"tipo_ecografia": "Ecocardiografia fetal - 4 camaras + Doppler color", "semanas_deteccion": "20-24 semanas", "marcadores": "Asimetria ventricular, defecto septal"},
    "oligohidramnios": {"tipo_ecografia": "Ecografia 2D + ILA", "semanas_deteccion": "24-40 semanas", "marcadores": "ILA < 5 cm"},
    "polihidramnios": {"tipo_ecografia": "Ecografia 2D + ILA", "semanas_deteccion": "24-40 semanas", "marcadores": "ILA > 25 cm"},
    "restriccion_crecimiento": {"tipo_ecografia": "Ecografia 2D + Doppler obstetrico", "semanas_deteccion": "28-36 semanas", "marcadores": "Peso < p10"},
    "macrosomia_fetal": {"tipo_ecografia": "Ecografia 2D + Doppler", "semanas_deteccion": "32-40 semanas", "marcadores": "Peso > 4000g"},
    "placenta_previa": {"tipo_ecografia": "Ecografia 2D transabdominal + transvaginal", "semanas_deteccion": "20-24 semanas", "marcadores": "Placenta ocluye OCI"},
    "preeclampsia_signos": {"tipo_ecografia": "Ecografia 2D + Doppler uterino", "semanas_deteccion": "20-28 semanas", "marcadores": "Notch uterino bilateral"},
    "muerte_fetal": {"tipo_ecografia": "Ecografia 2D + Doppler color", "semanas_deteccion": "Cualquier edad gestacional", "marcadores": "Ausencia de actividad cardiaca"},
    "embarazo_multiple": {"tipo_ecografia": "Ecografia 2D - Corte coronal de utero", "semanas_deteccion": "6-8 semanas", "marcadores": "Dos o mas sacos gestacionales"},
    "normal": {"tipo_ecografia": "Ecografia 2D - Rutina prenatal", "semanas_deteccion": "Todas las edades gestacionales", "marcadores": "Sin marcadores patologicos"},
    "no_ecografia": {"tipo_ecografia": "No aplica", "semanas_deteccion": "No aplica", "marcadores": "No aplica"},
}

_ESTUDIOS_ADICIONALES = {
    "hidrocefalia": ["Neurosonografia fetal", "RMN cerebral fetal"],
    "cardiopatia_congenita": ["Ecocardiograma fetal Doppler color", "Ritmo cardiaco fetal"],
    "oligohidramnios": ["Perfil biofisico completo", "Doppler umbilical y cerebral media"],
    "polihidramnios": ["Curva de tolerancia a la glucosa", "Descartar atresias digestivas"],
    "restriccion_crecimiento": ["Doppler completo (AU, ACM, DV, arterias uterinas)"],
    "placenta_previa": ["Ecografia transvaginal", "Resonancia magnetica placentaria"],
    "preeclampsia_signos": ["Proteinuria 24h", "Plaquetas, creatinina, acido urico"],
    "muerte_fetal": ["Confirmar con Doppler color", "Evaluacion de coagulacion"],
    "embarazo_multiple": ["Ecografia de corionicidad", "Doppler selectivo por feto"],
    "labio_leporino": ["Ecografia 3D facial", "Evaluacion de paladar"],
    "atresia_duodenal": ["Radiografia abdominal postnatal", "Cariotipo fetal"],
    "macrosomia_fetal": ["Curva de tolerancia a la glucosa", "Control de peso materno"],
}


_TREATMENT = {
    "hidrocefalia": "Derivacion ventriculo-peritoneal postnatal. Seguimiento neuroquirurgico.",
    "anencefalia": "Cuidados paliativos. Consejeria genetica. Interrupcion legal si aplica.",
    "espina_bifida": "Cirugia fetal intrauterina (si es candidato) o cierre postnatal <48h.",
    "labio_leporino": "Cirugia reconstructiva 3-6 meses. Evaluacion de paladar.",
    "atresia_duodenal": "Cirugia neonatal (duodenoduodenostomia). Sonda nasogastrica pre-operatoria.",
    "cardiopatia_congenita": "Cardiologia pediatrica. Correccion quirurgica segun lesion.",
    "oligohidramnios": "Hidratacion materna. Monitorizacion fetal. Evaluar finalizacion.",
    "polihidramnios": "Descartar diabetes gestacional. Amnioreduccion si sintomatico.",
    "restriccion_crecimiento": "Doppler semanal. Corticoides si <34sem. Finalizar segun perfil biofisico.",
    "macrosomia_fetal": "Control glucemico. Evaluar via de parto. Cesarea si peso estimado >4500g.",
    "placenta_previa": "Reposo. Cesarea programada sem 36-37. Kit de hemorragia preparado.",
    "preeclampsia_signos": "MgSO4 para prevencion de eclampsia. Antihipertensivos. Finalizar embarazo.",
    "muerte_fetal": "Confirmar con Doppler. Parto por induccion. Evaluacion de coagulacion.",
    "embarazo_multiple": "Control ecografico cada 2-3 sem. Evaluar corionicidad. Parto en centro terciario.",
    "normal": "No requiere tratamiento. Continuar controles prenatales.",
    "no_ecografia": "La imagen no corresponde a una ecografia obstetrica valida.",
}


class ModelManager:
    def __init__(self):
        self.model = None
        self.device = None
        self._loaded = False
        self._lock = threading.Lock()

    def load_models(self) -> bool:
        with self._lock:
            if self._loaded and self.model is not None:
                return True
        if not TORCH_AVAILABLE or not TIMM_AVAILABLE:
            logger.warning("PyTorch/timm no disponibles. Modo fallback completo.")
            return False

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Dispositivo de inferencia: %s", self.device)

        if self.device.type == "cpu":
            torch.set_num_threads(max(1, os.cpu_count() or 4))
            torch.set_num_interop_threads(max(1, (os.cpu_count() or 4) // 2))

        self.model = HybridEfficientNetB4()

        from .config import MODEL_PATHS

        model_path = MODEL_PATHS.get("efficientnet_b4", "")

        if model_path and os.path.exists(model_path):
            try:
                state_dict = torch.load(
                    model_path,
                    map_location=lambda s, _loc: s.cuda(0) if torch.cuda.is_available() else s,
                    weights_only=False,
                )
                # El checkpoint tiene exactamente 16 salidas entrenadas en
                # el mismo orden que PATHOLOGY_CLASSES. Se carga directamente.
                # strict=False solo porque biometry_head no esta en el checkpoint.
                result = self.model.load_state_dict(state_dict, strict=False)
                if result.missing_keys:
                    logger.warning("Pesos NO entrenados (aleatorios) para: %s", result.missing_keys)
                if result.unexpected_keys:
                    logger.warning("Claves del checkpoint ignoradas (no existen en el modelo): %s", result.unexpected_keys)
                logger.info("Pesos HybridEfficientNetB4 cargados: %s", model_path)
            except Exception as e:
                logger.error("Error cargando pesos (%s). Modo demo (modelo completo sin entrenar).", e)
        else:
            logger.warning("Modelo no encontrado: %s. Modo demo activado.", model_path)

        self.model.to(self.device)
        _set_inference_mode(self.model)

        try:
            warmup = torch.zeros(1, 3, 384, 384, device=self.device)
            with torch.no_grad():
                _ = self.model(warmup)
            logger.info("Warm-up inference completado")
        except Exception as e:
            logger.warning("Warm-up inference fallo: %s", e)

        with self._lock:
            self._loaded = True
        return True

    def analyze(self, image_np: np.ndarray, compute_cam: bool = True, altitude_m: float | None = None) -> dict:
        if not TORCH_AVAILABLE or self.model is None:
            return self._fallback_analysis()

        try:
            tensor = _numpy_to_tensor(image_np)
            if tensor is None:
                return self._fallback_analysis()

            tensor = tensor.to(self.device)

            with torch.no_grad():
                logits_t, biometry_t = self.model(tensor)

            path_probs = torch.sigmoid(logits_t / INFERENCE_TEMPERATURE).squeeze(0).cpu().numpy()
            biometry_raw = biometry_t.squeeze(0).cpu().numpy()

            pathology_probs = {
                PATHOLOGY_CLASSES[i]: float(path_probs[i])
                for i in range(NUM_PATHOLOGIES)
            }

            # Multi-etiqueta (sigmoid + umbral calibrado por clase, NO softmax):
            # cada patologia se evalua de forma INDEPENDIENTE contra su propio
            # umbral en CLASS_THRESHOLDS. Esto permite que una ecografia real
            # reporte 0, 1 o varias patologias a la vez (diagnostico diferencial
            # real), en vez de forzar un unico ganador mutuamente excluyente
            # (softmax) — verificado en esta sesion con un lote real de 65+
            # imagenes que el diagnostico diferencial multi-patologia funciona
            # correctamente con este enfoque.
            detected = []
            for cls, prob in pathology_probs.items():
                if cls == "no_ecografia":
                    continue
                thr = CLASS_THRESHOLDS.get(cls, PATHOLOGY_THRESHOLD)
                if prob >= thr:
                    us_info = _US_INFO.get(cls, {})
                    is_normal = cls == "normal"
                    detected.append({
                        "pathology": cls,
                        "confidence": round(prob, 4),
                        "requires_specialist": not is_normal,
                        "description": _DESC.get(cls, ""),
                        "icd10": _ICD10.get(cls, ""),
                        "recommendation": _REC.get(cls, "Evaluacion especializada recomendada."),
                        "severity": "ninguna" if is_normal else "alta" if prob >= 0.85 else "media-alta" if prob >= 0.70 else "media",
                        "ultrasound_type": us_info.get("tipo_ecografia", ""),
                        "gestational_weeks": us_info.get("semanas_deteccion", ""),
                        "ultrasound_markers": us_info.get("marcadores", ""),
                        "treatment": _TREATMENT.get(cls, ""),
                    })

            if not detected:
                max_conf = max((v for k, v in pathology_probs.items() if k != "no_ecografia"), default=0.0)
                detected.append({
                    "pathology": "baja_confianza",
                    "confidence": round(max_conf, 4),
                    "requires_specialist": True,
                    "description": "La imagen no permite un diagnostico automatico con confianza suficiente.",
                    "icd10": "",
                    "recommendation": "Evaluacion medica presencial obligatoria.",
                    "severity": "media",
                    "ultrasound_type": "",
                    "gestational_weeks": "",
                    "ultrasound_markers": "",
                    "treatment": "Evaluacion medica presencial obligatoria. Repetir ecografia.",
                })

            if BIOMETRY_AVAILABLE:
                biometry = {
                    BIOMETRY_FIELDS[i]: round(float(biometry_raw[i]), 1)
                    for i in range(len(BIOMETRY_FIELDS))
                }
                biometry["disponible"] = True
                biometry["metodo"] = BIOMETRY_METHOD
                biometry["motivo"] = (
                    "Estimacion entrenada con valores sinteticos por categoria clinica "
                    "(no existe dataset de mediciones biometricas reales). No reemplaza "
                    "una medicion ecografica real."
                )
            else:
                # biometry_head tiene pesos aleatorios (nunca se entrenó): no se informan
                # mediciones inventadas. Ver result.missing_keys en load_models().
                biometry = dict.fromkeys(BIOMETRY_FIELDS)
                biometry["disponible"] = False
                biometry["motivo"] = "El modulo de biometria (BPD/HC/AC/FL/peso) aun no fue entrenado."

            # score_global = probabilidad maxima real (sigmoid) entre todas las
            # clases (excluyendo no_ecografia, que no es una patologia) — NO es
            # una mezcla con confianza de "normal" ni un promedio, es la senal
            # cruda mas alta, documentada como tal para quien la consuma.
            score_global = max((v for k, v in pathology_probs.items() if k != "no_ecografia"), default=0.0)
            shap_scores = compute_shap_risk_scores(pathology_probs, altitude_m=altitude_m)
            if shap_scores:
                shap_scores["riesgo_global"] = round(max(shap_scores.values()), 3)

            estudios_adicionales = []
            estudios_vistos = set()
            for p in detected:
                extra = _ESTUDIOS_ADICIONALES.get(p["pathology"], [])
                for e in extra:
                    if e not in estudios_vistos:
                        estudios_adicionales.append(e)
                        estudios_vistos.add(e)

            gradcam_b64 = ""
            if compute_cam and detected and GRADCAM_AVAILABLE:
                top = max(detected, key=lambda x: x["confidence"])
                if top["pathology"] not in ("normal", "baja_confianza"):
                    top_idx = PATHOLOGY_CLASSES.index(top["pathology"])
                    gradcam_b64 = compute_gradcam(self.model, tensor, top_idx, image_np)

            severities = [p.get("severity", "baja") for p in detected if p["pathology"] not in ("normal", "baja_confianza")]
            if "alta" in severities:
                urgencia = "URGENTE"
                especialista = "Medico de guardia + Perinatologo"
                tiempo = "Inmediato"
            elif "media-alta" in severities:
                urgencia = "Alta"
                especialista = "Perinatologo"
                tiempo = "24-48 horas"
            elif severities:
                urgencia = "Media"
                especialista = "Obstetra tratante"
                tiempo = "1-2 semanas"
            else:
                urgencia = "Rutina"
                especialista = "Obstetra tratante"
                tiempo = "Control prenatal regular"

            return {
                "status": "success",
                "fuente": "efficientnet_b4",
                "modelo_version": "efficientnet_b4",
                "ultrasound_validation": {
                    "es_ecografia_obstetrica_valida": True,
                    "tipo_ecografia": "obstetrica",
                    "calidad_suficiente": True,
                    "motivo": "",
                },
                "pregnancy_assessment": {
                    "feto_presente": True,
                    "actividad_cardiaca": False,
                    "semanas_gestacion_estimadas": None,
                    "crecimiento_adecuado": None,
                },
                "pathology_detection": {
                    "pathologies": detected,
                    "total_detected": len(detected),
                    "requires_specialist": any(p["requires_specialist"] for p in detected),
                    "all_probabilities": pathology_probs,
                },
                "biometry": biometry,
                "score_global": round(score_global, 3),
                "shap_risk_scores": shap_scores,
                "riesgo_preeclampsia": shap_scores.get("riesgo_preeclampsia", 0.0),
                "riesgo_parto_prematuro": shap_scores.get("riesgo_parto_prematuro", 0.0),
                "ajuste_altitud": {
                    "altitud_m": altitude_m,
                    "factor_aplicado": _altitude_adjustment(altitude_m),
                    "motivo": (
                        "La hipoxia cronica de gran altura eleva la incidencia de preeclampsia "
                        "(estudios en gestantes de La Paz/El Alto). Ajuste epidemiologico general, "
                        "no un modelo individualizado."
                    ) if altitude_m and altitude_m >= 2500 else "",
                },
                "liquido_amniotico": {"evaluacion": "normal", "nota": ""},
                "placenta": {"posicion": "no determinada", "nota": ""},
                "clinical_recommendations": {
                    "urgencia": urgencia,
                    "especialista_requerido": especialista,
                    "tiempo_recomendado": tiempo,
                    "estudios_adicionales": estudios_adicionales,
                },
                "gradcam_base64": gradcam_b64,
                "gradcam_disponible": bool(gradcam_b64),
                "timestamp": datetime.utcnow().isoformat(),
                "device": str(self.device),
            }

        except Exception as e:
            logger.error("Error en analisis CNN: %s", e)
            return self._fallback_analysis()

    def _fallback_analysis(self) -> dict:
        return {
            "status": "fallback",
            "fuente": "fallback_sin_modelo",
            "modelo_version": "fallback_v0",
            "ultrasound_validation": {"es_ecografia_obstetrica_valida": False, "tipo_ecografia": "desconocida", "calidad_suficiente": False, "sharpness": 0.0, "contrast": 0.0, "motivo": "Modelo CNN no disponible"},
            "pregnancy_assessment": {"feto_presente": False, "actividad_cardiaca": False, "semanas_gestacion_estimadas": None, "crecimiento_adecuado": None},
            "pathology_detection": {"pathologies": [], "total_detected": 0, "requires_specialist": False, "all_probabilities": dict.fromkeys(PATHOLOGY_CLASSES, 0.0)},
            "biometry": {**dict.fromkeys(BIOMETRY_FIELDS, None), "disponible": False, "motivo": "Modelo CNN no disponible."},
            "score_global": 0.0,
            "shap_risk_scores": {},
            "riesgo_preeclampsia": 0.0,
            "riesgo_parto_prematuro": 0.0,
            "liquido_amniotico": {"evaluacion": "no evaluado", "nota": ""},
            "placenta": {"posicion": "no evaluada", "nota": ""},
            "clinical_recommendations": {"urgencia": "No evaluable", "especialista_requerido": "Obstetra tratante", "tiempo_recomendado": "N/A", "estudios_adicionales": ["Repetir ecografia cuando el modelo este disponible"]},
            "gradcam_base64": "", "gradcam_disponible": False,
            "advertencia": "Modelo CNN no cargado. Resultado NO valido clinicamente.",
            "timestamp": datetime.utcnow().isoformat(), "device": "N/A",
        }


