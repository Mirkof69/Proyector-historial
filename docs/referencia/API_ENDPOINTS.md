# Notas de Evolución - API Quick Reference

## Base URL
```
/api/notas-evolucion/
```

## Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints

### 1. List All Notes
```
GET /api/notas-evolucion/
```

**Query Parameters:**
- `paciente` - Filter by patient ID
- `paciente__id_clinico` - Filter by clinical ID
- `embarazo` - Filter by pregnancy ID
- `medico` - Filter by doctor ID
- `tipo_consulta` - Filter by consultation type
- `activo` - Filter by active status (true/false)
- `fecha_consulta__gte` - Filter from date
- `fecha_consulta__lte` - Filter to date
- `search` - Search in motivo_consulta, diagnosticos, etc.
- `ordering` - Order by field (e.g., `-fecha_consulta`)
- `solo_activas=true` - Only active notes
- `fecha_desde=YYYY-MM-DD` - From date
- `fecha_hasta=YYYY-MM-DD` - To date
- `medico_id=N` - By doctor ID
- `sin_revisar=true` - Only unreviewed notes

**Response:** List of notes (lightweight serializer)

---

### 2. Create Note
```
POST /api/notas-evolucion/
Content-Type: application/json
```

**Required Fields:**
```json
{
  "paciente": 1,
  "medico": 1,
  "fecha_consulta": "2024-12-17T14:30:00",
  "tipo_consulta": "control_prenatal",
  "motivo_consulta": "Control prenatal de rutina",
  "examen_fisico": "...",
  "diagnosticos": "...",
  "plan_tratamiento": "..."
}
```

**Optional Fields:**
- `embarazo` - Pregnancy ID
- `control_prenatal` - Prenatal control ID
- `presion_arterial_sistolica` - Systolic BP
- `presion_arterial_diastolica` - Diastolic BP
- `frecuencia_cardiaca` - Heart rate
- `frecuencia_respiratoria` - Respiratory rate
- `temperatura` - Temperature
- `saturacion_oxigeno` - Oxygen saturation
- `edad_gestacional_semanas` - Gestational weeks
- `edad_gestacional_dias` - Gestational days (0-6)
- `altura_uterina` - Uterine height
- `frecuencia_cardiaca_fetal` - Fetal heart rate
- `presentacion_fetal` - Fetal presentation
- `movimientos_fetales` - Fetal movements
- `examen_obstetrico` - Obstetric exam
- `indicaciones` - Patient instructions
- `observaciones` - Additional observations
- `activo` - Active status (default: true)

**Response:** Created note (full serializer)

---

### 3. Get Note Detail
```
GET /api/notas-evolucion/{id}/
```

**Response:** Full note with nested objects (patient, pregnancy, doctor, etc.)

---

### 4. Update Note (Full)
```
PUT /api/notas-evolucion/{id}/
Content-Type: application/json
```

**Body:** Same as Create (all fields)

**Response:** Updated note (full serializer)

---

### 5. Update Note (Partial)
```
PATCH /api/notas-evolucion/{id}/
Content-Type: application/json
```

**Body:** Only fields to update
```json
{
  "observaciones": "Nueva observación",
  "activo": false
}
```

**Response:** Updated note (full serializer)

---

### 6. Delete Note
```
DELETE /api/notas-evolucion/{id}/
```

**Response:** 204 No Content

---

### 7. Notes by Patient
```
GET /api/notas-evolucion/por-paciente/{paciente_id}/
```

**Response:** Paginated list of patient's notes

---

### 8. Notes by Pregnancy
```
GET /api/notas-evolucion/por-embarazo/{embarazo_id}/
```

**Response:** Paginated list of pregnancy's notes

---

### 9. My Notes (Current Doctor)
```
GET /api/notas-evolucion/mis-notas/
```

**Response:** Paginated list of authenticated doctor's notes

---

### 10. Review Note
```
POST /api/notas-evolucion/{id}/revisar/
Content-Type: application/json
```

**Body (optional):**
```json
{
  "observaciones": "Revisión: todo correcto"
}
```

**Validations:**
- Doctor cannot review their own notes
- Automatically sets `revisado_por` and `fecha_revision`

**Response:** Updated note with review information

---

### 11. Statistics
```
GET /api/notas-evolucion/estadisticas/
```

**Response:**
```json
{
  "total_notas": 150,
  "notas_activas": 145,
  "notas_sin_revisar": 23,
  "por_tipo_consulta": [
    {"tipo_consulta": "control_prenatal", "total": 100},
    {"tipo_consulta": "urgencia", "total": 30},
    ...
  ],
  "top_medicos": [
    {
      "medico__id": 1,
      "medico__nombre": "Juan",
      "medico__apellido_paterno": "Pérez",
      "total": 45
    },
    ...
  ]
}
```

