# 🧠 Microservicio de IA — Fetal Medical

Microservicio **FastAPI** para análisis automático de ecografías fetales mediante
Deep Learning. Expone un modelo híbrido **EfficientNet-B4 (PyTorch)** entrenado
para detección multi-etiqueta de patologías obstétricas.

> ⚠️ **Uso clínico:** las salidas son de apoyo diagnóstico, no sustituyen el
> juicio médico. Ver [ESTADO_RED_NEURONAL.md](ESTADO_RED_NEURONAL.md) para el
> rendimiento medido por clase y las limitaciones conocidas.

---

## 🏗️ Arquitectura real

Un único modelo híbrido (`HybridEfficientNetB4` en [app/models.py](app/models.py)):

- **Frontend de denoising** convolucional (3→64→64→3).
- **Backbone EfficientNet-B4** (`timm`, `num_classes=0`, pooling promedio).
- **Pooling por atención Transformer** (1 capa, `d_model=256`, 4 cabezas).
- **Dos cabezas de salida**:
  - **Clasificación multi-etiqueta**: 16 salidas (14 patologías + `normal` + `no_ecografia`).
  - **Biometría** (BPD/HC/AC/FL/peso estimado) — ver advertencia abajo.

Checkpoint: `trained_models/efficientnet_b4_renamed.pth` (PyTorch `state_dict`).
Entrada: imágenes redimensionadas a **384×384**, normalizadas `/255.0`.

### Clases detectadas (orden del checkpoint)

`hidrocefalia`, `anencefalia`, `espina_bifida`, `labio_leporino`,
`atresia_duodenal`, `cardiopatia_congenita`, `oligohidramnios`, `polihidramnios`,
`restriccion_crecimiento`, `macrosomia_fetal`, `placenta_previa`,
`preeclampsia_signos`, `muerte_fetal`, `embarazo_multiple`, `normal`,
`no_ecografia`.

Los umbrales de decisión por clase están recalibrados empíricamente contra un
set de validación real (curva ROC + estadístico de Youden con margen de
seguridad). Ver `CLASS_THRESHOLDS` en [app/config.py](app/config.py).

---

## 📦 Instalación

```bash
cd Microservicio_IA
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

Dependencias clave: `torch`, `timm`, `monai`, `pytorch-grad-cam`, `opencv-python`,
`pydicom`, `fastapi`, `uvicorn`.

---

## 🏃 Ejecutar

La aplicación FastAPI vive en `app/main.py` (objeto `app`). Se lanza con Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Con mTLS (producción): ver [start_mtls.sh](start_mtls.sh).

Servicio disponible en **http://localhost:8001** · Swagger en **/docs**.

El modelo se carga en el evento `lifespan` de startup vía `ModelManager`.

---

## 📚 Endpoints REST (`app/routes.py`, prefijo `/api`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/analyze` | Análisis completo con EfficientNet-B4 (clasificación + biometría). |
| POST | `/api/detect-pathologies` | Detección de patologías fetales + biometría. |
| POST | `/api/detect-anomalies` | Detección de anomalías fetales. |
| POST | `/api/classify` | Clasificación de tipo de ecografía (endpoint legado). |
| POST | `/api/quality-check` | Evaluación de calidad de imagen médica. |
| POST | `/api/consultar` | Chatbot médico obstétrico. |
| GET  | `/health` | Estado del servicio, modelo cargado y device. |

Ejemplo:

```bash
curl -X POST "http://localhost:8001/api/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@ecografia.jpg"
```

---

## 🔗 Integración con Django

El flujo productivo **no** es una llamada HTTP directa desde la vista. Es:

```
Vista Django → tarea Celery → cnn_service (HTTP con circuit breaker + mTLS)
             → este microservicio FastAPI → callback/persistencia
```

Ver `ecografias/` (tareas Celery y `cnn_service`) en el backend Django.

---

## ⚠️ Limitaciones conocidas (honestidad clínica)

- **Biometría sintética no validada**: el `biometry_head` (BPD/HC/AC/FL/peso) se
  entrenó con objetivos **sintéticos** por categoría clínica, no con mediciones
  reales anotadas (`BIOMETRY_METHOD = "estimacion_sintetica_no_validada"` en
  [app/config.py](app/config.py)). Es orientativo; **nunca** debe tratarse como
  una medición validada.
- **`no_ecografia`**: el rechazo de imágenes no médicas se apoya sobre todo en
  heurística de saturación de color (pocas imágenes de entrenamiento reales para
  esa clase).
- **Clases más débiles**: `cardiopatia_congenita` y `polihidramnios` tienen el
  peor rendimiento medido. Ver [ESTADO_RED_NEURONAL.md](ESTADO_RED_NEURONAL.md).
- **Autenticación**: el acceso se protege por **mTLS** (ver `start_mtls.sh`) y
  la restricción de IP interna del gateway Kong. No hay JWT propio del
  microservicio.

---

## 🛠️ Tecnologías

- **FastAPI** + **Uvicorn** — servidor ASGI.
- **PyTorch** + **timm (EfficientNet-B4)** — modelo.
- **MONAI** — transforms médicas.
- **pytorch-grad-cam** — mapas de calor (Grad-CAM) para explicabilidad.
- **OpenCV** — procesamiento de imágenes.
- **PyDICOM** — lectura de imágenes DICOM.

---

## 📄 Licencia

Parte del sistema **Fetal Medical** — Historia Clínica Obstétrica.
