--
-- PostgreSQL database dump
--

\restrict 1BLFZaoBSCyoonfpWAxC3QOq8TNqZxrilXEnm9rseArMJd39qq27FzDR2iXKSfS

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

-- Started on 2025-10-17 03:53:43

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 340 (class 1255 OID 18578)
-- Name: calcular_edad(date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_edad(fecha_nac date) RETURNS integer
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM AGE(fecha_nac));
END;
$$;


ALTER FUNCTION public.calcular_edad(fecha_nac date) OWNER TO postgres;

--
-- TOC entry 339 (class 1255 OID 18580)
-- Name: calcular_edad_gestacional(date, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_edad_gestacional(fum date, fecha_actual date DEFAULT CURRENT_DATE) RETURNS TABLE(semanas integer, dias integer, texto character varying)
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    total_dias INTEGER;
    sem INTEGER;
    di INTEGER;
BEGIN
    total_dias := fecha_actual - fum;
    sem := total_dias / 7;
    di := total_dias % 7;
    
    RETURN QUERY SELECT sem, di, CONCAT(sem, ' semanas + ', di, ' días')::VARCHAR;
END;
$$;


ALTER FUNCTION public.calcular_edad_gestacional(fum date, fecha_actual date) OWNER TO postgres;

--
-- TOC entry 324 (class 1255 OID 18579)
-- Name: calcular_fpp(date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_fpp(fum date) RETURNS date
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    RETURN fum + INTERVAL '280 days';
END;
$$;


ALTER FUNCTION public.calcular_fpp(fum date) OWNER TO postgres;

--
-- TOC entry 343 (class 1255 OID 18640)
-- Name: calcular_ganancia_peso(numeric, numeric); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_ganancia_peso(peso_actual numeric, peso_pregestacional numeric) RETURNS numeric
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    RETURN ROUND(peso_actual - peso_pregestacional, 2);
END;
$$;


ALTER FUNCTION public.calcular_ganancia_peso(peso_actual numeric, peso_pregestacional numeric) OWNER TO postgres;

--
-- TOC entry 342 (class 1255 OID 18638)
-- Name: calcular_imc(numeric, numeric); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_imc(peso numeric, altura numeric) RETURNS TABLE(imc numeric, clasificacion character varying)
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    altura_m DECIMAL;
    imc_calculado DECIMAL;
    clasif VARCHAR;
BEGIN
    altura_m := altura / 100;
    imc_calculado := ROUND(peso / (altura_m * altura_m), 2);
    
    IF imc_calculado < 18.5 THEN
        clasif := 'Bajo peso';
    ELSIF imc_calculado < 25 THEN
        clasif := 'Normal';
    ELSIF imc_calculado < 30 THEN
        clasif := 'Sobrepeso';
    ELSE
        clasif := 'Obesidad';
    END IF;
    
    RETURN QUERY SELECT imc_calculado, clasif;
END;
$$;


ALTER FUNCTION public.calcular_imc(peso numeric, altura numeric) OWNER TO postgres;

--
-- TOC entry 329 (class 1255 OID 18639)
-- Name: calcular_pam(integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_pam(sistolica integer, diastolica integer) RETURNS numeric
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    RETURN ROUND((sistolica + (2 * diastolica)) / 3.0, 2);
END;
$$;


ALTER FUNCTION public.calcular_pam(sistolica integer, diastolica integer) OWNER TO postgres;

--
-- TOC entry 355 (class 1255 OID 19357)
-- Name: calcular_peso_fetal_estimado(numeric, numeric, numeric, numeric); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_peso_fetal_estimado(dbp numeric DEFAULT NULL::numeric, cc numeric DEFAULT NULL::numeric, ca numeric DEFAULT NULL::numeric, lf numeric DEFAULT NULL::numeric) RETURNS numeric
    LANGUAGE plpgsql
    AS $$
DECLARE
    peso numeric;
BEGIN
    -- Usar directamente la fórmula Hadlock que sabemos que funciona
    IF dbp IS NOT NULL AND cc IS NOT NULL AND ca IS NOT NULL AND lf IS NOT NULL THEN
        peso := calcular_peso_fetal_hadlock(dbp, cc, ca, lf);
    ELSE
        -- Si faltan parámetros, devolver NULL o valor por defecto
        RAISE NOTICE 'Faltan parámetros para cálculo completo, usando valor estimado basado en CA';
        IF ca IS NOT NULL THEN
            -- Fórmula aproximada basada en circunferencia abdominal
            peso := 0.143 * POWER(ca / 10, 2.6);
        ELSE
            RETURN NULL;
        END IF;
    END IF;
    
    RETURN peso;
END;
$$;


ALTER FUNCTION public.calcular_peso_fetal_estimado(dbp numeric, cc numeric, ca numeric, lf numeric) OWNER TO postgres;

--
-- TOC entry 5885 (class 0 OID 0)
-- Dependencies: 355
-- Name: FUNCTION calcular_peso_fetal_estimado(dbp numeric, cc numeric, ca numeric, lf numeric); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.calcular_peso_fetal_estimado(dbp numeric, cc numeric, ca numeric, lf numeric) IS 'Calcula peso fetal estimado usando fórmula Hadlock o alternativa';


--
-- TOC entry 352 (class 1255 OID 19354)
-- Name: calcular_peso_fetal_hadlock(numeric, numeric, numeric, numeric); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_peso_fetal_hadlock(dbp numeric, cc numeric, ca numeric, lf numeric) RETURNS numeric
    LANGUAGE plpgsql
    AS $$
DECLARE
    log_peso numeric;
    peso numeric;
    -- Factores de conversión para evitar underflow
    dbp_cm numeric;
    cc_cm numeric;
    ca_cm numeric;
    lf_cm numeric;
BEGIN
    -- CONVERTIR mm a cm (¡ESTO ES CLAVE!)
    dbp_cm := dbp / 10;
    cc_cm := cc / 10;
    ca_cm := ca / 10;
    lf_cm := lf / 10;
    
    -- Fórmula de Hadlock VERIFICADA (usando cm en lugar de mm)
    -- Log10(EFW) = 1.3596 + 0.0064(CC) + 0.0424(AC) + 0.174(FL) + 0.00061(BPD*AC) - 0.00386(AC*FL)
    -- NOTA: Las medidas deben estar en CENTÍMETROS, no en milímetros
    log_peso := 1.3596 + 
                (0.0064 * cc_cm) + 
                (0.0424 * ca_cm) + 
                (0.174 * lf_cm) + 
                (0.00061 * dbp_cm * ca_cm) - 
                (0.00386 * ca_cm * lf_cm);
    
    peso := POWER(10, log_peso);
    
    RAISE NOTICE 'Cálculo intermedio - DBP: %cm, CC: %cm, CA: %cm, LF: %cm, LogPeso: %, Peso: %g', 
        dbp_cm, cc_cm, ca_cm, lf_cm, log_peso, peso;
    
    -- Validar rango razonable
    IF peso < 200 THEN
        RAISE WARNING 'Peso fetal calculado bajo: %g, revisar parámetros', peso;
        peso := 200;
    ELSIF peso > 5000 THEN
        RAISE WARNING 'Peso fetal calculado alto: %g, revisar parámetros', peso;
        peso := 5000;
    END IF;
    
    RETURN ROUND(peso, 0);
END;
$$;


ALTER FUNCTION public.calcular_peso_fetal_hadlock(dbp numeric, cc numeric, ca numeric, lf numeric) OWNER TO postgres;

--
-- TOC entry 5886 (class 0 OID 0)
-- Dependencies: 352
-- Name: FUNCTION calcular_peso_fetal_hadlock(dbp numeric, cc numeric, ca numeric, lf numeric); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.calcular_peso_fetal_hadlock(dbp numeric, cc numeric, ca numeric, lf numeric) IS 'Calcula peso fetal estimado según fórmula de Hadlock (medidas en mm, resultado en gramos)';


--
-- TOC entry 353 (class 1255 OID 19355)
-- Name: calcular_peso_fetal_shepard(numeric, numeric); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_peso_fetal_shepard(dbp numeric, ca numeric) RETURNS numeric
    LANGUAGE plpgsql
    AS $$
DECLARE
    log_peso numeric;
    peso numeric;
    dbp_cm numeric;
    ca_cm numeric;
BEGIN
    -- Convertir a cm
    dbp_cm := dbp / 10;
    ca_cm := ca / 10;
    
    -- Fórmula de Shepard: Log10(EFW) = -1.7492 + 0.166(BPD) + 0.046(AC) - 0.002646(AC*BPD)
    log_peso := -1.7492 + 
                (0.166 * dbp_cm) + 
                (0.046 * ca_cm) - 
                (0.002646 * ca_cm * dbp_cm);
    
    peso := POWER(10, log_peso) * 1000; -- Convertir de kg a gramos
    
    RAISE NOTICE 'Shepard - DBP: %cm, CA: %cm, Peso: %g', dbp_cm, ca_cm, peso;
    
    RETURN ROUND(peso, 0);
END;
$$;


ALTER FUNCTION public.calcular_peso_fetal_shepard(dbp numeric, ca numeric) OWNER TO postgres;

--
-- TOC entry 354 (class 1255 OID 19356)
-- Name: calcular_peso_fetal_simplificado(numeric); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_peso_fetal_simplificado(ca numeric) RETURNS numeric
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Fórmula simplificada basada en circunferencia abdominal
    -- Para CA ~240mm (24cm) en 28 semanas -> ~1150g
    RETURN ROUND(POWER(ca / 10, 2.6) * 0.143, 0);
END;
$$;


ALTER FUNCTION public.calcular_peso_fetal_simplificado(ca numeric) OWNER TO postgres;

--
-- TOC entry 349 (class 1255 OID 19343)
-- Name: crear_notificacion(integer, character varying, character varying, text, character varying, text, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.crear_notificacion(p_usuario_id integer, p_tipo_notificacion character varying, p_titulo character varying, p_mensaje text, p_prioridad character varying DEFAULT 'normal'::character varying, p_accion_url text DEFAULT NULL::text, p_expiracion timestamp without time zone DEFAULT NULL::timestamp without time zone) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_notificacion_id integer;
BEGIN
    INSERT INTO notificaciones (
        usuario_id,
        tipo_notificacion,
        titulo,
        mensaje,
        prioridad,
        accion_url,
        expiracion
    ) VALUES (
        p_usuario_id,
        p_tipo_notificacion,
        p_titulo,
        p_mensaje,
        p_prioridad,
        p_accion_url,
        p_expiracion
    ) RETURNING id INTO v_notificacion_id;
    
    RETURN v_notificacion_id;
END;
$$;


ALTER FUNCTION public.crear_notificacion(p_usuario_id integer, p_tipo_notificacion character varying, p_titulo character varying, p_mensaje text, p_prioridad character varying, p_accion_url text, p_expiracion timestamp without time zone) OWNER TO postgres;

--
-- TOC entry 5887 (class 0 OID 0)
-- Dependencies: 349
-- Name: FUNCTION crear_notificacion(p_usuario_id integer, p_tipo_notificacion character varying, p_titulo character varying, p_mensaje text, p_prioridad character varying, p_accion_url text, p_expiracion timestamp without time zone); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.crear_notificacion(p_usuario_id integer, p_tipo_notificacion character varying, p_titulo character varying, p_mensaje text, p_prioridad character varying, p_accion_url text, p_expiracion timestamp without time zone) IS 'Crea una nueva notificación para un usuario';


--
-- TOC entry 348 (class 1255 OID 19342)
-- Name: establecer_configuracion(character varying, text, character varying, character varying, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.establecer_configuracion(p_clave character varying, p_valor text, p_tipo_dato character varying DEFAULT 'texto'::character varying, p_categoria character varying DEFAULT 'general'::character varying, p_descripcion text DEFAULT NULL::text) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO configuraciones_sistema (clave, valor, tipo_dato, categoria, descripcion)
    VALUES (p_clave, p_valor, p_tipo_dato, p_categoria, p_descripcion)
    ON CONFLICT (clave) 
    DO UPDATE SET 
        valor = EXCLUDED.valor,
        tipo_dato = EXCLUDED.tipo_dato,
        categoria = EXCLUDED.categoria,
        descripcion = EXCLUDED.descripcion,
        fecha_actualizacion = CURRENT_TIMESTAMP;
END;
$$;


ALTER FUNCTION public.establecer_configuracion(p_clave character varying, p_valor text, p_tipo_dato character varying, p_categoria character varying, p_descripcion text) OWNER TO postgres;

--
-- TOC entry 5888 (class 0 OID 0)
-- Dependencies: 348
-- Name: FUNCTION establecer_configuracion(p_clave character varying, p_valor text, p_tipo_dato character varying, p_categoria character varying, p_descripcion text); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.establecer_configuracion(p_clave character varying, p_valor text, p_tipo_dato character varying, p_categoria character varying, p_descripcion text) IS 'Crea o actualiza una configuración del sistema';


--
-- TOC entry 344 (class 1255 OID 18641)
-- Name: evaluar_riesgo_presion(integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.evaluar_riesgo_presion(sistolica integer, diastolica integer) RETURNS character varying
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    IF sistolica >= 160 OR diastolica >= 110 THEN
        RETURN 'Critico - Preeclampsia Severa';
    ELSIF sistolica >= 140 OR diastolica >= 90 THEN
        RETURN 'Alto - Hipertension';
    ELSIF sistolica >= 120 OR diastolica >= 80 THEN
        RETURN 'Medio - Prehipertension';
    ELSE
        RETURN 'Normal';
    END IF;
END;
$$;


ALTER FUNCTION public.evaluar_riesgo_presion(sistolica integer, diastolica integer) OWNER TO postgres;

--
-- TOC entry 341 (class 1255 OID 18631)
-- Name: fn_auditoria_cambios(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.fn_auditoria_cambios() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO auditoria (usuario_id, accion, modulo, registro_id, datos_anteriores)
        VALUES (
            NULLIF(current_setting('app.current_user_id', true), '')::INTEGER,
            'DELETE',
            TG_TABLE_NAME,
            OLD.id,
            row_to_json(OLD)
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO auditoria (usuario_id, accion, modulo, registro_id, datos_anteriores, datos_nuevos)
        VALUES (
            NULLIF(current_setting('app.current_user_id', true), '')::INTEGER,
            'UPDATE',
            TG_TABLE_NAME,
            NEW.id,
            row_to_json(OLD),
            row_to_json(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO auditoria (usuario_id, accion, modulo, registro_id, datos_nuevos)
        VALUES (
            NULLIF(current_setting('app.current_user_id', true), '')::INTEGER,
            'INSERT',
            TG_TABLE_NAME,
            NEW.id,
            row_to_json(NEW)
        );
        RETURN NEW;
    END IF;
END;
$$;


ALTER FUNCTION public.fn_auditoria_cambios() OWNER TO postgres;

--
-- TOC entry 345 (class 1255 OID 18679)
-- Name: generar_id_clinico(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.generar_id_clinico() RETURNS character varying
    LANGUAGE plpgsql
    AS $$
DECLARE
    nuevo_id VARCHAR;
    anio VARCHAR;
    secuencia INTEGER;
BEGIN
    anio := TO_CHAR(CURRENT_DATE, 'YY');
    
    SELECT COALESCE(MAX(CAST(SUBSTRING(id_clinico FROM 4 FOR 6) AS INTEGER)), 0) + 1
    INTO secuencia
    FROM pacientes
    WHERE id_clinico LIKE 'HC-' || anio || '%';
    
    nuevo_id := 'HC-' || anio || LPAD(secuencia::TEXT, 6, '0');
    
    RETURN nuevo_id;
END;
$$;


ALTER FUNCTION public.generar_id_clinico() OWNER TO postgres;

--
-- TOC entry 338 (class 1255 OID 19341)
-- Name: obtener_configuracion(character varying); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.obtener_configuracion(p_clave character varying) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_valor text;
BEGIN
    SELECT valor INTO v_valor
    FROM configuraciones_sistema
    WHERE clave = p_clave;
    
    RETURN v_valor;
END;
$$;


ALTER FUNCTION public.obtener_configuracion(p_clave character varying) OWNER TO postgres;

--
-- TOC entry 5891 (class 0 OID 0)
-- Dependencies: 338
-- Name: FUNCTION obtener_configuracion(p_clave character varying); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.obtener_configuracion(p_clave character varying) IS 'Obtiene el valor de una configuración del sistema';


--
-- TOC entry 350 (class 1255 OID 19351)
-- Name: obtener_siguiente_numero_control(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.obtener_siguiente_numero_control(p_embarazo_id integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_max_numero integer;
BEGIN
    SELECT COALESCE(MAX(numero_control), 0) INTO v_max_numero
    FROM controles_prenatales
    WHERE embarazo_id = p_embarazo_id;
    
    RETURN v_max_numero + 1;
END;
$$;


ALTER FUNCTION public.obtener_siguiente_numero_control(p_embarazo_id integer) OWNER TO postgres;

--
-- TOC entry 5892 (class 0 OID 0)
-- Dependencies: 350
-- Name: FUNCTION obtener_siguiente_numero_control(p_embarazo_id integer); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.obtener_siguiente_numero_control(p_embarazo_id integer) IS 'Obtiene el siguiente número de control disponible para un embarazo';


--
-- TOC entry 351 (class 1255 OID 19352)
-- Name: sp_crear_control_prenatal(integer, integer, numeric, numeric, numeric, integer, integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_crear_control_prenatal(p_embarazo_id integer, p_paciente_id integer, p_peso_actual numeric, p_peso_pregestacional numeric, p_talla numeric, p_pa_sistolica integer, p_pa_diastolica integer, p_medico_id integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_control_id integer;
    v_imc numeric;
    v_clasificacion_imc character varying;
    v_pam numeric;
    v_ganancia_peso numeric;
    v_riesgo_pa character varying;
    v_numero_control integer;
BEGIN
    -- Obtener el siguiente número de control automáticamente
    SELECT obtener_siguiente_numero_control(p_embarazo_id) INTO v_numero_control;
    
    -- Calcular valores derivados
    SELECT * INTO v_imc, v_clasificacion_imc FROM calcular_imc(p_peso_actual, p_talla);
    v_pam := calcular_pam(p_pa_sistolica, p_pa_diastolica);
    v_ganancia_peso := calcular_ganancia_peso(p_peso_actual, p_peso_pregestacional);
    v_riesgo_pa := evaluar_riesgo_presion(p_pa_sistolica, p_pa_diastolica);
    
    -- Insertar control prenatal
    INSERT INTO controles_prenatales (
        embarazo_id,
        paciente_id,
        numero_control,
        peso_actual,
        peso_pregestacional,
        ganancia_peso,
        talla,
        imc_actual,
        clasificacion_imc,
        presion_arterial_sistolica,
        presion_arterial_diastolica,
        presion_arterial_media,
        medico_id
    ) VALUES (
        p_embarazo_id,
        p_paciente_id,
        v_numero_control,  -- ✅ Usar número automático
        p_peso_actual,
        p_peso_pregestacional,
        v_ganancia_peso,
        p_talla,
        v_imc,
        v_clasificacion_imc,
        p_pa_sistolica,
        p_pa_diastolica,
        v_pam,
        p_medico_id
    ) RETURNING id INTO v_control_id;
    
    -- Generar alertas si corresponde
    IF v_riesgo_pa != 'Normal' THEN
        INSERT INTO alertas_clinicas (
            control_prenatal_id,
            paciente_id,
            embarazo_id,
            tipo_alerta,
            nivel_urgencia,
            descripcion,
            parametro_afectado,
            valor_detectado,
            recomendacion
        ) VALUES (
            v_control_id,
            p_paciente_id,
            p_embarazo_id,
            'Presion Arterial Elevada',
            CASE 
                WHEN v_riesgo_pa LIKE 'Critico%' THEN 'critica'
                WHEN v_riesgo_pa LIKE 'Alto%' THEN 'alta'
                ELSE 'media'
            END,
            v_riesgo_pa,
            'Presion Arterial',
            p_pa_sistolica || '/' || p_pa_diastolica || ' mmHg',
            'Evaluacion medica inmediata, control de presion arterial, evaluar preeclampsia'
        );
    END IF;
    
    RETURN v_control_id;
END;
$$;


ALTER FUNCTION public.sp_crear_control_prenatal(p_embarazo_id integer, p_paciente_id integer, p_peso_actual numeric, p_peso_pregestacional numeric, p_talla numeric, p_pa_sistolica integer, p_pa_diastolica integer, p_medico_id integer) OWNER TO postgres;

--
-- TOC entry 5893 (class 0 OID 0)
-- Dependencies: 351
-- Name: FUNCTION sp_crear_control_prenatal(p_embarazo_id integer, p_paciente_id integer, p_peso_actual numeric, p_peso_pregestacional numeric, p_talla numeric, p_pa_sistolica integer, p_pa_diastolica integer, p_medico_id integer); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.sp_crear_control_prenatal(p_embarazo_id integer, p_paciente_id integer, p_peso_actual numeric, p_peso_pregestacional numeric, p_talla numeric, p_pa_sistolica integer, p_pa_diastolica integer, p_medico_id integer) IS 'Crea un nuevo control prenatal con número automático y cálculos integrados';


--
-- TOC entry 347 (class 1255 OID 18644)
-- Name: sp_registrar_ecografia_completa(integer, integer, character varying, integer, numeric, numeric, numeric, numeric); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sp_registrar_ecografia_completa(p_paciente_id integer, p_embarazo_id integer, p_tipo_ecografia character varying, p_medico_id integer, p_dbp numeric DEFAULT NULL::numeric, p_cc numeric DEFAULT NULL::numeric, p_ca numeric DEFAULT NULL::numeric, p_lf numeric DEFAULT NULL::numeric) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_ecografia_id integer;
    v_peso_estimado numeric;
BEGIN
    -- Insertar ecografía
    INSERT INTO ecografias (
        paciente_id,
        embarazo_id,
        tipo_ecografia,
        medico_id
    ) VALUES (
        p_paciente_id,
        p_embarazo_id,
        p_tipo_ecografia,
        p_medico_id
    ) RETURNING id INTO v_ecografia_id;
    
    -- Si hay datos de biometría, insertarlos
    IF p_ca IS NOT NULL THEN -- Al menos CA es requerida
        -- Calcular peso fetal con función mejorada
        v_peso_estimado := calcular_peso_fetal_estimado(p_dbp, p_cc, p_ca, p_lf);
        
        INSERT INTO biometria_fetal (
            ecografia_id,
            diametro_biparietal,
            circunferencia_cefalica,
            circunferencia_abdominal,
            longitud_femur,
            peso_fetal_estimado
        ) VALUES (
            v_ecografia_id,
            p_dbp,
            p_cc,
            p_ca,
            p_lf,
            v_peso_estimado
        );
        
        RAISE NOTICE 'Ecografía ID: % - Peso fetal estimado: % gramos', v_ecografia_id, v_peso_estimado;
    END IF;
    
    RETURN v_ecografia_id;
END;
$$;


ALTER FUNCTION public.sp_registrar_ecografia_completa(p_paciente_id integer, p_embarazo_id integer, p_tipo_ecografia character varying, p_medico_id integer, p_dbp numeric, p_cc numeric, p_ca numeric, p_lf numeric) OWNER TO postgres;

--
-- TOC entry 336 (class 1255 OID 18682)
-- Name: trg_actualizar_timestamp(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trg_actualizar_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.fecha_actualizacion := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_actualizar_timestamp() OWNER TO postgres;

--
-- TOC entry 346 (class 1255 OID 18680)
-- Name: trg_generar_id_clinico(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trg_generar_id_clinico() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.id_clinico IS NULL OR NEW.id_clinico = '' THEN
        NEW.id_clinico := generar_id_clinico();
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.trg_generar_id_clinico() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 244 (class 1259 OID 18144)
-- Name: alertas_clinicas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alertas_clinicas (
    id integer NOT NULL,
    control_prenatal_id integer,
    paciente_id integer NOT NULL,
    embarazo_id integer,
    tipo_alerta character varying(100) NOT NULL,
    nivel_urgencia character varying(50) NOT NULL,
    descripcion text NOT NULL,
    parametro_afectado character varying(100),
    valor_detectado character varying(100),
    valor_normal_esperado character varying(100),
    recomendacion text,
    estado character varying(50) DEFAULT 'pendiente'::character varying,
    revisada_por integer,
    fecha_revision timestamp without time zone,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT alertas_clinicas_estado_check CHECK (((estado)::text = ANY ((ARRAY['pendiente'::character varying, 'revisada'::character varying, 'resuelta'::character varying, 'desestimada'::character varying])::text[]))),
    CONSTRAINT alertas_clinicas_nivel_urgencia_check CHECK (((nivel_urgencia)::text = ANY ((ARRAY['baja'::character varying, 'media'::character varying, 'alta'::character varying, 'critica'::character varying])::text[])))
);


ALTER TABLE public.alertas_clinicas OWNER TO postgres;

--
-- TOC entry 5895 (class 0 OID 0)
-- Dependencies: 244
-- Name: TABLE alertas_clinicas; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.alertas_clinicas IS 'Alertas clínicas automáticas y manuales';


--
-- TOC entry 5896 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN alertas_clinicas.nivel_urgencia; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.alertas_clinicas.nivel_urgencia IS 'Prioridad de atención: baja, media, alta, critica';


--
-- TOC entry 243 (class 1259 OID 18143)
-- Name: alertas_clinicas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.alertas_clinicas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alertas_clinicas_id_seq OWNER TO postgres;

--
-- TOC entry 5898 (class 0 OID 0)
-- Dependencies: 243
-- Name: alertas_clinicas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.alertas_clinicas_id_seq OWNED BY public.alertas_clinicas.id;


--
-- TOC entry 281 (class 1259 OID 18689)
-- Name: analisis_ia_ecografias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.analisis_ia_ecografias (
    id integer NOT NULL,
    ecografia_id integer NOT NULL,
    modelo_utilizado character varying(100) NOT NULL,
    version_modelo character varying(50),
    resultado_analisis jsonb NOT NULL,
    confianza_general numeric(5,4),
    patologias_detectadas jsonb,
    recomendaciones text,
    validado_por_medico boolean DEFAULT false,
    medico_validador integer,
    fecha_validacion timestamp without time zone,
    comentarios_medico text,
    fecha_analisis timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.analisis_ia_ecografias OWNER TO postgres;

--
-- TOC entry 5900 (class 0 OID 0)
-- Dependencies: 281
-- Name: TABLE analisis_ia_ecografias; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.analisis_ia_ecografias IS 'Análisis automático de ecografías mediante IA';


--
-- TOC entry 280 (class 1259 OID 18688)
-- Name: analisis_ia_ecografias_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.analisis_ia_ecografias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.analisis_ia_ecografias_id_seq OWNER TO postgres;

--
-- TOC entry 5901 (class 0 OID 0)
-- Dependencies: 280
-- Name: analisis_ia_ecografias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.analisis_ia_ecografias_id_seq OWNED BY public.analisis_ia_ecografias.id;


--
-- TOC entry 252 (class 1259 OID 18274)
-- Name: anatomia_fetal; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.anatomia_fetal (
    id integer NOT NULL,
    ecografia_id integer NOT NULL,
    craneo character varying(50) DEFAULT 'normal'::character varying,
    cerebro character varying(50) DEFAULT 'normal'::character varying,
    cara character varying(50) DEFAULT 'normal'::character varying,
    cuello character varying(50) DEFAULT 'normal'::character varying,
    corazon character varying(50) DEFAULT 'normal'::character varying,
    torax character varying(50) DEFAULT 'normal'::character varying,
    abdomen character varying(50) DEFAULT 'normal'::character varying,
    columna character varying(50) DEFAULT 'normal'::character varying,
    extremidades_superiores character varying(50) DEFAULT 'normal'::character varying,
    extremidades_inferiores character varying(50) DEFAULT 'normal'::character varying,
    genitales character varying(50),
    sexo_fetal character varying(20),
    observaciones text,
    CONSTRAINT anatomia_fetal_sexo_fetal_check CHECK (((sexo_fetal)::text = ANY ((ARRAY['masculino'::character varying, 'femenino'::character varying, 'indeterminado'::character varying])::text[])))
);


ALTER TABLE public.anatomia_fetal OWNER TO postgres;

--
-- TOC entry 251 (class 1259 OID 18273)
-- Name: anatomia_fetal_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.anatomia_fetal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.anatomia_fetal_id_seq OWNER TO postgres;

--
-- TOC entry 5903 (class 0 OID 0)
-- Dependencies: 251
-- Name: anatomia_fetal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.anatomia_fetal_id_seq OWNED BY public.anatomia_fetal.id;


--
-- TOC entry 254 (class 1259 OID 18303)
-- Name: anexos_fetales; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.anexos_fetales (
    id integer NOT NULL,
    ecografia_id integer NOT NULL,
    placenta_posicion character varying(100),
    placenta_grado_maduracion integer,
    placenta_distancia_oci numeric(5,2),
    cordon_umbilical_arterias integer DEFAULT 2,
    cordon_umbilical_circular boolean DEFAULT false,
    liquido_amniotico_indice numeric(5,2),
    liquido_amniotico_clasificacion character varying(50),
    cuello_uterino_longitud numeric(5,2),
    cuello_uterino_estado character varying(100),
    observaciones text,
    CONSTRAINT anexos_fetales_liquido_amniotico_clasificacion_check CHECK (((liquido_amniotico_clasificacion)::text = ANY ((ARRAY['oligohidramnios'::character varying, 'normal'::character varying, 'polihidramnios'::character varying])::text[]))),
    CONSTRAINT anexos_fetales_placenta_grado_maduracion_check CHECK (((placenta_grado_maduracion >= 0) AND (placenta_grado_maduracion <= 3)))
);


ALTER TABLE public.anexos_fetales OWNER TO postgres;

--
-- TOC entry 253 (class 1259 OID 18302)
-- Name: anexos_fetales_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.anexos_fetales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.anexos_fetales_id_seq OWNER TO postgres;

--
-- TOC entry 5906 (class 0 OID 0)
-- Dependencies: 253
-- Name: anexos_fetales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.anexos_fetales_id_seq OWNED BY public.anexos_fetales.id;


--
-- TOC entry 234 (class 1259 OID 17996)
-- Name: antecedentes_familiares; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.antecedentes_familiares (
    id integer NOT NULL,
    paciente_id integer NOT NULL,
    parentesco character varying(100) NOT NULL,
    enfermedad character varying(255) NOT NULL,
    observaciones text
);


ALTER TABLE public.antecedentes_familiares OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 17995)
-- Name: antecedentes_familiares_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.antecedentes_familiares_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.antecedentes_familiares_id_seq OWNER TO postgres;

--
-- TOC entry 5909 (class 0 OID 0)
-- Dependencies: 233
-- Name: antecedentes_familiares_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.antecedentes_familiares_id_seq OWNED BY public.antecedentes_familiares.id;


--
-- TOC entry 236 (class 1259 OID 18014)
-- Name: antecedentes_ginecologicos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.antecedentes_ginecologicos (
    id integer NOT NULL,
    paciente_id integer NOT NULL,
    edad_menarca integer,
    ciclos_regulares boolean,
    duracion_ciclo integer,
    fecha_ultima_menstruacion date,
    dismenorrea boolean DEFAULT false,
    metodo_anticonceptivo character varying(150),
    fecha_ultima_citologia date,
    resultado_ultima_citologia text,
    fecha_ultima_mamografia date,
    resultado_ultima_mamografia text,
    cirugias_ginecologicas text,
    infecciones_transmision_sexual text,
    observaciones text,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    actualizado_por integer
);


ALTER TABLE public.antecedentes_ginecologicos OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 18013)
-- Name: antecedentes_ginecologicos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.antecedentes_ginecologicos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.antecedentes_ginecologicos_id_seq OWNER TO postgres;

--
-- TOC entry 5912 (class 0 OID 0)
-- Dependencies: 235
-- Name: antecedentes_ginecologicos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.antecedentes_ginecologicos_id_seq OWNED BY public.antecedentes_ginecologicos.id;


--
-- TOC entry 238 (class 1259 OID 18039)
-- Name: antecedentes_obstetricos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.antecedentes_obstetricos (
    id integer NOT NULL,
    paciente_id integer NOT NULL,
    gestas integer DEFAULT 0,
    partos integer DEFAULT 0,
    cesareas integer DEFAULT 0,
    abortos integer DEFAULT 0,
    ectopicos integer DEFAULT 0,
    hijos_vivos integer DEFAULT 0,
    hijos_muertos integer DEFAULT 0,
    complicaciones_previas text,
    observaciones text,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    actualizado_por integer
);


ALTER TABLE public.antecedentes_obstetricos OWNER TO postgres;

--
-- TOC entry 237 (class 1259 OID 18038)
-- Name: antecedentes_obstetricos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.antecedentes_obstetricos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.antecedentes_obstetricos_id_seq OWNER TO postgres;

--
-- TOC entry 5915 (class 0 OID 0)
-- Dependencies: 237
-- Name: antecedentes_obstetricos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.antecedentes_obstetricos_id_seq OWNED BY public.antecedentes_obstetricos.id;


--
-- TOC entry 232 (class 1259 OID 17971)
-- Name: antecedentes_personales; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.antecedentes_personales (
    id integer NOT NULL,
    paciente_id integer NOT NULL,
    alergias text,
    enfermedades_cronicas text,
    cirugias_previas text,
    transfusiones_previas boolean DEFAULT false,
    hospitalizaciones_previas text,
    medicamentos_habituales text,
    habitos_toxicos text,
    actividad_fisica text,
    observaciones text,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    actualizado_por integer
);


ALTER TABLE public.antecedentes_personales OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 17970)
-- Name: antecedentes_personales_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.antecedentes_personales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.antecedentes_personales_id_seq OWNER TO postgres;

--
-- TOC entry 5918 (class 0 OID 0)
-- Dependencies: 231
-- Name: antecedentes_personales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.antecedentes_personales_id_seq OWNED BY public.antecedentes_personales.id;


--
-- TOC entry 226 (class 1259 OID 17904)
-- Name: auditoria; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auditoria (
    id integer NOT NULL,
    usuario_id integer,
    accion character varying(255) NOT NULL,
    modulo character varying(100) NOT NULL,
    registro_id integer,
    datos_anteriores jsonb,
    datos_nuevos jsonb,
    ip_address character varying(45),
    fecha_hora timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.auditoria OWNER TO postgres;

--
-- TOC entry 5920 (class 0 OID 0)
-- Dependencies: 226
-- Name: TABLE auditoria; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.auditoria IS 'Registro completo de auditoría del sistema (Ley 3871)';


--
-- TOC entry 225 (class 1259 OID 17903)
-- Name: auditoria_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.auditoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.auditoria_id_seq OWNER TO postgres;

--
-- TOC entry 5922 (class 0 OID 0)
-- Dependencies: 225
-- Name: auditoria_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.auditoria_id_seq OWNED BY public.auditoria.id;


--
-- TOC entry 312 (class 1259 OID 19393)
-- Name: auth_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO postgres;

--
-- TOC entry 311 (class 1259 OID 19392)
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 314 (class 1259 OID 19403)
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO postgres;

--
-- TOC entry 313 (class 1259 OID 19402)
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 310 (class 1259 OID 19383)
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO postgres;

--
-- TOC entry 309 (class 1259 OID 19382)
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 316 (class 1259 OID 19412)
-- Name: auth_user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_user OWNER TO postgres;

--
-- TOC entry 318 (class 1259 OID 19431)
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user_groups (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.auth_user_groups OWNER TO postgres;

--
-- TOC entry 317 (class 1259 OID 19430)
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user_groups ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 315 (class 1259 OID 19411)
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 320 (class 1259 OID 19440)
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user_user_permissions (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_user_user_permissions OWNER TO postgres;

--
-- TOC entry 319 (class 1259 OID 19439)
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user_user_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 250 (class 1259 OID 18256)
-- Name: biometria_fetal; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.biometria_fetal (
    id integer NOT NULL,
    ecografia_id integer NOT NULL,
    diametro_biparietal numeric(5,2),
    diametro_biparietal_percentil integer,
    circunferencia_cefalica numeric(5,2),
    circunferencia_cefalica_percentil integer,
    circunferencia_abdominal numeric(5,2),
    circunferencia_abdominal_percentil integer,
    longitud_femur numeric(5,2),
    longitud_femur_percentil integer,
    longitud_humero numeric(5,2),
    peso_fetal_estimado numeric(6,2),
    peso_fetal_percentil integer,
    edad_gestacional_biometrica character varying(50),
    observaciones text
);


ALTER TABLE public.biometria_fetal OWNER TO postgres;

--
-- TOC entry 249 (class 1259 OID 18255)
-- Name: biometria_fetal_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.biometria_fetal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.biometria_fetal_id_seq OWNER TO postgres;

--
-- TOC entry 5925 (class 0 OID 0)
-- Dependencies: 249
-- Name: biometria_fetal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.biometria_fetal_id_seq OWNED BY public.biometria_fetal.id;


--
-- TOC entry 246 (class 1259 OID 18182)
-- Name: calculos_obstetricos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.calculos_obstetricos (
    id integer NOT NULL,
    control_prenatal_id integer,
    paciente_id integer NOT NULL,
    embarazo_id integer NOT NULL,
    tipo_calculo character varying(100) NOT NULL,
    datos_entrada jsonb NOT NULL,
    resultado jsonb NOT NULL,
    interpretacion text,
    recomendacion text,
    fecha_calculo timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    calculado_por integer
);


ALTER TABLE public.calculos_obstetricos OWNER TO postgres;

--
-- TOC entry 245 (class 1259 OID 18181)
-- Name: calculos_obstetricos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.calculos_obstetricos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.calculos_obstetricos_id_seq OWNER TO postgres;

--
-- TOC entry 5928 (class 0 OID 0)
-- Dependencies: 245
-- Name: calculos_obstetricos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.calculos_obstetricos_id_seq OWNED BY public.calculos_obstetricos.id;


--
-- TOC entry 262 (class 1259 OID 18417)
-- Name: citas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.citas (
    id integer NOT NULL,
    uuid uuid DEFAULT gen_random_uuid(),
    paciente_id integer NOT NULL,
    embarazo_id integer,
    medico_id integer NOT NULL,
    fecha_hora timestamp without time zone NOT NULL,
    duracion_minutos integer DEFAULT 30,
    tipo_cita character varying(100) NOT NULL,
    motivo text,
    estado character varying(50) DEFAULT 'programada'::character varying,
    observaciones text,
    creada_por integer,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT citas_estado_check CHECK (((estado)::text = ANY ((ARRAY['programada'::character varying, 'confirmada'::character varying, 'en_curso'::character varying, 'completada'::character varying, 'cancelada'::character varying, 'reprogramada'::character varying])::text[]))),
    CONSTRAINT citas_tipo_cita_check CHECK (((tipo_cita)::text = ANY ((ARRAY['control_prenatal'::character varying, 'ecografia'::character varying, 'consulta_ginecologica'::character varying, 'emergencia'::character varying, 'resultados'::character varying])::text[])))
);


ALTER TABLE public.citas OWNER TO postgres;

--
-- TOC entry 261 (class 1259 OID 18416)
-- Name: citas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.citas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.citas_id_seq OWNER TO postgres;

--
-- TOC entry 5931 (class 0 OID 0)
-- Dependencies: 261
-- Name: citas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.citas_id_seq OWNED BY public.citas.id;


--
-- TOC entry 291 (class 1259 OID 19162)
-- Name: configuraciones_sistema; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.configuraciones_sistema (
    id integer NOT NULL,
    clave character varying(255) NOT NULL,
    valor text,
    tipo_dato character varying(50) DEFAULT 'texto'::character varying,
    categoria character varying(100) DEFAULT 'general'::character varying,
    descripcion text,
    editable boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    actualizado_por integer,
    CONSTRAINT configuraciones_sistema_tipo_dato_check CHECK (((tipo_dato)::text = ANY ((ARRAY['texto'::character varying, 'numero'::character varying, 'booleano'::character varying, 'json'::character varying])::text[])))
);


ALTER TABLE public.configuraciones_sistema OWNER TO postgres;

--
-- TOC entry 5933 (class 0 OID 0)
-- Dependencies: 291
-- Name: TABLE configuraciones_sistema; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.configuraciones_sistema IS 'Configuraciones generales del sistema';


--
-- TOC entry 290 (class 1259 OID 19161)
-- Name: configuraciones_sistema_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.configuraciones_sistema_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.configuraciones_sistema_id_seq OWNER TO postgres;

--
-- TOC entry 5934 (class 0 OID 0)
-- Dependencies: 290
-- Name: configuraciones_sistema_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.configuraciones_sistema_id_seq OWNED BY public.configuraciones_sistema.id;


--
-- TOC entry 230 (class 1259 OID 17954)
-- Name: contactos_emergencia; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contactos_emergencia (
    id integer NOT NULL,
    paciente_id integer NOT NULL,
    nombre_completo character varying(200) NOT NULL,
    parentesco character varying(100),
    telefono character varying(20) NOT NULL,
    telefono_alternativo character varying(20),
    es_contacto_principal boolean DEFAULT false
);


ALTER TABLE public.contactos_emergencia OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 17953)
-- Name: contactos_emergencia_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.contactos_emergencia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contactos_emergencia_id_seq OWNER TO postgres;

--
-- TOC entry 5936 (class 0 OID 0)
-- Dependencies: 229
-- Name: contactos_emergencia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.contactos_emergencia_id_seq OWNED BY public.contactos_emergencia.id;


--
-- TOC entry 242 (class 1259 OID 18104)
-- Name: controles_prenatales; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.controles_prenatales (
    id integer NOT NULL,
    uuid uuid DEFAULT gen_random_uuid(),
    embarazo_id integer NOT NULL,
    paciente_id integer NOT NULL,
    numero_control integer NOT NULL,
    fecha_control date DEFAULT CURRENT_DATE NOT NULL,
    semanas_gestacion integer,
    dias_gestacion integer,
    edad_gestacional_calculada character varying(50),
    peso_actual numeric(5,2),
    peso_pregestacional numeric(5,2),
    ganancia_peso numeric(5,2),
    talla numeric(5,2),
    imc_actual numeric(5,2),
    clasificacion_imc character varying(50),
    presion_arterial_sistolica integer,
    presion_arterial_diastolica integer,
    presion_arterial_media numeric(5,2),
    frecuencia_cardiaca integer,
    temperatura numeric(4,2),
    altura_uterina numeric(5,2),
    frecuencia_cardiaca_fetal integer,
    presentacion_fetal character varying(100),
    movimientos_fetales character varying(100),
    edema character varying(100),
    proteinuria character varying(50),
    observaciones text,
    medico_id integer NOT NULL,
    enfermero_id integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.controles_prenatales OWNER TO postgres;

--
-- TOC entry 5938 (class 0 OID 0)
-- Dependencies: 242
-- Name: TABLE controles_prenatales; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.controles_prenatales IS 'Controles prenatales periódicos';


--
-- TOC entry 5939 (class 0 OID 0)
-- Dependencies: 242
-- Name: COLUMN controles_prenatales.presion_arterial_media; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.controles_prenatales.presion_arterial_media IS 'PAM calculada automáticamente';


--
-- TOC entry 241 (class 1259 OID 18103)
-- Name: controles_prenatales_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.controles_prenatales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.controles_prenatales_id_seq OWNER TO postgres;

--
-- TOC entry 5941 (class 0 OID 0)
-- Dependencies: 241
-- Name: controles_prenatales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.controles_prenatales_id_seq OWNED BY public.controles_prenatales.id;


--
-- TOC entry 322 (class 1259 OID 19501)
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO postgres;

--
-- TOC entry 321 (class 1259 OID 19500)
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 308 (class 1259 OID 19371)
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO postgres;

--
-- TOC entry 307 (class 1259 OID 19370)
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 306 (class 1259 OID 19359)
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO postgres;

--
-- TOC entry 305 (class 1259 OID 19358)
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 323 (class 1259 OID 19541)
-- Name: django_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO postgres;

--
-- TOC entry 268 (class 1259 OID 18554)
-- Name: documentos_paciente; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documentos_paciente (
    id integer NOT NULL,
    paciente_id integer NOT NULL,
    tipo_documento character varying(100) NOT NULL,
    titulo character varying(255) NOT NULL,
    descripcion text,
    ruta_archivo text NOT NULL,
    tamano_kb integer,
    cargado_por integer,
    fecha_carga timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.documentos_paciente OWNER TO postgres;

--
-- TOC entry 267 (class 1259 OID 18553)
-- Name: documentos_paciente_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.documentos_paciente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.documentos_paciente_id_seq OWNER TO postgres;

--
-- TOC entry 5944 (class 0 OID 0)
-- Dependencies: 267
-- Name: documentos_paciente_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.documentos_paciente_id_seq OWNED BY public.documentos_paciente.id;


--
-- TOC entry 248 (class 1259 OID 18218)
-- Name: ecografias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ecografias (
    id integer NOT NULL,
    uuid uuid DEFAULT gen_random_uuid(),
    paciente_id integer NOT NULL,
    embarazo_id integer NOT NULL,
    fecha_ecografia date DEFAULT CURRENT_DATE NOT NULL,
    tipo_ecografia character varying(100) NOT NULL,
    semanas_gestacion integer,
    dias_gestacion integer,
    edad_gestacional_eco character varying(50),
    presentacion_fetal character varying(100),
    posicion_fetal character varying(100),
    numero_fetos integer DEFAULT 1,
    vitalidad_fetal boolean DEFAULT true,
    frecuencia_cardiaca_fetal integer,
    movimientos_fetales boolean,
    tono_fetal boolean,
    observaciones text,
    medico_id integer NOT NULL,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ecografias_tipo_ecografia_check CHECK (((tipo_ecografia)::text = ANY ((ARRAY['primer_trimestre'::character varying, 'segundo_trimestre'::character varying, 'tercer_trimestre'::character varying, 'genetica'::character varying, 'doppler'::character varying, 'morfologica'::character varying])::text[])))
);


ALTER TABLE public.ecografias OWNER TO postgres;

--
-- TOC entry 5946 (class 0 OID 0)
-- Dependencies: 248
-- Name: TABLE ecografias; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.ecografias IS 'Estudios ecográficos obstétricos';


--
-- TOC entry 247 (class 1259 OID 18217)
-- Name: ecografias_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ecografias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ecografias_id_seq OWNER TO postgres;

--
-- TOC entry 5948 (class 0 OID 0)
-- Dependencies: 247
-- Name: ecografias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ecografias_id_seq OWNED BY public.ecografias.id;


--
-- TOC entry 240 (class 1259 OID 18070)
-- Name: embarazos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.embarazos (
    id integer NOT NULL,
    uuid uuid DEFAULT gen_random_uuid(),
    paciente_id integer NOT NULL,
    numero_gesta integer NOT NULL,
    fecha_ultima_menstruacion date NOT NULL,
    embarazo_confirmado_por character varying(100),
    edad_gestacional_actual character varying(50),
    tipo_embarazo character varying(50) DEFAULT 'simple'::character varying,
    riesgo_embarazo character varying(50) DEFAULT 'bajo'::character varying,
    estado character varying(50) DEFAULT 'activo'::character varying,
    resultado_final character varying(100),
    fecha_finalizacion date,
    observaciones text,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    medico_responsable integer,
    CONSTRAINT embarazos_embarazo_confirmado_por_check CHECK (((embarazo_confirmado_por)::text = ANY ((ARRAY['prueba_orina'::character varying, 'prueba_sangre'::character varying, 'ecografia'::character varying, 'examen_clinico'::character varying])::text[]))),
    CONSTRAINT embarazos_estado_check CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'finalizado'::character varying, 'perdida'::character varying])::text[]))),
    CONSTRAINT embarazos_riesgo_embarazo_check CHECK (((riesgo_embarazo)::text = ANY ((ARRAY['bajo'::character varying, 'medio'::character varying, 'alto'::character varying])::text[]))),
    CONSTRAINT embarazos_tipo_embarazo_check CHECK (((tipo_embarazo)::text = ANY ((ARRAY['simple'::character varying, 'gemelar'::character varying, 'multiple'::character varying])::text[])))
);


ALTER TABLE public.embarazos OWNER TO postgres;

--
-- TOC entry 5950 (class 0 OID 0)
-- Dependencies: 240
-- Name: TABLE embarazos; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.embarazos IS 'Registro de embarazos actuales e históricos';


--
-- TOC entry 5951 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN embarazos.fecha_ultima_menstruacion; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.embarazos.fecha_ultima_menstruacion IS 'FUM - Base para cálculos gestacionales';


--
-- TOC entry 239 (class 1259 OID 18069)
-- Name: embarazos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.embarazos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.embarazos_id_seq OWNER TO postgres;

--
-- TOC entry 5953 (class 0 OID 0)
-- Dependencies: 239
-- Name: embarazos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.embarazos_id_seq OWNED BY public.embarazos.id;


--
-- TOC entry 299 (class 1259 OID 19271)
-- Name: historial_cambios_estado; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.historial_cambios_estado (
    id integer NOT NULL,
    tabla_afectada character varying(100) NOT NULL,
    registro_id integer NOT NULL,
    campo_afectado character varying(100) NOT NULL,
    valor_anterior text,
    valor_nuevo text,
    motivo_cambio text,
    cambiado_por integer,
    fecha_cambio timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ip_address character varying(45)
);


ALTER TABLE public.historial_cambios_estado OWNER TO postgres;

--
-- TOC entry 5955 (class 0 OID 0)
-- Dependencies: 299
-- Name: TABLE historial_cambios_estado; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.historial_cambios_estado IS 'Historial detallado de cambios de estado en registros críticos';


--
-- TOC entry 298 (class 1259 OID 19270)
-- Name: historial_cambios_estado_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.historial_cambios_estado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.historial_cambios_estado_id_seq OWNER TO postgres;

--
-- TOC entry 5956 (class 0 OID 0)
-- Dependencies: 298
-- Name: historial_cambios_estado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.historial_cambios_estado_id_seq OWNED BY public.historial_cambios_estado.id;


--
-- TOC entry 256 (class 1259 OID 18325)
-- Name: imagenes_ecografia; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.imagenes_ecografia (
    id integer NOT NULL,
    ecografia_id integer NOT NULL,
    tipo_archivo character varying(50),
    ruta_archivo text NOT NULL,
    descripcion text,
    fecha_carga timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    cargado_por integer,
    CONSTRAINT imagenes_ecografia_tipo_archivo_check CHECK (((tipo_archivo)::text = ANY ((ARRAY['DICOM'::character varying, 'JPG'::character varying, 'PNG'::character varying, 'PDF'::character varying])::text[])))
);


ALTER TABLE public.imagenes_ecografia OWNER TO postgres;

--
-- TOC entry 255 (class 1259 OID 18324)
-- Name: imagenes_ecografia_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.imagenes_ecografia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.imagenes_ecografia_id_seq OWNER TO postgres;

--
-- TOC entry 5958 (class 0 OID 0)
-- Dependencies: 255
-- Name: imagenes_ecografia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.imagenes_ecografia_id_seq OWNED BY public.imagenes_ecografia.id;


--
-- TOC entry 293 (class 1259 OID 19186)
-- Name: notificaciones; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notificaciones (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    tipo_notificacion character varying(100) NOT NULL,
    titulo character varying(255) NOT NULL,
    mensaje text NOT NULL,
    leida boolean DEFAULT false,
    accion_url text,
    prioridad character varying(50) DEFAULT 'normal'::character varying,
    fecha_envio timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_lectura timestamp without time zone,
    expiracion timestamp without time zone,
    CONSTRAINT notificaciones_prioridad_check CHECK (((prioridad)::text = ANY ((ARRAY['baja'::character varying, 'normal'::character varying, 'alta'::character varying, 'urgente'::character varying])::text[]))),
    CONSTRAINT notificaciones_tipo_notificacion_check CHECK (((tipo_notificacion)::text = ANY ((ARRAY['alerta'::character varying, 'recordatorio'::character varying, 'sistema'::character varying, 'seguimiento'::character varying])::text[])))
);


ALTER TABLE public.notificaciones OWNER TO postgres;

--
-- TOC entry 5960 (class 0 OID 0)
-- Dependencies: 293
-- Name: TABLE notificaciones; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.notificaciones IS 'Sistema de notificaciones para usuarios';


--
-- TOC entry 292 (class 1259 OID 19185)
-- Name: notificaciones_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notificaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notificaciones_id_seq OWNER TO postgres;

--
-- TOC entry 5961 (class 0 OID 0)
-- Dependencies: 292
-- Name: notificaciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notificaciones_id_seq OWNED BY public.notificaciones.id;


--
-- TOC entry 228 (class 1259 OID 17922)
-- Name: pacientes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pacientes (
    id integer NOT NULL,
    uuid uuid DEFAULT gen_random_uuid(),
    id_clinico character varying(50) NOT NULL,
    nombre character varying(100) NOT NULL,
    apellido_paterno character varying(100) NOT NULL,
    apellido_materno character varying(100),
    fecha_nacimiento date NOT NULL,
    genero character varying(20) NOT NULL,
    cedula_identidad character varying(50),
    telefono_principal character varying(20),
    telefono_emergencia character varying(20),
    email character varying(255),
    direccion text,
    ciudad character varying(100),
    zona character varying(100),
    estado_civil character varying(50),
    ocupacion character varying(150),
    nivel_educativo character varying(100),
    grupo_sanguineo character varying(10),
    foto_paciente text,
    activo boolean DEFAULT true,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    registrado_por integer,
    CONSTRAINT pacientes_estado_civil_check CHECK (((estado_civil)::text = ANY ((ARRAY['soltera'::character varying, 'casada'::character varying, 'divorciada'::character varying, 'viuda'::character varying, 'union_libre'::character varying])::text[]))),
    CONSTRAINT pacientes_genero_check CHECK (((genero)::text = ANY ((ARRAY['femenino'::character varying, 'masculino'::character varying, 'otro'::character varying])::text[]))),
    CONSTRAINT pacientes_grupo_sanguineo_check CHECK (((grupo_sanguineo)::text = ANY ((ARRAY['A+'::character varying, 'A-'::character varying, 'B+'::character varying, 'B-'::character varying, 'AB+'::character varying, 'AB-'::character varying, 'O+'::character varying, 'O-'::character varying])::text[])))
);


ALTER TABLE public.pacientes OWNER TO postgres;

--
-- TOC entry 5962 (class 0 OID 0)
-- Dependencies: 228
-- Name: TABLE pacientes; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.pacientes IS 'Registro de pacientes gineco-obstétricas';


--
-- TOC entry 5963 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN pacientes.id_clinico; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.pacientes.id_clinico IS 'Identificador único del paciente en la clínica';


--
-- TOC entry 227 (class 1259 OID 17921)
-- Name: pacientes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pacientes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pacientes_id_seq OWNER TO postgres;

--
-- TOC entry 5965 (class 0 OID 0)
-- Dependencies: 227
-- Name: pacientes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pacientes_id_seq OWNED BY public.pacientes.id;


--
-- TOC entry 224 (class 1259 OID 17881)
-- Name: permisos_especiales; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.permisos_especiales (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    modulo character varying(100) NOT NULL,
    accion character varying(50) NOT NULL,
    fecha_asignacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    asignado_por integer,
    CONSTRAINT permisos_especiales_accion_check CHECK (((accion)::text = ANY ((ARRAY['crear'::character varying, 'leer'::character varying, 'actualizar'::character varying, 'eliminar'::character varying, 'exportar'::character varying])::text[])))
);


ALTER TABLE public.permisos_especiales OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 17880)
-- Name: permisos_especiales_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.permisos_especiales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.permisos_especiales_id_seq OWNER TO postgres;

--
-- TOC entry 5968 (class 0 OID 0)
-- Dependencies: 223
-- Name: permisos_especiales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.permisos_especiales_id_seq OWNED BY public.permisos_especiales.id;


--
-- TOC entry 295 (class 1259 OID 19210)
-- Name: plantillas_documentos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.plantillas_documentos (
    id integer NOT NULL,
    nombre character varying(255) NOT NULL,
    tipo_documento character varying(100) NOT NULL,
    contenido text NOT NULL,
    variables_disponibles jsonb,
    activa boolean DEFAULT true,
    creada_por integer,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT plantillas_documentos_tipo_documento_check CHECK (((tipo_documento)::text = ANY ((ARRAY['consentimiento'::character varying, 'informe'::character varying, 'certificado'::character varying, 'receta'::character varying, 'reporte'::character varying])::text[])))
);


ALTER TABLE public.plantillas_documentos OWNER TO postgres;

--
-- TOC entry 5970 (class 0 OID 0)
-- Dependencies: 295
-- Name: TABLE plantillas_documentos; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.plantillas_documentos IS 'Plantillas para generación automática de documentos';


--
-- TOC entry 294 (class 1259 OID 19209)
-- Name: plantillas_documentos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.plantillas_documentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.plantillas_documentos_id_seq OWNER TO postgres;

--
-- TOC entry 5971 (class 0 OID 0)
-- Dependencies: 294
-- Name: plantillas_documentos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.plantillas_documentos_id_seq OWNED BY public.plantillas_documentos.id;


--
-- TOC entry 283 (class 1259 OID 18717)
-- Name: predicciones_riesgos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.predicciones_riesgos (
    id integer NOT NULL,
    paciente_id integer NOT NULL,
    embarazo_id integer NOT NULL,
    control_prenatal_id integer,
    tipo_riesgo character varying(100) NOT NULL,
    probabilidad numeric(5,4) NOT NULL,
    nivel_riesgo character varying(50),
    factores_contribuyentes jsonb,
    recomendaciones text,
    modelo_utilizado character varying(100),
    fecha_prediccion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT predicciones_riesgos_nivel_riesgo_check CHECK (((nivel_riesgo)::text = ANY ((ARRAY['bajo'::character varying, 'intermedio'::character varying, 'alto'::character varying, 'muy_alto'::character varying])::text[]))),
    CONSTRAINT predicciones_riesgos_tipo_riesgo_check CHECK (((tipo_riesgo)::text = ANY ((ARRAY['preeclampsia'::character varying, 'diabetes_gestacional'::character varying, 'parto_prematuro'::character varying, 'rciu'::character varying, 'ruptura_membranas'::character varying])::text[])))
);


ALTER TABLE public.predicciones_riesgos OWNER TO postgres;

--
-- TOC entry 5972 (class 0 OID 0)
-- Dependencies: 283
-- Name: TABLE predicciones_riesgos; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.predicciones_riesgos IS 'Predicciones de riesgos obstétricos mediante ML';


--
-- TOC entry 282 (class 1259 OID 18716)
-- Name: predicciones_riesgos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.predicciones_riesgos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.predicciones_riesgos_id_seq OWNER TO postgres;

--
-- TOC entry 5973 (class 0 OID 0)
-- Dependencies: 282
-- Name: predicciones_riesgos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.predicciones_riesgos_id_seq OWNED BY public.predicciones_riesgos.id;


--
-- TOC entry 264 (class 1259 OID 18460)
-- Name: recordatorios_citas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.recordatorios_citas (
    id integer NOT NULL,
    cita_id integer NOT NULL,
    tipo_recordatorio character varying(50),
    fecha_envio timestamp without time zone,
    enviado boolean DEFAULT false,
    respuesta_paciente character varying(50),
    CONSTRAINT recordatorios_citas_respuesta_paciente_check CHECK (((respuesta_paciente)::text = ANY ((ARRAY['confirmada'::character varying, 'cancelada'::character varying, 'sin_respuesta'::character varying])::text[]))),
    CONSTRAINT recordatorios_citas_tipo_recordatorio_check CHECK (((tipo_recordatorio)::text = ANY ((ARRAY['email'::character varying, 'sms'::character varying, 'whatsapp'::character varying])::text[])))
);


ALTER TABLE public.recordatorios_citas OWNER TO postgres;

--
-- TOC entry 263 (class 1259 OID 18459)
-- Name: recordatorios_citas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.recordatorios_citas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.recordatorios_citas_id_seq OWNER TO postgres;

--
-- TOC entry 5975 (class 0 OID 0)
-- Dependencies: 263
-- Name: recordatorios_citas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.recordatorios_citas_id_seq OWNED BY public.recordatorios_citas.id;


--
-- TOC entry 266 (class 1259 OID 18534)
-- Name: reportes_generados; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reportes_generados (
    id integer NOT NULL,
    tipo_reporte character varying(100) NOT NULL,
    parametros jsonb,
    formato character varying(20),
    ruta_archivo text NOT NULL,
    generado_por integer NOT NULL,
    fecha_generacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT reportes_generados_formato_check CHECK (((formato)::text = ANY ((ARRAY['PDF'::character varying, 'EXCEL'::character varying, 'CSV'::character varying])::text[])))
);


ALTER TABLE public.reportes_generados OWNER TO postgres;

--
-- TOC entry 265 (class 1259 OID 18533)
-- Name: reportes_generados_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reportes_generados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reportes_generados_id_seq OWNER TO postgres;

--
-- TOC entry 5978 (class 0 OID 0)
-- Dependencies: 265
-- Name: reportes_generados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reportes_generados_id_seq OWNED BY public.reportes_generados.id;


--
-- TOC entry 260 (class 1259 OID 18391)
-- Name: resultados_laboratorio; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resultados_laboratorio (
    id integer NOT NULL,
    solicitud_id integer NOT NULL,
    fecha_resultado date NOT NULL,
    parametro character varying(255) NOT NULL,
    valor character varying(100) NOT NULL,
    unidad character varying(50),
    valor_referencia character varying(100),
    estado character varying(50),
    observaciones text,
    archivo_resultado text,
    ingresado_por integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT resultados_laboratorio_estado_check CHECK (((estado)::text = ANY ((ARRAY['normal'::character varying, 'anormal'::character varying, 'critico'::character varying])::text[])))
);


ALTER TABLE public.resultados_laboratorio OWNER TO postgres;

--
-- TOC entry 259 (class 1259 OID 18390)
-- Name: resultados_laboratorio_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.resultados_laboratorio_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.resultados_laboratorio_id_seq OWNER TO postgres;

--
-- TOC entry 5981 (class 0 OID 0)
-- Dependencies: 259
-- Name: resultados_laboratorio_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.resultados_laboratorio_id_seq OWNED BY public.resultados_laboratorio.id;


--
-- TOC entry 297 (class 1259 OID 19234)
-- Name: seguimiento_medicamentos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.seguimiento_medicamentos (
    id integer NOT NULL,
    paciente_id integer NOT NULL,
    embarazo_id integer,
    control_prenatal_id integer,
    medicamento character varying(255) NOT NULL,
    dosis character varying(100),
    frecuencia character varying(100),
    via_administracion character varying(50),
    fecha_inicio date NOT NULL,
    fecha_fin date,
    indicacion text,
    estado character varying(50) DEFAULT 'activo'::character varying,
    efectos_secundarios text,
    prescrito_por integer,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT seguimiento_medicamentos_estado_check CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'suspendido'::character varying, 'completado'::character varying, 'cancelado'::character varying])::text[]))),
    CONSTRAINT seguimiento_medicamentos_via_administracion_check CHECK (((via_administracion)::text = ANY ((ARRAY['oral'::character varying, 'intramuscular'::character varying, 'intravenosa'::character varying, 'topica'::character varying, 'vaginal'::character varying])::text[])))
);


ALTER TABLE public.seguimiento_medicamentos OWNER TO postgres;

--
-- TOC entry 5983 (class 0 OID 0)
-- Dependencies: 297
-- Name: TABLE seguimiento_medicamentos; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.seguimiento_medicamentos IS 'Seguimiento de medicamentos prescritos a pacientes';


--
-- TOC entry 296 (class 1259 OID 19233)
-- Name: seguimiento_medicamentos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.seguimiento_medicamentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.seguimiento_medicamentos_id_seq OWNER TO postgres;

--
-- TOC entry 5984 (class 0 OID 0)
-- Dependencies: 296
-- Name: seguimiento_medicamentos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.seguimiento_medicamentos_id_seq OWNED BY public.seguimiento_medicamentos.id;


--
-- TOC entry 222 (class 1259 OID 17861)
-- Name: sesiones; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sesiones (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    token_jwt text NOT NULL,
    ip_address character varying(45),
    dispositivo text,
    navegador text,
    fecha_inicio timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion timestamp without time zone NOT NULL,
    activa boolean DEFAULT true
);


ALTER TABLE public.sesiones OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 17860)
-- Name: sesiones_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sesiones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sesiones_id_seq OWNER TO postgres;

--
-- TOC entry 5986 (class 0 OID 0)
-- Dependencies: 221
-- Name: sesiones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sesiones_id_seq OWNED BY public.sesiones.id;


--
-- TOC entry 275 (class 1259 OID 18647)
-- Name: sistema_backups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sistema_backups (
    id integer NOT NULL,
    tipo_backup character varying(50),
    ruta_archivo text NOT NULL,
    tamano_mb integer,
    estado character varying(50),
    mensaje_error text,
    fecha_inicio timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_fin timestamp without time zone,
    realizado_por character varying(100),
    CONSTRAINT sistema_backups_estado_check CHECK (((estado)::text = ANY ((ARRAY['exitoso'::character varying, 'fallido'::character varying, 'en_proceso'::character varying])::text[]))),
    CONSTRAINT sistema_backups_tipo_backup_check CHECK (((tipo_backup)::text = ANY ((ARRAY['completo'::character varying, 'incremental'::character varying, 'diferencial'::character varying])::text[])))
);


ALTER TABLE public.sistema_backups OWNER TO postgres;

--
-- TOC entry 5988 (class 0 OID 0)
-- Dependencies: 275
-- Name: TABLE sistema_backups; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.sistema_backups IS 'Registro de backups automáticos del sistema';


--
-- TOC entry 274 (class 1259 OID 18646)
-- Name: sistema_backups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sistema_backups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sistema_backups_id_seq OWNER TO postgres;

--
-- TOC entry 5989 (class 0 OID 0)
-- Dependencies: 274
-- Name: sistema_backups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sistema_backups_id_seq OWNED BY public.sistema_backups.id;


--
-- TOC entry 258 (class 1259 OID 18349)
-- Name: solicitudes_laboratorio; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solicitudes_laboratorio (
    id integer NOT NULL,
    uuid uuid DEFAULT gen_random_uuid(),
    paciente_id integer NOT NULL,
    embarazo_id integer,
    control_prenatal_id integer,
    fecha_solicitud date DEFAULT CURRENT_DATE NOT NULL,
    tipo_examen character varying(255) NOT NULL,
    indicacion text,
    urgente boolean DEFAULT false,
    estado character varying(50) DEFAULT 'solicitado'::character varying,
    laboratorio_externo character varying(255),
    solicitado_por integer NOT NULL,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT solicitudes_laboratorio_estado_check CHECK (((estado)::text = ANY ((ARRAY['solicitado'::character varying, 'en_proceso'::character varying, 'completado'::character varying, 'cancelado'::character varying])::text[])))
);


ALTER TABLE public.solicitudes_laboratorio OWNER TO postgres;

--
-- TOC entry 257 (class 1259 OID 18348)
-- Name: solicitudes_laboratorio_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.solicitudes_laboratorio_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.solicitudes_laboratorio_id_seq OWNER TO postgres;

--
-- TOC entry 5991 (class 0 OID 0)
-- Dependencies: 257
-- Name: solicitudes_laboratorio_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.solicitudes_laboratorio_id_seq OWNED BY public.solicitudes_laboratorio.id;


--
-- TOC entry 289 (class 1259 OID 19144)
-- Name: tablas_foraneas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tablas_foraneas (
    id integer NOT NULL,
    tabla_principal character varying(100) NOT NULL,
    tabla_referenciada character varying(100) NOT NULL,
    columna_foranea character varying(100) NOT NULL,
    accion_on_delete character varying(50) DEFAULT 'RESTRICT'::character varying,
    accion_on_update character varying(50) DEFAULT 'CASCADE'::character varying,
    descripcion text,
    fecha_registro timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tablas_foraneas_accion_on_delete_check CHECK (((accion_on_delete)::text = ANY ((ARRAY['CASCADE'::character varying, 'SET NULL'::character varying, 'RESTRICT'::character varying, 'NO ACTION'::character varying])::text[]))),
    CONSTRAINT tablas_foraneas_accion_on_update_check CHECK (((accion_on_update)::text = ANY ((ARRAY['CASCADE'::character varying, 'SET NULL'::character varying, 'RESTRICT'::character varying, 'NO ACTION'::character varying])::text[])))
);


ALTER TABLE public.tablas_foraneas OWNER TO postgres;

--
-- TOC entry 5993 (class 0 OID 0)
-- Dependencies: 289
-- Name: TABLE tablas_foraneas; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.tablas_foraneas IS 'Registro de relaciones foráneas entre tablas para documentación';


--
-- TOC entry 288 (class 1259 OID 19143)
-- Name: tablas_foraneas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tablas_foraneas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tablas_foraneas_id_seq OWNER TO postgres;

--
-- TOC entry 5994 (class 0 OID 0)
-- Dependencies: 288
-- Name: tablas_foraneas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tablas_foraneas_id_seq OWNED BY public.tablas_foraneas.id;


--
-- TOC entry 287 (class 1259 OID 19129)
-- Name: tipos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tipos (
    id integer NOT NULL,
    categoria character varying(100) NOT NULL,
    nombre character varying(255) NOT NULL,
    valor character varying(255),
    descripcion text,
    activo boolean DEFAULT true,
    orden integer DEFAULT 0,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tipos OWNER TO postgres;

--
-- TOC entry 5995 (class 0 OID 0)
-- Dependencies: 287
-- Name: TABLE tipos; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.tipos IS 'Tabla maestra para tipos y catálogos del sistema';


--
-- TOC entry 286 (class 1259 OID 19128)
-- Name: tipos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipos_id_seq OWNER TO postgres;

--
-- TOC entry 5996 (class 0 OID 0)
-- Dependencies: 286
-- Name: tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tipos_id_seq OWNED BY public.tipos.id;


--
-- TOC entry 220 (class 1259 OID 17837)
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    uuid uuid DEFAULT gen_random_uuid(),
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    rol character varying(50) NOT NULL,
    nombre character varying(100) NOT NULL,
    apellido_paterno character varying(100) NOT NULL,
    apellido_materno character varying(100),
    especialidad character varying(150),
    matricula_profesional character varying(50),
    telefono character varying(20),
    foto_perfil text,
    activo boolean DEFAULT true,
    ultimo_acceso timestamp without time zone,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT usuarios_rol_check CHECK (((rol)::text = ANY ((ARRAY['medico'::character varying, 'enfermero'::character varying, 'administrador'::character varying])::text[])))
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- TOC entry 5997 (class 0 OID 0)
-- Dependencies: 220
-- Name: TABLE usuarios; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.usuarios IS 'Usuarios del sistema con roles diferenciados';


--
-- TOC entry 219 (class 1259 OID 17836)
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- TOC entry 5999 (class 0 OID 0)
-- Dependencies: 219
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- TOC entry 272 (class 1259 OID 18595)
-- Name: v_alertas_criticas_pendientes; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_alertas_criticas_pendientes AS
 SELECT a.id,
    a.paciente_id,
    (((p.nombre)::text || ' '::text) || (p.apellido_paterno)::text) AS paciente,
    a.tipo_alerta,
    a.nivel_urgencia,
    a.descripcion,
    a.fecha_creacion,
    (((u.nombre)::text || ' '::text) || (u.apellido_paterno)::text) AS medico_asignado
   FROM (((public.alertas_clinicas a
     JOIN public.pacientes p ON ((a.paciente_id = p.id)))
     LEFT JOIN public.embarazos e ON ((a.embarazo_id = e.id)))
     LEFT JOIN public.usuarios u ON ((e.medico_responsable = u.id)))
  WHERE (((a.estado)::text = 'pendiente'::text) AND ((a.nivel_urgencia)::text = ANY ((ARRAY['alta'::character varying, 'critica'::character varying])::text[])))
  ORDER BY
        CASE a.nivel_urgencia
            WHEN 'critica'::text THEN 1
            WHEN 'alta'::text THEN 2
            ELSE NULL::integer
        END, a.fecha_creacion;


ALTER VIEW public.v_alertas_criticas_pendientes OWNER TO postgres;

--
-- TOC entry 284 (class 1259 OID 18755)
-- Name: v_analisis_ia_resumen; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_analisis_ia_resumen AS
 SELECT ai.id,
    ai.ecografia_id,
    (((p.nombre)::text || ' '::text) || (p.apellido_paterno)::text) AS paciente,
    e.fecha_ecografia,
    ai.modelo_utilizado,
    ai.confianza_general,
    ai.validado_por_medico,
    (((u.nombre)::text || ' '::text) || (u.apellido_paterno)::text) AS medico_validador,
    ai.fecha_analisis
   FROM (((public.analisis_ia_ecografias ai
     JOIN public.ecografias e ON ((ai.ecografia_id = e.id)))
     JOIN public.pacientes p ON ((e.paciente_id = p.id)))
     LEFT JOIN public.usuarios u ON ((ai.medico_validador = u.id)))
  ORDER BY ai.fecha_analisis DESC;


ALTER VIEW public.v_analisis_ia_resumen OWNER TO postgres;

--
-- TOC entry 278 (class 1259 OID 18669)
-- Name: v_citas_hoy; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_citas_hoy AS
 SELECT c.id,
    c.fecha_hora,
    (((p.nombre)::text || ' '::text) || (p.apellido_paterno)::text) AS paciente,
    p.telefono_principal,
    (((u.nombre)::text || ' '::text) || (u.apellido_paterno)::text) AS medico,
    c.tipo_cita,
    c.estado,
    c.motivo
   FROM ((public.citas c
     JOIN public.pacientes p ON ((c.paciente_id = p.id)))
     JOIN public.usuarios u ON ((c.medico_id = u.id)))
  WHERE ((date(c.fecha_hora) = CURRENT_DATE) AND ((c.estado)::text = ANY ((ARRAY['programada'::character varying, 'confirmada'::character varying])::text[])))
  ORDER BY c.fecha_hora;


ALTER VIEW public.v_citas_hoy OWNER TO postgres;

--
-- TOC entry 302 (class 1259 OID 19325)
-- Name: v_configuraciones_organizadas; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_configuraciones_organizadas AS
 SELECT categoria,
    count(*) AS total_configuraciones,
    string_agg((clave)::text, ', '::text ORDER BY (clave)::text) AS claves
   FROM public.configuraciones_sistema
  WHERE (editable = true)
  GROUP BY categoria
  ORDER BY categoria;


ALTER VIEW public.v_configuraciones_organizadas OWNER TO postgres;

--
-- TOC entry 273 (class 1259 OID 18600)
-- Name: v_controles_completos; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_controles_completos AS
 SELECT cp.id,
    cp.uuid,
    cp.embarazo_id,
    cp.paciente_id,
    cp.numero_control,
    cp.fecha_control,
    cp.semanas_gestacion,
    cp.dias_gestacion,
    cp.edad_gestacional_calculada,
    cp.peso_actual,
    cp.peso_pregestacional,
    cp.ganancia_peso,
    cp.talla,
    cp.imc_actual,
    cp.clasificacion_imc,
    cp.presion_arterial_sistolica,
    cp.presion_arterial_diastolica,
    cp.presion_arterial_media,
    cp.frecuencia_cardiaca,
    cp.temperatura,
    cp.altura_uterina,
    cp.frecuencia_cardiaca_fetal,
    cp.presentacion_fetal,
    cp.movimientos_fetales,
    cp.edema,
    cp.proteinuria,
    cp.observaciones,
    cp.medico_id,
    cp.enfermero_id,
    cp.fecha_registro,
    (((p.nombre)::text || ' '::text) || (p.apellido_paterno)::text) AS nombre_paciente,
    p.cedula_identidad,
    (((u.nombre)::text || ' '::text) || (u.apellido_paterno)::text) AS nombre_medico,
    e.fecha_ultima_menstruacion,
    public.calcular_fpp(e.fecha_ultima_menstruacion) AS fecha_probable_parto
   FROM (((public.controles_prenatales cp
     JOIN public.pacientes p ON ((cp.paciente_id = p.id)))
     JOIN public.usuarios u ON ((cp.medico_id = u.id)))
     JOIN public.embarazos e ON ((cp.embarazo_id = e.id)));


ALTER VIEW public.v_controles_completos OWNER TO postgres;

--
-- TOC entry 277 (class 1259 OID 18664)
-- Name: v_controles_por_medico; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_controles_por_medico AS
 SELECT u.id AS medico_id,
    (((u.nombre)::text || ' '::text) || (u.apellido_paterno)::text) AS nombre_medico,
    count(cp.id) AS total_controles,
    count(cp.id) FILTER (WHERE (cp.fecha_control >= (CURRENT_DATE - '30 days'::interval))) AS controles_ultimo_mes,
    count(DISTINCT cp.paciente_id) AS total_pacientes_atendidos
   FROM (public.usuarios u
     LEFT JOIN public.controles_prenatales cp ON ((u.id = cp.medico_id)))
  WHERE (((u.rol)::text = 'medico'::text) AND (u.activo = true))
  GROUP BY u.id, u.nombre, u.apellido_paterno;


ALTER VIEW public.v_controles_por_medico OWNER TO postgres;

--
-- TOC entry 271 (class 1259 OID 18590)
-- Name: v_embarazos_activos; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_embarazos_activos AS
SELECT
    NULL::integer AS embarazo_id,
    NULL::uuid AS embarazo_uuid,
    NULL::integer AS paciente_id,
    NULL::text AS nombre_completo,
    NULL::character varying(50) AS cedula_identidad,
    NULL::date AS fecha_ultima_menstruacion,
    NULL::date AS fecha_probable_parto,
    NULL::character varying(50) AS edad_gestacional_actual,
    NULL::character varying(50) AS tipo_embarazo,
    NULL::character varying(50) AS riesgo_embarazo,
    NULL::text AS medico_responsable,
    NULL::bigint AS total_controles;


ALTER VIEW public.v_embarazos_activos OWNER TO postgres;

--
-- TOC entry 270 (class 1259 OID 18586)
-- Name: v_embarazos_con_fpp; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_embarazos_con_fpp AS
 SELECT id,
    uuid,
    paciente_id,
    numero_gesta,
    fecha_ultima_menstruacion,
    embarazo_confirmado_por,
    edad_gestacional_actual,
    tipo_embarazo,
    riesgo_embarazo,
    estado,
    resultado_final,
    fecha_finalizacion,
    observaciones,
    fecha_registro,
    medico_responsable,
    public.calcular_fpp(fecha_ultima_menstruacion) AS fecha_probable_parto
   FROM public.embarazos e;


ALTER VIEW public.v_embarazos_con_fpp OWNER TO postgres;

--
-- TOC entry 276 (class 1259 OID 18660)
-- Name: v_estadisticas_embarazos; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_estadisticas_embarazos AS
 SELECT count(*) AS total_embarazos,
    count(*) FILTER (WHERE ((estado)::text = 'activo'::text)) AS embarazos_activos,
    count(*) FILTER (WHERE ((estado)::text = 'finalizado'::text)) AS embarazos_finalizados,
    count(*) FILTER (WHERE ((tipo_embarazo)::text = 'gemelar'::text)) AS embarazos_gemelares,
    count(*) FILTER (WHERE ((riesgo_embarazo)::text = 'alto'::text)) AS embarazos_alto_riesgo,
    avg(numero_gesta) AS promedio_gestas
   FROM public.embarazos;


ALTER VIEW public.v_estadisticas_embarazos OWNER TO postgres;

--
-- TOC entry 304 (class 1259 OID 19334)
-- Name: v_medicamentos_activos; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_medicamentos_activos AS
 SELECT sm.id,
    sm.paciente_id,
    sm.embarazo_id,
    sm.control_prenatal_id,
    sm.medicamento,
    sm.dosis,
    sm.frecuencia,
    sm.via_administracion,
    sm.fecha_inicio,
    sm.fecha_fin,
    sm.indicacion,
    sm.estado,
    sm.efectos_secundarios,
    sm.prescrito_por,
    sm.fecha_registro,
    (((p.nombre)::text || ' '::text) || (p.apellido_paterno)::text) AS nombre_paciente,
    p.cedula_identidad,
    (((u.nombre)::text || ' '::text) || (u.apellido_paterno)::text) AS nombre_medico,
    e.fecha_ultima_menstruacion
   FROM (((public.seguimiento_medicamentos sm
     JOIN public.pacientes p ON ((sm.paciente_id = p.id)))
     LEFT JOIN public.usuarios u ON ((sm.prescrito_por = u.id)))
     LEFT JOIN public.embarazos e ON ((sm.embarazo_id = e.id)))
  WHERE (((sm.estado)::text = 'activo'::text) AND ((sm.fecha_fin IS NULL) OR (sm.fecha_fin >= CURRENT_DATE)))
  ORDER BY sm.fecha_inicio DESC;


ALTER VIEW public.v_medicamentos_activos OWNER TO postgres;

--
-- TOC entry 303 (class 1259 OID 19329)
-- Name: v_notificaciones_pendientes; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_notificaciones_pendientes AS
 SELECT n.id,
    n.usuario_id,
    n.tipo_notificacion,
    n.titulo,
    n.mensaje,
    n.leida,
    n.accion_url,
    n.prioridad,
    n.fecha_envio,
    n.fecha_lectura,
    n.expiracion,
    (((u.nombre)::text || ' '::text) || (u.apellido_paterno)::text) AS nombre_usuario,
    u.rol
   FROM (public.notificaciones n
     JOIN public.usuarios u ON ((n.usuario_id = u.id)))
  WHERE ((n.leida = false) AND ((n.expiracion IS NULL) OR (n.expiracion > CURRENT_TIMESTAMP)))
  ORDER BY
        CASE n.prioridad
            WHEN 'urgente'::text THEN 1
            WHEN 'alta'::text THEN 2
            WHEN 'normal'::text THEN 3
            ELSE 4
        END, n.fecha_envio DESC;


ALTER VIEW public.v_notificaciones_pendientes OWNER TO postgres;

--
-- TOC entry 269 (class 1259 OID 18581)
-- Name: v_pacientes_con_edad; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_pacientes_con_edad AS
 SELECT id,
    uuid,
    id_clinico,
    nombre,
    apellido_paterno,
    apellido_materno,
    fecha_nacimiento,
    genero,
    cedula_identidad,
    telefono_principal,
    telefono_emergencia,
    email,
    direccion,
    ciudad,
    zona,
    estado_civil,
    ocupacion,
    nivel_educativo,
    grupo_sanguineo,
    foto_paciente,
    activo,
    fecha_registro,
    registrado_por,
    public.calcular_edad(fecha_nacimiento) AS edad
   FROM public.pacientes p;


ALTER VIEW public.v_pacientes_con_edad OWNER TO postgres;

--
-- TOC entry 279 (class 1259 OID 18674)
-- Name: v_pacientes_control_pendiente; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_pacientes_control_pendiente AS
 SELECT p.id AS paciente_id,
    (((p.nombre)::text || ' '::text) || (p.apellido_paterno)::text) AS nombre_completo,
    p.telefono_principal,
    e.id AS embarazo_id,
    max(cp.fecha_control) AS ultimo_control,
    (CURRENT_DATE - max(cp.fecha_control)) AS dias_sin_control
   FROM ((public.pacientes p
     JOIN public.embarazos e ON ((p.id = e.paciente_id)))
     LEFT JOIN public.controles_prenatales cp ON ((e.id = cp.embarazo_id)))
  WHERE (((e.estado)::text = 'activo'::text) AND (p.activo = true))
  GROUP BY p.id, p.nombre, p.apellido_paterno, p.telefono_principal, e.id
 HAVING ((max(cp.fecha_control) IS NULL) OR ((CURRENT_DATE - max(cp.fecha_control)) > 30))
  ORDER BY (CURRENT_DATE - max(cp.fecha_control)) DESC;


ALTER VIEW public.v_pacientes_control_pendiente OWNER TO postgres;

--
-- TOC entry 285 (class 1259 OID 18760)
-- Name: v_predicciones_alto_riesgo; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_predicciones_alto_riesgo AS
 SELECT pr.id,
    pr.paciente_id,
    (((p.nombre)::text || ' '::text) || (p.apellido_paterno)::text) AS paciente,
    pr.tipo_riesgo,
    pr.probabilidad,
    pr.nivel_riesgo,
    pr.recomendaciones,
    pr.fecha_prediccion,
    e.fecha_ultima_menstruacion,
    (((u.nombre)::text || ' '::text) || (u.apellido_paterno)::text) AS medico_responsable
   FROM (((public.predicciones_riesgos pr
     JOIN public.pacientes p ON ((pr.paciente_id = p.id)))
     JOIN public.embarazos e ON ((pr.embarazo_id = e.id)))
     LEFT JOIN public.usuarios u ON ((e.medico_responsable = u.id)))
  WHERE ((pr.nivel_riesgo)::text = ANY ((ARRAY['alto'::character varying, 'muy_alto'::character varying])::text[]))
  ORDER BY pr.probabilidad DESC, pr.fecha_prediccion DESC;


ALTER VIEW public.v_predicciones_alto_riesgo OWNER TO postgres;

--
-- TOC entry 301 (class 1259 OID 19321)
-- Name: v_relaciones_foraneas; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_relaciones_foraneas AS
 SELECT tabla_principal,
    tabla_referenciada,
    columna_foranea,
    accion_on_delete,
    accion_on_update,
    descripcion
   FROM public.tablas_foraneas tf
  ORDER BY tabla_principal, tabla_referenciada;


ALTER VIEW public.v_relaciones_foraneas OWNER TO postgres;

--
-- TOC entry 300 (class 1259 OID 19317)
-- Name: v_tipos_por_categoria; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_tipos_por_categoria AS
 SELECT categoria,
    count(*) AS total_tipos,
    string_agg((nombre)::text, ', '::text ORDER BY orden) AS tipos
   FROM public.tipos
  WHERE (activo = true)
  GROUP BY categoria
  ORDER BY categoria;


ALTER VIEW public.v_tipos_por_categoria OWNER TO postgres;

--
-- TOC entry 5204 (class 2604 OID 18147)
-- Name: alertas_clinicas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertas_clinicas ALTER COLUMN id SET DEFAULT nextval('public.alertas_clinicas_id_seq'::regclass);


--
-- TOC entry 5254 (class 2604 OID 18692)
-- Name: analisis_ia_ecografias id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analisis_ia_ecografias ALTER COLUMN id SET DEFAULT nextval('public.analisis_ia_ecografias_id_seq'::regclass);


--
-- TOC entry 5216 (class 2604 OID 18277)
-- Name: anatomia_fetal id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anatomia_fetal ALTER COLUMN id SET DEFAULT nextval('public.anatomia_fetal_id_seq'::regclass);


--
-- TOC entry 5227 (class 2604 OID 18306)
-- Name: anexos_fetales id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos_fetales ALTER COLUMN id SET DEFAULT nextval('public.anexos_fetales_id_seq'::regclass);


--
-- TOC entry 5181 (class 2604 OID 17999)
-- Name: antecedentes_familiares id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_familiares ALTER COLUMN id SET DEFAULT nextval('public.antecedentes_familiares_id_seq'::regclass);


--
-- TOC entry 5182 (class 2604 OID 18017)
-- Name: antecedentes_ginecologicos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_ginecologicos ALTER COLUMN id SET DEFAULT nextval('public.antecedentes_ginecologicos_id_seq'::regclass);


--
-- TOC entry 5185 (class 2604 OID 18042)
-- Name: antecedentes_obstetricos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_obstetricos ALTER COLUMN id SET DEFAULT nextval('public.antecedentes_obstetricos_id_seq'::regclass);


--
-- TOC entry 5178 (class 2604 OID 17974)
-- Name: antecedentes_personales id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_personales ALTER COLUMN id SET DEFAULT nextval('public.antecedentes_personales_id_seq'::regclass);


--
-- TOC entry 5170 (class 2604 OID 17907)
-- Name: auditoria id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditoria ALTER COLUMN id SET DEFAULT nextval('public.auditoria_id_seq'::regclass);


--
-- TOC entry 5215 (class 2604 OID 18259)
-- Name: biometria_fetal id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.biometria_fetal ALTER COLUMN id SET DEFAULT nextval('public.biometria_fetal_id_seq'::regclass);


--
-- TOC entry 5207 (class 2604 OID 18185)
-- Name: calculos_obstetricos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calculos_obstetricos ALTER COLUMN id SET DEFAULT nextval('public.calculos_obstetricos_id_seq'::regclass);


--
-- TOC entry 5240 (class 2604 OID 18420)
-- Name: citas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.citas ALTER COLUMN id SET DEFAULT nextval('public.citas_id_seq'::regclass);


--
-- TOC entry 5267 (class 2604 OID 19165)
-- Name: configuraciones_sistema id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configuraciones_sistema ALTER COLUMN id SET DEFAULT nextval('public.configuraciones_sistema_id_seq'::regclass);


--
-- TOC entry 5176 (class 2604 OID 17957)
-- Name: contactos_emergencia id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contactos_emergencia ALTER COLUMN id SET DEFAULT nextval('public.contactos_emergencia_id_seq'::regclass);


--
-- TOC entry 5200 (class 2604 OID 18107)
-- Name: controles_prenatales id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles_prenatales ALTER COLUMN id SET DEFAULT nextval('public.controles_prenatales_id_seq'::regclass);


--
-- TOC entry 5250 (class 2604 OID 18557)
-- Name: documentos_paciente id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documentos_paciente ALTER COLUMN id SET DEFAULT nextval('public.documentos_paciente_id_seq'::regclass);


--
-- TOC entry 5209 (class 2604 OID 18221)
-- Name: ecografias id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ecografias ALTER COLUMN id SET DEFAULT nextval('public.ecografias_id_seq'::regclass);


--
-- TOC entry 5194 (class 2604 OID 18073)
-- Name: embarazos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.embarazos ALTER COLUMN id SET DEFAULT nextval('public.embarazos_id_seq'::regclass);


--
-- TOC entry 5284 (class 2604 OID 19274)
-- Name: historial_cambios_estado id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historial_cambios_estado ALTER COLUMN id SET DEFAULT nextval('public.historial_cambios_estado_id_seq'::regclass);


--
-- TOC entry 5230 (class 2604 OID 18328)
-- Name: imagenes_ecografia id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.imagenes_ecografia ALTER COLUMN id SET DEFAULT nextval('public.imagenes_ecografia_id_seq'::regclass);


--
-- TOC entry 5273 (class 2604 OID 19189)
-- Name: notificaciones id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones ALTER COLUMN id SET DEFAULT nextval('public.notificaciones_id_seq'::regclass);


--
-- TOC entry 5172 (class 2604 OID 17925)
-- Name: pacientes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pacientes ALTER COLUMN id SET DEFAULT nextval('public.pacientes_id_seq'::regclass);


--
-- TOC entry 5168 (class 2604 OID 17884)
-- Name: permisos_especiales id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permisos_especiales ALTER COLUMN id SET DEFAULT nextval('public.permisos_especiales_id_seq'::regclass);


--
-- TOC entry 5277 (class 2604 OID 19213)
-- Name: plantillas_documentos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plantillas_documentos ALTER COLUMN id SET DEFAULT nextval('public.plantillas_documentos_id_seq'::regclass);


--
-- TOC entry 5257 (class 2604 OID 18720)
-- Name: predicciones_riesgos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predicciones_riesgos ALTER COLUMN id SET DEFAULT nextval('public.predicciones_riesgos_id_seq'::regclass);


--
-- TOC entry 5246 (class 2604 OID 18463)
-- Name: recordatorios_citas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recordatorios_citas ALTER COLUMN id SET DEFAULT nextval('public.recordatorios_citas_id_seq'::regclass);


--
-- TOC entry 5248 (class 2604 OID 18537)
-- Name: reportes_generados id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reportes_generados ALTER COLUMN id SET DEFAULT nextval('public.reportes_generados_id_seq'::regclass);


--
-- TOC entry 5238 (class 2604 OID 18394)
-- Name: resultados_laboratorio id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resultados_laboratorio ALTER COLUMN id SET DEFAULT nextval('public.resultados_laboratorio_id_seq'::regclass);


--
-- TOC entry 5281 (class 2604 OID 19237)
-- Name: seguimiento_medicamentos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seguimiento_medicamentos ALTER COLUMN id SET DEFAULT nextval('public.seguimiento_medicamentos_id_seq'::regclass);


--
-- TOC entry 5165 (class 2604 OID 17864)
-- Name: sesiones id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sesiones ALTER COLUMN id SET DEFAULT nextval('public.sesiones_id_seq'::regclass);


--
-- TOC entry 5252 (class 2604 OID 18650)
-- Name: sistema_backups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sistema_backups ALTER COLUMN id SET DEFAULT nextval('public.sistema_backups_id_seq'::regclass);


--
-- TOC entry 5232 (class 2604 OID 18352)
-- Name: solicitudes_laboratorio id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitudes_laboratorio ALTER COLUMN id SET DEFAULT nextval('public.solicitudes_laboratorio_id_seq'::regclass);


--
-- TOC entry 5263 (class 2604 OID 19147)
-- Name: tablas_foraneas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tablas_foraneas ALTER COLUMN id SET DEFAULT nextval('public.tablas_foraneas_id_seq'::regclass);


--
-- TOC entry 5259 (class 2604 OID 19132)
-- Name: tipos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipos ALTER COLUMN id SET DEFAULT nextval('public.tipos_id_seq'::regclass);


--
-- TOC entry 5160 (class 2604 OID 17840)
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- TOC entry 5809 (class 0 OID 18144)
-- Dependencies: 244
-- Data for Name: alertas_clinicas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alertas_clinicas (id, control_prenatal_id, paciente_id, embarazo_id, tipo_alerta, nivel_urgencia, descripcion, parametro_afectado, valor_detectado, valor_normal_esperado, recomendacion, estado, revisada_por, fecha_revision, fecha_creacion) FROM stdin;
1	2	1	1	Presion Arterial Elevada	alta	Alto - Hipertension	Presion Arterial	145/95 mmHg	\N	Evaluacion medica inmediata, control de presion arterial, evaluar preeclampsia	pendiente	\N	\N	2025-10-15 16:11:52.473641
2	4	1	1	Presion Arterial Elevada	alta	Alto - Hipertension	Presion Arterial	145/95 mmHg	\N	Evaluacion medica inmediata, control de presion arterial, evaluar preeclampsia	pendiente	\N	\N	2025-10-15 16:25:14.623172
3	6	1	1	Presion Arterial Elevada	alta	Alto - Hipertension	Presion Arterial	145/95 mmHg	\N	Evaluacion medica inmediata, control de presion arterial, evaluar preeclampsia	pendiente	\N	\N	2025-10-15 17:30:16.639781
\.


--
-- TOC entry 5837 (class 0 OID 18689)
-- Dependencies: 281
-- Data for Name: analisis_ia_ecografias; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.analisis_ia_ecografias (id, ecografia_id, modelo_utilizado, version_modelo, resultado_analisis, confianza_general, patologias_detectadas, recomendaciones, validado_por_medico, medico_validador, fecha_validacion, comentarios_medico, fecha_analisis) FROM stdin;
\.


--
-- TOC entry 5817 (class 0 OID 18274)
-- Dependencies: 252
-- Data for Name: anatomia_fetal; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.anatomia_fetal (id, ecografia_id, craneo, cerebro, cara, cuello, corazon, torax, abdomen, columna, extremidades_superiores, extremidades_inferiores, genitales, sexo_fetal, observaciones) FROM stdin;
\.


--
-- TOC entry 5819 (class 0 OID 18303)
-- Dependencies: 254
-- Data for Name: anexos_fetales; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.anexos_fetales (id, ecografia_id, placenta_posicion, placenta_grado_maduracion, placenta_distancia_oci, cordon_umbilical_arterias, cordon_umbilical_circular, liquido_amniotico_indice, liquido_amniotico_clasificacion, cuello_uterino_longitud, cuello_uterino_estado, observaciones) FROM stdin;
\.


--
-- TOC entry 5799 (class 0 OID 17996)
-- Dependencies: 234
-- Data for Name: antecedentes_familiares; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.antecedentes_familiares (id, paciente_id, parentesco, enfermedad, observaciones) FROM stdin;
\.


--
-- TOC entry 5801 (class 0 OID 18014)
-- Dependencies: 236
-- Data for Name: antecedentes_ginecologicos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.antecedentes_ginecologicos (id, paciente_id, edad_menarca, ciclos_regulares, duracion_ciclo, fecha_ultima_menstruacion, dismenorrea, metodo_anticonceptivo, fecha_ultima_citologia, resultado_ultima_citologia, fecha_ultima_mamografia, resultado_ultima_mamografia, cirugias_ginecologicas, infecciones_transmision_sexual, observaciones, fecha_registro, actualizado_por) FROM stdin;
1	1	13	t	28	2024-10-01	f	Ninguno	\N	\N	\N	\N	\N	\N	Sin antecedentes relevantes	2025-10-15 16:10:09.375379	\N
\.


--
-- TOC entry 5803 (class 0 OID 18039)
-- Dependencies: 238
-- Data for Name: antecedentes_obstetricos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.antecedentes_obstetricos (id, paciente_id, gestas, partos, cesareas, abortos, ectopicos, hijos_vivos, hijos_muertos, complicaciones_previas, observaciones, fecha_registro, actualizado_por) FROM stdin;
1	1	1	1	0	0	0	1	0	Ninguna	Primer embarazo sin complicaciones	2025-10-15 16:10:34.855224	\N
\.


--
-- TOC entry 5797 (class 0 OID 17971)
-- Dependencies: 232
-- Data for Name: antecedentes_personales; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.antecedentes_personales (id, paciente_id, alergias, enfermedades_cronicas, cirugias_previas, transfusiones_previas, hospitalizaciones_previas, medicamentos_habituales, habitos_toxicos, actividad_fisica, observaciones, fecha_registro, actualizado_por) FROM stdin;
\.


--
-- TOC entry 5791 (class 0 OID 17904)
-- Dependencies: 226
-- Data for Name: auditoria; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auditoria (id, usuario_id, accion, modulo, registro_id, datos_anteriores, datos_nuevos, ip_address, fecha_hora) FROM stdin;
1	\N	INSERT	usuarios	1	\N	{"id": 1, "rol": "administrador", "uuid": "fd597328-7a58-441f-8383-fe5c7180c46a", "email": "admin@fetalmedical.com", "activo": true, "nombre": "Administrador", "telefono": null, "foto_perfil": null, "especialidad": null, "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5LZq.ZYK6nQ4u", "ultimo_acceso": null, "fecha_creacion": "2025-10-15T02:14:11.806906", "apellido_materno": "Principal", "apellido_paterno": "Sistema", "fecha_actualizacion": "2025-10-15T02:14:11.806906", "matricula_profesional": null}	\N	2025-10-15 02:14:11.806906
22	\N	INSERT	tipos	1	\N	{"id": 1, "orden": 1, "valor": "CI", "activo": true, "nombre": "Cédula de Identidad", "categoria": "tipo_documento", "descripcion": "Documento de identificación nacional", "fecha_creacion": "2025-10-15T12:44:56.888725"}	\N	2025-10-15 12:44:56.888725
23	\N	INSERT	tipos	2	\N	{"id": 2, "orden": 2, "valor": "PASAPORTE", "activo": true, "nombre": "Pasaporte", "categoria": "tipo_documento", "descripcion": "Pasaporte internacional", "fecha_creacion": "2025-10-15T12:44:56.888725"}	\N	2025-10-15 12:44:56.888725
24	\N	INSERT	tipos	3	\N	{"id": 3, "orden": 1, "valor": "soltera", "activo": true, "nombre": "Soltera", "categoria": "estado_civil", "descripcion": "Estado civil soltera", "fecha_creacion": "2025-10-15T12:44:56.888725"}	\N	2025-10-15 12:44:56.888725
25	\N	INSERT	tipos	4	\N	{"id": 4, "orden": 2, "valor": "casada", "activo": true, "nombre": "Casada", "categoria": "estado_civil", "descripcion": "Estado civil casada", "fecha_creacion": "2025-10-15T12:44:56.888725"}	\N	2025-10-15 12:44:56.888725
26	\N	INSERT	tablas_foraneas	1	\N	{"id": 1, "descripcion": "Sesiones pertenecen a usuarios", "fecha_registro": "2025-10-15T12:44:56.888725", "columna_foranea": "usuario_id", "tabla_principal": "sesiones", "accion_on_delete": "CASCADE", "accion_on_update": "CASCADE", "tabla_referenciada": "usuarios"}	\N	2025-10-15 12:44:56.888725
27	\N	INSERT	tablas_foraneas	2	\N	{"id": 2, "descripcion": "Paciente registrado por usuario", "fecha_registro": "2025-10-15T12:44:56.888725", "columna_foranea": "registrado_por", "tabla_principal": "pacientes", "accion_on_delete": "SET NULL", "accion_on_update": "CASCADE", "tabla_referenciada": "usuarios"}	\N	2025-10-15 12:44:56.888725
28	\N	INSERT	configuraciones_sistema	1	\N	{"id": 1, "clave": "nombre_sistema", "valor": "Fetal Medical - Sistema de Historias Clínicas", "editable": true, "categoria": "general", "tipo_dato": "texto", "descripcion": "Nombre del sistema para mostrar en interfaz", "fecha_creacion": "2025-10-15T12:44:56.888725", "actualizado_por": null, "fecha_actualizacion": "2025-10-15T12:44:56.888725"}	\N	2025-10-15 12:44:56.888725
29	\N	INSERT	configuraciones_sistema	2	\N	{"id": 2, "clave": "version_sistema", "valor": "1.0.0", "editable": true, "categoria": "general", "tipo_dato": "texto", "descripcion": "Versión actual del sistema", "fecha_creacion": "2025-10-15T12:44:56.888725", "actualizado_por": null, "fecha_actualizacion": "2025-10-15T12:44:56.888725"}	\N	2025-10-15 12:44:56.888725
30	\N	INSERT	configuraciones_sistema	3	\N	{"id": 3, "clave": "dias_control_prenatal", "valor": "30", "editable": true, "categoria": "clinica", "tipo_dato": "numero", "descripcion": "Días máximos entre controles prenatales", "fecha_creacion": "2025-10-15T12:44:56.888725", "actualizado_por": null, "fecha_actualizacion": "2025-10-15T12:44:56.888725"}	\N	2025-10-15 12:44:56.888725
31	\N	INSERT	plantillas_documentos	1	\N	{"id": 1, "activa": true, "nombre": "Consentimiento Informado", "contenido": "Yo, {nombre_paciente}, identificada con CI {cedula_paciente}, doy mi consentimiento informado para el procedimiento {procedimiento} después de haber recibido información completa sobre los riesgos, beneficios y alternativas.", "creada_por": null, "fecha_creacion": "2025-10-15T12:44:56.888725", "tipo_documento": "consentimiento", "fecha_actualizacion": "2025-10-15T12:44:56.888725", "variables_disponibles": ["nombre_paciente", "cedula_paciente", "procedimiento", "fecha", "medico"]}	\N	2025-10-15 12:44:56.888725
32	\N	INSERT	plantillas_documentos	2	\N	{"id": 2, "activa": true, "nombre": "Informe Ecográfico Obstétrico", "contenido": "INFORME ECOGRÁFICO OBSTÉTRICO\\nPACIENTE: {nombre_paciente}\\nEDAD GESTACIONAL: {edad_gestacional}\\nFUM: {fecha_ultima_menstruacion}\\nFPP: {fecha_probable_parto}\\n\\nHALLAZGOS:\\n{hallazgos}\\n\\nCONCLUSIONES:\\n{conclusiones}\\n\\nRECOMENDACIONES:\\n{recomendaciones}\\n\\nMédico Tratante: {medico}\\nFecha: {fecha_estudio}", "creada_por": null, "fecha_creacion": "2025-10-15T12:44:56.888725", "tipo_documento": "informe", "fecha_actualizacion": "2025-10-15T12:44:56.888725", "variables_disponibles": ["nombre_paciente", "edad_gestacional", "fecha_ultima_menstruacion", "fecha_probable_parto", "hallazgos", "conclusiones", "recomendaciones", "medico", "fecha_estudio"]}	\N	2025-10-15 12:44:56.888725
33	\N	INSERT	usuarios	2	\N	{"id": 2, "rol": "medico", "uuid": "8e247c46-c562-4f09-b7d3-20fe4f3afc81", "email": "dr.perez@fetalmedical.com", "activo": true, "nombre": "Juan Carlos", "telefono": "+591-70123456", "foto_perfil": null, "especialidad": "Ginecología y Obstetricia", "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5LZq.ZYK6nQ4u", "ultimo_acceso": null, "fecha_creacion": "2025-10-15T16:04:21.574728", "apellido_materno": "López", "apellido_paterno": "Pérez", "fecha_actualizacion": "2025-10-15T16:04:21.574728", "matricula_profesional": "MAT-12345"}	\N	2025-10-15 16:04:21.574728
34	\N	INSERT	usuarios	3	\N	{"id": 3, "rol": "enfermero", "uuid": "e4b8ac63-27b8-4028-a483-c00f84e3e9dd", "email": "enf.martinez@fetalmedical.com", "activo": true, "nombre": "María Elena", "telefono": "+591-71234567", "foto_perfil": null, "especialidad": null, "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5LZq.ZYK6nQ4u", "ultimo_acceso": null, "fecha_creacion": "2025-10-15T16:04:36.881316", "apellido_materno": "Flores", "apellido_paterno": "Martínez", "fecha_actualizacion": "2025-10-15T16:04:36.881316", "matricula_profesional": null}	\N	2025-10-15 16:04:36.881316
35	\N	INSERT	pacientes	1	\N	{"id": 1, "uuid": "c11a59df-f28f-48be-b9a1-b238002451ac", "zona": null, "email": "ana.gonzalez@email.com", "activo": true, "ciudad": "La Paz", "genero": "femenino", "nombre": "Ana María", "direccion": "Calle Los Pinos #123, Zona Sur", "ocupacion": null, "id_clinico": "HC-25000001", "estado_civil": "casada", "foto_paciente": null, "fecha_registro": "2025-10-15T16:06:57.547196", "registrado_por": 1, "grupo_sanguineo": "O+", "nivel_educativo": null, "apellido_materno": "Rodríguez", "apellido_paterno": "González", "cedula_identidad": "1234567 LP", "fecha_nacimiento": "1990-05-15", "telefono_principal": "+591-72345678", "telefono_emergencia": null}	\N	2025-10-15 16:06:57.547196
36	\N	INSERT	embarazos	1	\N	{"id": 1, "uuid": "bce7d5f4-804e-4df6-9508-2141a31ad6f4", "estado": "activo", "paciente_id": 1, "numero_gesta": 2, "observaciones": null, "tipo_embarazo": "simple", "fecha_registro": "2025-10-15T16:10:55.193202", "resultado_final": null, "riesgo_embarazo": "bajo", "fecha_finalizacion": null, "medico_responsable": 2, "edad_gestacional_actual": null, "embarazo_confirmado_por": "ecografia", "fecha_ultima_menstruacion": "2024-10-01"}	\N	2025-10-15 16:10:55.193202
37	\N	INSERT	controles_prenatales	1	\N	{"id": 1, "uuid": "3f697425-c1e3-4aac-9f4b-d0872010010d", "edema": null, "talla": 165.00, "medico_id": 2, "imc_actual": 24.43, "embarazo_id": 1, "paciente_id": 1, "peso_actual": 66.50, "proteinuria": null, "temperatura": null, "enfermero_id": null, "fecha_control": "2025-10-15", "ganancia_peso": 1.50, "observaciones": null, "altura_uterina": null, "dias_gestacion": null, "fecha_registro": "2025-10-15T16:11:26.773768", "numero_control": 1, "clasificacion_imc": "Normal", "semanas_gestacion": null, "presentacion_fetal": null, "frecuencia_cardiaca": null, "movimientos_fetales": null, "peso_pregestacional": 65.00, "presion_arterial_media": 88.33, "frecuencia_cardiaca_fetal": null, "edad_gestacional_calculada": null, "presion_arterial_sistolica": 115, "presion_arterial_diastolica": 75}	\N	2025-10-15 16:11:26.773768
38	\N	INSERT	controles_prenatales	2	\N	{"id": 2, "uuid": "2b30ef58-3a2c-4383-b7f3-9f8592da11b4", "edema": null, "talla": 165.00, "medico_id": 2, "imc_actual": 24.61, "embarazo_id": 1, "paciente_id": 1, "peso_actual": 67.00, "proteinuria": null, "temperatura": null, "enfermero_id": null, "fecha_control": "2025-10-15", "ganancia_peso": 2.00, "observaciones": null, "altura_uterina": null, "dias_gestacion": null, "fecha_registro": "2025-10-15T16:11:52.473641", "numero_control": 2, "clasificacion_imc": "Normal", "semanas_gestacion": null, "presentacion_fetal": null, "frecuencia_cardiaca": null, "movimientos_fetales": null, "peso_pregestacional": 65.00, "presion_arterial_media": 111.67, "frecuencia_cardiaca_fetal": null, "edad_gestacional_calculada": null, "presion_arterial_sistolica": 145, "presion_arterial_diastolica": 95}	\N	2025-10-15 16:11:52.473641
39	\N	INSERT	ecografias	1	\N	{"id": 1, "uuid": "756dc545-f42a-4822-9b18-f31906c60db1", "medico_id": 2, "tono_fetal": null, "embarazo_id": 1, "paciente_id": 1, "numero_fetos": 1, "observaciones": null, "dias_gestacion": null, "fecha_registro": "2025-10-15T16:13:35.294868", "posicion_fetal": null, "tipo_ecografia": "segundo_trimestre", "fecha_ecografia": "2025-10-15", "vitalidad_fetal": true, "semanas_gestacion": null, "presentacion_fetal": null, "movimientos_fetales": null, "edad_gestacional_eco": null, "frecuencia_cardiaca_fetal": null}	\N	2025-10-15 16:13:35.294868
40	\N	UPDATE	pacientes	1	{"id": 1, "uuid": "c11a59df-f28f-48be-b9a1-b238002451ac", "zona": null, "email": "ana.gonzalez@email.com", "activo": true, "ciudad": "La Paz", "genero": "femenino", "nombre": "Ana María", "direccion": "Calle Los Pinos #123, Zona Sur", "ocupacion": null, "id_clinico": "HC-25000001", "estado_civil": "casada", "foto_paciente": null, "fecha_registro": "2025-10-15T16:06:57.547196", "registrado_por": 1, "grupo_sanguineo": "O+", "nivel_educativo": null, "apellido_materno": "Rodríguez", "apellido_paterno": "González", "cedula_identidad": "1234567 LP", "fecha_nacimiento": "1990-05-15", "telefono_principal": "+591-72345678", "telefono_emergencia": null}	{"id": 1, "uuid": "c11a59df-f28f-48be-b9a1-b238002451ac", "zona": null, "email": "ana.gonzalez@email.com", "activo": true, "ciudad": "La Paz", "genero": "femenino", "nombre": "Ana María", "direccion": "Calle Los Pinos #123, Zona Sur", "ocupacion": null, "id_clinico": "HC-25000001", "estado_civil": "casada", "foto_paciente": null, "fecha_registro": "2025-10-15T16:06:57.547196", "registrado_por": 1, "grupo_sanguineo": "O+", "nivel_educativo": null, "apellido_materno": "Rodríguez", "apellido_paterno": "González", "cedula_identidad": "1234567 LP", "fecha_nacimiento": "1990-05-15", "telefono_principal": "+591-79999999", "telefono_emergencia": null}	\N	2025-10-15 16:14:43.263652
41	\N	INSERT	pacientes	2	\N	{"id": 2, "uuid": "f040177a-3fcf-4741-ae8a-d462882814f2", "zona": null, "email": null, "activo": true, "ciudad": null, "genero": "femenino", "nombre": "Paciente", "direccion": null, "ocupacion": null, "id_clinico": "HC-25250001", "estado_civil": null, "foto_paciente": null, "fecha_registro": "2025-10-15T16:16:29.919362", "registrado_por": 1, "grupo_sanguineo": null, "nivel_educativo": null, "apellido_materno": null, "apellido_paterno": "Temporal", "cedula_identidad": "TEMP123", "fecha_nacimiento": "1995-01-01", "telefono_principal": null, "telefono_emergencia": null}	\N	2025-10-15 16:16:29.919362
42	\N	DELETE	pacientes	2	{"id": 2, "uuid": "f040177a-3fcf-4741-ae8a-d462882814f2", "zona": null, "email": null, "activo": true, "ciudad": null, "genero": "femenino", "nombre": "Paciente", "direccion": null, "ocupacion": null, "id_clinico": "HC-25250001", "estado_civil": null, "foto_paciente": null, "fecha_registro": "2025-10-15T16:16:29.919362", "registrado_por": 1, "grupo_sanguineo": null, "nivel_educativo": null, "apellido_materno": null, "apellido_paterno": "Temporal", "cedula_identidad": "TEMP123", "fecha_nacimiento": "1995-01-01", "telefono_principal": null, "telefono_emergencia": null}	\N	\N	2025-10-15 16:16:29.919362
46	\N	INSERT	controles_prenatales	4	\N	{"id": 4, "uuid": "e6b107df-d24d-4ece-8c19-bac9847247d5", "edema": null, "talla": 165.00, "medico_id": 2, "imc_actual": 24.61, "embarazo_id": 1, "paciente_id": 1, "peso_actual": 67.00, "proteinuria": null, "temperatura": null, "enfermero_id": null, "fecha_control": "2025-10-15", "ganancia_peso": 2.00, "observaciones": null, "altura_uterina": null, "dias_gestacion": null, "fecha_registro": "2025-10-15T16:25:14.623172", "numero_control": 3, "clasificacion_imc": "Normal", "semanas_gestacion": null, "presentacion_fetal": null, "frecuencia_cardiaca": null, "movimientos_fetales": null, "peso_pregestacional": 65.00, "presion_arterial_media": 111.67, "frecuencia_cardiaca_fetal": null, "edad_gestacional_calculada": null, "presion_arterial_sistolica": 145, "presion_arterial_diastolica": 95}	\N	2025-10-15 16:25:14.623172
51	\N	INSERT	configuraciones_sistema	9	\N	{"id": 9, "clave": "prueba_config", "valor": "valor_prueba", "editable": true, "categoria": "test", "tipo_dato": "texto", "descripcion": "Configuración de prueba", "fecha_creacion": "2025-10-15T17:28:16.111999", "actualizado_por": null, "fecha_actualizacion": "2025-10-15T17:28:16.111999"}	\N	2025-10-15 17:28:16.111999
52	\N	UPDATE	configuraciones_sistema	9	{"id": 9, "clave": "prueba_config", "valor": "valor_prueba", "editable": true, "categoria": "test", "tipo_dato": "texto", "descripcion": "Configuración de prueba", "fecha_creacion": "2025-10-15T17:28:16.111999", "actualizado_por": null, "fecha_actualizacion": "2025-10-15T17:28:16.111999"}	{"id": 9, "clave": "prueba_config", "valor": "valor_prueba", "editable": true, "categoria": "test", "tipo_dato": "texto", "descripcion": "Configuración de prueba", "fecha_creacion": "2025-10-15T17:28:16.111999", "actualizado_por": null, "fecha_actualizacion": "2025-10-15T17:29:18.735263"}	\N	2025-10-15 17:29:18.735263
53	\N	INSERT	notificaciones	3	\N	{"id": 3, "leida": false, "titulo": "Prueba notificación", "mensaje": "Esta es una notificación de prueba", "prioridad": "normal", "accion_url": null, "expiracion": null, "usuario_id": 2, "fecha_envio": "2025-10-15T17:29:22.758282", "fecha_lectura": null, "tipo_notificacion": "alerta"}	\N	2025-10-15 17:29:22.758282
54	\N	INSERT	controles_prenatales	6	\N	{"id": 6, "uuid": "b91f1854-2678-425e-8c27-3c08f5e26a63", "edema": null, "talla": 165.00, "medico_id": 2, "imc_actual": 24.61, "embarazo_id": 1, "paciente_id": 1, "peso_actual": 67.00, "proteinuria": null, "temperatura": null, "enfermero_id": null, "fecha_control": "2025-10-15", "ganancia_peso": 2.00, "observaciones": null, "altura_uterina": null, "dias_gestacion": null, "fecha_registro": "2025-10-15T17:30:16.639781", "numero_control": 4, "clasificacion_imc": "Normal", "semanas_gestacion": null, "presentacion_fetal": null, "frecuencia_cardiaca": null, "movimientos_fetales": null, "peso_pregestacional": 65.00, "presion_arterial_media": 111.67, "frecuencia_cardiaca_fetal": null, "edad_gestacional_calculada": null, "presion_arterial_sistolica": 145, "presion_arterial_diastolica": 95}	\N	2025-10-15 17:30:16.639781
55	\N	INSERT	ecografias	2	\N	{"id": 2, "uuid": "9c884f29-2d0b-4883-9028-233acd4cf19e", "medico_id": 2, "tono_fetal": null, "embarazo_id": 1, "paciente_id": 1, "numero_fetos": 1, "observaciones": null, "dias_gestacion": null, "fecha_registro": "2025-10-15T17:34:54.015483", "posicion_fetal": null, "tipo_ecografia": "segundo_trimestre", "fecha_ecografia": "2025-10-15", "vitalidad_fetal": true, "semanas_gestacion": null, "presentacion_fetal": null, "movimientos_fetales": null, "edad_gestacional_eco": null, "frecuencia_cardiaca_fetal": null}	\N	2025-10-15 17:34:54.015483
\.


--
-- TOC entry 5861 (class 0 OID 19393)
-- Dependencies: 312
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- TOC entry 5863 (class 0 OID 19403)
-- Dependencies: 314
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- TOC entry 5859 (class 0 OID 19383)
-- Dependencies: 310
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add user	4	add_user
14	Can change user	4	change_user
15	Can delete user	4	delete_user
16	Can view user	4	view_user
17	Can add content type	5	add_contenttype
18	Can change content type	5	change_contenttype
19	Can delete content type	5	delete_contenttype
20	Can view content type	5	view_contenttype
21	Can add session	6	add_session
22	Can change session	6	change_session
23	Can delete session	6	delete_session
24	Can view session	6	view_session
\.


--
-- TOC entry 5865 (class 0 OID 19412)
-- Dependencies: 316
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
1	pbkdf2_sha256$870000$FXzBxjMtZFvUQPGWNQd3X0$Vg7eYNHhwHJQsIndZkY2x60bT9I4Baq8GqrCDOnksLU=	2025-10-17 03:11:54.415776-04	t	mirkof			mirkof@fetalmedical.com	t	t	2025-10-17 03:09:19.05209-04
\.


--
-- TOC entry 5867 (class 0 OID 19431)
-- Dependencies: 318
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- TOC entry 5869 (class 0 OID 19440)
-- Dependencies: 320
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- TOC entry 5815 (class 0 OID 18256)
-- Dependencies: 250
-- Data for Name: biometria_fetal; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.biometria_fetal (id, ecografia_id, diametro_biparietal, diametro_biparietal_percentil, circunferencia_cefalica, circunferencia_cefalica_percentil, circunferencia_abdominal, circunferencia_abdominal_percentil, longitud_femur, longitud_femur_percentil, longitud_humero, peso_fetal_estimado, peso_fetal_percentil, edad_gestacional_biometrica, observaciones) FROM stdin;
1	1	70.50	\N	260.00	\N	240.00	\N	52.00	\N	\N	0.00	\N	\N	\N
2	2	70.50	\N	260.00	\N	240.00	\N	52.00	\N	\N	1175.00	\N	\N	\N
\.


--
-- TOC entry 5811 (class 0 OID 18182)
-- Dependencies: 246
-- Data for Name: calculos_obstetricos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.calculos_obstetricos (id, control_prenatal_id, paciente_id, embarazo_id, tipo_calculo, datos_entrada, resultado, interpretacion, recomendacion, fecha_calculo, calculado_por) FROM stdin;
\.


--
-- TOC entry 5827 (class 0 OID 18417)
-- Dependencies: 262
-- Data for Name: citas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.citas (id, uuid, paciente_id, embarazo_id, medico_id, fecha_hora, duracion_minutos, tipo_cita, motivo, estado, observaciones, creada_por, fecha_creacion, fecha_actualizacion) FROM stdin;
\.


--
-- TOC entry 5845 (class 0 OID 19162)
-- Dependencies: 291
-- Data for Name: configuraciones_sistema; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.configuraciones_sistema (id, clave, valor, tipo_dato, categoria, descripcion, editable, fecha_creacion, fecha_actualizacion, actualizado_por) FROM stdin;
1	nombre_sistema	Fetal Medical - Sistema de Historias Clínicas	texto	general	Nombre del sistema para mostrar en interfaz	t	2025-10-15 12:44:56.888725	2025-10-15 12:44:56.888725	\N
2	version_sistema	1.0.0	texto	general	Versión actual del sistema	t	2025-10-15 12:44:56.888725	2025-10-15 12:44:56.888725	\N
3	dias_control_prenatal	30	numero	clinica	Días máximos entre controles prenatales	t	2025-10-15 12:44:56.888725	2025-10-15 12:44:56.888725	\N
9	prueba_config	valor_prueba	texto	test	Configuración de prueba	t	2025-10-15 17:28:16.111999	2025-10-15 17:29:18.735263	\N
\.


--
-- TOC entry 5795 (class 0 OID 17954)
-- Dependencies: 230
-- Data for Name: contactos_emergencia; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.contactos_emergencia (id, paciente_id, nombre_completo, parentesco, telefono, telefono_alternativo, es_contacto_principal) FROM stdin;
\.


--
-- TOC entry 5807 (class 0 OID 18104)
-- Dependencies: 242
-- Data for Name: controles_prenatales; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.controles_prenatales (id, uuid, embarazo_id, paciente_id, numero_control, fecha_control, semanas_gestacion, dias_gestacion, edad_gestacional_calculada, peso_actual, peso_pregestacional, ganancia_peso, talla, imc_actual, clasificacion_imc, presion_arterial_sistolica, presion_arterial_diastolica, presion_arterial_media, frecuencia_cardiaca, temperatura, altura_uterina, frecuencia_cardiaca_fetal, presentacion_fetal, movimientos_fetales, edema, proteinuria, observaciones, medico_id, enfermero_id, fecha_registro) FROM stdin;
1	3f697425-c1e3-4aac-9f4b-d0872010010d	1	1	1	2025-10-15	\N	\N	\N	66.50	65.00	1.50	165.00	24.43	Normal	115	75	88.33	\N	\N	\N	\N	\N	\N	\N	\N	\N	2	\N	2025-10-15 16:11:26.773768
2	2b30ef58-3a2c-4383-b7f3-9f8592da11b4	1	1	2	2025-10-15	\N	\N	\N	67.00	65.00	2.00	165.00	24.61	Normal	145	95	111.67	\N	\N	\N	\N	\N	\N	\N	\N	\N	2	\N	2025-10-15 16:11:52.473641
4	e6b107df-d24d-4ece-8c19-bac9847247d5	1	1	3	2025-10-15	\N	\N	\N	67.00	65.00	2.00	165.00	24.61	Normal	145	95	111.67	\N	\N	\N	\N	\N	\N	\N	\N	\N	2	\N	2025-10-15 16:25:14.623172
6	b91f1854-2678-425e-8c27-3c08f5e26a63	1	1	4	2025-10-15	\N	\N	\N	67.00	65.00	2.00	165.00	24.61	Normal	145	95	111.67	\N	\N	\N	\N	\N	\N	\N	\N	\N	2	\N	2025-10-15 17:30:16.639781
\.


--
-- TOC entry 5871 (class 0 OID 19501)
-- Dependencies: 322
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- TOC entry 5857 (class 0 OID 19371)
-- Dependencies: 308
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	auth	user
5	contenttypes	contenttype
6	sessions	session
\.


--
-- TOC entry 5855 (class 0 OID 19359)
-- Dependencies: 306
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2025-10-16 21:00:41.195688-04
2	auth	0001_initial	2025-10-16 21:00:41.263652-04
3	admin	0001_initial	2025-10-16 21:00:41.281534-04
4	admin	0002_logentry_remove_auto_add	2025-10-16 21:00:41.287941-04
5	admin	0003_logentry_add_action_flag_choices	2025-10-16 21:00:41.302212-04
6	contenttypes	0002_remove_content_type_name	2025-10-16 21:00:41.319863-04
7	auth	0002_alter_permission_name_max_length	2025-10-16 21:00:41.326068-04
8	auth	0003_alter_user_email_max_length	2025-10-16 21:00:41.332544-04
9	auth	0004_alter_user_username_opts	2025-10-16 21:00:41.337343-04
10	auth	0005_alter_user_last_login_null	2025-10-16 21:00:41.343639-04
11	auth	0006_require_contenttypes_0002	2025-10-16 21:00:41.345016-04
12	auth	0007_alter_validators_add_error_messages	2025-10-16 21:00:41.35005-04
13	auth	0008_alter_user_username_max_length	2025-10-16 21:00:41.361352-04
14	auth	0009_alter_user_last_name_max_length	2025-10-16 21:00:41.369831-04
15	auth	0010_alter_group_name_max_length	2025-10-16 21:00:41.377856-04
16	auth	0011_update_proxy_permissions	2025-10-16 21:00:41.383803-04
17	auth	0012_alter_user_first_name_max_length	2025-10-16 21:00:41.391928-04
18	sessions	0001_initial	2025-10-16 21:00:41.401154-04
\.


--
-- TOC entry 5872 (class 0 OID 19541)
-- Dependencies: 323
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
920ocgqs5rkbn18cta8jf1gknj1geb7i	.eJxVjMsOgjAQAP9lz6bp9kFbjt79BrLtLoKaklA4Gf_dkHDQ68xk3jDQvk3D3mQdZoYeEC6_LFN5Sj0EP6jeF1WWuq1zVkeiTtvUbWF5Xc_2bzBRm6CHHJwNonXyZHwXfXCCoXSxCMYuIqGLIonDWDwlStqOI1tGncmxsSbB5wvF-Dd_:1v9ed0:vYBCRza95dYZiNEXdZQaBqiWoLnDFQUxQ3BdL4KLyoQ	2025-10-31 03:11:54.424635-04
\.


--
-- TOC entry 5833 (class 0 OID 18554)
-- Dependencies: 268
-- Data for Name: documentos_paciente; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.documentos_paciente (id, paciente_id, tipo_documento, titulo, descripcion, ruta_archivo, tamano_kb, cargado_por, fecha_carga) FROM stdin;
\.


--
-- TOC entry 5813 (class 0 OID 18218)
-- Dependencies: 248
-- Data for Name: ecografias; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ecografias (id, uuid, paciente_id, embarazo_id, fecha_ecografia, tipo_ecografia, semanas_gestacion, dias_gestacion, edad_gestacional_eco, presentacion_fetal, posicion_fetal, numero_fetos, vitalidad_fetal, frecuencia_cardiaca_fetal, movimientos_fetales, tono_fetal, observaciones, medico_id, fecha_registro) FROM stdin;
1	756dc545-f42a-4822-9b18-f31906c60db1	1	1	2025-10-15	segundo_trimestre	\N	\N	\N	\N	\N	1	t	\N	\N	\N	\N	2	2025-10-15 16:13:35.294868
2	9c884f29-2d0b-4883-9028-233acd4cf19e	1	1	2025-10-15	segundo_trimestre	\N	\N	\N	\N	\N	1	t	\N	\N	\N	\N	2	2025-10-15 17:34:54.015483
\.


--
-- TOC entry 5805 (class 0 OID 18070)
-- Dependencies: 240
-- Data for Name: embarazos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.embarazos (id, uuid, paciente_id, numero_gesta, fecha_ultima_menstruacion, embarazo_confirmado_por, edad_gestacional_actual, tipo_embarazo, riesgo_embarazo, estado, resultado_final, fecha_finalizacion, observaciones, fecha_registro, medico_responsable) FROM stdin;
1	bce7d5f4-804e-4df6-9508-2141a31ad6f4	1	2	2024-10-01	ecografia	\N	simple	bajo	activo	\N	\N	\N	2025-10-15 16:10:55.193202	2
\.


--
-- TOC entry 5853 (class 0 OID 19271)
-- Dependencies: 299
-- Data for Name: historial_cambios_estado; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.historial_cambios_estado (id, tabla_afectada, registro_id, campo_afectado, valor_anterior, valor_nuevo, motivo_cambio, cambiado_por, fecha_cambio, ip_address) FROM stdin;
\.


--
-- TOC entry 5821 (class 0 OID 18325)
-- Dependencies: 256
-- Data for Name: imagenes_ecografia; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.imagenes_ecografia (id, ecografia_id, tipo_archivo, ruta_archivo, descripcion, fecha_carga, cargado_por) FROM stdin;
\.


--
-- TOC entry 5847 (class 0 OID 19186)
-- Dependencies: 293
-- Data for Name: notificaciones; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notificaciones (id, usuario_id, tipo_notificacion, titulo, mensaje, leida, accion_url, prioridad, fecha_envio, fecha_lectura, expiracion) FROM stdin;
3	2	alerta	Prueba notificación	Esta es una notificación de prueba	f	\N	normal	2025-10-15 17:29:22.758282	\N	\N
\.


--
-- TOC entry 5793 (class 0 OID 17922)
-- Dependencies: 228
-- Data for Name: pacientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pacientes (id, uuid, id_clinico, nombre, apellido_paterno, apellido_materno, fecha_nacimiento, genero, cedula_identidad, telefono_principal, telefono_emergencia, email, direccion, ciudad, zona, estado_civil, ocupacion, nivel_educativo, grupo_sanguineo, foto_paciente, activo, fecha_registro, registrado_por) FROM stdin;
1	c11a59df-f28f-48be-b9a1-b238002451ac	HC-25000001	Ana María	González	Rodríguez	1990-05-15	femenino	1234567 LP	+591-79999999	\N	ana.gonzalez@email.com	Calle Los Pinos #123, Zona Sur	La Paz	\N	casada	\N	\N	O+	\N	t	2025-10-15 16:06:57.547196	1
\.


--
-- TOC entry 5789 (class 0 OID 17881)
-- Dependencies: 224
-- Data for Name: permisos_especiales; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.permisos_especiales (id, usuario_id, modulo, accion, fecha_asignacion, asignado_por) FROM stdin;
\.


--
-- TOC entry 5849 (class 0 OID 19210)
-- Dependencies: 295
-- Data for Name: plantillas_documentos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.plantillas_documentos (id, nombre, tipo_documento, contenido, variables_disponibles, activa, creada_por, fecha_creacion, fecha_actualizacion) FROM stdin;
1	Consentimiento Informado	consentimiento	Yo, {nombre_paciente}, identificada con CI {cedula_paciente}, doy mi consentimiento informado para el procedimiento {procedimiento} después de haber recibido información completa sobre los riesgos, beneficios y alternativas.	["nombre_paciente", "cedula_paciente", "procedimiento", "fecha", "medico"]	t	\N	2025-10-15 12:44:56.888725	2025-10-15 12:44:56.888725
2	Informe Ecográfico Obstétrico	informe	INFORME ECOGRÁFICO OBSTÉTRICO\nPACIENTE: {nombre_paciente}\nEDAD GESTACIONAL: {edad_gestacional}\nFUM: {fecha_ultima_menstruacion}\nFPP: {fecha_probable_parto}\n\nHALLAZGOS:\n{hallazgos}\n\nCONCLUSIONES:\n{conclusiones}\n\nRECOMENDACIONES:\n{recomendaciones}\n\nMédico Tratante: {medico}\nFecha: {fecha_estudio}	["nombre_paciente", "edad_gestacional", "fecha_ultima_menstruacion", "fecha_probable_parto", "hallazgos", "conclusiones", "recomendaciones", "medico", "fecha_estudio"]	t	\N	2025-10-15 12:44:56.888725	2025-10-15 12:44:56.888725
\.


--
-- TOC entry 5839 (class 0 OID 18717)
-- Dependencies: 283
-- Data for Name: predicciones_riesgos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.predicciones_riesgos (id, paciente_id, embarazo_id, control_prenatal_id, tipo_riesgo, probabilidad, nivel_riesgo, factores_contribuyentes, recomendaciones, modelo_utilizado, fecha_prediccion) FROM stdin;
\.


--
-- TOC entry 5829 (class 0 OID 18460)
-- Dependencies: 264
-- Data for Name: recordatorios_citas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.recordatorios_citas (id, cita_id, tipo_recordatorio, fecha_envio, enviado, respuesta_paciente) FROM stdin;
\.


--
-- TOC entry 5831 (class 0 OID 18534)
-- Dependencies: 266
-- Data for Name: reportes_generados; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.reportes_generados (id, tipo_reporte, parametros, formato, ruta_archivo, generado_por, fecha_generacion) FROM stdin;
\.


--
-- TOC entry 5825 (class 0 OID 18391)
-- Dependencies: 260
-- Data for Name: resultados_laboratorio; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resultados_laboratorio (id, solicitud_id, fecha_resultado, parametro, valor, unidad, valor_referencia, estado, observaciones, archivo_resultado, ingresado_por, fecha_registro) FROM stdin;
\.


--
-- TOC entry 5851 (class 0 OID 19234)
-- Dependencies: 297
-- Data for Name: seguimiento_medicamentos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.seguimiento_medicamentos (id, paciente_id, embarazo_id, control_prenatal_id, medicamento, dosis, frecuencia, via_administracion, fecha_inicio, fecha_fin, indicacion, estado, efectos_secundarios, prescrito_por, fecha_registro) FROM stdin;
\.


--
-- TOC entry 5787 (class 0 OID 17861)
-- Dependencies: 222
-- Data for Name: sesiones; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sesiones (id, usuario_id, token_jwt, ip_address, dispositivo, navegador, fecha_inicio, fecha_expiracion, activa) FROM stdin;
\.


--
-- TOC entry 5835 (class 0 OID 18647)
-- Dependencies: 275
-- Data for Name: sistema_backups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sistema_backups (id, tipo_backup, ruta_archivo, tamano_mb, estado, mensaje_error, fecha_inicio, fecha_fin, realizado_por) FROM stdin;
\.


--
-- TOC entry 5823 (class 0 OID 18349)
-- Dependencies: 258
-- Data for Name: solicitudes_laboratorio; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.solicitudes_laboratorio (id, uuid, paciente_id, embarazo_id, control_prenatal_id, fecha_solicitud, tipo_examen, indicacion, urgente, estado, laboratorio_externo, solicitado_por, fecha_registro) FROM stdin;
\.


--
-- TOC entry 5843 (class 0 OID 19144)
-- Dependencies: 289
-- Data for Name: tablas_foraneas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tablas_foraneas (id, tabla_principal, tabla_referenciada, columna_foranea, accion_on_delete, accion_on_update, descripcion, fecha_registro) FROM stdin;
1	sesiones	usuarios	usuario_id	CASCADE	CASCADE	Sesiones pertenecen a usuarios	2025-10-15 12:44:56.888725
2	pacientes	usuarios	registrado_por	SET NULL	CASCADE	Paciente registrado por usuario	2025-10-15 12:44:56.888725
\.


--
-- TOC entry 5841 (class 0 OID 19129)
-- Dependencies: 287
-- Data for Name: tipos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tipos (id, categoria, nombre, valor, descripcion, activo, orden, fecha_creacion) FROM stdin;
1	tipo_documento	Cédula de Identidad	CI	Documento de identificación nacional	t	1	2025-10-15 12:44:56.888725
2	tipo_documento	Pasaporte	PASAPORTE	Pasaporte internacional	t	2	2025-10-15 12:44:56.888725
3	estado_civil	Soltera	soltera	Estado civil soltera	t	1	2025-10-15 12:44:56.888725
4	estado_civil	Casada	casada	Estado civil casada	t	2	2025-10-15 12:44:56.888725
\.


--
-- TOC entry 5785 (class 0 OID 17837)
-- Dependencies: 220
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id, uuid, email, password_hash, rol, nombre, apellido_paterno, apellido_materno, especialidad, matricula_profesional, telefono, foto_perfil, activo, ultimo_acceso, fecha_creacion, fecha_actualizacion) FROM stdin;
1	fd597328-7a58-441f-8383-fe5c7180c46a	admin@fetalmedical.com	$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5LZq.ZYK6nQ4u	administrador	Administrador	Sistema	Principal	\N	\N	\N	\N	t	\N	2025-10-15 02:14:11.806906	2025-10-15 02:14:11.806906
2	8e247c46-c562-4f09-b7d3-20fe4f3afc81	dr.perez@fetalmedical.com	$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5LZq.ZYK6nQ4u	medico	Juan Carlos	Pérez	López	Ginecología y Obstetricia	MAT-12345	+591-70123456	\N	t	\N	2025-10-15 16:04:21.574728	2025-10-15 16:04:21.574728
3	e4b8ac63-27b8-4028-a483-c00f84e3e9dd	enf.martinez@fetalmedical.com	$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5LZq.ZYK6nQ4u	enfermero	María Elena	Martínez	Flores	\N	\N	+591-71234567	\N	t	\N	2025-10-15 16:04:36.881316	2025-10-15 16:04:36.881316
\.


--
-- TOC entry 6006 (class 0 OID 0)
-- Dependencies: 243
-- Name: alertas_clinicas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.alertas_clinicas_id_seq', 3, true);


--
-- TOC entry 6007 (class 0 OID 0)
-- Dependencies: 280
-- Name: analisis_ia_ecografias_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.analisis_ia_ecografias_id_seq', 1, false);


--
-- TOC entry 6008 (class 0 OID 0)
-- Dependencies: 251
-- Name: anatomia_fetal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.anatomia_fetal_id_seq', 1, false);


--
-- TOC entry 6009 (class 0 OID 0)
-- Dependencies: 253
-- Name: anexos_fetales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.anexos_fetales_id_seq', 1, false);


--
-- TOC entry 6010 (class 0 OID 0)
-- Dependencies: 233
-- Name: antecedentes_familiares_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.antecedentes_familiares_id_seq', 1, false);


--
-- TOC entry 6011 (class 0 OID 0)
-- Dependencies: 235
-- Name: antecedentes_ginecologicos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.antecedentes_ginecologicos_id_seq', 1, true);


--
-- TOC entry 6012 (class 0 OID 0)
-- Dependencies: 237
-- Name: antecedentes_obstetricos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.antecedentes_obstetricos_id_seq', 1, true);


--
-- TOC entry 6013 (class 0 OID 0)
-- Dependencies: 231
-- Name: antecedentes_personales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.antecedentes_personales_id_seq', 1, false);


--
-- TOC entry 6014 (class 0 OID 0)
-- Dependencies: 225
-- Name: auditoria_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auditoria_id_seq', 55, true);


--
-- TOC entry 6015 (class 0 OID 0)
-- Dependencies: 311
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- TOC entry 6016 (class 0 OID 0)
-- Dependencies: 313
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- TOC entry 6017 (class 0 OID 0)
-- Dependencies: 309
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 24, true);


--
-- TOC entry 6018 (class 0 OID 0)
-- Dependencies: 317
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 1, false);


--
-- TOC entry 6019 (class 0 OID 0)
-- Dependencies: 315
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 1, true);


--
-- TOC entry 6020 (class 0 OID 0)
-- Dependencies: 319
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 1, false);


--
-- TOC entry 6021 (class 0 OID 0)
-- Dependencies: 249
-- Name: biometria_fetal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.biometria_fetal_id_seq', 2, true);


--
-- TOC entry 6022 (class 0 OID 0)
-- Dependencies: 245
-- Name: calculos_obstetricos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.calculos_obstetricos_id_seq', 1, false);


--
-- TOC entry 6023 (class 0 OID 0)
-- Dependencies: 261
-- Name: citas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.citas_id_seq', 1, false);


--
-- TOC entry 6024 (class 0 OID 0)
-- Dependencies: 290
-- Name: configuraciones_sistema_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.configuraciones_sistema_id_seq', 10, true);


--
-- TOC entry 6025 (class 0 OID 0)
-- Dependencies: 229
-- Name: contactos_emergencia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.contactos_emergencia_id_seq', 1, true);


--
-- TOC entry 6026 (class 0 OID 0)
-- Dependencies: 241
-- Name: controles_prenatales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.controles_prenatales_id_seq', 6, true);


--
-- TOC entry 6027 (class 0 OID 0)
-- Dependencies: 321
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- TOC entry 6028 (class 0 OID 0)
-- Dependencies: 307
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 6, true);


--
-- TOC entry 6029 (class 0 OID 0)
-- Dependencies: 305
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 18, true);


--
-- TOC entry 6030 (class 0 OID 0)
-- Dependencies: 267
-- Name: documentos_paciente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.documentos_paciente_id_seq', 1, false);


--
-- TOC entry 6031 (class 0 OID 0)
-- Dependencies: 247
-- Name: ecografias_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ecografias_id_seq', 2, true);


--
-- TOC entry 6032 (class 0 OID 0)
-- Dependencies: 239
-- Name: embarazos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.embarazos_id_seq', 2, true);


--
-- TOC entry 6033 (class 0 OID 0)
-- Dependencies: 298
-- Name: historial_cambios_estado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.historial_cambios_estado_id_seq', 1, false);


--
-- TOC entry 6034 (class 0 OID 0)
-- Dependencies: 255
-- Name: imagenes_ecografia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.imagenes_ecografia_id_seq', 1, false);


--
-- TOC entry 6035 (class 0 OID 0)
-- Dependencies: 292
-- Name: notificaciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notificaciones_id_seq', 3, true);


--
-- TOC entry 6036 (class 0 OID 0)
-- Dependencies: 227
-- Name: pacientes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pacientes_id_seq', 2, true);


--
-- TOC entry 6037 (class 0 OID 0)
-- Dependencies: 223
-- Name: permisos_especiales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.permisos_especiales_id_seq', 1, false);


--
-- TOC entry 6038 (class 0 OID 0)
-- Dependencies: 294
-- Name: plantillas_documentos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.plantillas_documentos_id_seq', 2, true);


--
-- TOC entry 6039 (class 0 OID 0)
-- Dependencies: 282
-- Name: predicciones_riesgos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.predicciones_riesgos_id_seq', 1, false);


--
-- TOC entry 6040 (class 0 OID 0)
-- Dependencies: 263
-- Name: recordatorios_citas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.recordatorios_citas_id_seq', 1, false);


--
-- TOC entry 6041 (class 0 OID 0)
-- Dependencies: 265
-- Name: reportes_generados_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.reportes_generados_id_seq', 1, false);


--
-- TOC entry 6042 (class 0 OID 0)
-- Dependencies: 259
-- Name: resultados_laboratorio_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.resultados_laboratorio_id_seq', 1, false);


--
-- TOC entry 6043 (class 0 OID 0)
-- Dependencies: 296
-- Name: seguimiento_medicamentos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.seguimiento_medicamentos_id_seq', 1, false);


--
-- TOC entry 6044 (class 0 OID 0)
-- Dependencies: 221
-- Name: sesiones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sesiones_id_seq', 1, false);


--
-- TOC entry 6045 (class 0 OID 0)
-- Dependencies: 274
-- Name: sistema_backups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sistema_backups_id_seq', 1, false);


--
-- TOC entry 6046 (class 0 OID 0)
-- Dependencies: 257
-- Name: solicitudes_laboratorio_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.solicitudes_laboratorio_id_seq', 1, false);


--
-- TOC entry 6047 (class 0 OID 0)
-- Dependencies: 288
-- Name: tablas_foraneas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tablas_foraneas_id_seq', 2, true);


--
-- TOC entry 6048 (class 0 OID 0)
-- Dependencies: 286
-- Name: tipos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tipos_id_seq', 4, true);


--
-- TOC entry 6049 (class 0 OID 0)
-- Dependencies: 219
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 3, true);


