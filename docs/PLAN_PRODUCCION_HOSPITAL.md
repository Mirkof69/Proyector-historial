# Plan para dejar Fetal Medical Bolivia listo para un hospital

Rama de trabajo: `produccion-hospital`. Metodología Scrum: sprints cortos, cada uno
termina con el sistema funcionando y todas las pruebas en verde. Ningún cambio se
fusiona si no pasa los controles de calidad (sección 3).

Base del plan: seis auditorías de solo lectura hechas el 24-09-2026 (backend,
frontend, IA, reportes/Excel/registros, QA/CI, orden del repositorio). Cada
hallazgo se verificó en el código; lo que se marca «hecho» tiene commit y test.

---

## 1. Diagnóstico en una tabla

| Área | Estado | Decisión |
|---|---|---|
| Pacientes (modelo, cifrado, baja lógica) | Sano | Mantener; mejorar búsqueda |
| Peso fetal (Hadlock), citas, triaje, laboratorio | Sanos | Mantener |
| Permisos por rol | Roto (prefijos de URL, recepción ve datos clínicos) | **Rehacer** por acción |
| Usuarios | Escalada de privilegios | **Hecho** (sprint 0) |
| Rutas del backend | 5 rutas tapadas por el orden de los routers | **Hecho** (sprint 0) |
| Recién nacido | No se podía crear ni listar; pantalla con datos inventados | Reparar + implementar |
| Evoluciones | Ruta y filtros equivocados | **Hecho** (sprint 0); fusionar con Notas |
| Reportes | Dispersos en 8 páginas, KPIs vacíos, PDF roto, generador que no genera | **Rehacer** como Centro de reportes |
| Importación Excel | No existe (la pantalla es una maqueta) | Implementar |
| Auditoría | Sin vista de sesiones, sin filtros en la UI, acciones masivas sin registrar | Reparar + implementar |
| EfficientNet-B4 de patologías | Positivos mayormente sintéticos, sin métrica en prueba separada | **Retirar del uso clínico** |
| Redes con datos reales (cabeza, plano) | R² 0,978 · 92,7 % en madres no vistas | Usar e integrar en el flujo |
| Modelo de peso al nacer | Servido y verificado; entrenado con datos simulados | Usar como apoyo, con aviso |
| CI | Tests de frontend nunca fallan, sin ruff, sin tests del microservicio, sin e2e | Rehacer los controles |

---

## 2. Sprints

### Sprint 0 — Seguridad crítica (HECHO)

| Qué | Commit |
|---|---|
| La descarga de reportes podía leer cualquier archivo del servidor (`.env`) | `e80749e` |
| Admin de usuarios roto (`is_stafff`) | `e80749e` |
| Callback de IA anónimo que reescribía análisis de cualquier ecografía | `eeca110` |
| Cualquier usuario podía hacerse superusuario o desactivar al administrador | `75682f0` |
| Rutas tapadas: recién nacidos, partograma, horarios, asistente IA | `75682f0` |
| Evoluciones: ruta equivocada y filtros que mostraban las de todas las pacientes | `75682f0` |
| Zips duplicados (6 GB) a la papelera, conservando un original | — |

### Sprint 1 — Que nada mienta y que nada dé 500

Backend
- [ ] Permisos por acción, no por prefijo: recepción sin acceso a historia clínica, laboratorio ni exportaciones (`core/permissions.py`).
- [ ] `ecografias/ai_views.py`: `FetalMedicalPermission`/`EsSoloMedico` en lugar de `IsAuthenticated`.
- [ ] `ecografias/views.py destroy`: solo administrador y baja lógica.
- [ ] `partos/urls.py:45,50,56`: kwargs `parto_id/rn_id/paciente_id` que dan 500.
- [ ] `controles/serializers.py:594`: `import warnings` dentro de un `if` (UnboundLocalError).
- [ ] `embarazos/admin.py`: campos inexistentes (FieldError).
- [ ] `calculadoras_avanzadas/urls.py`: alias rotos.
- [ ] `settings.py`: `DEBUG` falso por defecto; tenant desconocido = 404; webhook Orthanc exige secreto.
- [ ] Subidas: validar tipo real (bytes mágicos), tamaño y nombre UUID; media servida solo con sesión.

