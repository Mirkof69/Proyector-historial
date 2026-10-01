# 07 · Modelo de datos

Entidades principales de cada clínica (esquema propio en PostgreSQL). Se
muestran solo los campos que explican el modelo; cada tabla tiene además
fechas de creación/modificación y quién las hizo. Los campos marcados
«cifrado» se guardan cifrados (EncryptedCharField); la CI se busca por su hash.

## Núcleo clínico

```mermaid
erDiagram
    PACIENTE ||--o{ EMBARAZO : tiene
    PACIENTE ||--o{ ANTECEDENTE_PATOLOGICO : registra
    PACIENTE ||--o| ANTECEDENTE_GINECO_OBSTETRICO : registra
    PACIENTE ||--o{ CITA : agenda
    PACIENTE ||--o{ TRIAJE : recibe
    EMBARAZO ||--o{ CONTROL_PRENATAL : incluye
    EMBARAZO ||--o{ ECOGRAFIA : incluye
    EMBARAZO ||--o{ NOTA_EVOLUCION : documenta
    EMBARAZO ||--o{ REGISTRO_VACUNA : asocia
    EMBARAZO ||--o| PARTO : termina_en
    ECOGRAFIA ||--o| BIOMETRIA_FETAL : mide
    ECOGRAFIA ||--o{ IMAGEN_ECOGRAFIA : contiene
    ECOGRAFIA ||--o{ ECOGRAFIA_ARCHIVO : adjunta
    PARTO ||--|{ RECIEN_NACIDO : nace
    PARTO ||--o{ COMPLICACION_PARTO : registra
    PACIENTE ||--o{ EXAMEN_LABORATORIO : solicita
    EXAMEN_LABORATORIO ||--o{ RESULTADO_LABORATORIO : produce
    TIPO_EXAMEN ||--o{ EXAMEN_LABORATORIO : clasifica
    TIPO_EXAMEN ||--o{ VALOR_REFERENCIA : define
    VALOR_REFERENCIA ||--o{ RESULTADO_LABORATORIO : evalua
    TIPO_VACUNA ||--o{ REGISTRO_VACUNA : clasifica
    USUARIO ||--o{ CONTROL_PRENATAL : realiza
    USUARIO ||--o{ PARTO : atiende

    PACIENTE {
        int id PK
        string id_clinico UK
        string nombre "cifrado"
        string apellido_paterno "cifrado"
        string ci "cifrado"
        string ci_hash UK "búsqueda"
        date fecha_nacimiento
        bool consentimiento_datos_aceptado
        bool activo
    }
    EMBARAZO {
        int id PK
        int paciente_id FK
        date fecha_ultima_menstruacion
        date fecha_probable_parto
        int numero_gesta
        string tipo_embarazo "simple, gemelar, multiple"
        string riesgo_embarazo
        string estado "activo (uno por paciente), finalizado, perdida"
    }
    CONTROL_PRENATAL {
        int id PK
        int embarazo_id FK
        date fecha_control
        int semanas_gestacion
        int presion_arterial_sistolica
        int presion_arterial_diastolica
        int frecuencia_cardiaca_fetal
        string edema
        string proteinuria
    }
    ECOGRAFIA {
        int id PK
        int embarazo_id FK
        date fecha_ecografia
        string tipo_ecografia
        int edad_gestacional_semanas
        decimal indice_liquido_amniotico
    }
    BIOMETRIA_FETAL {
        int id PK
        int ecografia_id FK
        decimal diametro_biparietal "mm"
        decimal circunferencia_cefalica "mm"
        decimal circunferencia_abdominal "mm"
        decimal longitud_femur "mm"
        int peso_fetal_estimado "Hadlock, g"
    }
    ECOGRAFIA_ARCHIVO {
        int id PK
        int ecografia_id FK
        file archivo "nombre aleatorio"
        string tipo_archivo "imagen, dicom, pdf, video"
    }
    PARTO {
        int id PK
        int embarazo_id FK
        datetime fecha_parto
        string tipo_parto
        string edad_gestacional_parto
    }
    RECIEN_NACIDO {
        int id PK
        int parto_id FK
        int numero_gemelo
        int peso_nacimiento "300-6000 g"
        int apgar_1_minuto
        int apgar_5_minutos
    }
    EXAMEN_LABORATORIO {
        int id PK
        int paciente_id FK
        int tipo_examen_id FK
        string estado "solicitado, en_proceso, completado, cancelado"
    }
    VALOR_REFERENCIA {
        int id PK
        int tipo_examen_id FK
        string parametro
        decimal valor_minimo
        decimal valor_maximo
        decimal es_critico_bajo
        decimal es_critico_alto
    }
    RESULTADO_LABORATORIO {
        int id PK
        int examen_id FK
        int valor_referencia_id FK
        decimal valor_numerico
        bool es_normal
        bool es_critico
    }
    REGISTRO_VACUNA {
        int id PK
        int paciente_id FK
        int tipo_vacuna_id FK
        datetime fecha_aplicacion
        int numero_dosis
        date proxima_dosis_fecha
    }
```

Reglas importantes que impone la base o el modelo:

- **Un solo embarazo activo por paciente** (restricción única condicional).
- **La historia clínica no se borra en cascada**: las relaciones clínicas usan
  `PROTECT`; borrar un embarazo con ecografías responde 409.
- **Cada recién nacido se valida** (`full_clean`) y un parto múltiple se guarda
  entero o nada (transacción).
- **El resultado de laboratorio se evalúa al guardarse** contra su rango.

## Usuarios, auditoría e IA

```mermaid
erDiagram
    CLIENT ||--o{ DOMAIN : responde_en
    USUARIO }o--o{ GRUPO_ROL : pertenece
    USUARIO ||--o{ REGISTRO_AUDITORIA : genera
    USUARIO ||--o{ NOTIFICACION : recibe
    PACIENTE ||--o{ IMAGEN_ECOGRAFICA_IA : sube
    IMAGEN_ECOGRAFICA_IA ||--o| ANALISIS_CNN : analiza
    ANALISIS_CNN ||--o{ PATOLOGIA_DETECTADA : detecta
    ANALISIS_CNN ||--o{ ALERTA_CNN : alerta

    CLIENT {
        string schema_name "un esquema por clínica"
        string nombre
    }
    USUARIO {
        int id PK
        string email UK
        string rol "medico, enfermera, recepcion, laboratorista, administrador"
        bool activo
    }
    REGISTRO_AUDITORIA {
        int id PK
        string accion "CREAR, EDITAR, ELIMINAR, EXPORTAR, LOGIN..."
        string modulo
        string sesion_id "agrupa una sesión"
        string ip
        datetime fecha "inmutable (trigger)"
    }
    NOTIFICACION {
        int id PK
        string tipo
        string prioridad
        bool leida
    }
    ANALISIS_CNN {
        int id PK
        string version_modelo "incluye sha256"
        string nivel_riesgo
    }
```
