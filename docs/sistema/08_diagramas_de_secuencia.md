# 08 · Diagramas de secuencia

## Inicio de sesión y llamadas autenticadas

El token JWT viaja en una cookie `httpOnly` (el JavaScript no lo puede leer) y
las escrituras llevan el token CSRF. Cada sesión tiene un identificador `sid`
que agrupa sus registros de auditoría.

```mermaid
sequenceDiagram
    actor U as Usuario
    participant F as Frontend
    participant B as Backend (Django)
    participant DB as PostgreSQL
    participant A as Auditoría

    U->>F: correo y contraseña
    F->>B: POST /api/usuarios/login/
    B->>DB: verifica credenciales (límite de intentos fallidos)
    B->>A: LOGIN (sid, IP, navegador)
    B-->>F: 200 + cookies access/refresh (httpOnly) + csrftoken
    F->>B: GET /api/pacientes/?page=1 (cookie)
    B-->>F: página de datos según el rol
    Note over F,B: Al vencer el access token
    F->>B: POST /api/token/refresh/ (cookie refresh)
    B-->>F: nuevo access token (mismo sid)
    U->>F: cerrar sesión
    F->>B: POST /api/usuarios/logout/
    B->>A: LOGOUT (mismo sid) y token a la lista negra
```

## Atención de una gestante (flujo principal)

```mermaid
sequenceDiagram
    actor R as Recepción
    actor M as Médico/a
    participant F as Frontend
    participant B as Backend
    participant N as Notificaciones

    R->>F: registra paciente + consentimiento
    F->>B: POST /api/pacientes/
    B-->>F: 201 (ID clínico)
    F-->>R: ¿registrar ahora su embarazo?
    M->>F: nuevo embarazo (FUM)
    F->>B: POST /api/embarazos/
    B->>B: FPP, gesta = P + A + 1, un solo activo
    B->>N: alerta si es de alto riesgo
    M->>F: control prenatal
    F->>B: POST /api/controles/
    B->>B: EG, IMC, alertas (PA, FCF, edema, proteinuria)
    M->>F: ecografía + imagen
    F->>B: POST /api/ecografias/ y subida de imagen
    B->>B: peso fetal (Hadlock), datación
    M->>F: parto con recién nacidos
    F->>B: POST /api/partos/ (transacción)
    B->>B: valida cada recién nacido, embarazo → finalizado
```

## Análisis de una ecografía con las redes medidas

```mermaid
sequenceDiagram
    actor M as Médico/a
    participant F as Frontend
    participant B as Backend
    participant IA as Microservicio de IA
    participant P as Red de planos
    participant C as Red de cabeza (HC18)
    participant X as Red de anomalías

    M->>F: «Analizar» en la pestaña IA medida
    F->>F: descarga la imagen protegida con la cookie
    par
        F->>B: POST /api/ecografias/plano-anatomico/
        B->>IA: POST /api/plano-anatomico
        IA->>P: clasificar
        P-->>IA: plano + probabilidades
        IA-->>B: resultado + métricas medidas
        B-->>F: 200
    and
        F->>B: POST /api/ecografias/anomalias-cerebrales/
        B->>IA: POST /api/anomalias-cerebrales
        IA->>P: ¿parece una cabeza? (P(cerebro) ≥ 0,02)
        alt no parece una cabeza
            IA-->>B: aplicable = false (no se clasifica)
        else es una cabeza
            IA->>X: normal / 4 familias
            IA-->>B: alarma, familia, probabilidades, métricas
        end
        B-->>F: 200
    and
        F->>B: POST /api/ecografias/circunferencia-cefalica/ (si hay tamaño de píxel)
        B->>IA: POST /api/biometria/circunferencia-cefalica
        IA->>C: medir
        IA-->>B: HC (mm) ± 7 mm, EG por Hadlock 1984
        B-->>F: 200
    end
    F-->>M: tarjetas con resultado y su fiabilidad
    Note over B,IA: Si el microservicio no responde: 503 con un mensaje claro
```

## Importación desde Excel (pacientes o resultados de laboratorio)

```mermaid
sequenceDiagram
    actor U as Usuario
    participant F as Frontend
    participant B as Backend
    participant DB as PostgreSQL
    participant A as Auditoría

    U->>F: descargar plantilla
    F->>B: GET .../plantilla-excel/
    B-->>F: .xlsx con instrucciones (y catálogo)
    U->>F: sube el archivo lleno
    F->>B: POST .../importar-excel/ (sin confirmar)
    B->>B: lee y valida cada fila con las MISMAS reglas que el formulario
    B-->>F: vista previa: válidas, con error (y por qué), duplicadas
    U->>F: confirmar
    F->>B: POST .../importar-excel/ confirmar=1
    loop por cada registro válido
        B->>DB: guarda en su propia transacción
    end
    B->>A: CREAR «Importación Excel …»
    B-->>F: resultado final
```

## Listado paginado en el servidor

```mermaid
sequenceDiagram
    actor U as Usuario
    participant F as Frontend (useListadoServidor)
    participant B as Backend (ViewSet)
    participant DB as PostgreSQL

    U->>F: abre la pantalla / escribe «quispe»
    F->>F: espera 350 ms (no busca en cada tecla)
    par página visible
        F->>B: GET /api/x/?search=quispe&page=1&page_size=20&...filtros
        B->>B: búsqueda en nombres cifrados (hash de CI, descifrado controlado, fonética)
        B->>DB: filtros + orden + LIMIT 20
        B-->>F: {count, results}
    and cifras de cabecera
        F->>B: GET /api/x/resumen/?mismos filtros
        B->>DB: COUNT / agregados sobre TODOS
        B-->>F: totales
    end
    U->>F: Exportar Excel
    F->>B: GET /api/x/exportar-excel/?mismos filtros
    B-->>F: .xlsx con todo lo filtrado (auditado)
```

## Notificaciones en tiempo real

```mermaid
sequenceDiagram
    participant S as Señal o tarea
    participant B as Backend
    participant CH as Capa de canales (Redis o memoria)
    participant F as Frontend
    actor M as Médico/a

    F->>B: WebSocket /ws/notifications/ (cookie)
    B-->>F: conectado al grupo del usuario
    S->>B: embarazo de alto riesgo / resultado crítico / cita en 24 h
    B->>B: crea la notificación (destinatario: médico responsable)
    B->>CH: envía al grupo del usuario
    CH-->>F: notificación
    F-->>M: campana con el aviso
```