---

## Response Formats

### List View (Lightweight)
```json
{
  "count": 100,
  "next": "http://...?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "paciente_nombre": "María García López",
      "paciente_id_clinico": "PAC-12345",
      "medico_nombre": "Dr. Juan Pérez",
      "fecha_consulta": "2024-12-17T14:30:00",
      "tipo_consulta": "control_prenatal",
      "tipo_consulta_display": "Control Prenatal",
      "motivo_consulta": "Control prenatal rutinario",
      "presion_arterial": "120/80",
      "temperatura": "36.5",
      "edad_gestacional_completa": "32s 4d",
      "diagnosticos": "Embarazo de 32 semanas sin complicaciones",
      "activo": true
    }
  ]
}
```

### Detail View (Full)
```json
{
  "id": 1,
  "paciente": {
    "id": 1,
    "id_clinico": "PAC-12345",
    "nombre": "María",
    "apellido_paterno": "García",
    "apellido_materno": "López",
    "nombre_completo": "María García López",
    "ci": "1234567",
    "edad": 28,
    "fecha_nacimiento": "1995-05-15",
    "genero": "femenino",
    "tipo_sangre": "O+"
  },
  "embarazo": {
    "id": 1,
    "uuid": "...",
    "numero_gesta": 1,
    "fecha_ultima_menstruacion": "2024-04-01",
    "fecha_probable_parto": "2025-01-06",
    "tipo_embarazo": "simple",
    "riesgo_embarazo": "bajo",
    "estado": "activo"
  },
  "control_prenatal": {
    "id": 5,
    "numero_control": 5,
    "fecha_control": "2024-12-17",
    "edad_gestacional_semanas": 32,
    "edad_gestacional_dias": 4
  },
  "medico": {
    "id": 1,
    "nombre": "Juan",
    "apellido_paterno": "Pérez",
    "apellido_materno": "Rodríguez",
    "nombre_completo": "Juan Pérez Rodríguez",
    "rol": "medico",
    "especialidad": "Ginecología y Obstetricia",
    "email": "juan.perez@hospital.com"
  },
  "fecha_consulta": "2024-12-17T14:30:00",
  "tipo_consulta": "control_prenatal",
  "tipo_consulta_display": "Control Prenatal",
  "motivo_consulta": "Control prenatal rutinario...",
  "presion_arterial_sistolica": 120,
  "presion_arterial_diastolica": 80,
  "presion_arterial": "120/80",
  "frecuencia_cardiaca": 72,
  "frecuencia_respiratoria": 16,
  "temperatura": "36.5",
  "saturacion_oxigeno": 98,
  "edad_gestacional_semanas": 32,
  "edad_gestacional_dias": 4,
  "edad_gestacional_completa": "32s 4d",
  "altura_uterina": "32.0",
  "frecuencia_cardiaca_fetal": 140,
  "presentacion_fetal": "Cefálica",
  "movimientos_fetales": "Presentes, activos",
  "examen_fisico": "Paciente en buen estado general...",
  "examen_obstetrico": "Altura uterina adecuada...",
  "diagnosticos": "Embarazo de 32 semanas sin complicaciones",
  "plan_tratamiento": "Continuar controles prenatales cada 2 semanas",
  "indicaciones": "Signos de alarma: sangrado...",
  "observaciones": "",
  "revisado_por": null,
  "fecha_revision": null,
  "fecha_creacion": "2024-12-17T14:35:00",
  "fecha_modificacion": "2024-12-17T14:35:00",
  "activo": true
}
```

---

## Consultation Types (tipo_consulta)

- `control_prenatal` - Control Prenatal
- `urgencia` - Consulta de Urgencia
- `seguimiento` - Seguimiento
- `interconsulta` - Interconsulta
- `puerperio` - Control Puerperio
- `otro` - Otro

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Error message",
  "field_name": ["Validation error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Validation Rules

1. **Pregnancy must belong to patient**
2. **Prenatal control must belong to patient and pregnancy**
3. **Systolic BP > Diastolic BP**
4. **Gestational days: 0-6**
5. **Doctor role: 'medico' or 'administrador'**
6. **If revisado_por is set, fecha_revision is required**
7. **Cannot review own notes**

---

## Performance Tips

1. Use `solo_activas=true` for better performance
2. Use date ranges to limit results
3. List endpoint returns lightweight data
4. Detail endpoint includes full nested objects
5. Search is indexed on key fields
6. Queries are optimized with select_related

---

## Pagination

Default: 25 items per page

```
?page=2
?page_size=50  (if configured)
```
