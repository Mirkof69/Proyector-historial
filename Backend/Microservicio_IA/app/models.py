"""CNN EfficientNet-B4 para análisis de ecografías fetales
Framework: PyTorch 2.2 + MONAI + timm
Dos cabezas: clasificación multi-label (15 patologías) + regresión biometría fetal
Grad-CAM: pytorch-grad-cam sobre última capa convolucional
SHAP: scores de riesgo materno aditivos ponderados por patología
"""

import base64
import io
import logging
import os
import threading
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)

PATHOLOGY_CLASSES = [
    "normal",
    "hidrocefalia",
    "anencefalia",
    "espina_bifida",
    "labio_leporino",
    "atresia_duodenal",
    "cardiopatia_congenita",
    "oligohidramnios",
    "polihidramnios",
    "restriccion_crecimiento",
    "macrosomia_fetal",
    "placenta_previa",
    "preeclampsia_signos",
    "muerte_fetal",
    "embarazo_multiple",
]

BIOMETRY_FIELDS = ["BPD_mm", "HC_mm", "AC_mm", "FL_mm", "peso_estimado_g"]

PATHOLOGY_THRESHOLD = 0.50

# ── IMPORTS OPCIONALES ────────────────────────────────────────────────────────
try:
    import torch
    from torch import nn

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch no disponible. Modo fallback activado.")

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
    logger.warning("MONAI no disponible. Usando fallback Pillow para preprocessing.")

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


# ── MONAI TRANSFORM PIPELINE ──────────────────────────────────────────────────
def _build_monai_transforms():
    """Build monai transforms"""
    if not MONAI_AVAILABLE:
        return None
    return Compose(
        [
            EnsureChannelFirst(channel_dim="no_channel"),
            Resize(spatial_size=(384, 384)),
            ScaleIntensityRange(a_min=0.0, a_max=255.0, b_min=0.0, b_max=1.0),
            NormalizeIntensity(nonzero=True),
        ],
    )


_MONAI_TRANSFORMS = _build_monai_transforms()


# ── MODELO ────────────────────────────────────────────────────────────────────
if TORCH_AVAILABLE and TIMM_AVAILABLE:

    class EfficientNetB4CNN(nn.Module):
        """EfficientNet-B4 backbone con dos cabezas:
          - classification_head: 15 patologías multi-label (sigmoid, umbral >= 0.50)
          - biometry_head: BPD, HC, AC, FL, peso estimado (regresión, ReLU)
        Input esperado: (B, 3, 384, 384) normalizado [0, 1]
        """

        NUM_PATHOLOGIES = len(PATHOLOGY_CLASSES)
        NUM_BIOMETRY = len(BIOMETRY_FIELDS)

        def __init__(self, pretrained: bool = False):
            super().__init__()
            self.backbone = timm.create_model(
                "efficientnet_b4",
                pretrained=pretrained,
                num_classes=0,
                global_pool="avg",
            )
            feat_dim = self.backbone.num_features  # 1792

            self.classification_head = nn.Sequential(
                nn.Dropout(0.3),
                nn.Linear(feat_dim, 512),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(512, self.NUM_PATHOLOGIES),
            )
            self.biometry_head = nn.Sequential(
                nn.Dropout(0.3),
                nn.Linear(feat_dim, 256),
                nn.ReLU(),
                nn.Linear(256, self.NUM_BIOMETRY),
                nn.ReLU(),
            )

        def forward(self, x):
            """Forward"""
            features = self.backbone(x)
            return self.classification_head(features), self.biometry_head(features)

        @property
        def last_conv_layer(self):
            """Last conv layer"""
            return self.backbone.conv_head

    def _set_inference_mode(model):
        """Desactiva dropout/batchnorm para inferencia (equivale a model.train(False))."""
        model.train(False)
        return model

else:
    class EfficientNetB4CNN:  # type: ignore[no-redef]
        """Stub cuando PyTorch/timm no estan disponibles."""

    def _set_inference_mode(_model):  # type: ignore[no-redef]
        pass


