# Datasets — Fetal Medical AI CNN
**Proyecto:** EfficientNet-B4 · 15 patologias + biometria fetal  
**Ultima actualizacion:** 2026-05-17

---

## DESCARGA DIRECTA SIN REGISTRO (Zenodo — CC BY 4.0)

Usar el script automatico:
```powershell
cd "C:\Users\Artemis\Desktop\atermis laptop\historial\Backend\Microservicio_IA"

# Un solo dataset
python scripts/download_datasets.py --source cardiac

# Todos los datasets Zenodo
python scripts/download_datasets.py --source all
```

| Dataset | Imagenes | Clase del modelo | Zenodo |
|---------|----------|-----------------|--------|
| FETAL_PLANES_DB | 12,400 | normal, hidrocefalia, preeclampsia_signos | 3904280 |
| HC18 Head Circumference | 1,334 | normal, hidrocefalia | 1327317 |
| Fetal Head Biometry 2023 | 3,832 | hidrocefalia, normal | 8265464 |
| FOCUS Cardiac 4-Chamber | 300 | cardiopatia_congenita | 14597550 |

**URLs directas de descarga:**
```
https://zenodo.org/records/3904280/files/FETAL_PLANES_ZENODO.zip
https://zenodo.org/records/1327317/files/training_set.zip
https://zenodo.org/records/1327317/files/test_set.zip
https://zenodo.org/records/14597550/files/FOCUS-dataset.zip
```

---

## DESCARGA CON REGISTRO GRATUITO — Kaggle

**Paso 1:** Crear cuenta en https://www.kaggle.com (gratis)  
**Paso 2:** Ir a https://www.kaggle.com/settings → API → Create New Token  
**Paso 3:** Guardar kaggle.json en C:\Users\Artemis\.kaggle\  
**Paso 4:** Instalar cliente: `pip install kaggle`

```powershell
# Instalar cliente Kaggle
pip install kaggle

# Descargar datasets
kaggle datasets download -d andrewmvd/fetal-health-classification -p datasets/_tmp_download/kaggle/
kaggle datasets download -d ankit8467/fetal-head-ultrasound-dataset-for-image-segment -p datasets/_tmp_download/kaggle/
kaggle datasets download -d vishwaskant786/2d-fetal-altrasound-images -p datasets/_tmp_download/kaggle/
```

| Dataset Kaggle | Patologias | Clase del modelo |
|---------------|-----------|-----------------|
| Fetal Health Classification (CTG) | Bienestar fetal general | normal / muerte_fetal |
| Fetal Head Segmentation | HC, BPD, hidrocefalia | hidrocefalia |
| 2D Fetal Ultrasound Images | Planos estandar | normal |

---

## DESCARGA MANUAL — Radiopaedia (cuenta gratuita)

Para las clases sin dataset automatico, descargar casos clinicos reales:

| Clase del modelo | URL de busqueda |
|-----------------|-----------------|
| labio_leporino | https://radiopaedia.org/search?q=cleft+lip+fetal&scope=cases |
| placenta_previa | https://radiopaedia.org/search?q=placenta+previa+ultrasound&scope=cases |
| oligohidramnios | https://radiopaedia.org/search?q=oligohydramnios+ultrasound&scope=cases |
| polihidramnios | https://radiopaedia.org/search?q=polyhydramnios+ultrasound&scope=cases |
| atresia_duodenal | https://radiopaedia.org/search?q=duodenal+atresia+ultrasound&scope=cases |
| espina_bifida | https://radiopaedia.org/search?q=spina+bifida+ultrasound&scope=cases |
| anencefalia | https://radiopaedia.org/search?q=anencephaly+ultrasound&scope=cases |
| embarazo_multiple | https://radiopaedia.org/search?q=twin+pregnancy+ultrasound&scope=cases |

**Como descargar:**
1. Ir a la URL de busqueda
2. Click en el caso clinico
3. Click en la imagen → boton de descarga (PNG/DICOM)
4. Guardar en: datasets_pathology/train/[nombre_clase]/

---

## SIN DATASET PUBLICO DISPONIBLE

| Clase | Razon | Estado |
|-------|-------|--------|
| muerte_fetal | Restricciones eticas globales — ningun repositorio publico | VACIO |
| restriccion_crecimiento | Requiere Doppler serie temporal + biometria longitudinal | VACIO |
| macrosomia_fetal | Solo detectable por biometria, no imagen morfologica aislada | VACIO |

---

## ESTADO ACTUAL DEL DATASET (post-descarga)

```
datasets_pathology/
  train/
    normal/              16,822 imgs  (FETAL_PLANES_DB + HC18)
    hidrocefalia/         2,631 imgs  (FETAL_PLANES_DB cerebro + HC18)
    preeclampsia_signos/  1,301 imgs  (cervix materno FETAL_PLANES_DB)
    cardiopatia_congenita/    0 imgs  (FOCUS pendiente descarga)
    [11 clases restantes]/    0 imgs  (sin dataset publico)
  validation/
    normal/               4,232 imgs
    hidrocefalia/           658 imgs
    preeclampsia_signos/    325 imgs

TOTAL REAL: 20,754 train + 5,215 val
```

---

## TOTAL ESTIMADO AL COMPLETAR TODAS LAS FUENTES

| Fuente | Imagenes | Estado |
|--------|---------|--------|
| FETAL_PLANES_DB | 12,400 | Descargado |
| HC18 | 1,334 | Descargado |
| FOCUS Cardiac | 300 | Pendiente |
| Kaggle (3 datasets) | ~3,000 | Requiere registro |
| Radiopaedia (manual) | ~200-400 | Manual |
| **TOTAL ESTIMADO** | **~17,000+** | |

Con estas fuentes se cubren **4 de 15 patologias** con datos reales abundantes.
Las 11 restantes requieren convenio con hospital o institucion medica.

---

*Documentacion generada: 2026-05-17 | Proyecto: Fetal Medical AI v1.0*
