"""Casos de prueba con resultado ESPERADO y OBTENIDO, trazados a pruebas automáticas.

    python quality-assurance/casos_de_prueba.py            # todo (~15 min)
    python quality-assurance/casos_de_prueba.py --sin-e2e  # sin navegador

Ejecuta de verdad las pruebas de cada caso (pytest del backend y del
microservicio de IA, Jest del frontend, Playwright E2E) y escribe
docs/QA_CASOS_DE_PRUEBA.md con lo que se obtuvo. Un caso PASA solo si TODAS
sus pruebas pasan; si una prueba no aparece en la ejecución, el caso queda
«SIN EJECUTAR» (nunca se da por bueno algo que no corrió).

Requisitos: Backend/.venv (backend), Python del sistema con torch (IA),
node_modules del frontend y de e2e, y para E2E el sistema levantado
(INICIAR_SISTEMA.bat) con la demo cargada.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BACKEND = RAIZ / "Backend"
IA = BACKEND / "Microservicio_IA"
FRONT = BACKEND / "frontend"
E2E = BACKEND / "e2e"
SALIDA = RAIZ / "docs" / "QA_CASOS_DE_PRUEBA.md"
PY_BACKEND = BACKEND / ".venv" / "Scripts" / "python.exe"
PY_IA = os.environ.get("PY_IA", r"C:\Users\Miscar\AppData\Local\Programs\Python\Python312\python.exe")

# Prefijos de referencia: py: backend · ia: microservicio · js: Jest · e2e: Playwright
# (id, módulo, riesgo, caso, esperado, [pruebas])
CASOS = [
    # ── Pacientes ──
    ("CP-001", "Pacientes", "Alto", "Registrar una paciente sin consentimiento de datos (Ley 164)",
     "Se rechaza; con consentimiento se registra",
     ["e2e:1. registrar la paciente con el asistente", "py:test_importacion_pacientes::test_confirmar_crea_solo_las_validas"]),
    ("CP-002", "Pacientes", "Alto", "Buscar por apellido sin tilde o con otra grafía (nombres cifrados)",
     "«lopez» encuentra a «López»; una CI parcial no devuelve a otra paciente",
     ["py:test_busqueda_clinica::test_encuentra_sin_tildes", "py:test_busqueda_clinica::test_encuentra_por_apellido",
      "py:test_busqueda_clinica::test_cedula_parcial_no_devuelve_a_otra_paciente"]),
    ("CP-003", "Pacientes", "Medio", "Importar pacientes desde Excel",
     "Vista previa sin guardar; al confirmar solo se crean las filas válidas; archivo inválido = 400",
     ["py:test_importacion_pacientes::test_la_vista_previa_no_crea_nada_y_clasifica_cada_fila",
      "py:test_importacion_pacientes::test_confirmar_crea_solo_las_validas",
      "py:test_importacion_pacientes::test_un_archivo_que_no_es_excel_se_rechaza"]),
    ("CP-004", "Pacientes", "Medio", "Listado de 3.200 pacientes paginado en el servidor",
     "Trae solo la página, el total real, cifras sobre TODAS y no ordena por nombres cifrados",
     ["py:test_listados_servidor_embarazos_citas_pacientes::test_resumen_calcula_la_edad_promedio_sobre_todas",
      "py:test_listados_servidor_embarazos_citas_pacientes::test_no_ordena_por_nombres_cifrados",
      "js:useListadoServidor::pide SOLO la página visible y usa el total del servidor"]),
    # ── Embarazo ──
    ("CP-010", "Embarazo", "Alto", "Registrar un segundo embarazo activo para la misma paciente",
     "La base lo rechaza", ["py:test_eg_embarazo_finalizado::test_la_base_rechaza_un_segundo_embarazo_activo"]),
    ("CP-011", "Embarazo", "Alto", "Edad gestacional de un embarazo terminado hace un año",
     "Muestra la EG del parto, no 90 semanas",
     ["py:test_eg_embarazo_finalizado::test_embarazo_terminado_hace_un_anio_muestra_la_eg_del_parto"]),
    ("CP-012", "Embarazo", "Alto", "Datación por ecografía (ACOG)",
     "Diferencia pequeña mantiene la FUM; grande redata con la ecografía",
     ["py:test_datacion::test_diferencia_pequena_mantiene_la_fum", "py:test_datacion::test_diferencia_grande_redata_con_la_ecografia"]),
    ("CP-013", "Embarazo", "Alto", "Borrar un embarazo con ecografías",
     "Protegido (409); uno vacío se borra y queda auditado",
     ["py:test_historia_protegida::test_un_embarazo_con_ecografia_no_se_borra",
      "py:test_historia_protegida::test_un_embarazo_vacio_se_borra_y_queda_auditado"]),
    # ── Control prenatal ──
    ("CP-020", "Control prenatal", "Alto", "Filtro «con alertas» del listado de controles",
     "Coincide exactamente con la columna «tiene alertas»",
     ["py:test_controles_listado_servidor::test_alerta_critica_coincide_con_tiene_alertas",
      "py:test_controles_listado_servidor::test_paginas_sin_repetidos"]),
    ("CP-021", "Control prenatal", "Medio", "Registrar un control desde la pantalla",
     "Se guarda con la paciente y el embarazo ya elegidos", ["e2e:3. registrar el control prenatal"]),
    # ── Ecografía e IA ──
    ("CP-030", "Ecografía", "Alto", "Peso fetal (Hadlock) con medidas en mm",
     "Feto de término 2.500-3.500 g, nunca 0; cm pasados como mm se rechazan; pantalla = servidor",
     ["py:test_peso_fetal_hadlock::test_un_feto_a_termino_en_milimetros_da_un_peso_a_termino",
      "py:test_peso_fetal_hadlock::test_centimetros_pasados_como_milimetros_se_rechazan",
      "js:pesoFetal::coincide con el backend", "js:pesoFetal::un feto de término no pesa 0 g"]),
    ("CP-031", "Ecografía", "Alto", "Imágenes de ecografía protegidas",
     "Sin sesión no se ven; recepción no ve archivos clínicos; no se sale de /media",
     ["py:test_media_protegida::test_sin_sesion_no_se_ve", "py:test_media_protegida::test_recepcion_no_ve_archivos_clinicos",
      "py:test_media_protegida::test_no_se_sale_de_media"]),
    ("CP-032", "Ecografía", "Medio", "Registrar una ecografía con imagen y analizarla con las redes medidas",
     "Reconoce cerebro fetal; la red de anomalías no da alarma en una cabeza normal",
     ["e2e:4. registrar la ecografía con su imagen", "e2e:5. analizar la ecografía con las redes medidas"]),
    ("CP-033", "IA", "Alto", "Red de anomalías cerebrales: falsas alarmas y preprocesado",
     "La API reproduce el entrenamiento; ≤ 2 % de alarmas en imágenes que no son cabezas; sin modelo = 503",
     ["ia:test_anomalias_cerebrales::test_la_api_reproduce_las_probabilidades_del_entrenamiento",
      "ia:test_anomalias_cerebrales::test_imagenes_que_no_son_cabezas_casi_nunca_dan_alarma",
      "ia:test_anomalias_cerebrales::test_sin_modelo_responde_503"]),
    ("CP-034", "IA", "Alto", "Plano anatómico y circunferencia cefálica por la API",
     "Exactitud ≥ 89 % y error medio < 8 mm (como en el notebook)",
     ["ia:test_ecografia_real::test_plano_por_la_api_acierta_como_en_el_notebook",
      "ia:test_ecografia_real::test_circunferencia_por_la_api_reproduce_el_error_del_notebook"]),
    ("CP-035", "IA", "Medio", "Microservicio de IA apagado",
     "Django responde 503 con un mensaje claro, no 500",
     ["py:test_redes_ecografia_real::test_microservicio_apagado_da_503_claro",
      "py:test_redes_ecografia_real::test_anomalias_cerebrales_va_a_su_red"]),
    ("CP-036", "IA (supervisado)", "Alto", "Predicción de peso al nacer",
     "Trae Hadlock al lado; sin modelo no inventa (409); gemelar o temprana se niega con motivo",
     ["py:test_prediccion_peso::test_predice_y_trae_hadlock_al_lado",
      "py:test_prediccion_peso::test_sin_modelo_entrenado_responde_409_sin_inventar",
      "py:test_prediccion_peso::test_gemelar_sin_biometria_y_temprana_dan_409_con_motivo"]),
    # ── Parto ──
    ("CP-040", "Parto", "Alto", "Parto gemelar", "Se registran los dos recién nacidos; uno inválido no deja un parto a medias",
     ["py:test_parto_gemelar::test_se_registran_los_dos_gemelos",
      "py:test_parto_gemelar::test_un_gemelo_invalido_no_deja_un_parto_a_medias"]),
    ("CP-041", "Parto", "Medio", "Registrar el parto desde el embarazo", "Llega con el embarazo y las semanas elegidas",
     ["e2e:6. el parto llega con el embarazo elegido"]),
    # ── Laboratorio ──
    ("CP-050", "Laboratorio", "Alto", "Catálogo de parámetros con rangos", "Los 30 tipos tienen rangos; el comando es idempotente",
     ["py:test_catalogo_laboratorio::test_el_comando_crea_tipos_y_rangos_para_todo_el_catalogo",
      "py:test_catalogo_laboratorio::test_es_idempotente"]),
    ("CP-051", "Laboratorio", "Alto", "Evaluar un resultado contra su rango",
     "Mínimo 0 y rangos de un solo límite evalúan bien; 0 es un valor",
     ["py:test_catalogo_laboratorio::test_minimo_cero_no_desactiva_el_rango", "py:test_catalogo_laboratorio::test_un_solo_limite",
      "py:test_catalogo_laboratorio::test_cero_es_un_valor"]),
    ("CP-052", "Laboratorio", "Medio", "Editar un resultado", "No da error y la interpretación no se duplica",
     ["py:test_catalogo_laboratorio::test_editar_un_resultado_no_duplica_la_interpretacion"]),
    ("CP-053", "Laboratorio", "Medio", "Importar resultados desde Excel",
     "Vista previa explica cada error; confirmar crea un examen evaluado; reimportar no duplica",
     ["py:test_importacion_laboratorio::test_vista_previa_no_guarda_y_explica_cada_error",
      "py:test_importacion_laboratorio::test_confirmar_crea_un_examen_con_sus_resultados_evaluados",
      "py:test_importacion_laboratorio::test_reimportar_el_mismo_archivo_no_duplica"]),
    # ── Vacunas ──
    ("CP-060", "Vacunas", "Medio", "Más de 200 vacunas", "El listado y las cifras cuentan todas, con los filtros",
     ["py:test_vacunas_listado_servidor::test_el_total_es_el_real_aunque_pase_de_200",
      "py:test_vacunas_listado_servidor::test_resumen_cuenta_todo_con_los_mismos_filtros"]),
    ("CP-061", "Vacunas", "Medio", "Corregir el lote de una vacuna antigua", "Se puede (la próxima dosis ya pasada no la invalida)",
     ["py:test_vacunas_listado_servidor::test_un_registro_antiguo_se_puede_corregir",
      "py:test_vacunas_listado_servidor::test_al_registrar_la_proxima_dosis_tiene_que_ser_futura"]),
    # ── Notas, triaje ──
    ("CP-070", "Notas de evolución", "Medio", "Unificar «evoluciones» en notas", "Cada evolución pasa a nota sin duplicarse; API vieja de solo lectura",
     ["py:test_unificar_evoluciones::test_cada_evolucion_pasa_a_ser_una_nota_y_no_se_duplica",
      "py:test_unificar_evoluciones::test_la_api_vieja_queda_de_solo_lectura"]),
    ("CP-071", "Triaje", "Alto", "Registrar un triaje con prioridad", "La prioridad elegida se guarda y se puede completar",
     ["py:test_triaje_listado_servidor::test_la_prioridad_del_formulario_se_guarda", "py:test_triaje_listado_servidor::test_completar_con_patch"]),
    # ── Calculadoras ──
    ("CP-080", "Calculadoras", "Alto", "Diabetes gestacional (PTOG 75 g, IADPSG)", "Un valor alterado basta; ayunas ≥ 126 = diabetes manifiesta",
     ["js:diabetesGestacional::UN solo valor alterado", "js:diabetesGestacional::ayunas ≥ 126"]),
    ("CP-081", "Calculadoras", "Alto", "Riesgo de preeclampsia", "Odds × LR, nunca > 100 %; los dos endpoints coinciden",
     ["py:test_preeclampsia_unificada::test_se_aplica_sobre_odds", "py:test_preeclampsia_unificada::test_los_dos_endpoints_dan_el_mismo_riesgo"]),
    ("CP-082", "Calculadoras", "Medio", "Índice de líquido amniótico", "Una sola clasificación en modelo y calculadora",
     ["py:test_ila_unico::test_modelo_y_calculadora_coinciden", "py:test_ila_unico::test_bordes"]),
    # ── Seguridad, auditoría, permisos ──
    ("CP-090", "Permisos", "Alto", "Médico nuevo y base recién creada", "Ve lo clínico sin asignar nada a mano; grupos con permisos tras migrar",
     ["py:test_permisos_por_rol::test_un_medico_nuevo_ve_lo_clinico_sin_asignar_nada_a_mano",
      "py:test_permisos_por_rol::test_grupos_vacios_se_reparan_al_migrar"]),
    ("CP-091", "Permisos", "Alto", "Recepción y enfermería", "Recepción solo pacientes y citas; enfermería sin partos ni reportes",
     ["py:test_permisos_por_rol::test_recepcion_solo_pacientes_y_citas", "py:test_permisos_por_rol::test_enfermeria_no_tiene_partos_ni_reportes"]),
    ("CP-092", "Auditoría", "Alto", "Sesiones y exportaciones auditadas", "Login/logout en la misma sesión; cada Excel queda auditado",
     ["py:test_sesiones_auditoria::test_login_y_logout_comparten_sesion", "py:test_exportaciones_excel::test_la_exportacion_queda_auditada",
      "py:test_admin_masivo_auditado::test_la_accion_masiva_se_audita"]),
    # ── Operación ──
    ("CP-100", "Operación", "Alto", "Recordatorio de una cita a las 23:00 (hora de Bolivia)", "Se envía (antes la fecha UTC lo saltaba)",
     ["py:test_notificaciones_clinicas::test_recordatorio_de_una_cita_a_las_23_horas_locales",
      "py:test_notificaciones_clinicas::test_controles_del_mes_a_las_21_del_ultimo_dia"]),
    ("CP-112", "Permisos", "Alto", "Otro funcionario: cargo «Obstetriz» sobre el rol médico sin laboratorio",
     "Lo crea el administrador desde la pantalla; quien lo tiene ve Partos y no Laboratorio, y la API le responde 403. "
     "Un cargo no puede agregar módulos a su rol",
     ["py:test_cargos::test_un_cargo_no_puede_agregar_modulos_a_su_rol",
      "py:test_cargos::test_el_usuario_toma_el_rol_base_y_solo_los_modulos_del_cargo",
      "py:test_cargos::test_la_api_rechaza_el_modulo_que_el_cargo_no_incluye",
      "py:test_cargos::test_solo_el_administrador_crea_cargos",
      "py:test_cargos::test_un_cargo_con_usuarios_no_se_borra",
      "js:FormularioRol::",
      "e2e:1. el administrador crea el cargo sin laboratorio",
      "e2e:2. un usuario nuevo con ese cargo entra: ve Partos, no Laboratorio, y la API lo bloquea"]),
    ("CP-108", "Operación", "Alto", "Notificación en tiempo real con la API y los WebSockets en procesos distintos",
     "Con Redis cruza de un proceso a otro; producción sin Redis avisa al arrancar (antes la alerta no llegaba nunca)",
     ["py:test_capa_canales_produccion::test_mensaje_cruza_entre_dos_capas_independientes",
      "py:test_capa_canales_produccion::test_produccion_sin_redis_avisa",
      "py:test_capa_canales_produccion::test_produccion_con_redis_no_avisa"]),
    ("CP-101", "Operación", "Alto", "Lanzadores .bat", "Cada comando y opción existe", ["py:test_lanzadores_bat::test_cada_comando_y_opcion_existen"]),
    ("CP-102", "Operación", "Alto", "Ninguna pantalla responde 500", "≈330 rutas GET sin error; estadísticas con base vacía sin error",
     ["py:test_rutas_sin_500::test_ninguna_ruta_get_da_500", "py:test_estadisticas_base_vacia::test_ninguna_da_500"]),
    ("CP-103", "Datos demo", "Medio", "Datos de demostración realistas", "Válidos contra el modelo y sin fechas futuras",
     ["py:test_seed_carga::test_paciente_con_valores_del_generador_es_valida",
      "py:test_seed_carga::test_vacunas_y_laboratorios_caen_dentro_del_embarazo_y_antes_de_hoy"]),
    ("CP-104", "Login", "Alto", "Iniciar sesión y abrir el sistema sin errores de JavaScript", "Entra al panel",
     ["e2e:1. registrar la paciente con el asistente"]),
    ("CP-037", "Ecografía", "Medio", "Adjuntar un archivo a una ecografía",
     "El tipo se deduce del contenido; un HTML disfrazado de PDF se rechaza; recepción no ve adjuntos",
     ["py:test_archivos_ecografia::test_subir_un_png_deduce_el_tipo_y_guarda_quien_lo_subio",
      "py:test_archivos_ecografia::test_un_html_disfrazado_de_pdf_se_rechaza",
      "py:test_archivos_ecografia::test_recepcion_no_ve_adjuntos_clinicos"]),
    ("CP-105", "Reportes", "Medio", "Centro de reportes y KPIs", "KPIs con su forma; estadísticas sin error aun con base vacía; «del mes» en hora local",
     ["py:test_kpis_dashboard::test_forma_y_valores", "py:test_estadisticas_base_vacia::test_ninguna_da_500",
      "py:test_notificaciones_clinicas::test_controles_del_mes_a_las_21_del_ultimo_dia"]),
    ("CP-106", "Exportación", "Medio", "Exportar un listado a Excel", "Respeta los filtros, usa etiquetas legibles y queda auditado",
     ["py:test_exportaciones_excel::test_el_excel_respeta_el_filtro_y_usa_etiquetas",
      "py:test_controles_listado_servidor::test_excel_respeta_filtros_y_queda_auditado",
      "py:test_listados_servidor_embarazos_citas_pacientes::test_excel_con_filtros_etiquetas_y_auditado"]),
    ("CP-038", "IA (imagen)", "Alto", "Segmentación de cabeza: la API mide igual que el entrenamiento",
     "En 40 cabezas de otro hospital (HC18) la HC por la API coincide con el entrenamiento (±0,5 mm) y el error es < 5 %",
     ["ia:test_segmentacion::test_la_api_mide_igual_que_el_entrenamiento_en_hc18",
      "ia:test_segmentacion::test_sin_tamano_de_pixel_no_da_milimetros",
      "ia:test_segmentacion::test_torax_de_prueba_da_indice_en_rango_y_metricas"]),
    ("CP-039", "IA (imagen)", "Alto", "Análisis completo con las redes medidas (reemplazo de la B4)",
     "Plano → red de su plano → medidas con margen; un plano sin red no inventa medidas; las rutas de la B4 no existen",
     ["ia:test_segmentacion::test_analisis_completo_de_una_cabeza",
      "ia:test_segmentacion::test_un_plano_sin_red_no_inventa_medidas",
      "ia:test_segmentacion::test_las_rutas_de_la_b4_ya_no_existen",
      "py:test_informe_redes_medidas::test_alarma_cerebral_no_queda_como_normal",
      "py:test_informe_redes_medidas::test_indice_cardiotoracico_alto_pide_revision"]),
    ("CP-042", "Partos", "Alto", "Epicrisis: redactar, validar y firmar",
     "CIE-10 válido, egreso posterior al parto; firmada no se edita ni se borra; reabrir solo el administrador, auditado",
     ["py:test_epicrisis_y_capurro::test_firmar_bloquea_edicion_y_reabrir_solo_admin",
      "py:test_epicrisis_y_capurro::test_cie10_invalido_y_egreso_antes_del_parto",
      "py:test_epicrisis_y_capurro::test_campos_propios_del_hospital",
      "py:test_epicrisis_y_capurro::test_pdf",
      "e2e:3. epicrisis: redactar con la sugerencia y firmar"]),
    ("CP-043", "Partos", "Medio", "Edad gestacional del recién nacido (Capurro / Ballard)",
     "Capurro 204 + puntos = 39,7 s; Ballard −10 → 20 s y 50 → 44 s; puntos inexistentes se rechazan",
     ["py:test_epicrisis_y_capurro::test_capurro_formula", "py:test_epicrisis_y_capurro::test_ballard_extremos",
      "py:test_epicrisis_y_capurro::test_capurro_incompleto_400",
      "e2e:2. Capurro del recién nacido: 39,7 semanas, a término"]),
    ("CP-044", "Partos", "Alto", "Partograma con líneas de alerta y acción de la OMS",
     "Fase activa desde 4 cm; cruza alerta con < 1 cm/h y acción 4 h después; el tacto registrado aparece en la tabla y el PDF",
     ["js:partogramaUtils::", "py:test_epicrisis_y_capurro::test_pdf_con_los_campos_reales",
      "e2e:1. partograma: registrar un tacto y verlo en la tabla"]),
    ("CP-045", "Partos", "Medio", "Ángulo de progresión con ecografía intraparto (IUGC 2024)",
     "La API mide igual que el entrenamiento (±0,5°); error medio ≈ 7° frente al experto; ángulo imposible no se guarda; IA caída → 503",
     ["ia:test_segmentacion::test_angulo_de_progresion_igual_que_el_entrenamiento",
      "py:test_angulo_progresion::test_devuelve_la_medida_y_queda_auditado",
      "py:test_angulo_progresion::test_microservicio_caido_503_con_mensaje",
      "py:test_angulo_progresion::test_partograma_rechaza_un_angulo_imposible",
      "e2e:1. partograma: registrar un tacto y verlo en la tabla"]),
    ("CP-054", "Laboratorio", "Medio", "Importar resultados desde CSV con otros encabezados",
     "CSV con punto y coma en Latin-1 se reconoce por sinónimos; si no, pide el mapeo y luego importa",
     ["py:test_importacion_laboratorio_csv::test_csv_punto_y_coma_latin1_con_sinonimos",
      "py:test_importacion_laboratorio_csv::test_encabezados_desconocidos_piden_mapeo_y_luego_importan",
      "py:test_importacion_laboratorio_csv::test_archivo_binario_no_valido_400"]),
    ("CP-055", "Laboratorio", "Medio", "Deshacer una importación completa",
     "Borra lo que creó el lote (y no lo cargado aparte), pide motivo, queda auditado y no se anula dos veces",
     ["py:test_importacion_laboratorio_csv::test_deshacer_lote_borra_todo_lo_que_creo",
      "py:test_importacion_laboratorio_csv::test_deshacer_no_borra_resultados_cargados_aparte",
      "e2e:4. laboratorio: importar un CSV con otros encabezados y deshacerlo"]),
    ("CP-083", "IA (supervisado)", "Alto", "Cardiotocografía: normal, sospechosa o patológica",
     "Exactitud ≥ 90 % y sensibilidad patológica ≥ 85 % en 423 registros reales no vistos; faltan datos → 409 sin clase",
     ["py:test_cardiotocografia::test_metricas_reales_en_prueba",
      "py:test_cardiotocografia::test_clasifica_un_registro_normal",
      "py:test_cardiotocografia::test_faltan_datos_409_sin_clase",
      "e2e:5. cardiotocografía: un trazado normal se clasifica «Normal»"]),
    ("CP-084", "IA (supervisado)", "Medio", "Peso al nacer medido contra el bebé real",
     "La predicción se cierra sola con el peso real (error del modelo y de Hadlock); con gemelos no se cierra",
     ["py:test_cierre_prediccion_peso::test_se_cierra_con_el_peso_real",
      "py:test_cierre_prediccion_peso::test_gemelos_no_se_cierra",
      "py:test_cierre_prediccion_peso::test_desempeno_con_nacimientos_reales"]),
    ("CP-093", "Seguridad", "Alto", "Todo permiso que pide la pantalla existe",
     "Ningún botón ni ruta pide un permiso inexistente (antes médicos y enfermeras no veían «Nuevo examen» ni «Nuevo control»)",
     ["py:test_permisos_frontend_existen::test_cada_permiso_pedido_existe"]),
    ("CP-107", "Reportes", "Medio", "Natalidad, morbilidad e IA con el período elegido",
     "Cifras reales del período (cesáreas, bajo peso, pretérmino, Apgar < 7); período sin partos → ceros, no ejemplos; Excel",
     ["py:test_reportes_natalidad_ia::test_cifras_del_periodo",
      "py:test_reportes_natalidad_ia::test_periodo_sin_partos_da_ceros_no_inventa",
      "py:test_reportes_natalidad_ia::test_excel", "py:test_reportes_natalidad_ia::test_reporte_ia_sin_microservicio",
      "js:rangoReportes::"]),
    ("CP-111", "Rendimiento", "Alto", "Latencia de la API con la configuración de producción",
     "Percentil 95 < 200 ms en los 16 listados y reportes (waitress, demo de 3.200 pacientes)",
     ["lat:"]),
    ("CP-110", "Rendimiento", "Alto", "Abrir cada listado con la demo de 3.200 pacientes",
     "Menos de 5 s y 15 peticiones o menos por pantalla, sin errores JS ni 500",
     [f"perf:/dashboard/{r}" for r in ("pacientes", "embarazos", "controles", "ecografias", "partos",
                                       "laboratorio", "citas", "vacunas", "triaje", "notas-evolucion")]),
]


def _ejecutar(cmd, cwd, env=None):
    r = subprocess.run(cmd, cwd=cwd, env={**os.environ, **(env or {})}, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def resultados_pytest(python, cwd, archivos, prefijo):
    """{prefijo:archivo::prueba -> (estado, segundos)} desde un JUnit XML."""
    xml = Path(tempfile.mkstemp(suffix=".xml")[1])
    _ejecutar([str(python), "-m", "pytest", *archivos, "-q", "--no-cov", "-p", "no:randomly", f"--junitxml={xml}"], cwd)
    salida = {}
    if xml.exists() and xml.stat().st_size:
        for caso in ET.parse(xml).getroot().iter("testcase"):
            archivo = caso.get("classname", "").split(".")
            stem = next((p for p in archivo if p.startswith("test_")), archivo[-1])
            estado = "PASA"
            if caso.find("failure") is not None or caso.find("error") is not None:
                estado = "FALLA"
            elif caso.find("skipped") is not None:
                estado = "OMITIDA"
            salida[f"{prefijo}:{stem}::{caso.get('name')}"] = (estado, float(caso.get("time", 0)))
    return salida


def resultados_jest():
    archivo = Path(tempfile.mkstemp(suffix=".json")[1])
    _ejecutar(["npx.cmd", "react-scripts", "test", "--watchAll=false", "--json", f"--outputFile={archivo}"],
              FRONT, {"CI": "true"})
    salida = {}
    if archivo.exists() and archivo.stat().st_size:
        for suite in json.loads(archivo.read_text(encoding="utf-8")).get("testResults", []):
            stem = Path(suite["name"]).name.split(".test")[0]
            for a in suite.get("assertionResults", []):
                salida[f"js:{stem}::{a['title']}"] = ("PASA" if a["status"] == "passed" else "FALLA",
                                                     (a.get("duration") or 0) / 1000)
    return salida


def resultados_e2e():
    _, texto = _ejecutar(["npx.cmd", "playwright", "test", "--reporter=json"], E2E)
    salida = {}
    try:
        datos = json.loads(texto[texto.index("{"):texto.rindex("}") + 1])
    except ValueError:
        return salida

    def recorrer(suite):
        for spec in suite.get("specs", []):
            r = (spec.get("tests") or [{}])[0].get("results") or [{}]
            estado = {"passed": "PASA", "skipped": "OMITIDA"}.get(r[-1].get("status"), "FALLA")
            salida[f"e2e:{spec['title']}"] = (estado, r[-1].get("duration", 0) / 1000)
        for hija in suite.get("suites", []):
            recorrer(hija)

    for s in datos.get("suites", []):
        recorrer(s)
    return salida


def resultados_rendimiento():
    """perf:<ruta> → PASA si carga en < 5 s, con ≤ 15 peticiones y sin errores."""
    _, texto = _ejecutar(["node", "recorrido_listados.js"], E2E)
    salida = {}
    for linea in texto.splitlines():
        partes = linea.split()
        if not partes or not partes[0].startswith("/dashboard") or "ms" not in partes:
            continue
        ruta, ms = partes[0], int(partes[1])
        peticiones = int(partes[partes.index("API") + 1])
        ok = linea.rstrip().endswith("ok") and ms < 5000 and peticiones <= 15
        salida[f"perf:{ruta}"] = ("PASA" if ok else "FALLA", ms / 1000)
    return salida


def resultados_latencia():
    """lat: → el último informe de medir_latencia_api.py con la configuración de
    producción (waitress). No se vuelve a medir aquí: el servidor de esta corrida
    es el de desarrollo. PASA si todos los endpoints tienen p95 < 200 ms."""
    informe = Path(__file__).resolve().parent / "reports" / "latencia_api.json"
    if not informe.exists():
        return {}
    d = json.loads(informe.read_text(encoding="utf-8"))
    ok = d.get("total") and d["cumplen"] == d["total"] and not d.get("errores")
    return {f"lat:{d.get('fecha')} {d['cumplen']}/{d['total']}": ("PASA" if ok else "FALLA", 0.0)}


def buscar(resultados, ref):
    """Coincidencia exacta, o por prefijo del título (Jest/E2E usan frases largas)."""
    if ref in resultados:
        return resultados[ref]
    for clave, valor in resultados.items():
        if clave.startswith(ref):
            return valor
    return None


def main():
    con_e2e = "--sin-e2e" not in sys.argv
    archivos_py = sorted({f"tests/{r[3:].split('::')[0]}.py" for *_, refs in CASOS for r in refs if r.startswith("py:")})
    archivos_ia = sorted({f"{r[3:].split('::')[0]}.py" for *_, refs in CASOS for r in refs if r.startswith("ia:")})
    print("Backend…", flush=True)
    resultados = resultados_pytest(PY_BACKEND, BACKEND, archivos_py, "py")
    print("Microservicio de IA…", flush=True)
    resultados |= resultados_pytest(PY_IA, IA, archivos_ia, "ia")
    print("Frontend (Jest)…", flush=True)
    resultados |= resultados_jest()
    if con_e2e:
        print("E2E (Playwright)…", flush=True)
        resultados |= resultados_e2e()
        _ejecutar([str(PY_BACKEND), "manage.py", "limpiar_datos_e2e", "--schema=clinica_demo"], BACKEND)
        print("Rendimiento de los listados…", flush=True)
        resultados |= resultados_rendimiento()
    resultados |= resultados_latencia()

    filas, cuenta = [], {"PASA": 0, "FALLA": 0, "SIN EJECUTAR": 0}
    for cid, modulo, riesgo, caso, esperado, refs in sorted(CASOS, key=lambda c: c[0]):
        estados = []
        for ref in refs:
            r = buscar(resultados, ref)
            estados.append("SIN EJECUTAR" if r is None or r[0] == "OMITIDA" else r[0])
        final = "FALLA" if "FALLA" in estados else "SIN EJECUTAR" if "SIN EJECUTAR" in estados else "PASA"
        cuenta[final] += 1
        pruebas = "<br>".join(f"`{r}`" + ("" if e == "PASA" else f" **{e}**") for r, e in zip(refs, estados, strict=True))
        obtenido = {"PASA": "✅ Pasa: obtenido = esperado", "FALLA": "❌ Falla", "SIN EJECUTAR": "⚪ Sin ejecutar"}[final]
        filas.append(f"| <a id=\"{cid.lower()}\"></a>{cid} | {modulo} | {riesgo} | {caso} | {esperado} | {obtenido} | {pruebas} |")

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    SALIDA.write_text(f"""# Casos de prueba — esperado frente a obtenido