--
-- TOC entry 5385 (class 2606 OID 18160)
-- Name: alertas_clinicas alertas_clinicas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertas_clinicas
    ADD CONSTRAINT alertas_clinicas_pkey PRIMARY KEY (id);


--
-- TOC entry 5435 (class 2606 OID 18702)
-- Name: analisis_ia_ecografias analisis_ia_ecografias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analisis_ia_ecografias
    ADD CONSTRAINT analisis_ia_ecografias_pkey PRIMARY KEY (id);


--
-- TOC entry 5402 (class 2606 OID 18296)
-- Name: anatomia_fetal anatomia_fetal_ecografia_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anatomia_fetal
    ADD CONSTRAINT anatomia_fetal_ecografia_id_key UNIQUE (ecografia_id);


--
-- TOC entry 5404 (class 2606 OID 18294)
-- Name: anatomia_fetal anatomia_fetal_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anatomia_fetal
    ADD CONSTRAINT anatomia_fetal_pkey PRIMARY KEY (id);


--
-- TOC entry 5406 (class 2606 OID 18318)
-- Name: anexos_fetales anexos_fetales_ecografia_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos_fetales
    ADD CONSTRAINT anexos_fetales_ecografia_id_key UNIQUE (ecografia_id);


--
-- TOC entry 5408 (class 2606 OID 18316)
-- Name: anexos_fetales anexos_fetales_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos_fetales
    ADD CONSTRAINT anexos_fetales_pkey PRIMARY KEY (id);