# ── PREPROCESSING ──────────────────────────────────────────────────────────────
def _numpy_to_tensor(image_np: np.ndarray):
    """Convierte numpy (H,W) o (H,W,C) a tensor PyTorch (1,3,384,384)."""
    if not TORCH_AVAILABLE:
        return None

    if image_np.ndim == 2:
        image_np = np.stack([image_np] * 3, axis=-1)
    elif image_np.shape[-1] == 1:
        image_np = np.concatenate([image_np] * 3, axis=-1)

    image_np = image_np.astype(np.float32)

    if MONAI_AVAILABLE and _MONAI_TRANSFORMS is not None:
        gray = image_np.mean(axis=-1)  # (H,W) para EnsureChannelFirst
        tensor = _MONAI_TRANSFORMS(gray)  # (1,384,384)
        tensor = tensor.repeat(3, 1, 1)  # (3,384,384)
    elif PIL_AVAILABLE:
        img_pil = PILImage.fromarray(image_np.astype(np.uint8)).resize((384, 384))
        arr = np.array(img_pil, dtype=np.float32) / 255.0
        if arr.ndim == 2:
            arr = np.stack([arr] * 3, axis=-1)
        tensor = torch.from_numpy(arr.transpose(2, 0, 1))
    else:
        return None

    return tensor.unsqueeze(0)  # (1,3,384,384)


# ── GRAD-CAM ──────────────────────────────────────────────────────────────────
def compute_gradcam(
    model, image_tensor, target_class: int, original_np: np.ndarray,
) -> str:
    """Grad-CAM sobre ultima capa conv. Retorna PNG base64 para OHIF overlay."""
    if not GRADCAM_AVAILABLE or not TORCH_AVAILABLE:
        return ""
    try:

        class _ClassificationWrapper(nn.Module):
            """Classificationwrapper"""
            def __init__(self, base):
                """Init"""
                super().__init__()
                self.base = base

            def forward(self, x):
                """Forward"""
                return self.base(x)[0]  # solo cabeza clasificacion

        wrapper = _ClassificationWrapper(model)
        target_layers = [model.last_conv_layer]

        with GradCAM(model=wrapper, target_layers=target_layers) as cam:
            grayscale_cam = cam(
                input_tensor=image_tensor,
                targets=[ClassifierOutputTarget(target_class)],
            )

        cam_map = grayscale_cam[0]  # (384,384)

        if original_np.ndim == 2:
            rgb = np.stack([original_np] * 3, axis=-1)
        else:
            rgb = original_np.copy()

        if CV2_AVAILABLE:
            rgb_r = cv2.resize(rgb.astype(np.uint8), (384, 384))
            heatmap = cv2.applyColorMap(
                (cam_map * 255).astype(np.uint8), cv2.COLORMAP_JET,
            )
            overlay = cv2.addWeighted(
                rgb_r.astype(np.float32),
                0.6,
                heatmap.astype(np.float32),
                0.4,
                0,
            )
            _, buf = cv2.imencode(".png", overlay.astype(np.uint8))
            return base64.b64encode(buf.tobytes()).decode()

        if PIL_AVAILABLE:
            cam_pil = PILImage.fromarray((cam_map * 255).astype(np.uint8)).convert(
                "RGB",
            )
            buf = io.BytesIO()
            cam_pil.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()

    except Exception as e:
        logger.warning("Grad-CAM error: %s", e)
    return ""


# ── SHAP RISK SCORES ──────────────────────────────────────────────────────────
_RISK_WEIGHTS = {
    "preeclampsia_signos": {
        "riesgo_preeclampsia": 0.80,
        "riesgo_parto_prematuro": 0.30,
    },
    "restriccion_crecimiento": {
        "riesgo_parto_prematuro": 0.65,
        "riesgo_preeclampsia": 0.25,
    },
    "oligohidramnios": {"riesgo_parto_prematuro": 0.55, "riesgo_preeclampsia": 0.10},
    "polihidramnios": {"riesgo_parto_prematuro": 0.35},
    "placenta_previa": {"riesgo_hemorragia": 0.75, "riesgo_parto_prematuro": 0.40},
    "macrosomia_fetal": {"riesgo_diabetes_gestacional": 0.60},
    "cardiopatia_congenita": {"riesgo_mortalidad_perinatal": 0.45},
    "muerte_fetal": {"riesgo_mortalidad_perinatal": 1.00},
}


