# Notas de Evolucion - Integration Guide

## Files Created

All backend files for the `notas_evolucion` Django module have been successfully created:

### 1. **serializers.py** (9.6 KB)
Complete serializers with validation and nested relationships:

- **PacienteSimpleSerializer**: Basic patient information for nested display
- **UsuarioSimpleSerializer**: Basic user information for nested display
- **EmbarazoSimpleSerializer**: Basic pregnancy information for nested display
- **ControlPrenatalSimpleSerializer**: Basic prenatal control information
- **NotaEvolucionSerializer**: Full serializer with nested objects (for detail view)
- **NotaEvolucionListSerializer**: Lightweight serializer for list view (optimized performance)
- **NotaEvolucionCreateUpdateSerializer**: Create/update serializer with validation

#### Key Features:
- Validates that pregnancy belongs to the patient
- Validates that prenatal control belongs to pregnancy and patient
- Validates blood pressure (systolic > diastolic)
- Validates gestational age days (0-6)
- Validates that assigned doctor has correct role
- Validates revision requires revision date

### 2. **views.py** (9.0 KB)
Complete ViewSet with advanced features:

- **NotaEvolucionViewSet**: Full CRUD ModelViewSet with:
  - List, Create, Retrieve, Update, Partial Update, Delete
  - Filtering by: patient, pregnancy, doctor, consultation type
  - Search by: motivo_consulta, diagnosticos, examen_fisico, plan_tratamiento
  - Ordering by: fecha_consulta, fecha_creacion, tipo_consulta
  - Query optimizations with select_related

#### Custom Actions:
- `GET /api/notas-evolucion/por-paciente/{id}/` - Get all notes for a patient
- `GET /api/notas-evolucion/por-embarazo/{id}/` - Get all notes for a pregnancy
- `GET /api/notas-evolucion/mis-notas/` - Get notes created by authenticated doctor
- `POST /api/notas-evolucion/{id}/revisar/` - Mark note as reviewed
- `GET /api/notas-evolucion/estadisticas/` - Get statistics

#### Query Parameters:
- `?solo_activas=true` - Filter only active notes
- `?fecha_desde=YYYY-MM-DD` - Filter from date
- `?fecha_hasta=YYYY-MM-DD` - Filter to date
- `?medico_id=N` - Filter by doctor
- `?sin_revisar=true` - Filter unreviewed notes
- `?search=text` - Full-text search
- `?ordering=-fecha_consulta` - Order by field

### 3. **urls.py** (1.6 KB)
Complete router configuration with DefaultRouter

Available endpoints:
```
GET    /api/notas-evolucion/                          - List all notes
POST   /api/notas-evolucion/                          - Create new note
GET    /api/notas-evolucion/{id}/                     - Note detail
PUT    /api/notas-evolucion/{id}/                     - Full update
PATCH  /api/notas-evolucion/{id}/                     - Partial update
DELETE /api/notas-evolucion/{id}/                     - Delete note
GET    /api/notas-evolucion/por-paciente/{id}/        - Notes by patient
GET    /api/notas-evolucion/por-embarazo/{id}/        - Notes by pregnancy
GET    /api/notas-evolucion/mis-notas/                - Authenticated doctor's notes
POST   /api/notas-evolucion/{id}/revisar/             - Review note
GET    /api/notas-evolucion/estadisticas/             - Statistics
```

### 4. **admin.py** (9.0 KB)
Complete Django Admin configuration with:

#### List Display:
- Patient name and clinical ID
- Doctor name and specialty
- Consultation date and time
- Consultation type (with color badges)
- Blood pressure (color-coded by value)
- Temperature (color-coded: fever/normal)
- Gestational age
- Review status
- Active status

#### Features:
- Advanced filtering by type, active status, date, pregnancy risk, reviewer
- Full-text search across multiple fields
- Readonly fields for dates and calculated properties
- Autocomplete for related objects
- Organized fieldsets (collapsible sections)
- Custom display methods with color coding
- Bulk actions: mark as active/inactive
- Query optimization with select_related

### 5. **__init__.py**
Already exists (empty file for Python package)

## Integration Steps