--
-- TOC entry 5358 (class 2606 OID 18007)
-- Name: antecedentes_familiares antecedentes_familiares_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_familiares
    ADD CONSTRAINT antecedentes_familiares_pkey PRIMARY KEY (id);


--
-- TOC entry 5360 (class 2606 OID 18027)
-- Name: antecedentes_ginecologicos antecedentes_ginecologicos_paciente_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_ginecologicos
    ADD CONSTRAINT antecedentes_ginecologicos_paciente_id_key UNIQUE (paciente_id);


--
-- TOC entry 5362 (class 2606 OID 18025)
-- Name: antecedentes_ginecologicos antecedentes_ginecologicos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_ginecologicos
    ADD CONSTRAINT antecedentes_ginecologicos_pkey PRIMARY KEY (id);


--
-- TOC entry 5364 (class 2606 OID 18058)
-- Name: antecedentes_obstetricos antecedentes_obstetricos_paciente_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_obstetricos
    ADD CONSTRAINT antecedentes_obstetricos_paciente_id_key UNIQUE (paciente_id);


--
-- TOC entry 5366 (class 2606 OID 18056)
-- Name: antecedentes_obstetricos antecedentes_obstetricos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_obstetricos
    ADD CONSTRAINT antecedentes_obstetricos_pkey PRIMARY KEY (id);


