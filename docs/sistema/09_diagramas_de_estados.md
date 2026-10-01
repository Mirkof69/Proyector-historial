# 09 · Diagramas de estados y de actividad

## Embarazo

```mermaid
stateDiagram-v2
    [*] --> activo: registrar (FUM)
    activo --> activo: controles, ecografías,<br/>laboratorio, vacunas
    activo --> finalizado: registrar parto
    activo --> perdida: aborto / pérdida
    finalizado --> [*]
    perdida --> [*]
    note right of activo
        Solo uno activo por paciente.
        La EG se cuenta hasta hoy;
        terminado, se muestra la del parto.
    end note
```

## Cita

```mermaid
stateDiagram-v2
    [*] --> agendada
    agendada --> confirmada
    agendada --> cancelada
    confirmada --> en_espera: llega la paciente
    confirmada --> no_asistio
    confirmada --> cancelada
    en_espera --> en_consulta
    en_consulta --> completada
    completada --> [*]
    cancelada --> [*]
    no_asistio --> [*]
    note right of confirmada
        Recordatorio al médico
        24 h antes (hora de Bolivia)
    end note
```

## Examen de laboratorio

```mermaid
stateDiagram-v2
    [*] --> solicitado
    solicitado --> en_proceso: toma de muestra
    en_proceso --> completado: carga de resultados<br/>(a mano o Excel)
    solicitado --> cancelado
    en_proceso --> cancelado
    completado --> [*]
    cancelado --> [*]
    note right of completado
        Cada resultado se evalúa contra su rango:
        normal, anormal o crítico.
        Al pasar a completado se avisa al médico
        (una vez, con los críticos destacados).
    end note
```

## Triaje

```mermaid
stateDiagram-v2
    [*] --> pendiente: enfermería registra<br/>signos y prioridad
    pendiente --> completado: el médico atiende
    pendiente --> cancelado
    completado --> [*]
    cancelado --> [*]
```

## Actividad: atención prenatal

```mermaid
flowchart TD
    A([Llega la paciente]) --> B{¿Está registrada?}
    B -- No --> C[Registrar con consentimiento]
    B -- Sí --> D[Buscar por nombre o CI]
    C --> E[Triaje: signos vitales y prioridad]
    D --> E
    E --> F{¿Tiene embarazo activo?}
    F -- No --> G[Registrar embarazo: FUM, gesta, riesgo]
    F -- Sí --> H[Control prenatal]
    G --> H
    H --> I{¿Alertas? PA, FCF,<br/>edema, proteinuria}
    I -- Sí --> J[Alerta al médico y conducta]
    I -- No --> K{¿Toca ecografía?}
    J --> K
    K -- Sí --> L[Ecografía: biometría, imagen, IA]
    K -- No --> M{¿Toca laboratorio?}
    L --> M
    M -- Sí --> N[Solicitar examen; cargar resultados]
    M -- No --> O[Nota de evolución y próxima cita]
    N --> O
    O --> P{¿Fin de la gestación?}
    P -- No --> A
    P -- Sí --> Q[Registrar parto y recién nacidos]
    Q --> R([Embarazo finalizado])
```

## Actividad: decisión de la red de anomalías cerebrales

```mermaid
flowchart TD
    A([Imagen recibida]) --> B[Red de planos]
    B --> C{¿Plano más probable<br/>= cerebro fetal?}
    C -- Sí --> E[Red de anomalías]
    C -- No --> D{¿P cerebro ≥ 0,02?}
    D -- No --> X([No aplicable:<br/>no se clasifica])
    D -- Sí --> E2[Red de anomalías]
    E --> F{P anomalía ≥ 0,5?}
    E2 --> G{P anomalía ≥ 0,5?}
    F -- No --> N([Sin alarma<br/>«no descarta una anomalía»])
    F -- Sí --> S([Alarma + familia sospechada])
    G -- No --> X
    G -- Sí --> S2([Alarma con aviso:<br/>«revise si es una cabeza»])
```
