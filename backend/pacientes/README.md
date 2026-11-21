# Pacientes

Descripción: Modelo que representa a las personas atendidas por el sistema. Incluye datos demográficos, contacto y atributos de salud relevantes.

Modelos principales:
- Paciente: identificador único, datos personales, contacto, dirección y metadatos.
- Relaciones: un Paciente tiene relaciones con embarazos, citas, notas de evolución, vacunas, etc.

EndPoints (DRF):
- GET  /api/pacientes/            -> Listar pacientes
- POST /api/pacientes/            -> Crear paciente
- GET  /api/pacientes/{id}/        -> Detalle del paciente
- PUT  /api/pacientes/{id}/        -> Actualizar
- PATCH /api/pacientes/{id}/        -> Actualizar parcial
- DELETE /api/pacientes/{id}/      -> Eliminar (según políticas)
- GET  /api/pacientes/filtros/     -> Búsqueda avanzada (si existe)

Ejemplos de uso:
```bash
curl -H "Authorization: Bearer <token>" https://host/api/pacientes/
```

Notas:
- El modelo es central; otras entidades (embarazos, citas, etc.) referencian a Paciente.
- Revisión de integridad y validaciones debe hacerse a través de serializers y/o model validators.