--
-- TOC entry 5354 (class 2606 OID 17984)
-- Name: antecedentes_personales antecedentes_personales_paciente_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_personales
    ADD CONSTRAINT antecedentes_personales_paciente_id_key UNIQUE (paciente_id);


--
-- TOC entry 5356 (class 2606 OID 17982)
-- Name: antecedentes_personales antecedentes_personales_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_personales
    ADD CONSTRAINT antecedentes_personales_pkey PRIMARY KEY (id);


--
-- TOC entry 5335 (class 2606 OID 17915)
-- Name: auditoria auditoria_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_pkey PRIMARY KEY (id);


--
-- TOC entry 5496 (class 2606 OID 19537)
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- TOC entry 5501 (class 2606 OID 19458)
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- TOC entry 5504 (class 2606 OID 19410)
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 5498 (class 2606 OID 19399)
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- TOC entry 5491 (class 2606 OID 19449)
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- TOC entry 5493 (class 2606 OID 19391)
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- TOC entry 5512 (class 2606 OID 19438)
-- Name: auth_user_groups auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- TOC entry 5515 (class 2606 OID 19473)
-- Name: auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq UNIQUE (user_id, group_id);


--
-- TOC entry 5506 (class 2606 OID 19427)
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- TOC entry 5518 (class 2606 OID 19447)
-- Name: auth_user_user_permissions auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 5521 (class 2606 OID 19487)
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq UNIQUE (user_id, permission_id);


