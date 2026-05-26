# 🧠 Microservicio de IA - Fetal Medical

Microservicio de **Inteligencia Artificial** para análisis automático de ecografías fetales usando Deep Learning.

## 🚀 Características

- ✅ **3 Modelos de IA** (CNN Classifier, U-Net Segmenter, ResNet Anomaly Detector)
- ✅ **5 Endpoints REST** con FastAPI
- ✅ **Soporte DICOM** para imágenes médicas
- ✅ **Procesamiento avanzado** de imágenes (CLAHE, denoising)
- ✅ **Detección de 7 anomalías** fetales
- ✅ **Recomendaciones médicas** automáticas
- ✅ **Documentación interactiva** con Swagger

## 📦 Instalación

### 1. Crear entorno virtual

```bash
cd Microservicio_IA
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 🏃 Ejecutar el Microservicio

```bash
python main.py
```

El servicio estará disponible en: **http://localhost:8001**

## 📚 API Endpoints

### 1. **Análisis Completo** - `/api/analyze`
Realiza análisis completo de la ecografía (clasificación + segmentación + anomalías).

**Ejemplo:**
```bash
curl -X POST "http://localhost:8001/api/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@ecografia.jpg"
```

### 2. **Clasificación** - `/api/classify`
Clasifica el tipo de ecografía.

### 3. **Segmentación** - `/api/segment`
Segmenta el feto en la imagen.

### 4. **Detección de Anomalías** - `/api/detect-anomalies`
Detecta anomalías fetales.

### 5. **Calidad de Imagen** - `/api/quality-check`
Evalúa la calidad de la imagen médica.

## 🧪 Documentación Interactiva

Visita: **http://localhost:8001/docs**

## 🤖 Modelos de IA

### 1. CNN Classifier
- **Arquitectura:** Custom CNN (4 bloques convolucionales)
- **Input:** 224x224x3
- **Clases:** 5 tipos de ecografía
- **Confianza mínima:** 60%

### 2. U-Net Segmenter
- **Arquitectura:** U-Net (encoder-decoder)
- **Input:** 256x256x1 (escala de grises)
- **Output:** Máscara binaria
- **Métrica:** Coeficiente Dice

### 3. ResNet Anomaly Detector
- **Arquitectura:** ResNet50 + Transfer Learning
- **Input:** 224x224x3
- **Detecciones:** 7 anomalías fetales
- **Confianza mínima:** 30%

## 🔬 Anomalías Detectadas

1. ✅ Normal
2. 🧠 Hidrocefalia
3. ⚠️ Anencefalia
4. 🦴 Espina bífida
5. 👄 Labio leporino
6. 🫁 Atresia duodenal
7. ❤️ Cardiopatía congénita

## 🎯 Entrenamiento de Modelos

### Preparar Dataset

```python
datasets/
├── train/
│   ├── ecografia_2d/
│   ├── ecografia_3d/
│   └── ...
├── validation/
└── test/
```

### Entrenar Clasificador

```python
from app.models import UltrasoundClassifier

classifier = UltrasoundClassifier()
history = classifier.train(
    train_dir='datasets/train',
    validation_dir='datasets/validation',
    epochs=50
)
classifier.save('trained_models/classifier_v1.h5')
```

## 🔗 Integración con Django

```python
# Backend Django - ecografias/views.py
import requests

@api_view(['POST'])
def analyze_with_ai(request):
    file = request.FILES['image']
    
    # Enviar al microservicio
    response = requests.post(
        'http://localhost:8001/api/analyze',
        files={'file': file}
    )
    
    return Response(response.json())
```

## 📊 Ejemplo de Respuesta

```json
{
  "status": "success",
  "filename": "ecografia_paciente.jpg",
  "image_quality": {
    "quality": "buena",
    "sharpness": 125.5,
    "contrast": 55.2,
    "brightness": 128.3
  },
  "classification": {
    "predicted_class": "ecografia_2d",
    "confidence": 0.95,
    "is_confident": true
  },
  "segmentation": {
    "fetal_area_pixels": 15420,
    "coverage_percentage": 23.5,
    "success": true
  },
  "anomaly_detection": {
    "status": "anomalies_detected",
    "total_detected": 1,
    "requires_specialist": false,
    "anomalies": [
      {
        "anomaly": "hidrocefalia",
        "confidence": 0.65,
        "severity": "media",
        "recommendation": "Realizar resonancia magnética. Consulta con neurocirujano pediátrico."
      }
    ]
  },
  "recommendations": {
    "priority": "normal",
    "actions": [],
    "next_steps": [...]
  }
}
```

## 🛠️ Tecnologías

- **FastAPI** - Framework web moderno
- **TensorFlow/Keras** - Deep Learning
- **OpenCV** - Procesamiento de imágenes
- **PyDICOM** - Imágenes médicas DICOM
- **NumPy** - Operaciones numéricas

## 📝 Notas Importantes

⚠️ **Los modelos NO están entrenados** - Este código proporciona la arquitectura completa, pero los modelos necesitan ser entrenados con datos reales de ecografías antes de usarse en producción.

✅ **Datasets recomendados:**
- FETAL_PLANES_DB
- Kaggle Fetal Head Dataset
- Grand Challenge Medical Imaging

## 🔐 Seguridad

- ✅ Validación de extensiones de archivo
- ✅ Límite de tamaño de archivo (10 MB)
- ✅ CORS configurado
- ⚠️ Implementar autenticación JWT para producción

## 📄 Licencia

Parte del sistema **Fetal Medical** - Historia Clínica Obstétrica

---

**Desarrollado con ❤️ usando FastAPI + TensorFlow**