Frontend
- [ ] 33 enlaces sin `/dashboard` que llevan a «no encontrado»; menú «IA Assistant».
- [ ] Permisos de ruta con codenames inexistentes (calculadoras, partograma, archivos).
- [ ] Retirar lo que finge: recién nacidos inventados, subida de documentos falsa, PDF falso, medidas DICOM con `Math.random()`, «precisión 87 %», maqueta de importación.

### Sprint 2 — Integridad clínica
- [ ] FCF: aceptar 50–240 lpm y alertar fuera de 110–160 (hoy no se pueden registrar las bradicardias).
- [ ] El parto finaliza el embarazo solo cuando `parto_finalizado`; embarazo obligatorio.
- [ ] `crear-desde-ia` no inventa embarazos; `ecografia_id` no mezcla dos tablas.
- [ ] Ecografía: sin fechas futuras; paciente = paciente del embarazo; EG contrastada con la FUM.
- [ ] EG de embarazos finalizados calculada a la fecha del parto.
- [ ] Una sola clasificación de líquido amniótico; una sola capa MoM (FMF) y un solo cálculo de preeclampsia.
- [ ] Un embarazo activo por paciente como restricción en la base.
- [ ] `on_delete=PROTECT` + baja lógica para no perder historia clínica.
- [ ] Datación ecográfica: FPP corregida por la ecografía del primer trimestre.

### Sprint 3 — IA honesta y útil
- [ ] EfficientNet-B4: fuera de la pantalla clínica (o «experimental, no validado» si se decide conservarla). `BIOMETRY_AVAILABLE=false`.
- [ ] «SHAP risk scores» → «indicador heurístico»; quitar campos fijos (`actividad_cardiaca: False`); una ecografía normal no puede salir «riesgo ALTO».
- [ ] Sin pesos → el microservicio no arranca (hoy responde con pesos aleatorios); `/health` real; inferencia fuera del bucle de eventos.
- [ ] Un solo traductor de resultados del microservicio (hoy hay tres).
- [ ] Integrar las redes reales en la ficha de la ecografía: plano + circunferencia + semanas, guardados y visibles.
- [ ] Registro de modelos: versión y sha256 en cada respuesta.

### Sprint 4 — Reportes, registros y Excel
- [ ] **Centro de reportes**: una sección del menú con pestañas (Resumen, Materno-fetal, Partos y neonatos, Laboratorio, Agenda, Vacunación, Indicadores, Generador, Importación, Auditoría), filtro de fechas común, exportación Excel/PDF desde el backend y auditada, actualización automática opcional cada 60 s.
- [ ] Corregir: contrato de `dashboard-kpis`, PDF `.pd`, fallo con rangos vacíos, último día excluido, gráficas con campos inexistentes, colores por entidad.
- [ ] Exportación Excel de laboratorio, citas, vacunas y auditoría.
- [ ] **Importación Excel** de pacientes y resultados de laboratorio: plantilla, validación en seco, vista previa, sin duplicados, confirmación atómica, informe de errores y deshacer por lote.
- [ ] **Registro por sesión**: `session_key` en cada registro; vista de sesiones (usuario, IP, navegador, inicio, fin, duración); filtros por fecha y usuario; IP también en altas/ediciones; auditar acciones masivas del admin.
- [ ] Los tests dejan de escribir en `Backend/logs/`.

### Sprint 5 — Flujo guiado y UX
- [ ] Historia clínica como centro de la paciente, con acceso directo a cada paso.
- [ ] Formularios que reciben `?paciente=` y `?embarazo=`; tras registrar paciente, ofrecer «crear embarazo».
- [ ] Detalle del parto con pestañas: recién nacidos (gemelos), Apgar, partograma, complicaciones.
- [ ] Unificar duplicados: Evoluciones + Notas, calculadoras, alias de laboratorio, dos modelos de imagen.
- [ ] Paginación en el servidor; dividir los componentes gigantes; modo oscuro y `aria-label`.