--
-- TOC entry 5509 (class 2606 OID 19530)
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- TOC entry 5398 (class 2606 OID 18267)
-- Name: biometria_fetal biometria_fetal_ecografia_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.biometria_fetal
    ADD CONSTRAINT biometria_fetal_ecografia_id_key UNIQUE (ecografia_id);


--
-- TOC entry 5400 (class 2606 OID 18265)
-- Name: biometria_fetal biometria_fetal_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.biometria_fetal
    ADD CONSTRAINT biometria_fetal_pkey PRIMARY KEY (id);


--
-- TOC entry 5389 (class 2606 OID 18196)
-- Name: calculos_obstetricos calculos_obstetricos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calculos_obstetricos
    ADD CONSTRAINT calculos_obstetricos_pkey PRIMARY KEY (id);


--
-- TOC entry 5420 (class 2606 OID 18436)
-- Name: citas citas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.citas
    ADD CONSTRAINT citas_pkey PRIMARY KEY (id);


--
-- TOC entry 5422 (class 2606 OID 18438)
-- Name: citas citas_uuid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.citas
    ADD CONSTRAINT citas_uuid_key UNIQUE (uuid);


--
-- TOC entry 5455 (class 2606 OID 19179)
-- Name: configuraciones_sistema configuraciones_sistema_clave_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configuraciones_sistema
    ADD CONSTRAINT configuraciones_sistema_clave_key UNIQUE (clave);


