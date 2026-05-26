# Citas

Descripción: Gestión de citas médicas entre pacientes y médicos. Incluye disponibilidad, agenda, recordatorios e historial de cambios.

Modelos principales:
- Disponibilidad: Horarios de atención de médicos.
- Cita: Citas agendadas (paciente, médico, fecha, hora, duración, estado, motivo, observaciones).
- HistorialCita: Traza de cambios de estado de una cita.

EndPoints (DRF):
- GET  /api/citas/citas/                   -> Listar citas
- POST /api/citas/citas/                   -> Crear cita
- GET  /api/citas/citas/{id}/               -> Detalle
- PUT  /api/citas/citas/{id}/               -> Actualizar
- PATCH /api/citas/citas/{id}/               -> Actualizar parcial
- DELETE /api/citas/citas/{id}/             -> Eliminar
- GET  /api/citas/citas/por-paciente/       -> Citas por paciente
- GET  /api/citas/citas/por-medico/         -> Citas por médico
- GET  /api/citas/citas/pendientes/          -> Citas pendientes
- GET  /api/citas/citas/hoy/                 -> Citas de hoy
- GET  /api/citas/citas/proximas/?dias=7      -> Citas próximas
- POST /api/citas/citas/{id}/confirmar/     -> Confirmar
- POST /api/citas/citas/{id}/cancelar/      -> Cancelar
- POST /api/citas/citas/{id}/completar/     -> Completar
- POST /api/citas/citas/{id}/no-asistio/    -> No asistió

Ejemplos de uso:
```bash
curl -H "Authorization: Bearer <token>" https://host/api/citas/citas/
```

Notas:
- La lógica de negocio contempla verificación de solapes y estado de la cita; hay soporte para historial de cambios.