Generado el {fecha} por `quality-assurance/casos_de_prueba.py`, que **ejecuta**
las pruebas de cada caso. No editar a mano: volver a correr el script.
Plan de QA y de pruebas: [QA_PLAN_DE_PRUEBAS.md](QA_PLAN_DE_PRUEBAS.md) ·
Requisitos, historias de usuario y casos de uso: [sistema/](sistema/README.md).

**Resultado: {cuenta['PASA']} de {len(CASOS)} casos pasan** · {cuenta['FALLA']} fallan · {cuenta['SIN EJECUTAR']} sin ejecutar
{'' if con_e2e else '(esta corrida se hizo sin E2E ni rendimiento)'}

Prefijos: `py:` backend (pytest) · `ia:` microservicio de IA (pytest) · `js:` frontend (Jest) ·
`e2e:` navegador (Playwright) · `perf:` tiempo y peticiones medidos en el navegador ·
`lat:` último informe de latencia de la API (`medir_latencia_api.py`, configuración de producción).

| ID | Módulo | Riesgo | Caso | Resultado esperado | Obtenido | Pruebas automáticas |
|---|---|---|---|---|---|---|
{chr(10).join(filas)}
""", encoding="utf-8")
    print(f"\n{cuenta['PASA']}/{len(CASOS)} casos pasan · {cuenta['FALLA']} fallan · {cuenta['SIN EJECUTAR']} sin ejecutar")
    print(f"Escrito {SALIDA}")
    return 1 if cuenta["FALLA"] else 0


if __name__ == "__main__":
    sys.exit(main())