--
-- TOC entry 5457 (class 2606 OID 19177)
-- Name: configuraciones_sistema configuraciones_sistema_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configuraciones_sistema
    ADD CONSTRAINT configuraciones_sistema_pkey PRIMARY KEY (id);


--
-- TOC entry 5352 (class 2606 OID 17964)
-- Name: contactos_emergencia contactos_emergencia_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contactos_emergencia
    ADD CONSTRAINT contactos_emergencia_pkey PRIMARY KEY (id);


--
-- TOC entry 5376 (class 2606 OID 18120)
-- Name: controles_prenatales controles_prenatales_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles_prenatales
    ADD CONSTRAINT controles_prenatales_pkey PRIMARY KEY (id);


--
-- TOC entry 5378 (class 2606 OID 18122)
-- Name: controles_prenatales controles_prenatales_uuid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles_prenatales
    ADD CONSTRAINT controles_prenatales_uuid_key UNIQUE (uuid);


--
-- TOC entry 5524 (class 2606 OID 19514)
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- TOC entry 5486 (class 2606 OID 19381)
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- TOC entry 5488 (class 2606 OID 19379)
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- TOC entry 5484 (class 2606 OID 19369)
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- TOC entry 5528 (class 2606 OID 19550)
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- TOC entry 5431 (class 2606 OID 18567)
-- Name: documentos_paciente documentos_paciente_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documentos_paciente
    ADD CONSTRAINT documentos_paciente_pkey PRIMARY KEY (id);


--
-- TOC entry 5391 (class 2606 OID 18237)
-- Name: ecografias ecografias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ecografias
    ADD CONSTRAINT ecografias_pkey PRIMARY KEY (id);


--
-- TOC entry 5393 (class 2606 OID 18239)
-- Name: ecografias ecografias_uuid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ecografias
    ADD CONSTRAINT ecografias_uuid_key UNIQUE (uuid);


--
-- TOC entry 5368 (class 2606 OID 18090)
-- Name: embarazos embarazos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.embarazos
    ADD CONSTRAINT embarazos_pkey PRIMARY KEY (id);


--
-- TOC entry 5370 (class 2606 OID 18092)
-- Name: embarazos embarazos_uuid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.embarazos
    ADD CONSTRAINT embarazos_uuid_key UNIQUE (uuid);


--
-- TOC entry 5479 (class 2606 OID 19283)
-- Name: historial_cambios_estado historial_cambios_estado_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historial_cambios_estado
    ADD CONSTRAINT historial_cambios_estado_pkey PRIMARY KEY (id);


--
-- TOC entry 5410 (class 2606 OID 18337)
-- Name: imagenes_ecografia imagenes_ecografia_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.imagenes_ecografia
    ADD CONSTRAINT imagenes_ecografia_pkey PRIMARY KEY (id);


--
-- TOC entry 5465 (class 2606 OID 19203)
-- Name: notificaciones notificaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones
    ADD CONSTRAINT notificaciones_pkey PRIMARY KEY (id);


--
-- TOC entry 5344 (class 2606 OID 17947)
-- Name: pacientes pacientes_cedula_identidad_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pacientes
    ADD CONSTRAINT pacientes_cedula_identidad_key UNIQUE (cedula_identidad);


--
-- TOC entry 5346 (class 2606 OID 17945)
-- Name: pacientes pacientes_id_clinico_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pacientes
    ADD CONSTRAINT pacientes_id_clinico_key UNIQUE (id_clinico);


--
-- TOC entry 5348 (class 2606 OID 17941)
-- Name: pacientes pacientes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pacientes
    ADD CONSTRAINT pacientes_pkey PRIMARY KEY (id);


--
-- TOC entry 5350 (class 2606 OID 17943)
-- Name: pacientes pacientes_uuid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pacientes
    ADD CONSTRAINT pacientes_uuid_key UNIQUE (uuid);


--
-- TOC entry 5333 (class 2606 OID 17892)
-- Name: permisos_especiales permisos_especiales_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permisos_especiales
    ADD CONSTRAINT permisos_especiales_pkey PRIMARY KEY (id);


--
-- TOC entry 5469 (class 2606 OID 19227)
-- Name: plantillas_documentos plantillas_documentos_nombre_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plantillas_documentos
    ADD CONSTRAINT plantillas_documentos_nombre_key UNIQUE (nombre);


