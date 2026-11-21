# redes-neuronales

Entrenamiento y evaluación de las redes que usa `../servicio-ia`, y de los modelos tabulares del backend.
Cada carpeta deja sus métricas medidas en datos que la red no vio (`salidas/*/metricas.json`), que son las cifras que
muestra la Guía de IA del sistema.

| Carpeta | Qué entrena | Destino de los pesos |
|---|---|---|
| `entrenamiento/redes_ecografia_real/` | Plano anatómico fetal y circunferencia cefálica (cuaderno) | `../modelos-ia/redes/` |
| `entrenamiento/segmentacion/` | U-Net de cabeza, tórax, abdomen, intraparto, ovario y mioma | `../modelos-ia/redes/` |
| `entrenamiento/biometria/` | Longitud del fémur y circunferencia abdominal (puntos) | `../modelos-ia/redes/` (`exportar.py`) |
| `entrenamiento/patologias_cerebrales/` | Cribado de anomalías cerebrales | `../modelos-ia/redes/` (`exportar.py`) |
| `entrenamiento/ginecologia/` | Clasificación de ovario y ovario poliquístico | `../modelos-ia/redes/` (`exportar.py`) |
| `entrenamiento/intraparto/` | Ángulo de progresión | evaluación de la U-Net intraparto |
| `entrenamiento/senales/`, `entrenamiento/translucencia/` | Modelos evaluados y descartados (sin señal suficiente) | no se publican |
| `entrenamiento/b4_retirada/` | Red B4 retirada del servicio y la evidencia de por qué | no se publica |
| `entrenamiento/peso_nacimiento/` | Cuaderno y muestra del modelo tabular de peso al nacer | `../modelos-ia/tabulares/` (con `manage.py entrenar_modelo_peso`) |

`datos/` guarda los conjuntos públicos descargados (decenas de GB, fuera de Git); `datos/CATALOGO.md` dice de dónde
sale cada uno y con qué licencia, y `datos/tabulares/` los datos para los modelos tabulares.

Los scripts que reutilizan la arquitectura del servicio (`app.unet`) agregan `../servicio-ia` a la ruta de Python;
se ejecutan desde su propia carpeta con el Python que tiene PyTorch:

```powershell
cd entrenamiento\segmentacion
python preparar.py
python entrenar.py cabeza
```

Dependencias: `requirements.txt`.