### Sprint 6 — QA, CI y puesta en producción
- [ ] CI: pytest en vez de `manage.py test`; ruff; tests del microservicio; tests del frontend sin `|| true`; se dispara también en `produccion-hospital`.
- [ ] E2E con Playwright del flujo completo; carga con Locust.
- [ ] Reparar los tests que no pueden fallar (lista en la sección 5).
- [ ] Versiones fijas, respaldo de base de datos, arranque único y documentado.
- [ ] Orden del repositorio (sección 6).

---

## 3. Controles de calidad (quality gates)

Un cambio solo entra si pasa **todos**:

| Control | Umbral |
|---|---|
| `pytest` backend | 100 % en verde, sin tests saltados nuevos |
| Cobertura backend | ≥ 50 % hoy, subir a 60 % en el sprint 6 |
| `ruff check` | 0 errores |
| `tsc --noEmit` | 0 errores |
| `eslint` | 0 errores |
| Tests frontend (Jest) | 100 % en verde |
| Tests microservicio IA | 100 % en verde (con los modelos presentes) |
| `manage.py check` | 0 problemas |
| Seguridad | Ningún endpoint nuevo con `AllowAny` ni sin test de permisos |
| IA | Ninguna métrica publicada que no se haya medido sobre prueba separada |

**Definición de terminado**: código + test que falla sin el arreglo + controles en
verde + commit con explicación del fallo que previene.

---

## 4. Plan de QA

| Nivel | Qué se prueba | Herramienta |
|---|---|---|
| Unitario | Cálculos clínicos (Hadlock, EG, FPP, MoM), validaciones | pytest |
| API caja negra | Cada endpoint por rol: 200/201/400/401/403/404 | pytest + APIClient |
| Caja blanca | Ramas internas: bordes exactos, descartes, errores | pytest |
| Caja gris | Consultas por petición (N+1), auditoría escrita, efectos laterales | pytest + CaptureQueriesContext |
| Integración | Flujo paciente → RN por la API | pytest |
| E2E | El mismo flujo en el navegador, en tema claro y oscuro | Playwright |
| Carga | 100 usuarios, 3 min: p95 < 1 s, 0 errores 500 | Locust |
| Seguridad | Escalada de privilegios, lectura de archivos, subidas | pytest + revisión |
| IA | Métricas en prueba separada por paciente; la API reproduce el notebook | pytest + notebook |

---

## 5. Casos de prueba prioritarios