--
-- TOC entry 5471 (class 2606 OID 19225)
-- Name: plantillas_documentos plantillas_documentos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plantillas_documentos
    ADD CONSTRAINT plantillas_documentos_pkey PRIMARY KEY (id);


--
-- TOC entry 5445 (class 2606 OID 18732)
-- Name: predicciones_riesgos predicciones_riesgos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predicciones_riesgos
    ADD CONSTRAINT predicciones_riesgos_pkey PRIMARY KEY (id);


--
-- TOC entry 5427 (class 2606 OID 18470)
-- Name: recordatorios_citas recordatorios_citas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recordatorios_citas
    ADD CONSTRAINT recordatorios_citas_pkey PRIMARY KEY (id);


--
-- TOC entry 5429 (class 2606 OID 18547)
-- Name: reportes_generados reportes_generados_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reportes_generados
    ADD CONSTRAINT reportes_generados_pkey PRIMARY KEY (id);


--
-- TOC entry 5418 (class 2606 OID 18405)
-- Name: resultados_laboratorio resultados_laboratorio_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resultados_laboratorio
    ADD CONSTRAINT resultados_laboratorio_pkey PRIMARY KEY (id);


--
-- TOC entry 5477 (class 2606 OID 19249)
-- Name: seguimiento_medicamentos seguimiento_medicamentos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seguimiento_medicamentos
    ADD CONSTRAINT seguimiento_medicamentos_pkey PRIMARY KEY (id);


--
-- TOC entry 5331 (class 2606 OID 17874)
-- Name: sesiones sesiones_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sesiones
    ADD CONSTRAINT sesiones_pkey PRIMARY KEY (id);


--
-- TOC entry 5433 (class 2606 OID 18659)
-- Name: sistema_backups sistema_backups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sistema_backups
    ADD CONSTRAINT sistema_backups_pkey PRIMARY KEY (id);


--
-- TOC entry 5414 (class 2606 OID 18367)
-- Name: solicitudes_laboratorio solicitudes_laboratorio_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitudes_laboratorio
    ADD CONSTRAINT solicitudes_laboratorio_pkey PRIMARY KEY (id);


--
-- TOC entry 5416 (class 2606 OID 18369)
-- Name: solicitudes_laboratorio solicitudes_laboratorio_uuid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitudes_laboratorio
    ADD CONSTRAINT solicitudes_laboratorio_uuid_key UNIQUE (uuid);


--
-- TOC entry 5453 (class 2606 OID 19160)
-- Name: tablas_foraneas tablas_foraneas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tablas_foraneas
    ADD CONSTRAINT tablas_foraneas_pkey PRIMARY KEY (id);


--
-- TOC entry 5449 (class 2606 OID 19142)
-- Name: tipos tipos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipos
    ADD CONSTRAINT tipos_pkey PRIMARY KEY (id);


--
-- TOC entry 5323 (class 2606 OID 17859)
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- TOC entry 5325 (class 2606 OID 17855)
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- TOC entry 5327 (class 2606 OID 17857)
-- Name: usuarios usuarios_uuid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_uuid_key UNIQUE (uuid);


--
-- TOC entry 5494 (class 1259 OID 19538)
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- TOC entry 5499 (class 1259 OID 19469)
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- TOC entry 5502 (class 1259 OID 19470)
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- TOC entry 5489 (class 1259 OID 19455)
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- TOC entry 5510 (class 1259 OID 19485)
-- Name: auth_user_groups_group_id_97559544; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_groups_group_id_97559544 ON public.auth_user_groups USING btree (group_id);


--
-- TOC entry 5513 (class 1259 OID 19484)
-- Name: auth_user_groups_user_id_6a12ed8b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_groups_user_id_6a12ed8b ON public.auth_user_groups USING btree (user_id);


--
-- TOC entry 5516 (class 1259 OID 19499)
-- Name: auth_user_user_permissions_permission_id_1fbb5f2c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_user_permissions_permission_id_1fbb5f2c ON public.auth_user_user_permissions USING btree (permission_id);


--
-- TOC entry 5519 (class 1259 OID 19498)
-- Name: auth_user_user_permissions_user_id_a95ead1b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_user_permissions_user_id_a95ead1b ON public.auth_user_user_permissions USING btree (user_id);


--
-- TOC entry 5507 (class 1259 OID 19531)
-- Name: auth_user_username_6821ab7c_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);


--
-- TOC entry 5522 (class 1259 OID 19525)
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- TOC entry 5525 (class 1259 OID 19526)
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- TOC entry 5526 (class 1259 OID 19552)
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- TOC entry 5529 (class 1259 OID 19551)
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- TOC entry 5386 (class 1259 OID 18628)
-- Name: idx_alertas_nivel_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_alertas_nivel_estado ON public.alertas_clinicas USING btree (nivel_urgencia, estado);


--
-- TOC entry 5387 (class 1259 OID 18627)
-- Name: idx_alertas_paciente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_alertas_paciente ON public.alertas_clinicas USING btree (paciente_id);


--
-- TOC entry 5436 (class 1259 OID 18713)
-- Name: idx_analisis_ia_ecografia; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_analisis_ia_ecografia ON public.analisis_ia_ecografias USING btree (ecografia_id);


--
-- TOC entry 5437 (class 1259 OID 18714)
-- Name: idx_analisis_ia_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_analisis_ia_fecha ON public.analisis_ia_ecografias USING btree (fecha_analisis);


--
-- TOC entry 5438 (class 1259 OID 18715)
-- Name: idx_analisis_ia_validado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_analisis_ia_validado ON public.analisis_ia_ecografias USING btree (validado_por_medico);


--
-- TOC entry 5336 (class 1259 OID 18623)
-- Name: idx_auditoria_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_auditoria_fecha ON public.auditoria USING btree (fecha_hora);


--
-- TOC entry 5337 (class 1259 OID 18624)
-- Name: idx_auditoria_modulo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_auditoria_modulo ON public.auditoria USING btree (modulo);


--
-- TOC entry 5338 (class 1259 OID 18622)
-- Name: idx_auditoria_usuario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_auditoria_usuario ON public.auditoria USING btree (usuario_id);


--
-- TOC entry 5423 (class 1259 OID 18618)
-- Name: idx_citas_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_citas_estado ON public.citas USING btree (estado);


--
-- TOC entry 5424 (class 1259 OID 18616)
-- Name: idx_citas_medico_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_citas_medico_fecha ON public.citas USING btree (medico_id, fecha_hora);


--
-- TOC entry 5425 (class 1259 OID 18617)
-- Name: idx_citas_paciente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_citas_paciente ON public.citas USING btree (paciente_id);


--
-- TOC entry 5458 (class 1259 OID 19294)
-- Name: idx_configuraciones_categoria; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_configuraciones_categoria ON public.configuraciones_sistema USING btree (categoria);


--
-- TOC entry 5459 (class 1259 OID 19293)
-- Name: idx_configuraciones_clave; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_configuraciones_clave ON public.configuraciones_sistema USING btree (clave);


--
-- TOC entry 5379 (class 1259 OID 18612)
-- Name: idx_controles_embarazo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_controles_embarazo ON public.controles_prenatales USING btree (embarazo_id);


--
-- TOC entry 5380 (class 1259 OID 18614)
-- Name: idx_controles_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_controles_fecha ON public.controles_prenatales USING btree (fecha_control);


--
-- TOC entry 5381 (class 1259 OID 18615)
-- Name: idx_controles_medico; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_controles_medico ON public.controles_prenatales USING btree (medico_id);


--
-- TOC entry 5382 (class 1259 OID 18613)
-- Name: idx_controles_paciente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_controles_paciente ON public.controles_prenatales USING btree (paciente_id);


--
-- TOC entry 5394 (class 1259 OID 18620)
-- Name: idx_ecografias_embarazo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ecografias_embarazo ON public.ecografias USING btree (embarazo_id);


--
-- TOC entry 5395 (class 1259 OID 18621)
-- Name: idx_ecografias_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ecografias_fecha ON public.ecografias USING btree (fecha_ecografia);


--
-- TOC entry 5396 (class 1259 OID 18619)
-- Name: idx_ecografias_paciente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ecografias_paciente ON public.ecografias USING btree (paciente_id);


--
-- TOC entry 5371 (class 1259 OID 18610)
-- Name: idx_embarazos_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_embarazos_estado ON public.embarazos USING btree (estado);


--
-- TOC entry 5372 (class 1259 OID 18611)
-- Name: idx_embarazos_medico; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_embarazos_medico ON public.embarazos USING btree (medico_responsable);


--
-- TOC entry 5373 (class 1259 OID 18609)
-- Name: idx_embarazos_paciente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_embarazos_paciente ON public.embarazos USING btree (paciente_id);


--
-- TOC entry 5480 (class 1259 OID 19307)
-- Name: idx_historial_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_historial_fecha ON public.historial_cambios_estado USING btree (fecha_cambio);


--
-- TOC entry 5481 (class 1259 OID 19306)
-- Name: idx_historial_registro; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_historial_registro ON public.historial_cambios_estado USING btree (registro_id);


--
-- TOC entry 5482 (class 1259 OID 19305)
-- Name: idx_historial_tabla; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_historial_tabla ON public.historial_cambios_estado USING btree (tabla_afectada);


--
-- TOC entry 5411 (class 1259 OID 18630)
-- Name: idx_laboratorio_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_laboratorio_estado ON public.solicitudes_laboratorio USING btree (estado);


--
-- TOC entry 5412 (class 1259 OID 18629)
-- Name: idx_laboratorio_paciente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_laboratorio_paciente ON public.solicitudes_laboratorio USING btree (paciente_id);


--
-- TOC entry 5472 (class 1259 OID 19302)
-- Name: idx_medicamentos_embarazo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_medicamentos_embarazo ON public.seguimiento_medicamentos USING btree (embarazo_id);


--
-- TOC entry 5473 (class 1259 OID 19303)
-- Name: idx_medicamentos_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_medicamentos_estado ON public.seguimiento_medicamentos USING btree (estado);


--
-- TOC entry 5474 (class 1259 OID 19304)
-- Name: idx_medicamentos_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_medicamentos_fecha ON public.seguimiento_medicamentos USING btree (fecha_inicio);


--
-- TOC entry 5475 (class 1259 OID 19301)
-- Name: idx_medicamentos_paciente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_medicamentos_paciente ON public.seguimiento_medicamentos USING btree (paciente_id);


--
-- TOC entry 5460 (class 1259 OID 19298)
-- Name: idx_notificaciones_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notificaciones_fecha ON public.notificaciones USING btree (fecha_envio);


--
-- TOC entry 5461 (class 1259 OID 19296)
-- Name: idx_notificaciones_leida; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notificaciones_leida ON public.notificaciones USING btree (leida);


--
-- TOC entry 5462 (class 1259 OID 19297)
-- Name: idx_notificaciones_prioridad; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notificaciones_prioridad ON public.notificaciones USING btree (prioridad);


--
-- TOC entry 5463 (class 1259 OID 19295)
-- Name: idx_notificaciones_usuario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notificaciones_usuario ON public.notificaciones USING btree (usuario_id);


--
-- TOC entry 5383 (class 1259 OID 18686)
-- Name: idx_numero_control_unico_por_embarazo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_numero_control_unico_por_embarazo ON public.controles_prenatales USING btree (embarazo_id, numero_control);


--
-- TOC entry 5339 (class 1259 OID 18608)
-- Name: idx_pacientes_activo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pacientes_activo ON public.pacientes USING btree (activo);


--
-- TOC entry 5340 (class 1259 OID 18605)
-- Name: idx_pacientes_cedula; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pacientes_cedula ON public.pacientes USING btree (cedula_identidad);


--
-- TOC entry 5341 (class 1259 OID 18606)
-- Name: idx_pacientes_id_clinico; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pacientes_id_clinico ON public.pacientes USING btree (id_clinico);


--
-- TOC entry 5342 (class 1259 OID 18607)
-- Name: idx_pacientes_nombre; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pacientes_nombre ON public.pacientes USING btree (nombre, apellido_paterno);


--
-- TOC entry 5466 (class 1259 OID 19300)
-- Name: idx_plantillas_activa; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_plantillas_activa ON public.plantillas_documentos USING btree (activa);


--
-- TOC entry 5467 (class 1259 OID 19299)
-- Name: idx_plantillas_tipo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_plantillas_tipo ON public.plantillas_documentos USING btree (tipo_documento);


--
-- TOC entry 5439 (class 1259 OID 18749)
-- Name: idx_predicciones_embarazo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_predicciones_embarazo ON public.predicciones_riesgos USING btree (embarazo_id);


--
-- TOC entry 5440 (class 1259 OID 18752)
-- Name: idx_predicciones_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_predicciones_fecha ON public.predicciones_riesgos USING btree (fecha_prediccion);


--
-- TOC entry 5441 (class 1259 OID 18751)
-- Name: idx_predicciones_nivel; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_predicciones_nivel ON public.predicciones_riesgos USING btree (nivel_riesgo);


--
-- TOC entry 5442 (class 1259 OID 18748)
-- Name: idx_predicciones_paciente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_predicciones_paciente ON public.predicciones_riesgos USING btree (paciente_id);


--
-- TOC entry 5443 (class 1259 OID 18750)
-- Name: idx_predicciones_tipo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_predicciones_tipo ON public.predicciones_riesgos USING btree (tipo_riesgo);


--
-- TOC entry 5328 (class 1259 OID 18626)
-- Name: idx_sesiones_activa; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sesiones_activa ON public.sesiones USING btree (activa);


--
-- TOC entry 5329 (class 1259 OID 18625)
-- Name: idx_sesiones_usuario; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sesiones_usuario ON public.sesiones USING btree (usuario_id);


--
-- TOC entry 5450 (class 1259 OID 19291)
-- Name: idx_tablas_foraneas_principal; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tablas_foraneas_principal ON public.tablas_foraneas USING btree (tabla_principal);


--
-- TOC entry 5451 (class 1259 OID 19292)
-- Name: idx_tablas_foraneas_referenciada; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tablas_foraneas_referenciada ON public.tablas_foraneas USING btree (tabla_referenciada);


--
-- TOC entry 5446 (class 1259 OID 19290)
-- Name: idx_tipos_activo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tipos_activo ON public.tipos USING btree (activo);


--
-- TOC entry 5447 (class 1259 OID 19289)
-- Name: idx_tipos_categoria; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tipos_categoria ON public.tipos USING btree (categoria);


--
-- TOC entry 5374 (class 1259 OID 18685)
-- Name: idx_un_embarazo_activo_por_paciente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_un_embarazo_activo_por_paciente ON public.embarazos USING btree (paciente_id) WHERE ((estado)::text = 'activo'::text);


--
-- TOC entry 5770 (class 2618 OID 18593)
-- Name: v_embarazos_activos _RETURN; Type: RULE; Schema: public; Owner: postgres
--

CREATE OR REPLACE VIEW public.v_embarazos_activos AS
 SELECT e.id AS embarazo_id,
    e.uuid AS embarazo_uuid,
    p.id AS paciente_id,
    (((((p.nombre)::text || ' '::text) || (p.apellido_paterno)::text) || ' '::text) || (COALESCE(p.apellido_materno, ''::character varying))::text) AS nombre_completo,
    p.cedula_identidad,
    e.fecha_ultima_menstruacion,
    public.calcular_fpp(e.fecha_ultima_menstruacion) AS fecha_probable_parto,
    e.edad_gestacional_actual,
    e.tipo_embarazo,
    e.riesgo_embarazo,
    (((u.nombre)::text || ' '::text) || (u.apellido_paterno)::text) AS medico_responsable,
    count(cp.id) AS total_controles
   FROM (((public.embarazos e
     JOIN public.pacientes p ON ((e.paciente_id = p.id)))
     LEFT JOIN public.usuarios u ON ((e.medico_responsable = u.id)))
     LEFT JOIN public.controles_prenatales cp ON ((e.id = cp.embarazo_id)))
  WHERE (((e.estado)::text = 'activo'::text) AND (p.activo = true))
  GROUP BY e.id, p.id, u.nombre, u.apellido_paterno;


--
-- TOC entry 5610 (class 2620 OID 18753)
-- Name: analisis_ia_ecografias trg_auditoria_analisis_ia; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_analisis_ia AFTER INSERT OR DELETE OR UPDATE ON public.analisis_ia_ecografias FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5608 (class 2620 OID 18637)
-- Name: citas trg_auditoria_citas; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_citas AFTER INSERT OR DELETE OR UPDATE ON public.citas FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5614 (class 2620 OID 19310)
-- Name: configuraciones_sistema trg_auditoria_configuraciones; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_configuraciones AFTER INSERT OR DELETE OR UPDATE ON public.configuraciones_sistema FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5606 (class 2620 OID 18634)
-- Name: controles_prenatales trg_auditoria_controles; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_controles AFTER INSERT OR DELETE OR UPDATE ON public.controles_prenatales FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5607 (class 2620 OID 18636)
-- Name: ecografias trg_auditoria_ecografias; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_ecografias AFTER INSERT OR DELETE OR UPDATE ON public.ecografias FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5605 (class 2620 OID 18633)
-- Name: embarazos trg_auditoria_embarazos; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_embarazos AFTER INSERT OR DELETE OR UPDATE ON public.embarazos FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5620 (class 2620 OID 19314)
-- Name: historial_cambios_estado trg_auditoria_historial_estado; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_historial_estado AFTER INSERT OR DELETE OR UPDATE ON public.historial_cambios_estado FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5619 (class 2620 OID 19313)
-- Name: seguimiento_medicamentos trg_auditoria_medicamentos; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_medicamentos AFTER INSERT OR DELETE OR UPDATE ON public.seguimiento_medicamentos FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5616 (class 2620 OID 19311)
-- Name: notificaciones trg_auditoria_notificaciones; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_notificaciones AFTER INSERT OR DELETE OR UPDATE ON public.notificaciones FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5603 (class 2620 OID 18632)
-- Name: pacientes trg_auditoria_pacientes; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_pacientes AFTER INSERT OR DELETE OR UPDATE ON public.pacientes FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5617 (class 2620 OID 19312)
-- Name: plantillas_documentos trg_auditoria_plantillas; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_plantillas AFTER INSERT OR DELETE OR UPDATE ON public.plantillas_documentos FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5611 (class 2620 OID 18754)
-- Name: predicciones_riesgos trg_auditoria_predicciones; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_predicciones AFTER INSERT OR DELETE OR UPDATE ON public.predicciones_riesgos FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5613 (class 2620 OID 19309)
-- Name: tablas_foraneas trg_auditoria_tablas_foraneas; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_tablas_foraneas AFTER INSERT OR DELETE OR UPDATE ON public.tablas_foraneas FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5612 (class 2620 OID 19308)
-- Name: tipos trg_auditoria_tipos; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_tipos AFTER INSERT OR DELETE OR UPDATE ON public.tipos FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5601 (class 2620 OID 18635)
-- Name: usuarios trg_auditoria_usuarios; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_auditoria_usuarios AFTER INSERT OR DELETE OR UPDATE ON public.usuarios FOR EACH ROW EXECUTE FUNCTION public.fn_auditoria_cambios();


--
-- TOC entry 5609 (class 2620 OID 18684)
-- Name: citas trg_citas_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_citas_timestamp BEFORE UPDATE ON public.citas FOR EACH ROW EXECUTE FUNCTION public.trg_actualizar_timestamp();


--
-- TOC entry 5615 (class 2620 OID 19315)
-- Name: configuraciones_sistema trg_configuraciones_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_configuraciones_timestamp BEFORE UPDATE ON public.configuraciones_sistema FOR EACH ROW EXECUTE FUNCTION public.trg_actualizar_timestamp();


--
-- TOC entry 5604 (class 2620 OID 18681)
-- Name: pacientes trg_pacientes_id_clinico; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_pacientes_id_clinico BEFORE INSERT ON public.pacientes FOR EACH ROW EXECUTE FUNCTION public.trg_generar_id_clinico();


--
-- TOC entry 5618 (class 2620 OID 19316)
-- Name: plantillas_documentos trg_plantillas_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_plantillas_timestamp BEFORE UPDATE ON public.plantillas_documentos FOR EACH ROW EXECUTE FUNCTION public.trg_actualizar_timestamp();


--
-- TOC entry 5602 (class 2620 OID 18683)
-- Name: usuarios trg_usuarios_timestamp; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_usuarios_timestamp BEFORE UPDATE ON public.usuarios FOR EACH ROW EXECUTE FUNCTION public.trg_actualizar_timestamp();


--
-- TOC entry 5549 (class 2606 OID 18161)
-- Name: alertas_clinicas alertas_clinicas_control_prenatal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertas_clinicas
    ADD CONSTRAINT alertas_clinicas_control_prenatal_id_fkey FOREIGN KEY (control_prenatal_id) REFERENCES public.controles_prenatales(id) ON DELETE CASCADE;


--
-- TOC entry 5550 (class 2606 OID 18171)
-- Name: alertas_clinicas alertas_clinicas_embarazo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertas_clinicas
    ADD CONSTRAINT alertas_clinicas_embarazo_id_fkey FOREIGN KEY (embarazo_id) REFERENCES public.embarazos(id) ON DELETE CASCADE;


--
-- TOC entry 5551 (class 2606 OID 18166)
-- Name: alertas_clinicas alertas_clinicas_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertas_clinicas
    ADD CONSTRAINT alertas_clinicas_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5552 (class 2606 OID 18176)
