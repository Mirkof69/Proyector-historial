# Módulo de Vacunas - Sistema de Atención Prenatal

## Descripción

Módulo completo para la gestión de vacunas en un sistema de atención prenatal. Permite administrar el catálogo de vacunas disponibles y registrar la aplicación de vacunas a pacientes embarazadas.

## Características Principales

### 1. Catálogo de Vacunas (TipoVacuna)
- Gestión completa de tipos de vacunas
- Esquemas de dosificación personalizables
- Contraindicaciones y efectos secundarios
- Clasificación de vacunas obligatorias durante el embarazo
- Validaciones automáticas de intervalos entre dosis

### 2. Registro de Vacunación (RegistroVacuna)
- Registro detallado de cada aplicación de vacuna
- Seguimiento de esquemas de vacunación
- Cálculo automático de próximas dosis
- Registro de reacciones adversas
- Asociación con pacientes y embarazos
- Trazabilidad completa (lote, laboratorio, aplicador)

## Modelos

### TipoVacuna
```python
- nombre (CharField, unique)
- descripcion (TextField)
- dosis_requeridas (IntegerField)
- intervalo_dosis_dias (IntegerField, opcional)
- edad_minima_aplicacion (IntegerField, opcional)
- contraindicaciones (TextField)
- efectos_secundarios (TextField)
- obligatoria_embarazo (BooleanField)
- activo (BooleanField)
```

**Propiedades Calculadas:**
- `es_multidosis`: Indica si requiere múltiples dosis
- `tiene_contraindicaciones`: Verifica si tiene contraindicaciones registradas

**Métodos:**
- `get_resumen()`: Retorna resumen de la vacuna

### RegistroVacuna
```python
- paciente (FK to Paciente)
- embarazo (FK to Embarazo, nullable)
- tipo_vacuna (FK to TipoVacuna)
- fecha_aplicacion (DateTimeField)
- numero_dosis (IntegerField, 1-10)
- lote (CharField)
- laboratorio (CharField)
- via_administracion (CharField, choices)
- sitio_aplicacion (CharField)
- aplicado_por (FK to Usuario, nullable)
- proxima_dosis_fecha (DateField, nullable)
- reacciones_adversas (TextField)
- observaciones (TextField)
- activo (BooleanField)
```

**Propiedades Calculadas:**
- `esquema_completo`: Indica si se completó el esquema
- `tiene_reacciones_adversas`: Verifica si hay reacciones reportadas
- `requiere_siguiente_dosis`: Indica si necesita siguiente dosis

**Métodos:**
- `get_progreso_esquema()`: Retorna progreso del esquema (dosis actual, total, porcentaje)
- `get_resumen()`: Resumen del registro
- `calcular_proxima_dosis_fecha()`: Calcula automáticamente la próxima dosis

## Serializers

### TipoVacuna
- **TipoVacunaSerializer**: Serializer completo con todos los campos
- **TipoVacunaListSerializer**: Serializer ligero para listados

### RegistroVacuna
- **RegistroVacunaSerializer**: Serializer completo con objetos anidados
- **RegistroVacunaListSerializer**: Serializer ligero para listados
- **RegistroVacunaCreateUpdateSerializer**: Serializer con validaciones para crear/actualizar

## API Endpoints

### Tipos de Vacunas

#### CRUD Básico
```
GET    /api/vacunas/tipos-vacunas/          - Lista tipos de vacunas
POST   /api/vacunas/tipos-vacunas/          - Crear tipo de vacuna
GET    /api/vacunas/tipos-vacunas/{id}/     - Detalle de tipo de vacuna
PUT    /api/vacunas/tipos-vacunas/{id}/     - Actualizar tipo de vacuna
PATCH  /api/vacunas/tipos-vacunas/{id}/     - Actualización parcial
DELETE /api/vacunas/tipos-vacunas/{id}/     - Eliminar tipo de vacuna
```