def compute_shap_risk_scores(pathology_probs: dict[str, float]) -> dict[str, float]:
    """Atribucion aditiva ponderada de riesgo materno (SHAP-like).
    Retorna scores 0-1 por categoria de riesgo.
    """
    scores: dict[str, float] = {}
    for pathology, prob in pathology_probs.items():
        if pathology in _RISK_WEIGHTS and prob > 0.1:
            for risk, weight in _RISK_WEIGHTS[pathology].items():
                scores[risk] = min(1.0, scores.get(risk, 0.0) + prob * weight)
    return {k: round(v, 3) for k, v in scores.items()}


# ── PATHOLOGY METADATA ────────────────────────────────────────────────────────
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
}

_ICD10 = {
    "hidrocefalia": "Q03",
    "anencefalia": "Q00",
    "espina_bifida": "Q05",
    "labio_leporino": "Q35",
    "atresia_duodenal": "Q41.0",
    "cardiopatia_congenita": "Q24.9",
    "oligohidramnios": "O41.0",
    "polihidramnios": "O40",
    "restriccion_crecimiento": "O36.5",
    "macrosomia_fetal": "O36.6",
    "placenta_previa": "O44",
    "preeclampsia_signos": "O14",
    "muerte_fetal": "P95",
    "embarazo_multiple": "O30",
    "normal": "",
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
}