-- Name: alertas_clinicas alertas_clinicas_revisada_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertas_clinicas
    ADD CONSTRAINT alertas_clinicas_revisada_por_fkey FOREIGN KEY (revisada_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5579 (class 2606 OID 18703)
-- Name: analisis_ia_ecografias analisis_ia_ecografias_ecografia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analisis_ia_ecografias
    ADD CONSTRAINT analisis_ia_ecografias_ecografia_id_fkey FOREIGN KEY (ecografia_id) REFERENCES public.ecografias(id) ON DELETE CASCADE;


--
-- TOC entry 5580 (class 2606 OID 18708)
-- Name: analisis_ia_ecografias analisis_ia_ecografias_medico_validador_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.analisis_ia_ecografias
    ADD CONSTRAINT analisis_ia_ecografias_medico_validador_fkey FOREIGN KEY (medico_validador) REFERENCES public.usuarios(id);


--
-- TOC entry 5561 (class 2606 OID 18297)
-- Name: anatomia_fetal anatomia_fetal_ecografia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anatomia_fetal
    ADD CONSTRAINT anatomia_fetal_ecografia_id_fkey FOREIGN KEY (ecografia_id) REFERENCES public.ecografias(id) ON DELETE CASCADE;


--
-- TOC entry 5562 (class 2606 OID 18319)
-- Name: anexos_fetales anexos_fetales_ecografia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.anexos_fetales
    ADD CONSTRAINT anexos_fetales_ecografia_id_fkey FOREIGN KEY (ecografia_id) REFERENCES public.ecografias(id) ON DELETE CASCADE;


--
-- TOC entry 5538 (class 2606 OID 18008)
-- Name: antecedentes_familiares antecedentes_familiares_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_familiares
    ADD CONSTRAINT antecedentes_familiares_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5539 (class 2606 OID 18033)
-- Name: antecedentes_ginecologicos antecedentes_ginecologicos_actualizado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_ginecologicos
    ADD CONSTRAINT antecedentes_ginecologicos_actualizado_por_fkey FOREIGN KEY (actualizado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5540 (class 2606 OID 18028)
-- Name: antecedentes_ginecologicos antecedentes_ginecologicos_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_ginecologicos
    ADD CONSTRAINT antecedentes_ginecologicos_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5541 (class 2606 OID 18064)
-- Name: antecedentes_obstetricos antecedentes_obstetricos_actualizado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_obstetricos
    ADD CONSTRAINT antecedentes_obstetricos_actualizado_por_fkey FOREIGN KEY (actualizado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5542 (class 2606 OID 18059)
-- Name: antecedentes_obstetricos antecedentes_obstetricos_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_obstetricos
    ADD CONSTRAINT antecedentes_obstetricos_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5536 (class 2606 OID 17990)
-- Name: antecedentes_personales antecedentes_personales_actualizado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_personales
    ADD CONSTRAINT antecedentes_personales_actualizado_por_fkey FOREIGN KEY (actualizado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5537 (class 2606 OID 17985)
-- Name: antecedentes_personales antecedentes_personales_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.antecedentes_personales
    ADD CONSTRAINT antecedentes_personales_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5533 (class 2606 OID 17916)
-- Name: auditoria auditoria_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- TOC entry 5593 (class 2606 OID 19464)
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5594 (class 2606 OID 19459)
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5592 (class 2606 OID 19450)
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5595 (class 2606 OID 19479)
-- Name: auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5596 (class 2606 OID 19474)
-- Name: auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5597 (class 2606 OID 19493)
-- Name: auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5598 (class 2606 OID 19488)
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5560 (class 2606 OID 18268)
-- Name: biometria_fetal biometria_fetal_ecografia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.biometria_fetal
    ADD CONSTRAINT biometria_fetal_ecografia_id_fkey FOREIGN KEY (ecografia_id) REFERENCES public.ecografias(id) ON DELETE CASCADE;


--
-- TOC entry 5553 (class 2606 OID 18212)
-- Name: calculos_obstetricos calculos_obstetricos_calculado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calculos_obstetricos
    ADD CONSTRAINT calculos_obstetricos_calculado_por_fkey FOREIGN KEY (calculado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5554 (class 2606 OID 18197)
-- Name: calculos_obstetricos calculos_obstetricos_control_prenatal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calculos_obstetricos
    ADD CONSTRAINT calculos_obstetricos_control_prenatal_id_fkey FOREIGN KEY (control_prenatal_id) REFERENCES public.controles_prenatales(id) ON DELETE CASCADE;


--
-- TOC entry 5555 (class 2606 OID 18207)
-- Name: calculos_obstetricos calculos_obstetricos_embarazo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calculos_obstetricos
    ADD CONSTRAINT calculos_obstetricos_embarazo_id_fkey FOREIGN KEY (embarazo_id) REFERENCES public.embarazos(id) ON DELETE CASCADE;


--
-- TOC entry 5556 (class 2606 OID 18202)
-- Name: calculos_obstetricos calculos_obstetricos_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.calculos_obstetricos
    ADD CONSTRAINT calculos_obstetricos_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5571 (class 2606 OID 18454)
-- Name: citas citas_creada_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.citas
    ADD CONSTRAINT citas_creada_por_fkey FOREIGN KEY (creada_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5572 (class 2606 OID 18444)
-- Name: citas citas_embarazo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.citas
    ADD CONSTRAINT citas_embarazo_id_fkey FOREIGN KEY (embarazo_id) REFERENCES public.embarazos(id) ON DELETE SET NULL;


--
-- TOC entry 5573 (class 2606 OID 18449)
-- Name: citas citas_medico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.citas
    ADD CONSTRAINT citas_medico_id_fkey FOREIGN KEY (medico_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 5574 (class 2606 OID 18439)
-- Name: citas citas_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.citas
    ADD CONSTRAINT citas_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5584 (class 2606 OID 19180)
-- Name: configuraciones_sistema configuraciones_sistema_actualizado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configuraciones_sistema
    ADD CONSTRAINT configuraciones_sistema_actualizado_por_fkey FOREIGN KEY (actualizado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5535 (class 2606 OID 17965)
-- Name: contactos_emergencia contactos_emergencia_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contactos_emergencia
    ADD CONSTRAINT contactos_emergencia_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5545 (class 2606 OID 18123)
-- Name: controles_prenatales controles_prenatales_embarazo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles_prenatales
    ADD CONSTRAINT controles_prenatales_embarazo_id_fkey FOREIGN KEY (embarazo_id) REFERENCES public.embarazos(id) ON DELETE CASCADE;


--
-- TOC entry 5546 (class 2606 OID 18138)
-- Name: controles_prenatales controles_prenatales_enfermero_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles_prenatales
    ADD CONSTRAINT controles_prenatales_enfermero_id_fkey FOREIGN KEY (enfermero_id) REFERENCES public.usuarios(id);


--
-- TOC entry 5547 (class 2606 OID 18133)
-- Name: controles_prenatales controles_prenatales_medico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles_prenatales
    ADD CONSTRAINT controles_prenatales_medico_id_fkey FOREIGN KEY (medico_id) REFERENCES public.usuarios(id);


--
-- TOC entry 5548 (class 2606 OID 18128)
-- Name: controles_prenatales controles_prenatales_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.controles_prenatales
    ADD CONSTRAINT controles_prenatales_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5599 (class 2606 OID 19515)
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5600 (class 2606 OID 19520)
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 5577 (class 2606 OID 18573)
-- Name: documentos_paciente documentos_paciente_cargado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documentos_paciente
    ADD CONSTRAINT documentos_paciente_cargado_por_fkey FOREIGN KEY (cargado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5578 (class 2606 OID 18568)
-- Name: documentos_paciente documentos_paciente_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documentos_paciente
    ADD CONSTRAINT documentos_paciente_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5557 (class 2606 OID 18245)
-- Name: ecografias ecografias_embarazo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ecografias
    ADD CONSTRAINT ecografias_embarazo_id_fkey FOREIGN KEY (embarazo_id) REFERENCES public.embarazos(id) ON DELETE CASCADE;


--
-- TOC entry 5558 (class 2606 OID 18250)
-- Name: ecografias ecografias_medico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ecografias
    ADD CONSTRAINT ecografias_medico_id_fkey FOREIGN KEY (medico_id) REFERENCES public.usuarios(id);


--
-- TOC entry 5559 (class 2606 OID 18240)
-- Name: ecografias ecografias_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ecografias
    ADD CONSTRAINT ecografias_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5543 (class 2606 OID 18098)
-- Name: embarazos embarazos_medico_responsable_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.embarazos
    ADD CONSTRAINT embarazos_medico_responsable_fkey FOREIGN KEY (medico_responsable) REFERENCES public.usuarios(id);


--
-- TOC entry 5544 (class 2606 OID 18093)
-- Name: embarazos embarazos_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.embarazos
    ADD CONSTRAINT embarazos_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5591 (class 2606 OID 19284)
-- Name: historial_cambios_estado historial_cambios_estado_cambiado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historial_cambios_estado
    ADD CONSTRAINT historial_cambios_estado_cambiado_por_fkey FOREIGN KEY (cambiado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5563 (class 2606 OID 18343)
-- Name: imagenes_ecografia imagenes_ecografia_cargado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.imagenes_ecografia
    ADD CONSTRAINT imagenes_ecografia_cargado_por_fkey FOREIGN KEY (cargado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5564 (class 2606 OID 18338)
-- Name: imagenes_ecografia imagenes_ecografia_ecografia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.imagenes_ecografia
    ADD CONSTRAINT imagenes_ecografia_ecografia_id_fkey FOREIGN KEY (ecografia_id) REFERENCES public.ecografias(id) ON DELETE CASCADE;


--
-- TOC entry 5585 (class 2606 OID 19204)
-- Name: notificaciones notificaciones_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notificaciones
    ADD CONSTRAINT notificaciones_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 5534 (class 2606 OID 17948)
-- Name: pacientes pacientes_registrado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pacientes
    ADD CONSTRAINT pacientes_registrado_por_fkey FOREIGN KEY (registrado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5531 (class 2606 OID 17898)
-- Name: permisos_especiales permisos_especiales_asignado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permisos_especiales
    ADD CONSTRAINT permisos_especiales_asignado_por_fkey FOREIGN KEY (asignado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5532 (class 2606 OID 17893)
-- Name: permisos_especiales permisos_especiales_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permisos_especiales
    ADD CONSTRAINT permisos_especiales_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 5586 (class 2606 OID 19228)
-- Name: plantillas_documentos plantillas_documentos_creada_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plantillas_documentos
    ADD CONSTRAINT plantillas_documentos_creada_por_fkey FOREIGN KEY (creada_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5581 (class 2606 OID 18743)
-- Name: predicciones_riesgos predicciones_riesgos_control_prenatal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predicciones_riesgos
    ADD CONSTRAINT predicciones_riesgos_control_prenatal_id_fkey FOREIGN KEY (control_prenatal_id) REFERENCES public.controles_prenatales(id) ON DELETE SET NULL;


--
-- TOC entry 5582 (class 2606 OID 18738)
-- Name: predicciones_riesgos predicciones_riesgos_embarazo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predicciones_riesgos
    ADD CONSTRAINT predicciones_riesgos_embarazo_id_fkey FOREIGN KEY (embarazo_id) REFERENCES public.embarazos(id) ON DELETE CASCADE;


--
-- TOC entry 5583 (class 2606 OID 18733)
-- Name: predicciones_riesgos predicciones_riesgos_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.predicciones_riesgos
    ADD CONSTRAINT predicciones_riesgos_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5575 (class 2606 OID 18471)
-- Name: recordatorios_citas recordatorios_citas_cita_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recordatorios_citas
    ADD CONSTRAINT recordatorios_citas_cita_id_fkey FOREIGN KEY (cita_id) REFERENCES public.citas(id) ON DELETE CASCADE;


--
-- TOC entry 5576 (class 2606 OID 18548)
-- Name: reportes_generados reportes_generados_generado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reportes_generados
    ADD CONSTRAINT reportes_generados_generado_por_fkey FOREIGN KEY (generado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5569 (class 2606 OID 18411)
-- Name: resultados_laboratorio resultados_laboratorio_ingresado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resultados_laboratorio
    ADD CONSTRAINT resultados_laboratorio_ingresado_por_fkey FOREIGN KEY (ingresado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5570 (class 2606 OID 18406)
-- Name: resultados_laboratorio resultados_laboratorio_solicitud_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resultados_laboratorio
    ADD CONSTRAINT resultados_laboratorio_solicitud_id_fkey FOREIGN KEY (solicitud_id) REFERENCES public.solicitudes_laboratorio(id) ON DELETE CASCADE;


--
-- TOC entry 5587 (class 2606 OID 19260)
-- Name: seguimiento_medicamentos seguimiento_medicamentos_control_prenatal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seguimiento_medicamentos
    ADD CONSTRAINT seguimiento_medicamentos_control_prenatal_id_fkey FOREIGN KEY (control_prenatal_id) REFERENCES public.controles_prenatales(id) ON DELETE SET NULL;


--
-- TOC entry 5588 (class 2606 OID 19255)
-- Name: seguimiento_medicamentos seguimiento_medicamentos_embarazo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seguimiento_medicamentos
    ADD CONSTRAINT seguimiento_medicamentos_embarazo_id_fkey FOREIGN KEY (embarazo_id) REFERENCES public.embarazos(id) ON DELETE CASCADE;


--
-- TOC entry 5589 (class 2606 OID 19250)
-- Name: seguimiento_medicamentos seguimiento_medicamentos_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seguimiento_medicamentos
    ADD CONSTRAINT seguimiento_medicamentos_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5590 (class 2606 OID 19265)
-- Name: seguimiento_medicamentos seguimiento_medicamentos_prescrito_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seguimiento_medicamentos
    ADD CONSTRAINT seguimiento_medicamentos_prescrito_por_fkey FOREIGN KEY (prescrito_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5530 (class 2606 OID 17875)
-- Name: sesiones sesiones_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sesiones
    ADD CONSTRAINT sesiones_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 5565 (class 2606 OID 18380)
-- Name: solicitudes_laboratorio solicitudes_laboratorio_control_prenatal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitudes_laboratorio
    ADD CONSTRAINT solicitudes_laboratorio_control_prenatal_id_fkey FOREIGN KEY (control_prenatal_id) REFERENCES public.controles_prenatales(id) ON DELETE SET NULL;


--
-- TOC entry 5566 (class 2606 OID 18375)
-- Name: solicitudes_laboratorio solicitudes_laboratorio_embarazo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitudes_laboratorio
    ADD CONSTRAINT solicitudes_laboratorio_embarazo_id_fkey FOREIGN KEY (embarazo_id) REFERENCES public.embarazos(id) ON DELETE CASCADE;


--
-- TOC entry 5567 (class 2606 OID 18370)
-- Name: solicitudes_laboratorio solicitudes_laboratorio_paciente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitudes_laboratorio
    ADD CONSTRAINT solicitudes_laboratorio_paciente_id_fkey FOREIGN KEY (paciente_id) REFERENCES public.pacientes(id) ON DELETE CASCADE;


--
-- TOC entry 5568 (class 2606 OID 18385)
-- Name: solicitudes_laboratorio solicitudes_laboratorio_solicitado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitudes_laboratorio
    ADD CONSTRAINT solicitudes_laboratorio_solicitado_por_fkey FOREIGN KEY (solicitado_por) REFERENCES public.usuarios(id);


--
-- TOC entry 5878 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT USAGE ON SCHEMA public TO app_fetal_medical;


--
-- TOC entry 5879 (class 0 OID 0)
-- Dependencies: 340
-- Name: FUNCTION calcular_edad(fecha_nac date); Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON FUNCTION public.calcular_edad(fecha_nac date) FROM PUBLIC;
GRANT ALL ON FUNCTION public.calcular_edad(fecha_nac date) TO app_fetal_medical;


--
-- TOC entry 5880 (class 0 OID 0)
-- Dependencies: 339
-- Name: FUNCTION calcular_edad_gestacional(fum date, fecha_actual date); Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON FUNCTION public.calcular_edad_gestacional(fum date, fecha_actual date) FROM PUBLIC;
GRANT ALL ON FUNCTION public.calcular_edad_gestacional(fum date, fecha_actual date) TO app_fetal_medical;


--
-- TOC entry 5881 (class 0 OID 0)
-- Dependencies: 324
-- Name: FUNCTION calcular_fpp(fum date); Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON FUNCTION public.calcular_fpp(fum date) FROM PUBLIC;
GRANT ALL ON FUNCTION public.calcular_fpp(fum date) TO app_fetal_medical;


--
-- TOC entry 5882 (class 0 OID 0)
-- Dependencies: 343
-- Name: FUNCTION calcular_ganancia_peso(peso_actual numeric, peso_pregestacional numeric); Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON FUNCTION public.calcular_ganancia_peso(peso_actual numeric, peso_pregestacional numeric) FROM PUBLIC;
GRANT ALL ON FUNCTION public.calcular_ganancia_peso(peso_actual numeric, peso_pregestacional numeric) TO app_fetal_medical;


--
-- TOC entry 5883 (class 0 OID 0)
-- Dependencies: 342
-- Name: FUNCTION calcular_imc(peso numeric, altura numeric); Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON FUNCTION public.calcular_imc(peso numeric, altura numeric) FROM PUBLIC;
GRANT ALL ON FUNCTION public.calcular_imc(peso numeric, altura numeric) TO app_fetal_medical;


--
-- TOC entry 5884 (class 0 OID 0)
-- Dependencies: 329
-- Name: FUNCTION calcular_pam(sistolica integer, diastolica integer); Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON FUNCTION public.calcular_pam(sistolica integer, diastolica integer) FROM PUBLIC;
GRANT ALL ON FUNCTION public.calcular_pam(sistolica integer, diastolica integer) TO app_fetal_medical;


--
-- TOC entry 5889 (class 0 OID 0)
-- Dependencies: 344
-- Name: FUNCTION evaluar_riesgo_presion(sistolica integer, diastolica integer); Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON FUNCTION public.evaluar_riesgo_presion(sistolica integer, diastolica integer) FROM PUBLIC;
GRANT ALL ON FUNCTION public.evaluar_riesgo_presion(sistolica integer, diastolica integer) TO app_fetal_medical;


--
-- TOC entry 5890 (class 0 OID 0)
-- Dependencies: 341
-- Name: FUNCTION fn_auditoria_cambios(); Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON FUNCTION public.fn_auditoria_cambios() FROM PUBLIC;
GRANT ALL ON FUNCTION public.fn_auditoria_cambios() TO app_fetal_medical;


--
-- TOC entry 5894 (class 0 OID 0)
-- Dependencies: 347
-- Name: FUNCTION sp_registrar_ecografia_completa(p_paciente_id integer, p_embarazo_id integer, p_tipo_ecografia character varying, p_medico_id integer, p_dbp numeric, p_cc numeric, p_ca numeric, p_lf numeric); Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON FUNCTION public.sp_registrar_ecografia_completa(p_paciente_id integer, p_embarazo_id integer, p_tipo_ecografia character varying, p_medico_id integer, p_dbp numeric, p_cc numeric, p_ca numeric, p_lf numeric) FROM PUBLIC;
GRANT ALL ON FUNCTION public.sp_registrar_ecografia_completa(p_paciente_id integer, p_embarazo_id integer, p_tipo_ecografia character varying, p_medico_id integer, p_dbp numeric, p_cc numeric, p_ca numeric, p_lf numeric) TO app_fetal_medical;


--
-- TOC entry 5897 (class 0 OID 0)
-- Dependencies: 244
-- Name: TABLE alertas_clinicas; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.alertas_clinicas TO app_fetal_medical;


--
-- TOC entry 5899 (class 0 OID 0)
-- Dependencies: 243
-- Name: SEQUENCE alertas_clinicas_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.alertas_clinicas_id_seq TO app_fetal_medical;


--
-- TOC entry 5902 (class 0 OID 0)
-- Dependencies: 252
-- Name: TABLE anatomia_fetal; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.anatomia_fetal TO app_fetal_medical;


--
-- TOC entry 5904 (class 0 OID 0)
-- Dependencies: 251
-- Name: SEQUENCE anatomia_fetal_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.anatomia_fetal_id_seq TO app_fetal_medical;


--
-- TOC entry 5905 (class 0 OID 0)
-- Dependencies: 254
-- Name: TABLE anexos_fetales; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.anexos_fetales TO app_fetal_medical;


--
-- TOC entry 5907 (class 0 OID 0)
-- Dependencies: 253
-- Name: SEQUENCE anexos_fetales_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.anexos_fetales_id_seq TO app_fetal_medical;


--
-- TOC entry 5908 (class 0 OID 0)
-- Dependencies: 234
-- Name: TABLE antecedentes_familiares; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.antecedentes_familiares TO app_fetal_medical;


--
-- TOC entry 5910 (class 0 OID 0)
-- Dependencies: 233
-- Name: SEQUENCE antecedentes_familiares_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.antecedentes_familiares_id_seq TO app_fetal_medical;


--
-- TOC entry 5911 (class 0 OID 0)
-- Dependencies: 236
-- Name: TABLE antecedentes_ginecologicos; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.antecedentes_ginecologicos TO app_fetal_medical;


--
-- TOC entry 5913 (class 0 OID 0)
-- Dependencies: 235
-- Name: SEQUENCE antecedentes_ginecologicos_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.antecedentes_ginecologicos_id_seq TO app_fetal_medical;


--
-- TOC entry 5914 (class 0 OID 0)
-- Dependencies: 238
-- Name: TABLE antecedentes_obstetricos; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.antecedentes_obstetricos TO app_fetal_medical;


--
-- TOC entry 5916 (class 0 OID 0)
-- Dependencies: 237
-- Name: SEQUENCE antecedentes_obstetricos_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.antecedentes_obstetricos_id_seq TO app_fetal_medical;


--
-- TOC entry 5917 (class 0 OID 0)
-- Dependencies: 232
-- Name: TABLE antecedentes_personales; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.antecedentes_personales TO app_fetal_medical;


--
-- TOC entry 5919 (class 0 OID 0)
-- Dependencies: 231
-- Name: SEQUENCE antecedentes_personales_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.antecedentes_personales_id_seq TO app_fetal_medical;


--
-- TOC entry 5921 (class 0 OID 0)
-- Dependencies: 226
-- Name: TABLE auditoria; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.auditoria TO app_fetal_medical;


--
-- TOC entry 5923 (class 0 OID 0)
-- Dependencies: 225
-- Name: SEQUENCE auditoria_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.auditoria_id_seq TO app_fetal_medical;


--
-- TOC entry 5924 (class 0 OID 0)
-- Dependencies: 250
-- Name: TABLE biometria_fetal; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.biometria_fetal TO app_fetal_medical;


--
-- TOC entry 5926 (class 0 OID 0)
-- Dependencies: 249
-- Name: SEQUENCE biometria_fetal_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.biometria_fetal_id_seq TO app_fetal_medical;


--
-- TOC entry 5927 (class 0 OID 0)
-- Dependencies: 246
-- Name: TABLE calculos_obstetricos; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.calculos_obstetricos TO app_fetal_medical;


--
-- TOC entry 5929 (class 0 OID 0)
-- Dependencies: 245
-- Name: SEQUENCE calculos_obstetricos_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.calculos_obstetricos_id_seq TO app_fetal_medical;


--
-- TOC entry 5930 (class 0 OID 0)
-- Dependencies: 262
-- Name: TABLE citas; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.citas TO app_fetal_medical;


--
-- TOC entry 5932 (class 0 OID 0)
-- Dependencies: 261
-- Name: SEQUENCE citas_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.citas_id_seq TO app_fetal_medical;


--
-- TOC entry 5935 (class 0 OID 0)
-- Dependencies: 230
-- Name: TABLE contactos_emergencia; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.contactos_emergencia TO app_fetal_medical;


--
-- TOC entry 5937 (class 0 OID 0)
-- Dependencies: 229
-- Name: SEQUENCE contactos_emergencia_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.contactos_emergencia_id_seq TO app_fetal_medical;


--
-- TOC entry 5940 (class 0 OID 0)
-- Dependencies: 242
-- Name: TABLE controles_prenatales; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.controles_prenatales TO app_fetal_medical;


--
-- TOC entry 5942 (class 0 OID 0)
-- Dependencies: 241
-- Name: SEQUENCE controles_prenatales_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.controles_prenatales_id_seq TO app_fetal_medical;


--
-- TOC entry 5943 (class 0 OID 0)
-- Dependencies: 268
-- Name: TABLE documentos_paciente; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.documentos_paciente TO app_fetal_medical;


--
-- TOC entry 5945 (class 0 OID 0)
-- Dependencies: 267
-- Name: SEQUENCE documentos_paciente_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.documentos_paciente_id_seq TO app_fetal_medical;


--
-- TOC entry 5947 (class 0 OID 0)
-- Dependencies: 248
-- Name: TABLE ecografias; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.ecografias TO app_fetal_medical;


--
-- TOC entry 5949 (class 0 OID 0)
-- Dependencies: 247
-- Name: SEQUENCE ecografias_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.ecografias_id_seq TO app_fetal_medical;


--
-- TOC entry 5952 (class 0 OID 0)
-- Dependencies: 240
-- Name: TABLE embarazos; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.embarazos TO app_fetal_medical;


--
-- TOC entry 5954 (class 0 OID 0)
-- Dependencies: 239
-- Name: SEQUENCE embarazos_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.embarazos_id_seq TO app_fetal_medical;


--
-- TOC entry 5957 (class 0 OID 0)
-- Dependencies: 256
-- Name: TABLE imagenes_ecografia; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.imagenes_ecografia TO app_fetal_medical;


--
-- TOC entry 5959 (class 0 OID 0)
-- Dependencies: 255
-- Name: SEQUENCE imagenes_ecografia_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.imagenes_ecografia_id_seq TO app_fetal_medical;


--
-- TOC entry 5964 (class 0 OID 0)
-- Dependencies: 228
-- Name: TABLE pacientes; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.pacientes TO app_fetal_medical;


--
-- TOC entry 5966 (class 0 OID 0)
-- Dependencies: 227
-- Name: SEQUENCE pacientes_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.pacientes_id_seq TO app_fetal_medical;


--
-- TOC entry 5967 (class 0 OID 0)
-- Dependencies: 224
-- Name: TABLE permisos_especiales; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.permisos_especiales TO app_fetal_medical;


--
-- TOC entry 5969 (class 0 OID 0)
-- Dependencies: 223
-- Name: SEQUENCE permisos_especiales_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.permisos_especiales_id_seq TO app_fetal_medical;


--
-- TOC entry 5974 (class 0 OID 0)
-- Dependencies: 264
-- Name: TABLE recordatorios_citas; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.recordatorios_citas TO app_fetal_medical;


--
-- TOC entry 5976 (class 0 OID 0)
-- Dependencies: 263
-- Name: SEQUENCE recordatorios_citas_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.recordatorios_citas_id_seq TO app_fetal_medical;


--
-- TOC entry 5977 (class 0 OID 0)
-- Dependencies: 266
-- Name: TABLE reportes_generados; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.reportes_generados TO app_fetal_medical;


--
-- TOC entry 5979 (class 0 OID 0)
-- Dependencies: 265
-- Name: SEQUENCE reportes_generados_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.reportes_generados_id_seq TO app_fetal_medical;


--
-- TOC entry 5980 (class 0 OID 0)
-- Dependencies: 260
-- Name: TABLE resultados_laboratorio; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.resultados_laboratorio TO app_fetal_medical;


--
-- TOC entry 5982 (class 0 OID 0)
-- Dependencies: 259
-- Name: SEQUENCE resultados_laboratorio_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.resultados_laboratorio_id_seq TO app_fetal_medical;


--
-- TOC entry 5985 (class 0 OID 0)
-- Dependencies: 222
-- Name: TABLE sesiones; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.sesiones TO app_fetal_medical;


--
-- TOC entry 5987 (class 0 OID 0)
-- Dependencies: 221
-- Name: SEQUENCE sesiones_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.sesiones_id_seq TO app_fetal_medical;


--
-- TOC entry 5990 (class 0 OID 0)
-- Dependencies: 258
-- Name: TABLE solicitudes_laboratorio; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.solicitudes_laboratorio TO app_fetal_medical;


--
-- TOC entry 5992 (class 0 OID 0)
-- Dependencies: 257
-- Name: SEQUENCE solicitudes_laboratorio_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.solicitudes_laboratorio_id_seq TO app_fetal_medical;


--
-- TOC entry 5998 (class 0 OID 0)
-- Dependencies: 220
-- Name: TABLE usuarios; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.usuarios TO app_fetal_medical;


--
-- TOC entry 6000 (class 0 OID 0)
-- Dependencies: 219
-- Name: SEQUENCE usuarios_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.usuarios_id_seq TO app_fetal_medical;


--
-- TOC entry 6001 (class 0 OID 0)
-- Dependencies: 272
-- Name: TABLE v_alertas_criticas_pendientes; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.v_alertas_criticas_pendientes TO app_fetal_medical;


--
-- TOC entry 6002 (class 0 OID 0)
-- Dependencies: 273
-- Name: TABLE v_controles_completos; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.v_controles_completos TO app_fetal_medical;


--
-- TOC entry 6003 (class 0 OID 0)
-- Dependencies: 271
-- Name: TABLE v_embarazos_activos; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.v_embarazos_activos TO app_fetal_medical;


--
-- TOC entry 6004 (class 0 OID 0)
-- Dependencies: 270
-- Name: TABLE v_embarazos_con_fpp; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.v_embarazos_con_fpp TO app_fetal_medical;


--
-- TOC entry 6005 (class 0 OID 0)
-- Dependencies: 269
-- Name: TABLE v_pacientes_con_edad; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.v_pacientes_con_edad TO app_fetal_medical;


-- Completed on 2025-10-17 03:53:43

--
-- PostgreSQL database dump complete
--

\unrestrict 1BLFZaoBSCyoonfpWAxC3QOq8TNqZxrilXEnm9rseArMJd39qq27FzDR2iXKSfS