#### Acciones Personalizadas
```
GET /api/vacunas/tipos-vacunas/activas/
    Retorna solo las vacunas activas

GET /api/vacunas/tipos-vacunas/obligatorias_embarazo/
    Retorna vacunas obligatorias durante el embarazo

GET /api/vacunas/tipos-vacunas/estadisticas/
    Estadísticas generales de tipos de vacunas

GET /api/vacunas/tipos-vacunas/{id}/registros/
    Registros de aplicación de esta vacuna
    Parámetros opcionales: fecha_desde, fecha_hasta
```

### Registros de Vacunación

#### CRUD Básico
```
GET    /api/vacunas/registros/          - Lista registros de vacunación
POST   /api/vacunas/registros/          - Crear registro de vacunación
GET    /api/vacunas/registros/{id}/     - Detalle de registro
PUT    /api/vacunas/registros/{id}/     - Actualizar registro
PATCH  /api/vacunas/registros/{id}/     - Actualización parcial
DELETE /api/vacunas/registros/{id}/     - Eliminar registro
```

#### Acciones Personalizadas
```
GET /api/vacunas/registros/por_paciente/?paciente_id={id}
    Registros de vacunación de un paciente específico

GET /api/vacunas/registros/por_embarazo/?embarazo_id={id}
    Registros de vacunación de un embarazo específico

GET /api/vacunas/registros/proximas_dosis/?dias={dias}
    Registros con próximas dosis programadas (default: 30 días)

GET /api/vacunas/registros/esquemas_incompletos/
    Pacientes con esquemas de vacunación incompletos

GET /api/vacunas/registros/reacciones_adversas/
    Registros con reacciones adversas reportadas

GET /api/vacunas/registros/estadisticas/
    Estadísticas generales de vacunación

POST /api/vacunas/registros/{id}/marcar_reaccion_adversa/
    Body: {"reaccion": "descripción"}
    Marca una reacción adversa en un registro

POST /api/vacunas/registros/{id}/programar_siguiente_dosis/
    Body: {"fecha": "YYYY-MM-DD"} (opcional, se calcula automáticamente)
    Programa la fecha de siguiente dosis
```

## Filtros y Búsqueda

### TipoVacuna
**Filtros:**
- `activo`: exact
- `obligatoria_embarazo`: exact
- `dosis_requeridas`: exact, gte, lte

**Búsqueda:**
- nombre
- descripcion
- laboratorio

**Ordenamiento:**
- nombre (default)
- dosis_requeridas
- fecha_creacion

### RegistroVacuna
**Filtros:**
- `paciente`: exact
- `embarazo`: exact
- `tipo_vacuna`: exact
- `fecha_aplicacion`: gte, lte, date
- `numero_dosis`: exact
- `via_administracion`: exact
- `activo`: exact
- `proxima_dosis_fecha`: gte, lte, isnull

**Búsqueda:**
- paciente__nombre
- paciente__apellido_paterno
- paciente__apellido_materno
- paciente__id_clinico
- tipo_vacuna__nombre
- lote
- laboratorio

**Ordenamiento:**
- fecha_aplicacion (default descendente)
- numero_dosis
- proxima_dosis_fecha

## Panel de Administración

### TipoVacunaAdmin
**Características:**
- Listado con badges visuales (dosis, obligatoria, estado)
- Filtros por activo, obligatoria_embarazo, dosis_requeridas
- Búsqueda por nombre, descripción, contraindicaciones
- Estadísticas de aplicación en detalle
- Fieldsets organizados por categorías
- Acciones en lote: activar, desactivar, marcar obligatorias

### RegistroVacunaAdmin
**Características:**
- Listado con información del paciente y progreso
- Badges visuales para dosis, próxima dosis, reacciones
- Filtros avanzados por múltiples campos
- Búsqueda por paciente y vacuna
- Autocomplete para relaciones
- Progreso visual del esquema de vacunación
- Información detallada de paciente y vacuna
- Acciones en lote: activar, desactivar, calcular próximas dosis

