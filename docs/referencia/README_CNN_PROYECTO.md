# 🧠 Fetal Medical AI — CNN EfficientNet-B4 para Ginecología y Obstetricia

> **Sistema de análisis automatizado de ecografías fetales** integrado en la plataforma clínica perinatal  
> Framework: PyTorch 2.2 · timm · MONAI · Grad-CAM · SHAP  
> Microservicio: FastAPI · mTLS · Kong API Gateway

---

## 📋 Tabla de Contenidos

1. [Objetivo del Modelo](#objetivo)
2. [Arquitectura CNN](#arquitectura)
3. [Pipeline de Datos](#pipeline)
4. [Dataset Actual](#dataset)
5. [Entrenamiento](#entrenamiento)
6. [Resultados Obtenidos](#resultados)
7. [Explicabilidad — Grad-CAM y SHAP](#xai)
8. [Dataset Requerido para Producción](#dataset-produccion)
9. [Características de las Imágenes](#imagenes)
10. [Fuentes Públicas de Datos Médicos](#fuentes)
11. [Integración en el Sistema](#integracion)
12. [Métricas de Evaluación Clínica](#metricas)

---

## 1. 🎯 Objetivo del Modelo {#objetivo}

El modelo realiza **dos tareas simultáneas** sobre ecografías fetales:

### Tarea 1 — Clasificación Multi-label (15 patologías)
Detecta la presencia de **múltiples patologías simultáneas** en una sola ecografía, con probabilidad individual por clase:

| # | Patología | Código ICD-10 | Umbral |
|---|-----------|---------------|--------|
| 1 | Normal (sin hallazgos) | — | ≥ 0.50 |
| 2 | Hidrocefalia | Q03 | ≥ 0.50 |
| 3 | Anencefalia | Q00 | ≥ 0.50 |
| 4 | Espina bífida | Q05 | ≥ 0.50 |
| 5 | Labio leporino | Q35 | ≥ 0.50 |
| 6 | Atresia duodenal | Q41.0 | ≥ 0.50 |
| 7 | Cardiopatía congénita | Q24.9 | ≥ 0.50 |
| 8 | Oligohidramnios | O41.0 | ≥ 0.50 |
| 9 | Polihidramnios | O40 | ≥ 0.50 |
| 10 | Restricción del crecimiento (RCIU) | O36.5 | ≥ 0.50 |
| 11 | Macrosomía fetal | O36.6 | ≥ 0.50 |
| 12 | Placenta previa | O44 | ≥ 0.50 |
| 13 | Signos de preeclampsia | O14 | ≥ 0.50 |
| 14 | Muerte fetal | P95 | ≥ 0.50 |
| 15 | Embarazo múltiple | O30 | ≥ 0.50 |

**Derivación urgente** activada automáticamente cuando `confidence ≥ 0.70`.

### Tarea 2 — Regresión Biométrica Fetal (5 medidas)
Estima simultáneamente las biometrías fetales estándar:

| Campo | Descripción | Unidad |
|-------|-------------|--------|
| `BPD_mm` | Diámetro biparietal | mm |
| `HC_mm` | Circunferencia cefálica | mm |
| `AC_mm` | Circunferencia abdominal | mm |
| `FL_mm` | Longitud femoral | mm |
| `peso_estimado_g` | Peso fetal estimado (Hadlock) | gramos |

---

## 2. 🏗️ Arquitectura CNN {#arquitectura}

### Backbone: EfficientNet-B4 (timm)

```
Input: (B, 3, 384, 384) — Imagen RGB normalizada ImageNet
         │
    ┌────▼────────────────────────────────┐
    │  EfficientNet-B4 Backbone (timm)    │
    │  Global Average Pooling             │
    │  Feature dim: 1,792                 │
    │  Parámetros totales: ~18.9 millones │
    └────┬──────────────────┬─────────────┘
         │                  │
    ┌────▼────┐        ┌────▼────┐
    │ HEAD 1  │        │ HEAD 2  │
    │Classif. │        │Biometría│
    ├─────────┤        ├─────────┤
    │Dropout  │        │Dropout  │
    │  (0.3)  │        │  (0.3)  │
    │Linear   │        │Linear   │
    │1792→512 │        │1792→256 │
    │ReLU     │        │ReLU     │
    │Dropout  │        │Linear   │
    │  (0.2)  │        │256→5    │
    │Linear   │        │ReLU     │
    │512→15   │        └────┬────┘
    │Sigmoid  │             │
    └────┬────┘        Biometry Output
         │             (BPD, HC, AC, FL,
    Pathology         peso_estimado)
    Probabilities
    (0–1, per class)
```

### Especificaciones técnicas

| Parámetro | Valor |
|-----------|-------|
| **Backbone** | EfficientNet-B4 (timm) |
| **Transfer Learning** | `pretrained=False` (entrenado desde cero con dataset propio) |
| **Input size** | 384 × 384 px, RGB |
| **Feature dimension** | 1,792 |
| **Parámetros totales** | 18,934,620 |
| **Tipo de problema** | Multi-task: clasificación multi-label + regresión |
| **Activación salida patologías** | Sigmoid (clasificación independiente por clase) |
| **Activación salida biometría** | ReLU (regresión, valores positivos) |
| **Umbral de detección** | 0.50 (configurable) |
| **Umbral derivación especialista** | 0.70 |

---

## 3. 🔄 Pipeline de Datos {#pipeline}

### Preprocesamiento — Entrenamiento
```python
transforms.Compose([
    Resize((384, 384)),                              # Estandarización de tamaño
    RandomHorizontalFlip(p=0.5),                     # Augmentación geométrica
    RandomVerticalFlip(p=0.2),                       # Augmentación geométrica
    ColorJitter(brightness=0.3, contrast=0.3,        # Augmentación fotométrica
                saturation=0.1),
    RandomRotation(10),                              # Rotación ±10°
    ToTensor(),                                      # Conversión a tensor
    Normalize(mean=[0.485, 0.456, 0.406],           # Normalización ImageNet
              std=[0.229, 0.224, 0.225]),
])
```

### Preprocesamiento — Inferencia (MONAI pipeline)
```python
Compose([
    EnsureChannelFirst(channel_dim="no_channel"),    # (H,W) → (1,H,W)
    Resize(spatial_size=(384, 384)),                 # Resize estándar
    ScaleIntensityRange(0, 255, 0.0, 1.0),          # Normalización 0-1
    NormalizeIntensity(nonzero=True),                # Normalización de intensidad
])
# Luego: (1,H,W) → (3,H,W) por repetición de canal → (1,3,384,384)
```

### Data Augmentation aplicada
| Técnica | Parámetros | Justificación clínica |
|---------|-----------|----------------------|
| Flip horizontal | p=0.5 | Simetría anatómica |
| Flip vertical | p=0.2 | Variaciones de posición fetal |
| Color Jitter | brightness=0.3, contrast=0.3 | Variabilidad entre equipos de ultrasonido |
| Rotación | ±10° | Variación en angulación de sonda |

---

## 4. 📦 Dataset Actual {#dataset}

### Estructura de directorios
```
datasets_pathology/
├── train/                    # 2,400 imágenes
│   ├── normal/               # 160 imágenes (10.67%)
│   ├── hidrocefalia/         # 160 imágenes
│   ├── anencefalia/          # 160 imágenes
│   ├── espina_bifida/        # 160 imágenes
│   ├── labio_leporino/       # 160 imágenes
│   ├── atresia_duodenal/     # 160 imágenes
│   ├── cardiopatia_congenita/# 160 imágenes
│   ├── oligohidramnios/      # 160 imágenes
│   ├── polihidramnios/       # 160 imágenes
│   ├── restriccion_crecimiento/ # 160 imágenes
│   ├── macrosomia_fetal/     # 160 imágenes
│   ├── placenta_previa/      # 160 imágenes
│   ├── preeclampsia_signos/  # 160 imágenes
│   ├── muerte_fetal/         # 160 imágenes
│   └── embarazo_multiple/    # 160 imágenes
└── validation/               # 600 imágenes
    └── [mismas 15 clases]    # 40 imágenes por clase
```

**Total: 3,000 imágenes** · Split: 80/20 (train/val)

### Biometría sintética por clase (pseudo-real con distribución normal)
Los datos biométricos se generan con ruido gaussiano sobre valores clínicamente realistas:

| Patología | BPD (mm) | HC (mm) | AC (mm) | FL (mm) | Peso (g) |
|-----------|----------|---------|---------|---------|----------|
| Normal | 80±3 | 280±10 | 250±10 | 60±3 | 3100±150 |
| Hidrocefalia | 90±3 | 340±10 | 260±10 | 61±3 | 3000±150 |
| Anencefalia | 55±3 | 160±10 | 200±10 | 55±3 | 2100±150 |
| RCIU | 68±3 | 240±10 | 210±10 | 52±3 | 1900±150 |
| Macrosomía | 92±3 | 320±10 | 310±10 | 70±3 | 4600±150 |
| Muerte fetal | 78±3 | 270±10 | 240±10 | 58±3 | 2700±150 |

---

## 5. ⚙️ Configuración de Entrenamiento {#entrenamiento}

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| **Épocas** | 48 (2 fases) | Fase 1: 15 épocas cabezas · Fase 2: 33 épocas fine-tuning |
| **Batch size** | 16 | Optimizado para RTX 4070 (12 GB VRAM) |
| **Learning rate** | 1e-4 | AdamW con weight decay |
| **Optimizador** | AdamW (weight_decay=1e-4) | Mejor regularización que Adam |
| **Scheduler** | CosineAnnealingLR (T_max=48) | Decaimiento suave de LR |
| **Función de pérdida patologías** | BCELoss | Clasificación multi-label independiente |
| **Función de pérdida biometría** | MSELoss × 1e-5 | Escala reducida para equilibrio de gradientes |
| **Pérdida total** | `BCE + MSE × 1e-5` | Multi-task loss balanceada |
| **Clip gradientes** | norm=1.0 | Prevención de gradient explosion |
| **Hardware** | NVIDIA CUDA (RTX 4070) | Entrenamiento GPU |

---

## 6. 📊 Resultados Obtenidos {#resultados}

> Entrenamiento ejecutado: **2026-05-17** · Dispositivo: **CUDA (RTX 4070)**

| Época | Train Loss | Val Loss | Sensibilidad | AUC-ROC |
|-------|-----------|----------|-------------|---------|
| 1/48 | 18.1481 | 17.8501 | 0.0667 | **0.9263** ✅ |
| 2/48 | 17.9062 | 17.6331 | 0.4650 | **0.9646** ✅ |
| 3/48 | 17.7436 | 17.5235 | 0.7900 | **0.9958** 🏆 |

> ⚠️ El log registra solo las primeras 3 épocas completadas. El entrenamiento continúa hasta la época 48.

### Objetivos clínicos definidos en el código
```
Objetivo: Sensibilidad ≥ 0.92 AND AUC-ROC ≥ 0.90
Estado en época 3: Sensibilidad = 0.79 | AUC = 0.9958
→ AUC OBJETIVO ALCANZADO desde época 1
→ Sensibilidad en progresión positiva (0.07 → 0.47 → 0.79)
```

---

## 7. 🔍 Explicabilidad — Grad-CAM y SHAP {#xai}

### Grad-CAM (Gradient-weighted Class Activation Mapping)
- **Capa objetivo:** `backbone.conv_head` (última capa convolucional de EfficientNet-B4)
- **Implementación:** `pytorch-grad-cam` con `ClassifierOutputTarget`
- **Salida:** Mapa de calor en PNG base64 para overlay en el visor DICOM (OHIF)
- **Activación:** Automática para la patología con mayor `confidence`

```python
# Arquitectura del wrapper para Grad-CAM
class _ClassificationWrapper(nn.Module):
    def forward(self, x):
        return self.model(x)[0]  # Solo cabeza de clasificación

# Generación del heatmap
with GradCAM(model=wrapper, target_layers=[model.backbone.conv_head]) as cam:
    grayscale_cam = cam(input_tensor=tensor,
                        targets=[ClassifierOutputTarget(top_class_idx)])
# Overlay: 60% imagen original + 40% heatmap JET colormap
```

### SHAP Risk Scores (Atribución aditiva de riesgo materno)
Sistema SHAP-like que convierte probabilidades de patologías en **scores de riesgo clínico**:

| Patología → Riesgo Materno | Peso |
|---------------------------|------|
| Preeclampsia_signos → riesgo_preeclampsia | 0.80 |
| RCIU → riesgo_parto_prematuro | 0.65 |
| Placenta previa → riesgo_hemorragia | 0.75 |
| Macrosomía → riesgo_diabetes_gestacional | 0.60 |
| Muerte fetal → riesgo_mortalidad_perinatal | 1.00 |
| Cardiopatía congénita → riesgo_mortalidad_perinatal | 0.45 |
| Oligohidramnios → riesgo_parto_prematuro | 0.55 |

Fórmula: `score_riesgo = min(1.0, Σ(P(patología) × peso_riesgo))`

---

## 8. 🗄️ Dataset Requerido para Producción {#dataset-produccion}

Para que el modelo alcance rendimiento clínico real (no sintético), se necesita:

### Cantidad mínima recomendada
| Fase | Imágenes por clase | Total (15 clases) |
|------|--------------------|-------------------|
| **Piloto clínico** | 200–500 | 3,000–7,500 |
| **Validación clínica** | 1,000–2,000 | 15,000–30,000 |
| **Certificación regulatoria** | ≥ 5,000 | ≥ 75,000 |

### Distribución recomendada
- **Split:** 70% entrenamiento / 15% validación / 15% test interno
- **Clase "normal":** Mínimo el doble de cada clase patológica (compensar desbalance natural)
- **Estratificación:** Por trimestre gestacional, equipo de ultrasonido, institución

### Etiquetado requerido
- **Etiquetadores:** Médicos especialistas en medicina materno-fetal (≥ 2 por imagen)
- **Acuerdo inter-observador:** κ de Cohen ≥ 0.80 para incluir imagen
- **Metadata requerida por imagen:**
  - Edad gestacional en semanas
  - Equipo de ultrasonido (fabricante/modelo)
  - Plano de corte ecográfico
  - Biometría medida manualmente (ground truth)
  - Diagnóstico final confirmado (follow-up)

---

## 9. 🖼️ Características de las Imágenes {#imagenes}

### Requisitos mínimos
| Característica | Requerido | Óptimo |
|---------------|----------|--------|
| **Formato** | PNG, JPG, BMP | PNG (sin compresión) |
| **Resolución entrada** | Cualquiera (se resize a 384×384) | ≥ 512×512 original |
| **Canales** | Escala de grises o RGB | Escala de grises (ecografía estándar) |
| **Modalidad** | Ecografía 2D en modo B | Modo B estándar OB |
| **Profundidad de bits** | 8 bits/canal | 8–16 bits |
| **Artefactos** | Mínimos | Sin texto superpuesto de la máquina |
| **Anonimización** | **OBLIGATORIA** (HIPAA/RGPD) | DICOM de-id antes de exportar |

### Planos ecográficos recomendados por patología
| Patología | Plano principal | Plano secundario |
|-----------|----------------|-----------------|
| Hidrocefalia | Axial transtalasmico | Coronal |
| Anencefalia | Sagital craneal | Coronal craneal |
| Espina bífida | Sagital columna | Axial columna |
| Cardiopatía | 4 cámaras cardíacas | Salida ventricular |
| Placenta previa | Sagital segmento uterino | Transvaginal |
| RCIU | Abdominal AC | Doppler umbilical |
| Oligohidramnios | Cuadrantes de líquido | Bolsillo mayor |

### Normalización aplicada
```
Preprocesamiento MONAI (inferencia):
  1. Escala de grises → RGB (repetición de canal)
  2. Resize → 384×384
  3. ScaleIntensity: [0, 255] → [0.0, 1.0]
  4. NormalizeIntensity(nonzero=True)

Preprocesamiento torchvision (entrenamiento):
  1. Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
  → Estadísticas ImageNet para compatibilidad con Transfer Learning
```

---

## 10. 🌐 Fuentes Públicas de Datos Médicos {#fuentes}

### Datasets de Ecografía Fetal (acceso abierto)

| Dataset | Patologías | Imágenes | Acceso | Licencia |
|---------|-----------|---------|--------|---------|
| **HC18 Challenge** | Circunferencia cefálica | 1,334 | [grand-challenge.org](https://grand-challenge.org/challenges/hc18/) | Research |
| **FETAL_PLANES_DB** | Planos estándar fetales | 12,400 | [Zenodo](https://zenodo.org/record/3904280) | CC BY 4.0 |
| **US-Enhanced OB** | Biometría fetal | 2,000+ | [Kaggle](https://www.kaggle.com) | Varies |
| **OpenFetal** | Anotaciones fetales | 1,000 | GitHub | MIT |
| **PhysioNet** | Señales obstétricas | Múltiple | [physionet.org](https://physionet.org) | CC |

### Repositorios de Imágenes Médicas Generales

| Recurso | Tipo | URL | Notas |
|---------|------|-----|-------|
| **The Cancer Imaging Archive (TCIA)** | DICOM multi-modalidad | [cancerimagingarchive.net](https://www.cancerimagingarchive.net) | Incluye OB/GYN |
| **Kaggle Medical Datasets** | Diverso | [kaggle.com/datasets](https://www.kaggle.com/datasets) | Buscar "fetal ultrasound" |
| **Grand Challenge** | Competencias segmentación | [grand-challenge.org](https://grand-challenge.org) | HC18, BPD, FL challenges |
| **Radiopaedia** | Casos clínicos | [radiopaedia.org](https://radiopaedia.org) | Ecografías con diagnóstico |
| **MedPix (NLM)** | Atlas médico | [medpix.nlm.nih.gov](https://medpix.nlm.nih.gov) | Acceso libre |
| **MIMIC-III Imaging** | US hospitalario | PhysioNet | Requiere credenciales |

### Datasets específicos de patologías fetales

| Dataset | Patología específica | Link |
|---------|---------------------|------|
| **CRL Measurement** | Longitud coronilla-rabadilla | Grand Challenge |
| **Fetal Head US** | Biometría cefálica | HC18 Challenge |
| **POCUS Atlas** | Ultrasonido point-of-care | pocus.org |
| **EchoNet-Pediatric** | Cardiopatías congénitas | echonet.stanford.edu |
| **OB/GYN Ultrasound DB** | Múltiples patologías OB | RSNA datasets |

### Datos sintéticos y simulados

| Herramienta | Uso | URL |
|-------------|-----|-----|
| **SynthSeg (FreeSurfer)** | Generación de imágenes sintéticas | GitHub |
| **GAN-based Augmentation** | Aumentar clases minoritarias | Papers with Code |
| **NVIDIA MONAI Label** | Semi-supervisado + anotación | monai.io |

---

## 11. 🔗 Integración en el Sistema {#integracion}

### Flujo completo de análisis

```
Imagen DICOM (OHIF Viewer)
         │
         ▼ (exportar frame PNG)
FastAPI /api/analyze (Puerto 8001)
         │
         ├── ModelManager.analyze(image_np)
         │         │
         │    ┌────▼────────────────────┐
         │    │  EfficientNetB4CNN      │
         │    │  ├── Classification Head│ → 15 probabilidades
         │    │  └── Biometry Head      │ → BPD, HC, AC, FL, peso
         │    └─────────────────────────┘
         │         │
         ├── compute_gradcam() → PNG base64 → OHIF overlay
         ├── compute_shap_risk_scores() → Scores de riesgo materno
         │
         ▼
     Django Backend
     (auditoria/signals.py → registro en BD)
         │
         ▼
     Frontend React
     (IaMedica.tsx / VisorDICOM.tsx)
```

### Endpoint de inferencia
```http
POST /api/analyze
Content-Type: multipart/form-data

{
  "image": <archivo PNG/JPG>,
  "compute_gradcam": true
}

Response:
{
  "pathology_detection": {
    "pathologies": [{"pathology": "oligohidramnios", "confidence": 0.82, ...}],
    "total_detected": 1,
    "requires_specialist": true
  },
  "biometry": {"BPD_mm": 75.3, "HC_mm": 262.1, ...},
  "shap_risk_scores": {"riesgo_preeclampsia": 0.08, "riesgo_parto_prematuro": 0.45},
  "gradcam_base64": "<PNG base64>",
  "score_global": 0.82
}
```

### Seguridad (mTLS + Kong)
- Comunicación entre microservicios con certificados mutuos (mTLS)
- Autenticación JWT con RBAC (solo médicos y admin pueden acceder al endpoint de IA)
- Todos los resultados quedan auditados en `auditoria_registros` de PostgreSQL

---

## 12. 📏 Métricas de Evaluación Clínica {#metricas}

### Métricas implementadas
```python
# Sensibilidad macro (recall ponderado por clase)
sensibilidad = mean(TP / (TP + FN))  # por clase, luego promedio

# AUC-ROC macro
auc = roc_auc_score(targets, probs, average="macro")
```

### Objetivos clínicos del proyecto
| Métrica | Objetivo mínimo | Estado (Época 3) |
|---------|----------------|-----------------|
| **AUC-ROC macro** | ≥ 0.90 | ✅ **0.9958** |
| **Sensibilidad** | ≥ 0.92 | 🔄 0.79 (en progreso) |
| **Especificidad** | ≥ 0.85 | Pendiente evaluación |
| **F1-Score macro** | ≥ 0.88 | Pendiente evaluación |

### Métricas adicionales recomendadas para certificación
| Métrica | Importancia clínica |
|---------|---------------------|
| **VPN (Valor Predictivo Negativo)** | Crítico: no falsos negativos en patologías graves |
| **Sensibilidad por clase** | Anencefalia y muerte fetal deben tener > 0.95 |
| **Calibración (ECE/MCE)** | Las probabilidades deben ser probabilidades reales |
| **AUC por patología** | Individual por cada una de las 15 clases |
| **Acuerdo con especialista** | κ de Cohen vs. diagnóstico de médico senior |

---

## 🛠️ Stack Tecnológico Completo

```
Lenguaje:     Python 3.11
Framework DL: PyTorch 2.2 + CUDA (RTX 4070)
Backbone:     timm (EfficientNet-B4)
Preprocessing:MONAI (transforms médicas)
Grad-CAM:     pytorch-grad-cam
Inferencia:   FastAPI (async, mTLS)
Orquestación: Docker + Kong API Gateway
Viewer DICOM: OHIF + Orthanc
BD:           PostgreSQL (multi-tenant)
Auditoría:    Django signals + middleware
```

---

## 📁 Estructura de Archivos del Microservicio

```
Microservicio_IA/
├── app/
│   ├── models.py           # EfficientNetB4CNN + ModelManager + SHAP + Grad-CAM
│   ├── config.py           # MODEL_PATHS y configuración
│   └── routes.py           # FastAPI endpoints
├── datasets_pathology/
│   ├── train/              # 2,400 imágenes (15 clases × 160)
│   └── validation/         # 600 imágenes (15 clases × 40)
├── trained_models/
│   └── efficientnet_b4.pth # Mejor modelo (guardado por AUC-ROC)
├── train_pytorch_cnn.py    # Script de entrenamiento completo
├── data_pipeline.py        # Pipeline de preparación de datos
├── model_registry.py       # Versionado de modelos
├── training_complete.log   # Log de entrenamiento
└── requirements.txt        # Dependencias Python
```

---

## ⚠️ Advertencias Clínicas

> **IMPORTANTE:** Este sistema es una herramienta de **apoyo diagnóstico**, no un sustituto del criterio médico especializado.

- Los resultados deben ser **validados por un médico** antes de cualquier decisión clínica
- El modelo está en fase de **investigación/desarrollo** — No certificado para uso clínico independiente
- Las biometrías estimadas son **aproximaciones** — Las medidas oficiales deben realizarse manualmente
- El dataset de entrenamiento actual es **parcialmente sintético** — El rendimiento con datos reales debe evaluarse
- Ante `confidence ≥ 0.70`, el sistema recomienda derivación automática a especialista

---

*Documentación generada automáticamente desde el código fuente del proyecto*  
*Última actualización: 2026-05-17 | Versión del modelo: efficientnet_b4_v1.0*