### Step 1: Register the App
Add to `settings.py` in INSTALLED_APPS:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'notas_evolucion',  # Add this line
]
```

### Step 2: Register URLs
Add to main `urls.py`:

```python
urlpatterns = [
    # ... existing patterns ...
    path('api/', include('notas_evolucion.urls')),  # Add this line
]
```

### Step 3: Create Migrations
Run these commands:

```bash
python manage.py makemigrations notas_evolucion
python manage.py migrate notas_evolucion
```

### Step 4: Test the Admin
1. Start the server: `python manage.py runserver`
2. Go to: http://localhost:8000/admin/notas_evolucion/notaevolucion/
3. You should see the complete admin interface

### Step 5: Test the API
Use these curl commands or Postman:

```bash
# List all notes (requires authentication)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/notas-evolucion/

# Get notes for a specific patient
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/notas-evolucion/por-paciente/1/

# Create a new note
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "paciente": 1,
    "medico": 1,
    "fecha_consulta": "2024-01-15T10:30:00",
    "tipo_consulta": "control_prenatal",
    "motivo_consulta": "Control prenatal rutinario",
    "presion_arterial_sistolica": 120,
    "presion_arterial_diastolica": 80,
    "examen_fisico": "Paciente en buen estado general",
    "diagnosticos": "Embarazo de 32 semanas sin complicaciones",
    "plan_tratamiento": "Continuar con controles prenatales rutinarios"
  }' \
  http://localhost:8000/api/notas-evolucion/
```

## API Request Examples

### Create Note (POST)
```json
{
  "paciente": 1,
  "embarazo": 1,
  "medico": 1,
  "fecha_consulta": "2024-12-17T14:30:00",
  "tipo_consulta": "control_prenatal",
  "motivo_consulta": "Control prenatal de rutina",
  "presion_arterial_sistolica": 120,
  "presion_arterial_diastolica": 80,
  "frecuencia_cardiaca": 72,
  "temperatura": 36.5,
  "edad_gestacional_semanas": 32,
  "edad_gestacional_dias": 4,
  "altura_uterina": 32.0,
  "frecuencia_cardiaca_fetal": 140,
  "presentacion_fetal": "Cefálica",
  "movimientos_fetales": "Presentes, activos",
  "examen_fisico": "Paciente en buen estado general...",
  "examen_obstetrico": "Altura uterina adecuada para edad gestacional...",
  "diagnosticos": "Embarazo de 32 semanas sin complicaciones",
  "plan_tratamiento": "Continuar controles prenatales cada 2 semanas",
  "indicaciones": "Signos de alarma: sangrado, dolor abdominal intenso...",
  "activo": true
}
```

### Update Note (PATCH)
```json
{
  "observaciones": "Paciente refiere mejoría en síntomas",
  "revisado_por": 2,
  "fecha_revision": "2024-12-17T16:00:00"
}
```

## Permissions
All endpoints require `IsAuthenticated` permission. Make sure to include JWT token:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

## Model Relationships
- `NotaEvolucion` -> `Paciente` (required, CASCADE)
- `NotaEvolucion` -> `Embarazo` (optional, SET_NULL)
- `NotaEvolucion` -> `ControlPrenatal` (optional, SET_NULL)
- `NotaEvolucion` -> `Usuario` (medico, required, PROTECT)
- `NotaEvolucion` -> `Usuario` (revisado_por, optional, SET_NULL)

## Field Validation
- Blood pressure: systolic must be > diastolic
- Gestational age days: 0-6
- Temperature: 35.0-42.0°C
- Heart rate: 40-200 bpm
- Respiratory rate: 10-40 rpm
- Oxygen saturation: 70-100%
- Fetal heart rate: 100-180 bpm

## Production Checklist
- [ ] App registered in INSTALLED_APPS
- [ ] URLs configured in main urls.py
- [ ] Migrations created and applied
- [ ] Permissions configured correctly
- [ ] API endpoints tested
- [ ] Admin interface tested
- [ ] Validation working correctly
- [ ] Query optimization verified
- [ ] Error handling tested

## Notes
- The module uses `select_related` for query optimization
- All dates are in ISO 8601 format
- The admin interface includes color-coded displays
- Custom actions allow bulk operations
- Statistics endpoint provides useful metrics

## Support
For issues or questions, review:
1. Model definitions in `models.py`
2. Serializer validations in `serializers.py`
3. ViewSet filters in `views.py`
4. Admin configuration in `admin.py`