## Validaciones

### TipoVacuna
- Vacunas multidosis deben especificar intervalo entre dosis
- Nombre único en el sistema

### RegistroVacuna
- Número de dosis no puede exceder las requeridas por la vacuna
- No se permite duplicar misma dosis para mismo paciente en misma fecha
- Fecha de próxima dosis debe ser futura
- Debe existir dosis anterior antes de aplicar dosis subsiguiente
- Validación de lote y laboratorio obligatorios

## Características de Seguridad

- Autenticación requerida (IsAuthenticated)
- PROTECT en FK a TipoVacuna (no se puede eliminar si tiene registros)
- CASCADE en FK a Paciente
- SET_NULL en FK a Embarazo y Usuario (mantiene historial)
- Constraint de unicidad para prevenir duplicados
- Índices para optimización de consultas

## Optimizaciones

### Query Optimization
- `select_related` para paciente, embarazo, tipo_vacuna, aplicado_por
- Índices en campos frecuentemente consultados
- Serializers ligeros para listados

### Cálculo Automático
- Próxima dosis se calcula automáticamente al guardar
- Validaciones en modelo y serializer
- Propiedades calculadas en lugar de campos adicionales

## Uso Típico

### 1. Crear Tipo de Vacuna
```json
POST /api/vacunas/tipos-vacunas/
{
    "nombre": "Toxoide Tetánico",
    "descripcion": "Vacuna contra el tétanos",
    "dosis_requeridas": 2,
    "intervalo_dosis_dias": 30,
    "obligatoria_embarazo": true,
    "activo": true
}
```

### 2. Registrar Aplicación de Vacuna
```json
POST /api/vacunas/registros/
{
    "paciente": 1,
    "embarazo": 5,
    "tipo_vacuna": 1,
    "fecha_aplicacion": "2025-12-17T10:30:00Z",
    "numero_dosis": 1,
    "lote": "LOT12345",
    "laboratorio": "Laboratorio XYZ",
    "via_administracion": "intramuscular",
    "sitio_aplicacion": "Deltoides izquierdo"
}
```

### 3. Consultar Vacunas de un Paciente
```
GET /api/vacunas/registros/por_paciente/?paciente_id=1
```

### 4. Consultar Próximas Dosis
```
GET /api/vacunas/registros/proximas_dosis/?dias=7
```

## Estructura de Base de Datos

### Tablas
- `tipos_vacunas`: Catálogo de vacunas
- `registros_vacunas`: Registros de aplicación

### Índices
- tipos_vacunas: nombre, activo, obligatoria_embarazo
- registros_vacunas: paciente+tipo_vacuna, fecha_aplicacion, embarazo, tipo_vacuna+numero_dosis, proxima_dosis_fecha

### Constraints
- unique_vacuna_aplicacion: (paciente, tipo_vacuna, numero_dosis, fecha_aplicacion)

## Integración con Otros Módulos

- **pacientes**: Relación con modelo Paciente
- **embarazos**: Relación con modelo Embarazo
- **usuarios**: Relación con Usuario (aplicador)

## Próximos Pasos Sugeridos

1. Crear migraciones: `python manage.py makemigrations vacunas`
2. Aplicar migraciones: `python manage.py migrate`
3. Registrar en settings.py: Agregar 'vacunas' a INSTALLED_APPS
4. Agregar URLs al proyecto: Incluir urls de vacunas en urls.py principal
5. Crear datos de prueba de tipos de vacunas comunes
6. Implementar notificaciones para próximas dosis vencidas

## Notas Técnicas

- Compatible con Django 4.x+
- Requiere Django REST Framework 3.x+
- Usa django-filter para filtrado avanzado
- Timezone-aware para fechas
- Validaciones tanto en modelo como en serializer
- Documentación completa en docstrings

---

**Versión:** 1.0.0
**Fecha:** Diciembre 2025
**Autor:** Sistema de Historias Clínicas - Fetal Medical
