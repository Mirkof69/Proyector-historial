# 10 · Inteligencia artificial

Principio: **la IA apoya, no diagnostica**. Cada resultado viaja con las
métricas medidas en datos que el modelo no vio al entrenar, y si no hay
modelo el sistema lo dice en lugar de inventar un número.

## Componentes

```mermaid
flowchart LR
    subgraph Backend[Backend Django · ia_medica]
        PUENTE[Puente HTTP<br/>ecografias/ai_views.py]
        SUP[Modelo supervisado<br/>peso al nacer<br/>ia_medica/ml/]
    end
    subgraph MS[Microservicio FastAPI · :8001]
        PL[Plano anatómico<br/>EfficientNet-B0]
        HC[Circunferencia cefálica<br/>regresión]
        AN[Anomalías cerebrales<br/>EfficientNet-B0]
        B4[EfficientNet-B4<br/>experimental]
    end
    D1[(FETAL_PLANES_DB<br/>12.400 imágenes)]
    D2[(HC18<br/>999 + 335)]
    D3[(Fetal Brain Abnormalities<br/>212 originales)]
    D4[(Partos simulados<br/>del sistema)]

    PUENTE --> PL & HC & AN & B4
    D1 -. entrena .-> PL
    D2 -. entrena .-> HC
    D3 -. entrena .-> AN
    D1 -. normales .-> AN
    D4 -. entrena .-> SUP
```

## Modelos y métricas medidas

| Modelo | Tarea | Datos | Métrica en datos no vistos | Estado |
|---|---|---|---|---|
| Plano anatómico | 6 clases (abdomen, cerebro, fémur, tórax, cérvix, otro) | FETAL_PLANES_DB (Zenodo 3904280) | 92,7 % de exactitud en 5.271 imágenes de 896 madres; 93,1 % de cabezas de otro hospital | En uso |
| Circunferencia cefálica | Regresión (mm) + EG por Hadlock 1984 | HC18 (Zenodo 1327317) | R² 0,978; error medio 7,0 mm en 146 imágenes de 117 madres | En uso |
| Anomalías cerebrales | Normal + 4 familias | Fetal Brain Abnormalities + normales de FETAL_PLANES | Falsas alarmas: 0,2 % en 999 cabezas de otro hospital; 0,4 % en 3.199 imágenes que no son cabezas. **Sensibilidad real no medible** con datos públicos | Cribado de apoyo |
| Peso al nacer (supervisado) | Regresión (g) + clase | Partos simulados del sistema (513) | Ridge: error medio 183 g frente a 297 g de Hadlock; R² 0,836 | Demostración: hay que reentrenarlo con partos reales |
| EfficientNet-B4 | 14 patologías | Datasets con etiquetas no verificables | Sin métrica válida | Experimental, marcada en pantalla |

Detalles y límites: `Backend/Microservicio_IA/entrenamiento/patologias_cerebrales/INFORME.md`,
`Backend/Microservicio_IA/entrenamiento/redes_ecografia_real/LEEME.md` y
`Backend/Microservicio_IA/datos/CATALOGO.md`.

## Entrenamiento honesto

```mermaid
flowchart LR
    A[Datos reales con<br/>etiqueta verificable] --> B[Partición por paciente<br/>o imagen original<br/>sin fugas]
    B --> C[Entrenar<br/>época elegida con validación interna]
    C --> D[Medir en datos no vistos<br/>+ otro hospital<br/>+ prueba de estilo]
    D --> E{¿Hay atajos?<br/>fuente, duplicados, estilo}
    E -- Sí --> F[Corregir y volver a entrenar]
    F --> C
    E -- No --> G[Exportar con métricas<br/>dentro del modelo]
    G --> H[Test: la API reproduce<br/>lo medido al entrenar]
```

## Modelo supervisado de peso al nacer

- Variables: biometría de la ecografía (DBP, CC, CA, LF), semanas en la
  ecografía y semana objetivo del parto, datos maternos y antecedentes.
- Se comparan Hadlock proyectado, Ridge, Random Forest y Gradient Boosting con
  partición por paciente; se guarda el que mejora significativamente a Hadlock.
- Se niega a predecir en embarazos múltiples, ecografías de menos de 20
  semanas o si las variables del modelo no coinciden con las actuales.
- Comandos: `construir_dataset_peso`, `entrenar_modelo_peso`.