| ID | Caso | Entrada | Resultado esperado | Estado |
|---|---|---|---|---|
| SEG-01 | Escalada de privilegios | Recepción PATCH `is_superuser=true` en su perfil | 200, privilegios sin cambiar | ✅ |
| SEG-02 | Editar a otro usuario | Recepción PATCH a un médico | 403 | ✅ |
| SEG-03 | Lectura de archivos | `marcar_completado` con ruta del `.env` | 400; descarga 404 | ✅ |
| SEG-04 | Callback anónimo | POST `/ecografias/1/ai-result/` sin sesión | 401/404 | ✅ |
| SEG-05 | Recepción y datos clínicos | Recepción GET historia clínica | 403 | pendiente |
| SEG-06 | Subida disfrazada | HTML con extensión `.pdf` | 400 | pendiente |
| AUT-01 | Login con MFA | Contraseña ok, sin TOTP | Pide TOTP, sin tokens | pendiente |
| AUT-02 | TOTP inválido ×5 | 5 intentos | Cuenta bloqueada + auditoría | pendiente |
| AUT-03 | Logout | Cerrar sesión | Refresh en blacklist; LOGOUT con IP | pendiente |
| PAC-01 | Paciente duplicada | Mismo CI | 400 | pendiente |
| EMB-01 | Segundo embarazo activo | Paciente con uno activo | 400 | pendiente |
| EMB-02 | FUM futura | FUM mañana | 400 | pendiente |
| CTL-01 | Bradicardia fetal | FCF 80 | Se guarda + alerta | pendiente |
| CTL-02 | PA ≥ 160/110 | Control | Notificación al médico | pendiente |
| ECO-01 | Ecografía de otra paciente | Paciente ≠ paciente del embarazo | 400 | pendiente |
| ECO-02 | Microservicio caído | Analizar | 503 claro, sin diagnóstico guardado | pendiente |
| ECO-03 | Circunferencia por la API | 146 imágenes de prueba | Error medio ≤ 8 mm | ✅ |
| ECO-04 | Plano por la API | 600 imágenes | Exactitud ≥ 89 % | ✅ |
| PES-01 | Predicción de peso | Eco con 4 medidas | = modelo sobre la fila de entrenamiento | ✅ |
| PAR-01 | Peso imposible | 500 g a las 40 sem | 400 | pendiente |
| PAR-02 | Gemelos | Parto con 2 RN | 2 RN guardados | pendiente |
| RN-01 | Crear recién nacido | POST `/partos/recien-nacidos/` | 201 | pendiente |
| REP-01 | Excel de controles | Rango con 3 controles | xlsx con 3 filas + auditoría EXPORTAR | pendiente |
| REP-02 | Rango sin datos | Excel/PDF | Archivo vacío válido, no 500 | pendiente |
| IMP-01 | Importar pacientes | Excel con 1 fila mala | Vista previa marca la fila; nada se guarda hasta confirmar | pendiente |
| AUD-01 | Sesiones | Login + logout | Aparece en «Sesiones» con IP y duración | pendiente |
| E2E-01 | Flujo completo | Navegador | Paciente → RN sin errores de consola | pendiente |
| CAR-01 | Carga | 100 usuarios, 3 min | p95 < 1 s, 0 errores 500 | pendiente |

---

## 6. Orden del repositorio

| Qué | Acción |
|---|---|
| Zips duplicados idénticos (3 de FETAL_PLANES, 2 de Fetal Abdominal, 2 de Ultrasound Fetus) | ✅ copias a la papelera, originales en `nuveos data seeds/` |
| Worktrees `.claude/worktrees/infra-conexiones` y `.kilo/worktrees/nervous-timer` | Limpios y ya fusionados: se pueden quitar |
| `_archive/microservicio_ia_checkpoints` (2,5 GB, 34 épocas del modelo viejo) | Preguntar |
| `Microservicio_IA/datasets_pathology` (4,1 GB) y `_v2` (2,6 GB) | Preguntar (base del modelo que se retira) |
| `Microservicio_IA/.venv` roto (apunta a otro usuario) | Borrar |
| Carpetas vacías `datasets/`, `clinical_training_data/images`, `temp/` | Borrar |
| Scripts `debug_*.py`, `start_gpu_training.bat` con rutas de otro usuario | Borrar |
| Scripts de arranque en la raíz (5 `.bat`) | Dejar uno de desarrollo y uno de producción |

---

## 7. Lo que no se puede prometer (y por qué)

- **La EfficientNet-B4 de patologías no llega al 90 % real sin datos nuevos.** La mayoría
  de sus positivos son imágenes sintéticas y no tiene ninguna métrica medida en una
  prueba separada. Hace falta un conjunto de ecografías reales etiquetadas por
  especialistas, separado por paciente.
- **Las redes que sí pasan del umbral**: plano anatómico 92,7 %; circunferencia
  cefálica R² 0,978. Ambas con datos reales y madres no vistas.
- **El peso al nacer con ecografía** da R² 0,836 con datos simulados, del orden del
  estudio real de Lima (0,847–0,873). Hay que reentrenarlo con partos reales.
- **La alerta de bajo peso** detecta 86 % de los casos a costa de muchas falsas alarmas;
  mejorarla exige ecografía cercana al parto.