# ── MODEL MANAGER ─────────────────────────────────────────────────────────────
class ModelManager:
    """Singleton que carga y gestiona EfficientNetB4CNN."""

    def __init__(self):
        """Init"""
        self.model = None
        self.device = None
        self._loaded = False
        self._lock = threading.Lock()

    def load_models(self) -> bool:
        """Load models"""
        with self._lock:
            if self._loaded and self.model is not None:
                return True
        if not TORCH_AVAILABLE or not TIMM_AVAILABLE:
            logger.warning("PyTorch/timm no disponibles. Modo fallback completo.")
            return False

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Dispositivo de inferencia: %s", self.device)

        # CPU optimization: set thread counts for faster inference
        if self.device.type == "cpu":
            torch.set_num_threads(max(1, os.cpu_count() or 4))
            torch.set_num_interop_threads(max(1, (os.cpu_count() or 4) // 2))
            logger.info(
                "CPU threads: intra=%d, inter=%d",
                torch.get_num_threads(),
                torch.get_num_interop_threads(),
            )

        self.model = EfficientNetB4CNN()

        from .config import MODEL_PATHS

        model_path = MODEL_PATHS.get("efficientnet_b4", "")

        if model_path and os.path.exists(model_path):
            try:
                state_dict = torch.load(
                    model_path, map_location=self.device, weights_only=True,
                )
                self.model.load_state_dict(state_dict)
                logger.info("Pesos EfficientNet-B4 cargados: %s", model_path)
            except Exception as e:
                logger.warning(
                    "Error cargando pesos (%s). Modo demo (pesos aleatorios).", e,
                )
        else:
            logger.warning("Modelo no encontrado: %s. Modo demo activado.", model_path)

        self.model.to(self.device)
        # Modo inferencia: desactiva dropout y batch norm training behavior
        _set_inference_mode(self.model)

        # Warm-up inference to pre-allocate buffers and optimize execution paths
        try:
            warmup = torch.zeros(1, 3, 384, 384, device=self.device)
            with torch.no_grad():
                _ = self.model(warmup)
            logger.info("Warm-up inference completado (buffers pre-alocados)")
        except Exception as e:
            logger.warning("Warm-up inference fallo: %s", e)

        with self._lock:
            self._loaded = True
        return True

    def analyze(self, image_np: np.ndarray, compute_cam: bool = True) -> dict:
        """Analisis completo: patologias + biometria + Grad-CAM + SHAP."""
        if not TORCH_AVAILABLE or self.model is None:
            return self._fallback_analysis()

        try:
            tensor = _numpy_to_tensor(image_np)
            if tensor is None:
                return self._fallback_analysis()

            tensor = tensor.to(self.device)

            with torch.no_grad():
                logits_t, biometry_t = self.model(tensor)

            path_probs = torch.sigmoid(logits_t).squeeze(0).cpu().numpy()
            biometry_raw = biometry_t.squeeze(0).cpu().numpy()

            pathology_probs = {
                PATHOLOGY_CLASSES[i]: float(path_probs[i])
                for i in range(len(PATHOLOGY_CLASSES))
            }

            detected = [
                {
                    "pathology": cls,
                    "confidence": float(prob),
                    "requires_specialist": prob >= 0.70,
                    "description": _DESC.get(cls, ""),
                    "icd10": _ICD10.get(cls, ""),
                    "recommendation": _REC.get(
                        cls, "Evaluacion especializada recomendada.",
                    ),
                    "severity": "alta"
                    if prob >= 0.85
                    else "media-alta"
                    if prob >= 0.70
                    else "media",
                }
                for cls, prob in pathology_probs.items()
                if prob >= PATHOLOGY_THRESHOLD and cls != "normal"
            ]

            biometry = {
                BIOMETRY_FIELDS[i]: round(float(biometry_raw[i]), 1)
                for i in range(len(BIOMETRY_FIELDS))
            }

            score_global = (
                float(np.mean([p["confidence"] for p in detected])) if detected else 0.0
            )
            shap_scores = compute_shap_risk_scores(pathology_probs)

            gradcam_b64 = ""
            if compute_cam and detected and GRADCAM_AVAILABLE:
                top = max(detected, key=lambda x: x["confidence"])
                top_idx = PATHOLOGY_CLASSES.index(top["pathology"])
                gradcam_b64 = compute_gradcam(self.model, tensor, top_idx, image_np)

            return {
                "status": "success",
                "fuente": "efficientnet_b4_pytorch",
                "modelo_version": "efficientnet_b4_v1.0",
                "pathology_detection": {
                    "pathologies": detected,
                    "total_detected": len(detected),
                    "requires_specialist": any(
                        p["requires_specialist"] for p in detected
                    ),
                    "all_probabilities": pathology_probs,
                },
                "biometry": biometry,
                "score_global": round(score_global, 3),
                "shap_risk_scores": shap_scores,
                "riesgo_preeclampsia": shap_scores.get("riesgo_preeclampsia", 0.0),
                "riesgo_parto_prematuro": shap_scores.get(
                    "riesgo_parto_prematuro", 0.0,
                ),
                "gradcam_base64": gradcam_b64,
                "gradcam_disponible": bool(gradcam_b64),
                "timestamp": datetime.utcnow().isoformat(),
                "device": str(self.device),
            }

        except Exception as e:
            logger.error("Error en analisis CNN: %s", e)
            return self._fallback_analysis()

    def _fallback_analysis(self) -> dict:
        """Fallback analysis"""
        return {
            "status": "fallback",
            "fuente": "fallback_sin_modelo",
            "modelo_version": "fallback_v0",
            "pathology_detection": {
                "pathologies": [],
                "total_detected": 0,
                "requires_specialist": False,
                "all_probabilities": dict.fromkeys(PATHOLOGY_CLASSES, 0.0),
            },
            "biometry": dict.fromkeys(BIOMETRY_FIELDS, 0.0),
            "score_global": 0.0,
            "shap_risk_scores": {},
            "riesgo_preeclampsia": 0.0,
            "riesgo_parto_prematuro": 0.0,
            "gradcam_base64": "",
            "gradcam_disponible": False,
            "advertencia": "Modelo CNN no cargado. Resultado NO valido clinicamente.",
            "timestamp": datetime.utcnow().isoformat(),
            "device": "N/A",
        }
