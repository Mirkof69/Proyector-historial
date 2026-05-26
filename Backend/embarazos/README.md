# Embarazos

Descripción: Registro y seguimiento de embarazos asociados a pacientes. Incluye fecha de inicio, gestación, partos y controles prenatales.

Modelos principales:
- Embarazo: FK a Paciente; fecha_inicio_menstruacion, fecha_confirmacion, numero_embarazo, numero_para, numero_abortos, numero_cesareas; estado; observaciones.
- Campos recientes: numero_para (partos previos), numero_abortos, numero_cesareas.

EndPoints (DRF):
- GET  /api/embarazos/                    -> Listar embarazos
- POST /api/embarazos/                    -> Crear embarazo
- GET  /api/embarazos/{id}/               -> Detalle
- PUT  /api/embarazos/{id}/               -> Actualizar
- PATCH /api/embarazos/{id}/               -> Actualizar parcial
- POST /api/embarazos/{id}/semanas/       -> Calcular semanas gestacionales
- POST /api/embarazos/{id}/fecha-parto/   -> Fecha estimada de parto

Notas:
- Cálculos automáticos: semanas gestacionales, FPP (FUM + 280 días), rango de fechas permitidas para parto.
- Este módulo se integra con Pacientes y Citas para seguimiento.
